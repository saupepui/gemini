import google.generativeai as genai
from groq import Groq
import subprocess
import os
import time
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ==========================================
# 2. HERRAMIENTAS DEL CREADOR (GEMINI)
# ==========================================
def ejecutar_comando_bash(comando: str) -> str:
    print(f"\n[🔧 Bash]: {comando}")
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=180)
        return f"Salida:\n{result.stdout}\nError:\n{result.stderr}" if result.returncode == 0 else f"Error (Código {result.returncode}):\n{result.stderr}"
    except Exception as e:
        return f"Excepción: {str(e)}"

def escribir_archivo(ruta: str, contenido: str) -> str:
    print(f"\n[📝 Escribir Archivo]: {ruta}")
    try:
        os.makedirs(os.path.dirname(ruta) if os.path.dirname(ruta) else '.', exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return f"Archivo '{ruta}' guardado."
    except Exception as e:
        return f"Error al escribir: {e}"

def leer_archivo(ruta: str) -> str:
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error al leer: {e}"

def ver_estructura_proyecto(directorio: str = ".") -> str:
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
    "No debes gestionar el control de versiones. Cuando termines de modificar los archivos solicitados en la tarea, simplemente da una respuesta final explicando qué archivos has modificado y finaliza tu turno. "
    "El Departamento de QA se encargará de revisar tu código y subirlo a producción."
)

MODELOS_DISPONIBLES = []
try:
    for m in genai.list_models():
        nombre = m.name.lower()
        if 'generatecontent' in [metodo.lower() for metodo in m.supported_generation_methods] and 'gemini' in nombre:
            if 'tts' not in nombre and 'audio' not in nombre:
                MODELOS_DISPONIBLES.append(m.name)
except Exception:
    MODELOS_DISPONIBLES = ['models/gemini-2.0-flash']

def crear_chat_creador(idx, historial=[]):
    model = genai.GenerativeModel(
        model_name=MODELOS_DISPONIBLES[idx], 
        tools=list(mapa_funciones.values()),
        system_instruction=instrucciones_creador
    )
    return model.start_chat(history=historial)

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
            model="llama-3.3-70b-versatile", # <--- MODELO ACTUALIZADO
            temperature=0.1
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        # <--- AHORA ES "FAIL-CLOSED" (BLOQUEO DE EMERGENCIA)
        return f"EVALUACION: Fallo crítico en el motor de QA ({e}). Por seguridad, se bloquea el paso a producción.\nVEREDICTO: RECHAZADO"

# ==========================================
# 5. EL ORQUESTADOR (BUCLE PRINCIPAL)
# ==========================================
print("🤖 Mega-Fábrica Dual-Agent (Maker + QA Checker) Iniciada.")
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
        llamadas = getattr(response.candidates[0].content.parts[0], 'function_call', None)
        
        # Bucle de herramientas (simplificado para no saturar la pantalla)
        while llamadas:
            respuestas_herramientas = []
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    func_name = part.function_call.name
                    args = {k: v for k, v in part.function_call.args.items()}
                    res = mapa_funciones[func_name](**args)
                    respuestas_herramientas.append({
                        "function_response": {"name": func_name, "response": {"resultado": res}}
                    })
            time.sleep(10) # Pausa de red
            response = chat.send_message(respuestas_herramientas)
            llamadas = getattr(response.candidates[0].content.parts[0], 'function_call', None)
            
        print(f"✅ Creador finalizó. Mensaje: {response.text[:100]}...")
        
    except ResourceExhausted:
        print("❌ Límite Gemini. Cambiando modelo...")
        modelo_idx = (modelo_idx + 1) % len(MODELOS_DISPONIBLES)
        chat = crear_chat_creador(modelo_idx)
        continue
    except Exception as e:
        print(f"⚠️ Creador falló ({e}). Reiniciando tarea.")
        chat = crear_chat_creador(modelo_idx)
        continue

    # --- FASE 2: INSPECTOR DE CALIDAD (QA) ---
    print(f"\n🚀 FASE 2: INSPECCIÓN Y DESPLIEGUE")
    
    # Empaquetamos los cambios (staged) para ver qué ha hecho realmente
    subprocess.run("git add -A", shell=True)
    diff_check = subprocess.run("git diff --staged", shell=True, capture_output=True, text=True)
    cambios_codigo = diff_check.stdout.strip()
    
    if not cambios_codigo:
        print("ℹ️ El creador no modificó ningún código. Marcando como completado.")
        veredicto_final = "APROBADO"
    else:
        # Enviamos a Groq a juzgar
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
        subprocess.run("git reset", shell=True) # Quitamos el 'staged' pero dejamos los archivos editados
        
        # Inyectamos el feedback como la nueva máxima prioridad
        feedback = reporte_qa.split('\n')[0] # Cogemos la evaluación
        nueva_tarea = f"URGENTE (Fallo QA en tarea anterior): {feedback}. Revisa los archivos y arregla el error."
        tareas_pendientes.insert(0, nueva_tarea)
        with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
            f.writelines([l + "\n" for l in tareas_pendientes])

    print("\n🧹 Limpiando memoria para el siguiente ciclo...")
    chat = crear_chat_creador(modelo_idx)