import streamlit as st
import bcrypt
import requests
import pandas as pd
import os
import secrets
import string

# Archivos CSV para usuarios y progreso
USUARIOS_CSV = 'usuarios.csv'
PROGRESO_CSV = 'progreso.csv'

# API key de OpenRouter desde los secretos
api_key = st.secrets["openrouter"]["api_key"]

# Función para generar un hash seguro de la contraseña con bcrypt
def generar_hash_bcrypt(contraseña):
    salt = bcrypt.gensalt()  # Genera un salt aleatorio
    hash_contraseña = bcrypt.hashpw(contraseña.encode('utf-8'), salt)
    return hash_contraseña

# Función para verificar la contraseña usando bcrypt
def verificar_contraseña(contraseña, hash_guardado):
    return bcrypt.checkpw(contraseña.encode('utf-8'), hash_guardado)

# Función para generar una contraseña aleatoria segura
def generar_contraseña_segura(longitud=12):
    # Generar una contraseña segura utilizando caracteres aleatorios
    caracteres = string.ascii_letters + string.digits + string.punctuation
    contraseña = ''.join(secrets.choice(caracteres) for i in range(longitud))
    return contraseña

# Función para generar texto de OpenRouter
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

# Función para generar preguntas relacionadas con el texto
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
    if os.path.exists(USUARIOS_CSV):
        usuarios = pd.read_csv(USUARIOS_CSV)
    else:
        usuarios = pd.DataFrame(columns=["email", "password"])

    email = st.text_input("Correo electrónico", "")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar sesión"):
        usuario = usuarios[usuarios['email'] == email]
        if not usuario.empty and verificar_contraseña(password, usuario['password'].values[0]):
            return email
        else:
            st.error("Correo electrónico o contraseña incorrectos.")
            return None
    return None

# Función para agregar, editar y eliminar usuarios
def gestionar_usuarios():
    st.title("Gestión de Usuarios")
    action = st.radio("Selecciona una acción", ["Agregar Usuario", "Editar Usuario", "Eliminar Usuario"])
    email = st.text_input("Correo electrónico")
    
    if action == "Agregar Usuario":
        if st.button("Agregar"):
            # Generar una contraseña segura aleatoria
            contraseña_segura = generar_contraseña_segura()
            hashed_password = generar_hash_bcrypt(contraseña_segura)
            
            # Agregar usuario al archivo CSV
            usuarios = pd.read_csv(USUARIOS_CSV) if os.path.exists(USUARIOS_CSV) else pd.DataFrame(columns=["email", "password"])
            usuarios = usuarios.append({"email": email, "password": hashed_password}, ignore_index=True)
            usuarios.to_csv(USUARIOS_CSV, index=False)
            st.success(f"Usuario {email} agregado correctamente. La contraseña es: {contraseña_segura}")
    elif action == "Editar Usuario":
        password = st.text_input("Nueva Contraseña", type="password")
        if st.button("Editar"):
            usuarios = pd.read_csv(USUARIOS_CSV)
            if email in usuarios['email'].values:
                hashed_password = generar_hash_bcrypt(password)
                usuarios.loc[usuarios['email'] == email, 'password'] = hashed_password
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

# Función para mostrar el progreso de los estudiantes
def ver_progreso():
    st.title("Progreso de los Estudiantes")
    if os.path.exists(PROGRESO_CSV):
        progreso = pd.read_csv(PROGRESO_CSV)
        st.dataframe(progreso)  # Mostrar el progreso en una tabla
    else:
        st.warning("No hay registros de progreso aún.")

# Función principal para manejar el flujo de la aplicación
def main():
    # Menú de navegación
    st.sidebar.title("Menú de administración")
    opcion = st.sidebar.radio("Selecciona una opción", ["Inicio", "Administración", "Ver Progreso"])

    if opcion == "Inicio":
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
        
    elif opcion == "Administración":
        # Gestión de usuarios (solo accesible por el administrador)
        gestionar_usuarios()

    elif opcion == "Ver Progreso":
        # Ver progreso de los estudiantes
        ver_progreso()

if __name__ == "__main__":
    main()
