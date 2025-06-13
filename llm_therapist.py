import os
import streamlit as st
import tempfile
import base64
import json
import numpy as np
import sounddevice as sd
import soundfile as sf
import queue
import whisper
from dotenv import load_dotenv
import openai  # Changed to use openai directly instead of OpenAI client
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage

import requests  # Added for DALL-E image generation
import re  # Added for pattern detection

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key  # Configure API key directly

# Verify API Key
if not openai_api_key:
    st.error("OpenAI API key not found. Please check your .env file.")
    st.stop()

# Client OpenAI for TTS (using openai directly)
client = openai

# Audio recording configuration
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16

# =======================================================
# NEW FUNCTION: Generate image with DALL·E 3 using requests
def generate_dalle_image(prompt_text):
    """Generate image using DALL-E 3 API"""
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt_text,
        "n": 1,
        "size": "1024x1024",
        "model": "dall-e-3"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        image_url = result['data'][0]['url']
        return image_url
    else:
        st.error(f"Error generating image with DALL·E: {response.text}")
        return None

# =======================================================
# NEW FUNCTION: Detect if image should be generated
def get_dalle_prompt(user_text, ai_text):
    """Heuristically detect if an image should be generated"""
    triggers = [
        "quiero una imagen", "haz un dibujo", "puedes hacer un dibujo",
        "dibuja", "pinta", "ilustra", "quiero ver una imagen", "haz una imagen"
    ]
    combined_text = (user_text + " " + ai_text).lower()
    if any(trigger in combined_text for trigger in triggers):
        return user_text if len(user_text) > 10 else "dibujo sugerido basado en el elemento clave mencionado en la conversación (animal, lugar, situación...)"
    return None

# UPDATED FUNCTION: Robot image selection (simplified, removed llm parameter)
def select_robot_image(user_message, ai_response):
    """Select robot image based on conversation context"""
    base_path = "Multimedia"
    images = {
        'defecto': os.path.join(base_path, 'cara_robot.jpg'),
        'saludo': os.path.join(base_path, 'saludo_robot.jpg'),
        'correcto': os.path.join(base_path, 'correcto_robot.jpg'),
        'risa': os.path.join(base_path, 'risa_robot.jpg'),
        'sorprendido': os.path.join(base_path, 'sorprendido_robot.jpg'),
        'deporte': os.path.join(base_path, 'deporte_robot.jpg'),
        'bailar': os.path.join(base_path, 'bailar_robot.jpg'),
        'pensar': os.path.join(base_path, 'pensar_robot.jpg')
    }
    
    priority_order = [
        'saludo', 'bailar', 'deporte', 'pensar', 
        'sorprendido', 'risa', 'correcto'
    ]
    
    image_contexts = {
        'saludo': "La imagen debe mostrar un saludo, una presentación inicial, o un encuentro amistoso.",
        'bailar': "La imagen debe representar baile, movimiento, o alegría física.",
        'deporte': "La imagen debe mostrar actividad deportiva, ejercicio o competencia.",
        'pensar': "La imagen debe reflejar concentración, resolución de problemas o reflexión.",
        'sorprendido': "La imagen debe capturar asombro, admiración o una reacción de sorpresa.",
        'risa': "La imagen debe transmitir humor, diversión o una situación cómica.",
        'correcto': "La imagen debe mostrar aprobación, éxito, confirmación, logro o una sensación positiva de validación."
    }
    
    context_prompt = f"""Analiza el siguiente diálogo y determina qué imagen representa mejor el contexto emocional:

Mensaje del usuario: {user_message}
Respuesta del asistente: {ai_response}

Contextos de imágenes:
{json.dumps(image_contexts, indent=2)}

Instrucciones:
- Lee el diálogo y entiende su tono emocional.
- Identifica palabras clave.
- Prioriza la imagen que mejor se ajuste.
- Responde SOLO con el nombre de la imagen (ej. 'correcto', 'saludo', etc.).
"""
    try:
        # Create a temporary LLM instance for image selection
        temp_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=openai_api_key)
        context_evaluation = temp_llm.invoke(context_prompt).content.strip().lower()
        
        if context_evaluation in images:
            return images[context_evaluation]
        
        for priority_image in priority_order:
            if priority_image in context_evaluation:
                return images[priority_image]
        
        return images['defecto']
    
    except Exception as e:
        st.error(f"Error selecting image: {e}")
        return images['defecto']
    
# Initialize Whisper model (cache to prevent reloading)
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("small")

# Function to generate audio with TTS
def generate_speech(text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="fable",
            input=text
        )
        
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "temp_speech.mp3")
        response.stream_to_file(temp_path)
        
        with open(temp_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        os.remove(temp_path)
        os.rmdir(temp_dir)
        
        return audio_bytes
    
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return None
    
# Function to create audio player HTML
def create_audio_player(audio_bytes):
    if audio_bytes:
        b64 = base64.b64encode(audio_bytes).decode()
        audio_player = f"""
            <div id="audio-player-container">
                <audio id="audio-player" autoplay="true">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            </div>
            <script>
                var player = document.getElementById('audio-player');
                player.onended = function() {{
                    window.parent.postMessage({{type: 'audio_ended'}}, '*');
                }};
            </script>
        """
        return audio_player
    return ""

# Initialize the LLM model and chain
def initialize_llm_chain(system_prompt):
    # Configure the model
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=openai_api_key)
    
    # Define the prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="input")
    ])
    
    # Create the chain with history
    agent_chain = prompt | llm
    
    return llm, agent_chain

# UPDATED FUNCTION: Process message with DALL-E image generation capability
def process_message(agent_chain, user_input, chat_history):
    # Create the message for LLM
    human_message = HumanMessage(content=user_input)
    
    # Generate response from LLM
    response = agent_chain.invoke({
        "input": [human_message],
        "history": chat_history.messages
    })
    
    # Create AI message from response
    ai_message = AIMessage(content=response.content)
    
    # Check if image should be generated
    dalle_prompt = get_dalle_prompt(user_input, response.content)
    image_url = None
    if dalle_prompt:
        image_url = generate_dalle_image(dalle_prompt)
    
    return human_message, ai_message, response.content, image_url