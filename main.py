import streamlit as st
import pymongo
import os
from dotenv import load_dotenv
from auth import display_auth_page
from staff_page import display_staff_page
from child_page import display_child_page

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="ASD Therapy Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Optimized MongoDB connection with caching
@st.cache_resource
def initialize_db():
    """Initialize MongoDB connection with Atlas-optimized settings"""
    # Get MongoDB URI from environment variable
    MONGODB_URI = os.getenv("MONGODB_URI")
    
    # Check if MongoDB URI is provided
    if not MONGODB_URI:
        st.error("MongoDB URI not found. Please check your .env file.")
        st.stop()

    client = pymongo.MongoClient(
        MONGODB_URI,
        # Atlas-optimized connection settings
        maxPoolSize=10,        # Limit concurrent connections
        minPoolSize=1,         # Keep minimum connections alive
        maxIdleTimeMS=30000,   # Close idle connections after 30s
        waitQueueTimeoutMS=5000,  # Wait max 5s for connection
        serverSelectionTimeoutMS=5000,  # Server selection timeout
        socketTimeoutMS=20000,  # Socket timeout
        connectTimeoutMS=20000, # Connection timeout
        retryWrites=True,      # Retry failed writes
        w="majority"           # Write concern for data safety
    )
    
    db = client["asd-therapy"]
    
    # Get users collection
    users_collection = db["users"]
    
    # Create unique index on email field only if it doesn't exist
    try:
        existing_indexes = users_collection.list_indexes()
        index_names = [idx["name"] for idx in existing_indexes]
        if "email_1" not in index_names:
            users_collection.create_index([("email", pymongo.ASCENDING)], unique=True)
    except Exception as e:
        print(f"Index creation warning: {e}")
    
    return db

# Function to initialize session state variables
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = {"message": "", "type": ""}

# Function for main app flow
def main():
    if st.session_state.logged_in:
        # Display different pages based on user type
        if st.session_state.user_info["user_type"] == "child":
            display_child_page(db)
        elif st.session_state.user_info["user_type"] == "staff":
            display_staff_page(db)
    else:
        # Display login/signup page if not logged in
        display_auth_page(db) 

# Initialize MongoDB (cached)
db = initialize_db()

# Initialize session state variables
init_session_state()

if __name__ == "__main__":
    main()