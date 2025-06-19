import streamlit as st
from auth import logout
from child_page_components import (
    ChatHandler,
    AudioHandler,
    SessionHandler,
    UIRenderer,
    get_child_page_styles
)

def display_child_page(db):
    """Main function to display the child-friendly therapy assistant interface"""
    
    # Apply custom CSS
    st.markdown(get_child_page_styles(), unsafe_allow_html=True)
    
    # Initialize components
    chat_handler = ChatHandler(db)
    audio_handler = AudioHandler()
    session_handler = SessionHandler(db)
    ui_renderer = UIRenderer()
    
    # Initialize session states
    _initialize_session_states()
    
    # Handle user change and prepare for fresh session (but don't create yet)
    _handle_user_change_and_prepare_fresh(session_handler)
    
    # Create two-column layout
    col1, col2 = st.columns([1, 2], gap="small")
    
    # Render sidebar
    _render_sidebar()
    
    # Column 1: Robot character
    with col1:
        ui_renderer.render_robot_section()
    
    # Column 2: Chat interface
    with col2:
        _render_chat_section(chat_handler, audio_handler, session_handler)

def _initialize_session_states():
    """Initialize all required session states"""
    required_states = {
        "audio_recorder": None,
        "recording": False,
        "audio_response": None,
        "current_audio_container": None,
        "current_session_id": None,
        "sessions_loaded": False,
        "tts_enabled": True,
        "messages": [],  
        "fresh_session_prepared": False,  # Track if fresh session was prepared for this login
        "session_created_in_db": False    # Track if session exists in database
    }
    
    for state, default_value in required_states.items():
        if state not in st.session_state:
            st.session_state[state] = default_value

def _handle_user_change_and_prepare_fresh(session_handler):
    """Handle user change and prepare for a fresh session (but don't create in DB yet)"""
    current_user = st.session_state.user_info["user_id"]
    
    # Check if user changed OR if we haven't prepared a fresh session yet
    if ("last_active_user" not in st.session_state or 
        st.session_state.last_active_user != current_user or
        not st.session_state.fresh_session_prepared):
        
        # Reset all session data
        session_handler.reset_user_sessions()
        
        # Prepare a new session (generate ID but don't save to DB yet)
        session_handler.prepare_new_session()
        
        # Mark that we've prepared a fresh session for this user
        st.session_state.last_active_user = current_user
        st.session_state.fresh_session_prepared = True

def _render_sidebar():
    """Render the sidebar with user info and settings (no conversation history)"""
    # User info
    st.sidebar.title(f"Welcome, {st.session_state.user_info.get('name', 'User')}")
    st.sidebar.write(f"Type: {st.session_state.user_info['user_type'].capitalize()}")
    
    # Settings section
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Settings")
    
    # TTS toggle
    st.session_state["tts_enabled"] = st.sidebar.toggle(
        "Enable voice responses", 
        value=st.session_state["tts_enabled"]
    )
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        # Reset session flags on logout
        st.session_state.fresh_session_prepared = False
        st.session_state.session_created_in_db = False
        logout()
        st.rerun()

def _render_chat_section(chat_handler, audio_handler, session_handler):
    """Render the main chat interface"""
    
    # Display chat messages
    chat_handler.display_messages()
    
    # Display audio player if needed
    chat_handler.display_audio_player()
    
    # Chat input area
    input_container = st.container()
    with input_container:
        col1, col2 = st.columns([6, 1])
        
        with col1:
            st.text_input(
                "Escribe tu mensaje aquí...",
                key="text_input",
                on_change=lambda: chat_handler.handle_submit(session_handler)
            )
        
        with col2:
            audio_handler.render_audio_input(chat_handler, session_handler)