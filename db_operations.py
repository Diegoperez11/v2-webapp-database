from datetime import datetime
import uuid
import streamlit as st

def setup_database_indexes(db):
    """Set up MongoDB indexes for better query performance - only run once"""
    # Check if indexes already exist to avoid recreating them
    if "indexes_created" not in st.session_state:
        try:
            # Create indexes only if they don't exist
            existing_indexes = db["sessions"].list_indexes()
            index_names = [idx["name"] for idx in existing_indexes]
            
            if "user_id_1" not in index_names:
                db["sessions"].create_index("user_id")
            
            existing_msg_indexes = db["messages"].list_indexes()
            msg_index_names = [idx["name"] for idx in existing_msg_indexes]
            
            if "session_id_1" not in msg_index_names:
                db["messages"].create_index("session_id")
            if "timestamp_1" not in msg_index_names:
                db["messages"].create_index("timestamp")
            
            # Mark as completed
            st.session_state.indexes_created = True
            
        except Exception as e:
            st.error(f"Error setting up indexes: {str(e)}")

# ==================== MESSAGE OPERATIONS ====================

def save_message_batch(db, messages_list):
    """Save multiple messages in a single batch operation"""
    try:
        if messages_list:
            db["messages"].insert_many(messages_list)
    except Exception as e:
        st.error(f"Error saving messages: {str(e)}")

def save_message(db, session_id, role, content):
    """Save chat messages to MongoDB"""
    try:
        message_doc = {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        db["messages"].insert_one(message_doc)
    except Exception as e:
        st.error(f"Error saving message: {str(e)}")

def load_session_messages(db, session_id):
    """Load all messages for a specific therapy session with optimized projection"""
    try:
        # Only select the fields we need to reduce data transfer
        cursor = db["messages"].find(
            {"session_id": session_id},
            {"role": 1, "content": 1, "timestamp": 1, "_id": 0}  # Only get needed fields
        ).sort("timestamp", 1)
        
        messages = []
        for doc in cursor:
            messages.append({
                "role": doc["role"],
                "content": doc["content"]
            })
        return messages
    except Exception as e:
        st.error(f"Error loading messages: {str(e)}")
        return []

def delete_session_messages(db, session_id):
    """Delete all messages for a specific session"""
    try:
        result = db["messages"].delete_many({"session_id": session_id})
        return result.deleted_count
    except Exception as e:
        st.error(f"Error deleting messages: {str(e)}")
        return 0

# ==================== SESSION OPERATIONS ====================

def create_session(db, user_id):
    """Create a new therapy session in the database"""
    try:
        session_id = str(uuid.uuid4())
        new_session = {
            "session_id": session_id,
            "user_id": user_id,
            "title": f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": datetime.now(),
        }
        db["sessions"].insert_one(new_session)
        return session_id
    except Exception as e:
        st.error(f"Error creating new session: {str(e)}")
        return None

def load_user_sessions(db, user_id):
    """Load user therapy sessions from MongoDB with optimized query"""
    try:
        # Use projection to only get needed fields and limit results
        user_sessions = list(db["sessions"].find(
            {"user_id": user_id},
            {"_id": 0, "session_id": 1, "title": 1, "created_at": 1}  # Only get needed fields
        ).sort("created_at", -1).limit(50))  # Limit to last 50 sessions
        return user_sessions
    except Exception as e:
        st.error(f"Error loading sessions: {str(e)}")
        return []

def delete_session(db, session_id):
    """Delete a session and all its associated messages"""
    try:
        # First, delete all messages for this session
        messages_deleted = delete_session_messages(db, session_id)
        
        # Then delete the session itself
        session_result = db["sessions"].delete_one({"session_id": session_id})
        
        if session_result.deleted_count > 0:
            return {
                "success": True,
                "session_deleted": True,
                "messages_deleted": messages_deleted
            }
        else:
            return {
                "success": False,
                "error": "Session not found"
            }
            
    except Exception as e:
        st.error(f"Error deleting session: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ==================== USER OPERATIONS ====================

def get_children(db):
    """Get all child users with optimized projection"""
    try:
        return list(db["users"].find(
            {"user_type": "child"},
            {"user_id": 1, "name": 1, "email": 1, "age": 1, "created_at": 1, "_id": 0}
        ).sort("name", 1))
    except Exception as e:
        st.error(f"Error loading children: {str(e)}")
        return []
