import streamlit as st
from auth import logout
from db_operations import (
    get_children, 
    load_user_sessions, 
    load_session_messages,
    delete_session
)
from pdf_generator import PDFGenerator

def display_staff_page(db):
    """Main staff page with conversation viewing and PDF download"""
    # Sidebar
    st.sidebar.title(f"Welcome, {st.session_state.user_info.get('name', 'User')}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()
    
    # Main content
    st.title("Staff Dashboard")
    st.write("View client conversations, download as PDF, and manage sessions")
    
    # Fix: Pass the db parameter instead of undefined db_ops
    display_conversations(db)

def display_conversations(db):
    """Display client conversations with download and delete functionality"""
    try:
        # Get all children - Fix: Use db parameter directly
        children = get_children(db)
        
        if not children:
            st.info("No children registered")
            return
        
        # Client selection
        client_names = [child["name"] for child in children if child.get("name")]
        if not client_names:
            st.info("No valid client data found")
            return
            
        selected_client = st.selectbox("Select a client:", client_names)
        
        # Get client info
        client_info = next((child for child in children if child["name"] == selected_client), None)
        if not client_info:
            return
            
        client_id = client_info.get("user_id") or client_info.get("_id")
        
        # Get and display sessions - Fix: Use db parameter directly
        sessions = load_user_sessions(db, client_id)
        if not sessions:
            st.info(f"No conversations found for {selected_client}")
            return
        
        st.write(f"**Conversations for {selected_client}:**")
        
        # Display sessions count
        st.write(f"Total sessions: {len(sessions)}")
        
        for session in sessions:
            if not session.get("session_id"):
                continue
                
            session_id = session["session_id"]
            session_title = session.get("title", "Untitled Session")
            session_date = session.get("created_at", "Unknown Date")
            
            with st.expander(f"{session_title} ({session_date})"):
                # Get and display messages - Fix: Use db parameter directly
                messages = load_session_messages(db, session_id)
                
                if messages:
                    # Display conversation
                    for message in messages:
                        role = message.get("role", "")
                        content = message.get("content", "")
                        
                        if role == "system":
                            continue
                        elif role == "user":
                            st.markdown(f"**{selected_client}:** {content}")
                        elif role == "assistant":
                            st.markdown(f"**Therapist:** {content}")
                    
                    # Action buttons in columns
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        # PDF download button
                        if st.button(f"📄 Download PDF", key=f"pdf_{session_id}"):
                            generate_pdf(messages, selected_client, session_title)
                    
                    with col2:
                        # Delete button with confirmation
                        if st.button(f"🗑️ Delete Session", key=f"delete_{session_id}", type="secondary"):
                            # Store the session to delete in session state for confirmation
                            st.session_state[f"confirm_delete_{session_id}"] = True
                            st.rerun()
                    
                    # Confirmation dialog
                    if st.session_state.get(f"confirm_delete_{session_id}", False):
                        st.warning("⚠️ **Are you sure you want to delete this session?**")
                        st.write("This action will permanently delete:")
                        st.write(f"- Session: {session_title}")
                        st.write(f"- All {len(messages)} messages in this session")
                        st.write("**This action cannot be undone!**")
                        
                        col_confirm, col_cancel = st.columns([1, 1])
                        
                        with col_confirm:
                            if st.button("✅ Yes, Delete", key=f"confirm_yes_{session_id}", type="primary"):
                                handle_session_deletion(db, session_id, session_title)
                                
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"confirm_no_{session_id}"):
                                # Remove confirmation state
                                if f"confirm_delete_{session_id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_{session_id}"]
                                st.rerun()
                else:
                    st.info("No messages found")
                    
                    # Even empty sessions can be deleted
                    st.markdown("---")
                    if st.button(f"🗑️ Delete Empty Session", key=f"delete_empty_{session_id}", type="secondary"):
                        st.session_state[f"confirm_delete_{session_id}"] = True
                        st.rerun()
                    
                    # Confirmation for empty sessions
                    if st.session_state.get(f"confirm_delete_{session_id}", False):
                        st.warning("⚠️ **Delete this empty session?**")
                        
                        col_confirm, col_cancel = st.columns([1, 1])
                        
                        with col_confirm:
                            if st.button("✅ Yes, Delete", key=f"confirm_yes_empty_{session_id}", type="primary"):
                                handle_session_deletion(db, session_id, session_title)
                                
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"confirm_no_empty_{session_id}"):
                                if f"confirm_delete_{session_id}" in st.session_state:
                                    del st.session_state[f"confirm_delete_{session_id}"]
                                st.rerun()
                    
    except Exception as e:
        st.error(f"Error: {str(e)}")

def handle_session_deletion(db, session_id, session_title):
    """Handle the session deletion process"""
    try:
        with st.spinner("Deleting session..."):
            result = delete_session(db, session_id)
            
        if result["success"]:
            st.success(f"✅ Session deleted successfully!")
            st.info(f"Deleted session '{session_title}' and {result['messages_deleted']} messages")
            
            # Clear confirmation state
            if f"confirm_delete_{session_id}" in st.session_state:
                del st.session_state[f"confirm_delete_{session_id}"]
            
            # Refresh the page to show updated session list
            st.rerun()
            
        else:
            st.error(f"❌ Failed to delete session: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"❌ Error during deletion: {str(e)}")

def generate_pdf(messages, client_name, session_title):
    """Generate and provide PDF download"""
    try:
        pdf_generator = PDFGenerator()
        
        with st.spinner("Generating PDF..."):
            # Create PDF
            pdf_buffer = pdf_generator.create_pdf(messages, client_name, session_title)
            filename = pdf_generator.create_filename(client_name, session_title)
            
            # Download button
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_buffer.getvalue(),
                file_name=filename,
                mime="application/pdf"
            )
            
        st.success("PDF ready for download!")
        
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")