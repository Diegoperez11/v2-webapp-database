import streamlit as st
import PIL.Image
import tempfile
import soundfile as sf
import os
import uuid
from audiorecorder import audiorecorder
from datetime import datetime  
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import SystemMessage
from llm_therapist import (
    initialize_llm_chain, 
    process_message, 
    generate_speech, 
    create_audio_player,
    select_robot_image
)
from db_operations import (
    setup_database_indexes,
    save_message,
    save_message_batch
)

class ChatHandler:
    """Handles all chat-related functionality"""
    
    def __init__(self, db):
        self.db = db
        self._initialize_llm()
        self._ensure_database_setup()
        self._pending_messages = []  # For batch operations
    
    def _initialize_llm(self):
        """Initialize LLM chain if needed"""
        if "llm" not in st.session_state or "agent_chain" not in st.session_state:
            # Load system prompt from file
            with open("system_prompt4.txt", "r", encoding="utf-8") as file:
                system_prompt_content = file.read()
            
            st.session_state.llm, st.session_state.agent_chain = initialize_llm_chain(system_prompt_content)
            
            # Initialize chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = ChatMessageHistory()
                st.session_state.chat_history.add_message(SystemMessage(content=system_prompt_content))
    
    def _ensure_database_setup(self):
        """Ensure database indexes exist for better performance - only once"""
        setup_database_indexes(self.db)
        
    def display_messages(self):
        """Display chat messages from history"""
        # Display chat messages from history
        for message in st.session_state.messages:
            role_class = "user-message" if message["role"] == "user" else "assistant-message"
            
            if message.get("type", "text") == "text":
                with st.chat_message(message["role"]):
                    st.markdown(f'<div class="{role_class}">{message["content"]}</div>', unsafe_allow_html=True)
            elif message.get("type") == "image":
                with st.chat_message(message["role"]):
                    st.image(message["content"], caption="Imagen generada por DALL·E", use_container_width=True)
    
    def display_audio_player(self):
        """Display audio player if there's a response to be played"""
        if st.session_state.audio_response and st.session_state.tts_enabled:
            audio_player = create_audio_player(st.session_state.audio_response)
            st.session_state.current_audio_container = st.container()
            with st.session_state.current_audio_container:
                st.markdown(audio_player, unsafe_allow_html=True)
            st.session_state.audio_response = None
    
    def handle_submit(self, session_handler):
        """Handle form submission from text input"""
        if st.session_state.text_input.strip():
            user_message = st.session_state.text_input
            st.session_state.text_input = ""
            self.process_user_message(user_message, session_handler)
    
    def handle_user_input(self, user_input, session_handler):
        """Handle user text input - for compatibility with audio handler"""
        self.process_user_message(user_input, session_handler)
    
    def process_user_message(self, user_input, session_handler):
        """Process user message through LLM and handle response"""
        # Create session in database only when first message is sent
        if not st.session_state.session_created_in_db:
            session_handler.create_session_in_database()
        
        # Add user message to UI messages
        st.session_state.messages.append({"role": "user", "content": user_input, "type": "text"})
        
        # Process message through LLM agent (updated to handle 4 return values)
        human_message, ai_message, response_content, image_url = process_message(
            st.session_state.agent_chain,
            user_input,
            st.session_state.chat_history
        )
        
        # Add messages to chat history
        st.session_state.chat_history.add_message(human_message)
        st.session_state.chat_history.add_message(ai_message)
        
        # Add assistant response to UI messages
        st.session_state.messages.append({"role": "assistant", "content": response_content, "type": "text"})
        
        # Add image if generated
        if image_url:
            st.session_state.messages.append({"role": "assistant", "content": image_url, "type": "image"})
        
        # Save messages to database using batch operation for better performance
        self._save_messages_batch([
            {
                "message_id": f"user_{len(st.session_state.messages)}",
                "session_id": st.session_state.current_session_id,
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            },
            {
                "message_id": f"assistant_{len(st.session_state.messages)}",
                "session_id": st.session_state.current_session_id,
                "role": "assistant",
                "content": response_content,
                "timestamp": datetime.now()
            }
        ])
        
        # Generate audio if TTS is enabled
        if st.session_state.tts_enabled:
            st.session_state.audio_response = generate_speech(response_content)
    
    def _save_messages_batch(self, messages):
        """Save multiple messages in a single batch operation"""
        try:
            # Add UUIDs to messages
            for msg in messages:
                if 'message_id' not in msg or not msg['message_id']:
                    msg['message_id'] = str(uuid.uuid4())
            
            save_message_batch(self.db, messages)
        except Exception as e:
            st.error(f"Error saving messages: {str(e)}")
            # Fallback to individual saves
            for msg in messages:
                save_message(self.db, msg['session_id'], msg['role'], msg['content'])

class AudioHandler:
    """Handles audio recording and transcription using audiorecorder library"""
    
    def __init__(self):
        # Initialize audio state tracking
        if "audio_last_len" not in st.session_state:
            st.session_state["audio_last_len"] = 0
    
    def render_audio_input(self, chat_handler, session_handler):
        """Render the audio input widget and handle recording"""
        # Use audiorecorder widget
        audio = audiorecorder("🎤", "🔴")
        
        # Check if new audio was recorded
        if len(audio) > 0 and len(audio) != st.session_state["audio_last_len"]:
            st.session_state["audio_last_len"] = len(audio)
            self._process_recorded_audio(audio, chat_handler, session_handler)
        
        # Reset tracking when no audio
        if len(audio) == 0:
            st.session_state["audio_last_len"] = 0
    
    def _process_recorded_audio(self, audio, chat_handler, session_handler):
        """Process the recorded audio data"""
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "temp_audio.wav")
        
        try:
            # Save audio to temporary file
            try:
                sf.write(temp_path, audio, 16000)
            except Exception:
                audio.export(temp_path, format="wav")
            
            # Transcribe the audio
            with st.spinner("Transcribiendo audio..."):
                try:
                    from llm_therapist import load_whisper_model
                    model = load_whisper_model()
                    result = model.transcribe(temp_path, language="es")
                    transcribed_text = result["text"]
                    
                    if transcribed_text and transcribed_text.strip():
                        st.info(f"Transcribed: {transcribed_text}")
                        # Process through chat handler
                        chat_handler.process_user_message(transcribed_text, session_handler)
                        st.rerun()
                    else:
                        st.error("No se pudo transcribir el audio. Por favor, inténtalo de nuevo.")
                except Exception as e:
                    st.error(f"Error durante la transcripción: {str(e)}")
        
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                os.rmdir(temp_dir)
            except Exception:
                pass 

class SessionHandler:
    """Handles session management operations"""
    
    def __init__(self, db):
        self.db = db
    
    def reset_user_sessions(self):
        """Reset session data to start completely fresh"""
        # Clear all session-related state completely
        st.session_state.sessions_loaded = False
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.session_state.session_created_in_db = False
        
        # Clear chat history completely
        if "chat_history" in st.session_state:
            del st.session_state["chat_history"]
        
        # Clear any other session-related keys
        session_keys_to_clear = ["user_sessions", "chat_history"]
        for key in session_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def prepare_new_session(self):
        """Prepare a new therapy session (generate ID but don't save to DB yet)"""
        
        # Generate session ID but don't save to database yet
        session_id = str(uuid.uuid4())
        st.session_state.current_session_id = session_id
        
        # Ensure messages list is completely empty
        st.session_state.messages = []
        
        # Re-initialize chat history with system prompt
        from langchain_community.chat_message_histories import ChatMessageHistory
        from langchain.schema import SystemMessage
        
        st.session_state.chat_history = ChatMessageHistory()
        
        # Re-add system prompt
        try:
            with open("system_prompt4.txt", "r", encoding="utf-8") as file:
                system_prompt_content = file.read()
            st.session_state.chat_history.add_message(SystemMessage(content=system_prompt_content))
        except Exception as e:
            st.error(f"Error loading system prompt: {str(e)}")
        
        # Reset sessions loaded flag
        st.session_state.sessions_loaded = False
        
        # Mark that session is not yet created in database
        st.session_state.session_created_in_db = False
    
    def create_session_in_database(self):
        """Actually create the session in the database when first message is sent"""
        if not st.session_state.session_created_in_db and st.session_state.current_session_id:
            try:
                # Create session in database using the pre-generated ID
                from datetime import datetime
                
                new_session = {
                    "session_id": st.session_state.current_session_id,
                    "user_id": st.session_state.user_info["user_id"],
                    "title": f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "created_at": datetime.now(),
                }
                
                self.db["sessions"].insert_one(new_session)
                st.session_state.session_created_in_db = True
                
            except Exception as e:
                st.error(f"Error creating session in database: {str(e)}")
                # Generate a new session ID as fallback
                st.session_state.current_session_id = str(uuid.uuid4())

class UIRenderer:
    """Handles UI rendering components"""
    
    def render_robot_section(self):
        """Render the robot character section"""
        st.markdown("""
        <div class="rainbow-title">¡Juega con Pepper!</div>
        """, unsafe_allow_html=True)
        
        try:
            # Get the last messages for image selection if available
            user_message = ""
            ai_message = ""
            
            if (hasattr(st.session_state, 'messages') and 
                len(st.session_state.messages) > 0):
                # Get last user message
                user_message = st.session_state.messages[-1]['content'] if st.session_state.messages else ""
                ai_message = st.session_state.messages[-2]['content'] if len(st.session_state.messages) > 1 else ""
            
            # Select appropriate robot image based on conversation context
            current_image_path = select_robot_image(user_message, ai_message)
            robot_image = PIL.Image.open(current_image_path)
            st.image(robot_image, use_container_width=True, caption="Pepper, tu asistente")
        except Exception as e:
            st.error(f"No se pudo cargar la imagen: {e}")
            st.write("Imagen no disponible")


def get_child_page_styles():
    """Return CSS styles for the child page"""
    return """
    <style>
        .stApp {
            background: linear-gradient(45deg, #FFC3A0, #A6F6FF, #FFDBAC);
            background-size: 400% 400%;
            animation: gradientAnimation 15s ease infinite;
            font-family: 'Comic Sans MS', 'Comic Sans', cursive;
        }
        @keyframes gradientAnimation {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .user-message {
            background: linear-gradient(135deg, #FFD1DC, #FFEBCD);
            border-radius: 20px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .assistant-message {
            background: linear-gradient(135deg, #B0E0E6, #E6E6FA);
            border-radius: 20px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .user-message:hover, .assistant-message:hover {
            transform: scale(1.02);
        }
        .stColumn:first-child {
            position: sticky;
            top: 80px;
            height: calc(100vh - 120px);
            overflow-y: hidden;
        }
        .stColumn:first-child > div {
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .rainbow-title {
            text-align: center;
            font-family: 'Comic Sans MS', 'Comic Sans', cursive;
            font-size: 3.5em;
            font-weight: bold;
            background: linear-gradient(90deg, red, orange, yellow, green, blue, indigo, violet);
            background-size: 400% 400%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: colorFlow 3s linear infinite, bounce 1s infinite alternate;
        }
        @keyframes colorFlow {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }
        @keyframes bounce {
            0% { transform: translateY(0); }
            100% { transform: translateY(-20px); }
        }
    </style>
    """