import streamlit as st
import openai
import requests
import pandas as pd
from hashlib import sha256
import csv
import os

# Ruta para los archivos CSV
USUARIOS_CSV = 'usuarios.csv'
PROGRESO_CSV = 'progreso.csv'

# API key de OpenRouter desde los secretos
api_key = st.secrets["openrouter"]["api_key"]

# Función para generar textos de OpenRouter
def generar_texto(nivel):
    prompt = f"Genera un texto de comprensión lectora en español para un estudiante de bachillerato de nivel {nivel}."
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "microsoft/phi-4-reasoning-plus:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json().get("choices")[0]["message"]["content"]

# Función para generar preguntas más variadas
def generar_preguntas(texto):
    prompt = f"Genera preguntas de opción múltiple sobre el siguiente texto: {texto}. Haz preguntas sobre comprensión, vocabulario, pensamiento crítico y lógica."
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "microsoft/phi-4-reasoning-plus:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json().get("choices")[0]["message"]["content"]

# Función para evaluar las respuestas y dar retroalimentación
def evaluar_respuestas(respuestas_usuario, respuestas_correctas):
    puntaje = sum([1 for user, correct in zip(respuestas_usuario, respuestas_correctas) if user == correct])
    feedback = "¡Bien hecho!" if puntaje == 5 else "Intenta de nuevo."
    return puntaje, feedback

# Función para iniciar sesión
def login():
    # Cargar los usuarios desde el archivo CSV
    if os.path.exists(USUARIOS_CSV):
        usuarios = pd.read_csv(USUARIOS_CSV)
        usuarios_dict = dict(zip(usuarios['email'], usuarios['password']))
    else:
        usuarios_dict = {}

    email = st.text_input("Correo electrónico", "")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar sesión"):
        if email in usuarios_dict and usuarios_dict[email] == sha256(password.encode()).hexdigest():
            return email
        else:
            st.error("Correo electrónico o contraseña incorrectos.")
            return None
    return None

# Función para agregar, editar y eliminar usuarios (solo accesible para el administrador)
def gestionar_usuarios():
    st.title("Gestión de Usuarios")
    action = st.radio("Selecciona una acción", ["Agregar Usuario", "Editar Usuario", "Eliminar Usuario"])
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")

    if action == "Agregar Usuario":
        if st.button("Agregar"):
            # Agregar usuario al archivo CSV
            usuarios = pd.read_csv(USUARIOS_CSV) if os.path.exists(USUARIOS_CSV) else pd.DataFrame(columns=["email", "password"])
            usuarios = usuarios.append({"email": email, "password": sha256(password.encode()).hexdigest()}, ignore_index=True)
            usuarios.to_csv(USUARIOS_CSV, index=False)
            st.success(f"Usuario {email} agregado correctamente.")
    elif action == "Editar Usuario":
        if st.button("Editar"):
            usuarios = pd.read_csv(USUARIOS_CSV)
            if email in usuarios['email'].values:
                usuarios.loc[usuarios['email'] == email, 'password'] = sha256(password.encode()).hexdigest()
                usuarios.to_csv(USUARIOS_CSV, index=False)
                st.success(f"Contraseña de {email} actualizada.")
            else:
                st.error("Usuario no encontrado.")
    elif action == "Eliminar Usuario":
        if st.button("Eliminar"):
            usuarios = pd.read_csv(USUARIOS_CSV)
            if email in usuarios['email'].values:
                usuarios = usuarios[usuarios['email'] != email]
                usuarios.to_csv(USUARIOS_CSV, index=False)
                st.success(f"Usuario {email} eliminado.")
            else:
                st.error("Usuario no encontrado.")

# Función para almacenar y mostrar el progreso
def almacenar_progreso(usuario, nivel, puntaje):
    progreso = pd.read_csv(PROGRESO_CSV) if os.path.exists(PROGRESO_CSV) else pd.DataFrame(columns=["Usuario", "Nivel", "Puntaje"])
    nuevo_registro = {"Usuario": usuario, "Nivel": nivel, "Puntaje": puntaje}
    progreso = progreso.append(nuevo_registro, ignore_index=True)
    progreso.to_csv(PROGRESO_CSV, index=False)

# Función principal para manejar el flujo de la aplicación
def main():
    # Control de acceso
    usuario = login()
    if not usuario:
        return
    
    # Selección de nivel
    st.title("Mejora tu comprensión lectora")
    nivel = st.radio("Selecciona tu nivel de dificultad", ["Básico", "Intermedio", "Avanzado"])
    
    # Generar texto y preguntas
    texto = generar_texto(nivel)
    st.subheader("Texto de lectura:")
    st.write(texto)
    
    preguntas = generar_preguntas(texto).split("\n")
    respuestas_correctas = ["a", "b", "c", "a", "b"]  # Este es un ejemplo, en la implementación real obtendrás las respuestas correctas
    
    respuestas_usuario = []
    
    # Mostrar preguntas
    for i, pregunta in enumerate(preguntas):
        opciones = pregunta.split(";")  # Asumiendo que las opciones están separadas por ";"
        respuesta = st.radio(f"Pregunta {i + 1}", opciones)
        respuestas_usuario.append(respuesta)
    
    if st.button("Enviar respuestas"):
        puntaje, feedback = evaluar_respuestas(respuestas_usuario, respuestas_correctas)
        st.write(f"Puntaje: {puntaje}/5")
        st.write(feedback)
        
        # Almacenar el progreso
        almacenar_progreso(usuario, nivel, puntaje)
    
    # Administrar usuarios (solo accesible por el administrador)
    if usuario == "admin@dominio.com":  # Solo el admin puede gestionar usuarios
        gestionar_usuarios()

if __name__ == "__main__":
    main()
