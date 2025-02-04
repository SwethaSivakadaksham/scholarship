import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# Function to create database tables
def create_tables():
    conn = sqlite3.connect("scholarship_finder.db")
    cursor = conn.cursor()
    
    # User table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')

    # Student details table
    cursor.execute('''CREATE TABLE IF NOT EXISTS student_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        age INTEGER,
                        gender TEXT,
                        category TEXT,
                        percentage FLOAT,
                        FOREIGN KEY(username) REFERENCES users(username))''')

    # Scholarship table
    cursor.execute('''CREATE TABLE IF NOT EXISTS scholarships (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        min_percentage FLOAT,
                        category TEXT)''')

    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a user
def register_user(username, password):
    conn = sqlite3.connect("scholarship_finder.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

# Function to check login
def check_login(username, password):
    conn = sqlite3.connect("scholarship_finder.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    stored_password = cursor.fetchone()
    conn.close()
    
    if stored_password and stored_password[0] == hash_password(password):
        return True
    return False

# Function to save student details
def save_student_details(username, age, gender, category, percentage):
    conn = sqlite3.connect("scholarship_finder.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO student_details (username, age, gender, category, percentage) VALUES (?, ?, ?, ?, ?)", 
                   (username, age, gender, category, percentage))
    conn.commit()
    conn.close()

# Function to fetch eligible scholarships
def get_eligible_scholarships(username):
    conn = sqlite3.connect("scholarship_finder.db")
    cursor = conn.cursor()

    cursor.execute("SELECT category, percentage FROM student_details WHERE username = ?", (username,))
    user_details = cursor.fetchone()

    if user_details:
        category, percentage = user_details
        cursor.execute("SELECT name FROM scholarships WHERE category = ? AND min_percentage <= ?", (category, percentage))
        scholarships = cursor.fetchall()
        conn.close()
        return [sch[0] for sch in scholarships]
    
    conn.close()
    return []

# Initialize DB and insert some sample scholarships
def initialize_data():
    conn = sqlite3.connect("scholarship_finder.db")
    cursor = conn.cursor()

    sample_scholarships = [
        ("Merit Scholarship", 85, "General"),
        ("SC/ST Special Scholarship", 60, "SC/ST"),
        ("Girls Education Grant", 70, "Female"),
        ("Minority Scholarship", 75, "OBC"),
    ]

    cursor.executemany("INSERT INTO scholarships (name, min_percentage, category) VALUES (?, ?, ?)", sample_scholarships)
    conn.commit()
    conn.close()

# Streamlit App
st.set_page_config(page_title="Scholarship Finder", page_icon="🎓")

create_tables()
initialize_data()

st.title("🎓 Scholarship Finder")

# Sidebar for navigation
menu = ["Login", "Register", "Enter Details", "Find Scholarships"]
choice = st.sidebar.selectbox("Menu", menu)

# Session state to track user login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# Login Page
if choice == "Login":
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if check_login(username, password):
            st.success(f"Welcome, {username}!")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username

            # Check if the user has entered their details
            conn = sqlite3.connect("scholarship_finder.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student_details WHERE username = ?", (username,))
            student_details = cursor.fetchone()
            conn.close()

            # Redirect to Enter Details page if details are missing
            if not student_details:
                st.session_state["next_page"] = "Enter Details"
            else:
                st.session_state["next_page"] = "Find Scholarships"

            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# Register Page
elif choice == "Register":
    st.subheader("📝 Register")
    new_username = st.text_input("Choose a username")
    new_password = st.text_input("Choose a password", type="password")

    if st.button("Register"):
        if register_user(new_username, new_password):
            st.success("Account created! You can now log in.")
        else:
            st.error("Username already exists. Try a different one.")

# Enter Details Page
elif choice == "Enter Details":
    if st.session_state["logged_in"]:
        st.subheader("📝 Enter Student Details")
        
        age = st.number_input("Age", min_value=15, max_value=30)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        category = st.selectbox("Category", ["General", "SC/ST", "OBC", "EWS"])
        percentage = st.number_input("Percentage (%)", min_value=0.0, max_value=100.0)

        if st.button("Save Details"):
            save_student_details(st.session_state["username"], age, gender, category, percentage)
            st.success("Details saved successfully!")
            
            # Trigger page refresh to go to "Find Scholarships" page
            st.session_state["next_page"] = "Find Scholarships"
            st.experimental_rerun()
    else:
        st.warning("Please log in to enter details.")

# Scholarship Display Page
elif choice == "Find Scholarships":
    if st.session_state["logged_in"]:
        st.subheader("🎯 Eligible Scholarships")
        scholarships = get_eligible_scholarships(st.session_state["username"])
        
        if scholarships:
            st.success("You are eligible for the following scholarships:")
            for sch in scholarships:
                st.write(f"- {sch}")
        else:
            st.warning("No scholarships found for your criteria.")
    else:
        st.warning("Please log in to find scholarships.")
