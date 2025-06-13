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
    
    # Reset sessions when user changes
    _handle_user_change(session_handler)
    
    # Create two-column layout
    col1, col2 = st.columns([1, 2], gap="small")
    
    # Render sidebar
    _render_sidebar(session_handler)
    
    # Column 1: Robot character
    with col1:
        ui_renderer.render_robot_section()
    
    # Column 2: Chat interface
    with col2:
        _render_chat_section(chat_handler, audio_handler)

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
        "messages": []  # Added messages initialization
    }
    
    for state, default_value in required_states.items():
        if state not in st.session_state:
            st.session_state[state] = default_value

def _handle_user_change(session_handler):
    """Handle user change and reset session data"""
    current_user = st.session_state.user_info["user_id"]
    
    if ("last_active_user" not in st.session_state or 
        st.session_state.last_active_user != current_user):
        
        session_handler.reset_user_sessions()
        st.session_state.last_active_user = current_user

def _render_sidebar(session_handler):
    """Render the sidebar with user info, sessions, and settings"""
    # User info
    st.sidebar.title(f"Welcome, {st.session_state.user_info.get('name', 'User')}")
    st.sidebar.write(f"Type: {st.session_state.user_info['user_type'].capitalize()}")
    
    # Session management
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Therapy Sessions")
    
    # Load and display sessions
    session_handler.load_user_sessions()
    
    # New session button
    if st.sidebar.button("➕ Start New Session"):
        session_handler.create_new_session()
        st.rerun()
    
    # Display past sessions
    st.sidebar.markdown("### Past Sessions")
    session_handler.display_past_sessions()
    
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
        logout()
        st.rerun()

def _render_chat_section(chat_handler, audio_handler):
    """Render the main chat interface"""
    # Check if we have an active session
    if st.session_state.current_session_id is None:
        st.info("👋 Welcome! Please start a new therapy session using the sidebar.")
        return
    
    # Show current session info
    chat_handler.display_current_session_info()
    
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
                on_change=lambda: chat_handler.handle_submit()
            )
        
        with col2:
            audio_handler.render_audio_input(chat_handler)