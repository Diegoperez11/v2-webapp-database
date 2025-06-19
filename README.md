# 🤖 v2-webapp-database – Chatbot Terapéutico para Niños con TEA

**VERSIÓN 2: Integración Completa con Base de Datos MongoDB**

**v2-webapp-database** es la segunda versión de una aplicación web interactiva orientada a facilitar y mejorar sesiones terapéuticas con niños con Trastorno del Espectro Autista (TEA), basada en IA y ahora potenciada con gestión avanzada de usuarios, almacenamiento de sesiones y mensajes en una base de datos, y herramientas para terapeutas y administradores.

---

## 🧠 Novedades Principales v2

- **Base de Datos MongoDB Integrada:**  
  Todos los usuarios, sesiones y mensajes se almacenan de manera segura en MongoDB, permitiendo el registro e inicio de sesión personalizado y la gestión de datos históricos.
- **Gestión de Roles (Administradores/Participantes):**  
  Distinción clara entre usuarios administradores (staff/terapeutas) y participantes (niños con TEA), con acceso diferenciado a funcionalidades y vistas.
- **Visualización y Análisis de Sesiones:**  
  El staff puede acceder al historial de conversaciones, analizar el desarrollo de cada participante y descargar sesiones completas en formato PDF.
- **Interfaz de Inicio de Sesión y Registro:**  
  Sistema de autenticación integrado para control de acceso y personalización de la experiencia.
- **Estructura de Código Modular:**  
  El backend está dividido en módulos específicos, facilitando el mantenimiento y la escalabilidad.

---

## 🧩 Funcionalidades Generales

- **Agente LLM Terapéutico:**  
  Integración con modelos de lenguaje OpenAI para simular conversaciones terapéuticas adaptadas a las necesidades emocionales y comunicativas de los niños.
- **Generación de Imágenes IA:**  
  Uso de DALL·E 3 para crear imágenes en tiempo real durante la sesión, reforzando la experiencia inmersiva.
- **Audio Bidireccional:**  
  Transcripción de audio (Whisper) y generación de respuestas habladas (TTS) para una comunicación multimodal.
- **Interfaz Visual Adaptativa:**  
  El “robot virtual” expresa emociones y cambia de aspecto según el diálogo, mejorando la conexión empática con el niño.

---

## 🚀 Tecnologías Utilizadas

- **Frontend:** Streamlit (UI web interactiva y adaptable)
- **Backend:** Python modularizado
- **Base de datos:** MongoDB (gestión de usuarios, sesiones y mensajes)
- **IA Conversacional:** OpenAI LLMs, DALL·E 3, Whisper, TTS
- **Otros:** FPDF para generación de PDFs, gestión de entorno con `.env`

---

## 🗂️ Estructura y Archivos Principales

| Archivo / Carpeta              | Descripción breve                                                                                  |
|-------------------------------|----------------------------------------------------------------------------------------------------|
| `main.py`                     | Punto de entrada. Inicializa la app, conecta con MongoDB y gestiona la navegación entre páginas.   |
| `auth.py`                     | Lógica de autenticación: registro, login, logout y validación de usuarios.                         |
| `db_operations.py`            | Funciones para interactuar con MongoDB: guardar/cargar usuarios, sesiones y mensajes.              |
| `child_page.py`               | Interfaz y lógica de la página para niños (participantes), organiza la sesión de terapia.          |
| `child_page_components.py`    | Componentes y funciones para chat, audio, manejo de sesiones e imágenes del robot en child_page.    |
| `llm_therapist.py`            | Lógica de IA: comunicación con LLM de OpenAI, generación de imágenes, selección de emociones y TTS.|
| `staff_page.py`               | Interfaz para administradores: visualización, análisis y descarga de sesiones en PDF.              |
| `pdf_generator.py`            | Clase para crear y descargar PDFs de las sesiones, con estilos diferenciados para terapeuta/niño.  |
| `system_prompt4.txt`          | Prompt detallado que define el comportamiento y tono del asistente virtual (Pepper).               |
| `.env`                        | Variables de entorno sensibles (APIs, URIs).                                                       |
| `requirements.txt`            | Dependencias del proyecto (librerías y versiones).                                                 |
| `Multimedia/`                 | Imágenes y recursos multimedia para la interfaz y emociones del robot.                             |

---

## 🎯 Objetivo del Proyecto

Proveer una herramienta terapéutica digital, basada en inteligencia artificial, que facilite el apoyo emocional y comunicativo a niños con TEA, y proporcione recursos analíticos y de seguimiento para los profesionales y familias.

---

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

---

## 🤝 Contribuciones

Las contribuciones y sugerencias son bienvenidas. Por favor, abre un *issue* o envía un *pull request* para proponer mejoras.

---
