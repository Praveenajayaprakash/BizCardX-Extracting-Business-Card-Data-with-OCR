import streamlit as st
import easyocr
from PIL import Image
import re
import numpy as np
import pandas as pd
import sqlite3

# Function to perform OCR on the uploaded image
def perform_ocr(import_image):
    try:
        reader = easyocr.Reader(['en'])
        image = Image.open(import_image)
        image_array = np.array(image)
        result = reader.readtext(image_array)
        return result
    except Exception as e:
        st.error(f"Error occurred during OCR: {e}")
        return None

# Function to create SQLite connection and table
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to SQLite database: {e}")
    return conn

def create_table(conn):
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS extracted_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            designation TEXT,
            company_name TEXT,
            contact TEXT,
            email TEXT,
            website TEXT,
            address TEXT,
            city TEXT,
            pincode TEXT,
            state TEXT
        );
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")

# Function to insert extracted data into SQLite
# Function to insert extracted data into SQLite
# Function to insert extracted data into SQLite
def insert_data(conn, data):
    sql = """
        INSERT INTO extracted_info (name, designation, company_name, contact, email, website, address, city, pincode, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cur = conn.cursor()

        # Check if the entry already exists
        cur.execute("SELECT * FROM extracted_info WHERE name = ? AND designation = ?", (data[0], data[1]))
        existing_entry = cur.fetchone()

        if existing_entry:
            st.warning("Duplicate entry detected. Data not inserted.")
            return None
        else:
            cur.execute(sql, data)
            conn.commit()
            st.success("Data inserted into SQLite database successfully!")
            return cur.lastrowid

    except sqlite3.Error as e:
        st.error(f"Error inserting data into SQLite database: {e}")
        return None


# Function to extract relevant information from OCR results
def extracted_text(texts):
    extrd_dict = {
        "NAME": [],
        "DESIGNATION": [],
        "COMPANY_NAME": [],
        "CONTACT": [],
        "EMAIL": [],
        "WEBSITE": [],
        "ADDRESS": [],
        "CITY": [],
        "PINCODE": [],
        "STATE": []
    }

    extrd_dict["NAME"].append(texts[0])
    extrd_dict["DESIGNATION"].append(texts[1])

    for i in range(2, len(texts)):
        if texts[i].startswith("+") or (texts[i].replace("-", "").isdigit() and '-' in texts[i]):
            extrd_dict["CONTACT"].append(texts[i])
        elif "@" in texts[i] and ".com" in texts[i]:
            small = texts[i].lower()
            extrd_dict["EMAIL"].append(small)
        elif any(prefix in texts[i].lower() for prefix in ("www", "http", "https")) and ".com" in texts[i]:
            small = texts[i].lower()
            extrd_dict["WEBSITE"].append(small)
        elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i]:
            extrd_dict["STATE"].append("TamilNadu")
        elif re.match(r'^\d{6}$', texts[i]):  # Match pin code with 6 digits
            extrd_dict["PINCODE"].append(texts[i])
        elif len(texts[i]) >= 6 and texts[i].isdigit():
            extrd_dict["PINCODE"].append(texts[i])
        elif re.findall("[a-zA-Z]{9} +[0-9]", texts[i]):
            extrd_dict["PINCODE"].append(texts[i][10:])
        elif re.search(r'St\.\s+(\w+)\s+TamilNadu', texts[i]):
            city = re.search(r'St\.\s+(\w+)\s+TamilNadu', texts[i]).group(1)
            extrd_dict["CITY"].append(city)
        elif re.match(r'^[A-Za-z]', texts[i]):
            extrd_dict["COMPANY_NAME"].append(texts[i])
            if extrd_dict["COMPANY_NAME"]:
              extrd_dict["COMPANY_NAME"] = [' '.join(extrd_dict["COMPANY_NAME"])]
        else:
            remove_colon = re.sub(r'[,;]', '', texts[i])
            extrd_dict["ADDRESS"].append(remove_colon)

    # Join contact information into a single string
    extrd_dict["CONTACT"] = [', '.join(extrd_dict["CONTACT"])]

    for key, value in extrd_dict.items():
        if len(value) == 0:
            extrd_dict[key] = ["NA"]

    return extrd_dict

def display_home():
    st.markdown(
        """
        <style>
            .big-font {
                font-size: 24px;
                font-weight: bold;
                color: #2f4f4f;
            }
            .info-box {
                background-color: #f0f8ff;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .marquee {
                color: #4682b4;
                font-size: 18px;
                white-space: nowrap;
                overflow: hidden;
                border: 1px solid #b0c4de;
                padding: 10px;
                border-radius: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    

    st.markdown("<p class='big-font'>Extracting Business Card Data with OCR</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='info-box'>
            <p><strong>About Bizcard:</strong></p>
            <p>Bizcard is a revolutionary platform for extracting information from business cards. It provides a convenient
            way for users to digitize business card data, making it easily accessible and searchable.</p>
            <p><strong>Uses of Bizcard:</strong></p>
            <ul>
                <li>Extracting Business Card Information</li>
                <li>Managing Contact Details</li>
                <li>Digitizing Networking Efforts</li>
            </ul>
            <p>Explore Bizcard Pulse to understand the dynamics of business card data and improve user experiences.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        Bizcard Pulse is a revolutionary project designed to offer comprehensive insights into business card data and trends.
        Explore the data to gain valuable information about contact details, networking patterns, and much more.
    """)



def main():
    # Create a connection to SQLite database
    conn = create_connection("extracted_info.db")
    if conn is not None:
        # Create table if not exists
        create_table(conn)

    # Define the options for the main menu
    main_options = ("Home", "Upload & Extract", "Delete")

    # Use option menus for all sections
    with st.sidebar:
        select = st.selectbox("Main Menu", main_options)

    if select == "Home":
        image_url1 = "data:image/jpeg;base64,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"
        st.sidebar.image(image_url1, caption='PhonePe- Easy Pay', use_column_width=True)
        display_home()
    elif select== "Upload & Extract":
        st.markdown("### Upload a Business Card")
        uploaded_card = st.file_uploader("Upload here", type=["png", "jpeg", "jpg"])

        if uploaded_card is not None:
            image = Image.open(uploaded_card)
            st.image(image, caption='Uploaded Business Card', use_column_width=True)

            # Perform OCR on the uploaded image
            result = perform_ocr(uploaded_card)

            if result:
                # Extract text from the OCR result
                text_result = [text[1] for text in result]
                st.success("### Data Extracted!")
                extracted_info = extracted_text(text_result)  
                df = pd.DataFrame(extracted_info)
                st.write("Extracted Information:")
                st.write(df)

                # Insert data into SQLite
                if conn is not None:
                    with conn:
                        data = (
                            extracted_info["NAME"][0],
                            extracted_info["DESIGNATION"][0],
                            extracted_info["COMPANY_NAME"][0],
                            extracted_info["CONTACT"][0],
                            extracted_info["EMAIL"][0],
                            extracted_info["WEBSITE"][0],
                            extracted_info["ADDRESS"][0],
                            extracted_info["CITY"][0],
                            extracted_info["PINCODE"][0],
                            extracted_info["STATE"][0]
                        )
                        insert_data(conn, data)
                        
                        # Query the database to retrieve inserted data
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM extracted_info")
                        rows = cursor.fetchall()
                        if rows:
                            st.write("Data in SQLite Database:")
                            df_sqlite = pd.DataFrame(rows, columns=["ID", "Name", "Designation", "Company Name", "Contact", "Email", "Website", "Address", "City", "Pincode", "State"])
                            st.write(df_sqlite)

            else:
                st.error("Error occurred during OCR, please try again.")

    elif select == "Delete":
        st.title("Manage Extracted Data")
        st.sidebar.subheader("Options")
        
        # Check if there is data available for deletion
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM extracted_info")
            rows = cursor.fetchall()
            if rows:
                # Define options for deletion section
                delete_options = ("View Data", "Delete Entry")
                # Use option menu for selection
                selection = st.sidebar.selectbox("View Data or Delete Entry", delete_options)
            else:
                selection = "View Data"
        else:
            selection = "View Data"

        if selection == "View Data":
            st.subheader("View Extracted Data")
            if conn is not None:
                # Query the database to retrieve all data
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM extracted_info")
                rows = cursor.fetchall()
                if rows:
                    df_sqlite = pd.DataFrame(rows, columns=["ID", "Name", "Designation", "Company Name", "Contact", "Email", "Website", "Address", "City", "Pincode", "State"])
                    st.write(df_sqlite)
                else:
                    st.write("No data available in SQLite database.")

        elif selection == "Delete Entry":
            st.subheader("Delete Specific Entry")
            # Display dropdown menu to select entry for deletion
            if conn is not None:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM extracted_info")
                rows = cursor.fetchall()
                entries = [f"{row[0]} - {row[1]}" for row in rows]  # Display ID and Name for each entry
                selected_entry = st.selectbox("Select entry to delete", entries)

                if st.button("Delete"):
                    selected_id = int(selected_entry.split(" - ")[0])
                    cursor.execute("DELETE FROM extracted_info WHERE id=?", (selected_id,))
                    conn.commit()
                    st.success("Entry deleted successfully.")

if __name__ == "__main__":
    st.set_page_config(page_title="Bizcard OCR App", layout="wide")
    scrolling_text = "<h1 style='color:red; font-style: italic; font-weight: bold;'>Welcome to Bizcard OCR App</marquee></h1>"
    st.markdown(scrolling_text, unsafe_allow_html=True)
    main()








