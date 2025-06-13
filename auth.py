import streamlit as st
import hashlib
import re
import secrets
from datetime import datetime

# Function to handle user signup
# This function checks if the email already exists, hashes the password, and stores the user information in the database.
def signup(email, password, user_type, name, db, age=None):
    try:
        # Get users collection
        users_collection = db["users"]
        
        # Check if email already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            st.session_state.auth_status = {
                "message": "This email is already registered. Please use a different email or try logging in.",
                "type": "error"
            }
            return False
            
        # Generate a user ID
        user_id = secrets.token_hex(16)
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Prepare user document for MongoDB
        user_document = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "user_type": user_type,
            "created_at": datetime.now()
        }
        
        # Add age if provided (for child users)
        if age is not None:
            user_document["age"] = age
        
        # Insert user document into MongoDB collection
        users_collection.insert_one(user_document)
        
        # Set auth status for signup success
        st.session_state.auth_status = {
            "message": "Account created successfully! Please log in with your new credentials.",
            "type": "success"
        }
        
        return True
        
    except Exception as e:
        st.session_state.auth_status = {
            "message": f"Signup failed: {str(e)}",
            "type": "error"
        }
        return False
    
# Function to handle user login
# This function checks the user's credentials against the database and sets session state variables accordingly.
def login(email, password, db):
    try:
        # Get users collection
        users_collection = db["users"]

        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Query user by email and password hash
        user = users_collection.find_one({
            "email": email,
            "password_hash": password_hash
        })
        
        if not user:
            st.session_state.auth_status = {
                "message": "Invalid email or password. Please try again.",
                "type": "error"
            }
            return False
        
        # Convert MongoDB document to dictionary for session state
        # Exclude _id field (MongoDB ObjectId) as it's not JSON serializable
        user_data = {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"], 
            "user_type": user["user_type"],
            "age": user.get("age")  # Use get() to handle case when age might not exist
        }
        
        # Set session state
        st.session_state.logged_in = True
        st.session_state.user_info = user_data
        st.session_state.auth_status = {
            "message": f"Welcome back, {user_data['name']}!",
            "type": "success"
        }
        
        return True
        
    except Exception as e:
        st.session_state.auth_status = {
            "message": f"Login failed: {str(e)}",
            "type": "error"
        }
        return False

# Function to display status message
def display_status_message():
    if st.session_state.auth_status["message"]:
        if st.session_state.auth_status["type"] == "success":
            st.success(st.session_state.auth_status["message"])
        elif st.session_state.auth_status["type"] == "error":
            st.error(st.session_state.auth_status["message"])
        elif st.session_state.auth_status["type"] == "info":
            st.info(st.session_state.auth_status["message"])
        elif st.session_state.auth_status["type"] == "warning":
            st.warning(st.session_state.auth_status["message"])

# Function to validate email format
# This function uses a regex pattern to check if the email is valid.
def is_valid_email(email):

    # Regular expression pattern for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Check if the email matches the pattern
    if re.match(pattern, email):
        return True
    
    return False

# Function to handle logout
# This function resets the session state variables related to authentication.
def logout():
    st.session_state.logged_in = False
    st.session_state.user_info = {}
    st.session_state.auth_status = {
        "message": "You have been logged out successfully.",
        "type": "info"
    }

# Function to display login/signup page
def display_auth_page(db):
    st.title("ASD Therapy Assistant")
    
    # Display any status messages at the top
    display_status_message()
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # Login tab
    with tab1:
        st.subheader("Login to Your Account")
        
        login_email = st.text_input("Email", key="login_email", placeholder="Enter your email")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        login_button = st.button("Login", key="login_button", use_container_width=True)
        
        if login_button:
            if login_email and login_password:
                if login(login_email, login_password, db):
                    st.rerun()
            else:  
                st.session_state.auth_status = {
                    "message": "Please fill in both email and password fields.",
                    "type": "warning"
                }
                st.rerun()
    
    # Sign Up tab
    with tab2:
        st.subheader("Create a New Account")
        
        # User type selection with more visual appeal
        user_type_options = ["Child", "Staff"]
        user_type_index = st.radio(
            "I am a:",
            options=range(len(user_type_options)),
            format_func=lambda x: user_type_options[x],
            key="user_type_radio",
            horizontal=True
        )
        user_type = user_type_options[user_type_index].lower()  # Convert to lowercase for database consistency
        
        # Common fields
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", key="signup_name", placeholder="Enter your full name")
        with col2:
            email = st.text_input("Email", key="signup_email", placeholder="Enter your email address")
        
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password (min 6 characters)")
        with col2:
            password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm", placeholder="Confirm your password")
        
        # Additional fields for children
        age = None
        if user_type == "child":
            age = st.number_input("Age", min_value=3, max_value=18, value=8, key="child_age", help="Please enter the child's age")
        
        signup_button = st.button("Create Account", key="signup_button", use_container_width=True)
        
        if signup_button:
            if not (name and email and password and password_confirm):
                st.session_state.auth_status = {
                    "message": "Please fill in all required fields.",
                    "type": "warning"
                }
                st.rerun()
            elif not is_valid_email(email):
                st.session_state.auth_status = {
                    "message": "Please enter a valid email address.",
                    "type": "error"
                }
                st.rerun()
            elif password != password_confirm:
                st.session_state.auth_status = {
                    "message": "Passwords do not match. Please try again.",
                    "type": "error"
                }
                st.rerun()
            elif len(password) < 6:
                st.session_state.auth_status = {
                    "message": "Password should be at least 6 characters long.",
                    "type": "warning"
                }
                st.rerun()
            else:
                if signup(email, password, user_type, name, db, age):
                    # Stay on the signup tab and show success message
                    st.rerun()