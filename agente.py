import os
import time
import subprocess
from google import genai
from google.genai import types
from groq import Groq

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ==========================================
# 2. HERRAMIENTAS DEL CREADOR
# ==========================================
def ejecutar_comando_bash(comando: str) -> str:
    """Ejecuta un comando en la terminal bash de Linux y devuelve la salida o el error."""
    print(f"\n[🔧 Bash]: {comando}")
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=180)
        return f"Salida:\n{result.stdout}\nError:\n{result.stderr}" if result.returncode == 0 else f"Error (Código {result.returncode}):\n{result.stderr}"
    except Exception as e:
        return f"Excepción: {str(e)}"

def escribir_archivo(ruta: str, contenido: str) -> str:
    """Escribe o sobreescribe contenido de texto en la ruta de archivo especificada."""
    print(f"\n[📝 Escribir Archivo]: {ruta}")
    try:
        os.makedirs(os.path.dirname(ruta) if os.path.dirname(ruta) else '.', exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return f"Archivo '{ruta}' guardado."
    except Exception as e:
        return f"Error al escribir: {e}"

def leer_archivo(ruta: str) -> str:
    """Lee el contenido de un archivo existente en la ruta especificada."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error al leer: {e}"

def ver_estructura_proyecto(directorio: str = ".") -> str:
    """Devuelve la estructura de árbol de carpetas y archivos del directorio actual."""
    resultado = []
    ignorar = {'.git', '__pycache__', 'venv', 'node_modules', 'dist'}
    for raiz, dirs, archivos in os.walk(directorio):
        dirs[:] = [d for d in dirs if d not in ignorar]
        nivel = raiz.replace(directorio, '').count(os.sep)
        sangria = ' ' * 4 * (nivel)
        resultado.append(f"{sangria}{os.path.basename(raiz)}/")
        sub_sangria = ' ' * 4 * (nivel + 1)
        for archivo in archivos:
            resultado.append(f"{sub_sangria}{archivo}")
    return "\n".join(resultado)

mapa_funciones = {
    "ejecutar_comando_bash": ejecutar_comando_bash,
    "escribir_archivo": escribir_archivo,
    "leer_archivo": leer_archivo,
    "ver_estructura_proyecto": ver_estructura_proyecto
}

# ==========================================
# 3. EL CEREBRO DEL CREADOR (SYSTEM PROMPT)
# ==========================================
instrucciones_creador = (
    "Eres un programador senior autónomo. Tu única misión es escribir código y probar que funcione localmente.\n"
    "REGLA CRÍTICA Y ABSOLUTA: Tienes ESTRICTAMENTE PROHIBIDO usar comandos de Git (ni git add, ni git commit, ni git push). "
    "No debes gestionar el control de versiones. Cuando termines de modificar los archivos solicitados en la tarea, "
    "simplemente da una respuesta final explicando qué archivos has modificado y finaliza tu turno. "
    "El Departamento de QA se encargará de revisar tu código y subirlo a producción."
)

print("🔍 Conectando con Google GenAI y consultando modelos...")
MODELOS_DISPONIBLES = []
try:
    for m in gemini_client.models.list():
        nombre = m.name.lower()
        if 'gemini' in nombre and 'tts' not in nombre and 'audio' not in nombre:
            MODELOS_DISPONIBLES.append(m.name)
    print(f"✅ Encontrados {len(MODELOS_DISPONIBLES)} modelos.")
except Exception as e:
    print(f"⚠️ Error al listar modelos: {e}. Usando fallback.")
    MODELOS_DISPONIBLES = ['gemini-2.5-flash', 'gemini-2.0-flash']

def crear_chat_creador(idx):
    config = types.GenerateContentConfig(
        tools=list(mapa_funciones.values()),
        system_instruction=instrucciones_creador,
        temperature=0.2
    )
    return gemini_client.chats.create(model=MODELOS_DISPONIBLES[idx], config=config)

# ==========================================
# 4. SISTEMA DE QA / INSPECTOR (GROQ)
# ==========================================
def evaluar_codigo_qa(tarea, git_diff):
    print("\n🕵️‍♂️ [QA Inspector] Evaluando código con Groq LLaMA-3.3...")
    prompt_qa = f"""Eres un Ingeniero Jefe de QA. 
El programador acaba de intentar resolver esta tarea: '{tarea}'

Aquí están los cambios exactos que ha hecho en el código (formato Git Diff):
{git_diff}

Tu trabajo es evaluar si estos cambios son correctos, no rompen nada obvio, y cumplen la tarea.
Debes responder ESTRICTAMENTE con este formato de dos líneas:
EVALUACION: (Tu análisis técnico breve de 1 o 2 frases)
VEREDICTO: [APROBADO o RECHAZADO]
"""
    try:
        respuesta = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_qa}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"EVALUACION: Fallo crítico en el motor de QA ({e}). Por seguridad, se bloquea el paso a producción.\nVEREDICTO: RECHAZADO"

# ==========================================
# 5. EL ORQUESTADOR (BUCLE PRINCIPAL)
# ==========================================
print("🤖 Mega-Fábrica Dual-Agent V2 (Google GenAI) Iniciada.")
ARCHIVO_BACKLOG = "backlog.txt"
ARCHIVO_COMPLETADAS = "tareas_completadas.txt"

for archivo in [ARCHIVO_BACKLOG, ARCHIVO_COMPLETADAS]:
    if not os.path.exists(archivo): open(archivo, 'w').close()

modelo_idx = 0
chat = crear_chat_creador(modelo_idx)

while True:
    with open(ARCHIVO_BACKLOG, 'r', encoding='utf-8') as f:
        tareas_pendientes = [l.strip() for l in f.readlines() if l.strip()]
    
    if not tareas_pendientes:
        time.sleep(30)
        continue
        
    tarea_actual = tareas_pendientes[0]
    print(f"\n==================================================")
    print(f"🚀 FASE 1: CREADOR TRABAJANDO EN -> {tarea_actual[:60]}...")
    
    # --- CICLO DEL CREADOR (GEMINI) ---
    try:
        response = chat.send_message(tarea_actual)
        
        while response.function_calls:
            respuestas_herramientas = []
            for tool_call in response.function_calls:
                func_name = tool_call.name
                args = tool_call.args if tool_call.args else {}
                
                res = mapa_funciones[func_name](**args)
                
                respuestas_herramientas.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"resultado": res}
                    )
                )
                
            time.sleep(10)
            response = chat.send_message(respuestas_herramientas)
            
        try:
            texto_final = response.text
        except Exception:
            texto_final = "(Sin respuesta de texto)"
            
        print(f"✅ Creador finalizó. Mensaje: {texto_final[:100]}...")
        
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
            print("❌ Límite Gemini (429). Cambiando modelo...")
            modelo_idx = (modelo_idx + 1) % len(MODELOS_DISPONIBLES)
            chat = crear_chat_creador(modelo_idx)
            continue
        else:
            print(f"⚠️ Creador falló ({e}). Reiniciando tarea...")
            chat = crear_chat_creador(modelo_idx)
            continue

    # --- FASE 2: INSPECTOR DE CALIDAD (QA) ---
    print(f"\n🚀 FASE 2: INSPECCIÓN Y DESPLIEGUE")
    
    subprocess.run("git add -A", shell=True)
    diff_check = subprocess.run("git diff --staged", shell=True, capture_output=True, text=True)
    cambios_codigo = diff_check.stdout.strip()
    
    if not cambios_codigo:
        print("ℹ️ El creador no modificó ningún código. Marcando como completado.")
        veredicto_final = "APROBADO"
    else:
        reporte_qa = evaluar_codigo_qa(tarea_actual, cambios_codigo)
        print(f"📄 Reporte QA:\n{reporte_qa}")
        veredicto_final = "APROBADO" if "APROBADO" in reporte_qa.upper() else "RECHAZADO"

    # --- FASE 3: RESOLUCIÓN ---
    if veredicto_final == "APROBADO":
        if cambios_codigo:
            print("🟢 QA Aprobado. Subiendo a producción...")
            subprocess.run(f'git commit --no-gpg-sign -m "Auto: {tarea_actual[:40]}"', shell=True)
            subprocess.run("git push origin main", shell=True)
            
        with open(ARCHIVO_COMPLETADAS, 'a', encoding='utf-8') as f:
            f.write(tarea_actual + "\n")
        with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
            f.writelines([l + "\n" for l in tareas_pendientes[1:]])
    else:
        print("🔴 QA RECHAZÓ EL CÓDIGO. Bloqueando despliegue.")
        subprocess.run("git reset", shell=True)
        
        feedback = reporte_qa.split('\n')[0]
        nueva_tarea = f"URGENTE (Fallo QA en tarea anterior): {feedback}. Revisa los archivos y arregla el error."
        tareas_pendientes.insert(0, nueva_tarea)
        with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
            f.writelines([l + "\n" for l in tareas_pendientes])

    print("\n🧹 Limpiando memoria para el siguiente ciclo...")
    chat = crear_chat_creador(modelo_idx)