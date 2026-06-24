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
# 2. HERRAMIENTAS
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
    "REGLA CRÍTICA: Tienes ESTRICTAMENTE PROHIBIDO usar comandos de Git. El Departamento de QA subirá el código a producción.\n"
    "Se te proporcionará el contexto de los archivos necesarios en la propia tarea. Úsalo para planificar tu solución y emplea la herramienta 'escribir_archivo' para aplicar los cambios."
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
        return f"EVALUACION: Fallo crítico en QA ({e}). Bloqueo de emergencia.\nVEREDICTO: RECHAZADO"

# ==========================================
# 5. EL ORQUESTADOR (BUCLE PRINCIPAL)
# ==========================================
print("🤖 Mega-Fábrica Tri-Agent V4 (Smart Routing Operativo) Iniciada.")
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
    print(f"\n" + "="*50)
    print(f"🚀 INICIANDO MISIÓN -> {tarea_actual[:60]}...")
    
    # --- FASE 0.1: CLASIFICADOR / ENRUTADOR (GROQ) ---
    print(f"\n🔀 FASE 0.1: ENRUTADOR ANALIZANDO TIPO DE TRABAJO...")
    prompt_router = f"""Analiza la siguiente tarea de desarrollo:
Tarea: '{tarea_actual}'

Determina si la tarea consiste ÚNICAMENTE en ejecutar comandos de terminal (como compilar, comprobar estados con bash, instalar librerías, lanzar tests) o si requiere escribir/modificar código en archivos.
Responde ESTRICTAMENTE con una de estas dos palabras:
- MICROTAREA (Si es solo ejecutar comandos bash o revisar la terminal)
- CODIGO (Si implica crear, editar o pensar la lógica de archivos de código)"""
    
    es_microtarea = False
    try:
        respuesta_router = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_router}],
            model="llama-3.1-8b-instant",
            temperature=0.0
        )
        tipo_tarea = respuesta_router.choices[0].message.content.strip().upper()
        if "MICROTAREA" in tipo_tarea:
            es_microtarea = True
            print("   ↳ ⚡ Enrutamiento Inteligente: Detectada MICROTAREA de terminal. Asignada a Groq LLaMA-3.1.")
        else:
            print("   ↳ 🧠 Enrutamiento Inteligente: Tarea de CÓDIGO complejo. Asignada al arsenal de Gemini.")
    except Exception as e:
        print(f"   ⚠️ Falló el Enrutador ({e}). Por defecto se usará la ruta general.")

    # --- CAMINO B: EJECUCIÓN DIRECTA DE MICROTAREA (GROQ ULTRA-FAST) ---
    if es_microtarea:
        print(f"\n⚡ FASE 1 (MICROTAREA): EJECUTOR COMPILANDO...")
        prompt_ejecutor = f"""Eres un operador de sistemas Linux. Tu única misión es ejecutar el comando bash exacto necesario para cumplir esta tarea: '{tarea_actual}'.
Escribe únicamente el comando bash que vas a ejecutar, envuelto en un bloque de código markdown, por ejemplo: ```bash\nnpm run build\n```. No des explicaciones."""
        try:
            respuesta_ejecutor = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_ejecutor}],
                model="llama-3.1-8b-instant",
                temperature=0.1
            )
            contenido_ejecutor = respuesta_ejecutor.choices[0].message.content
            if "```bash" in contenido_ejecutor:
                comando_extraido = contenido_ejecutor.split("```bash")[1].split("```")[0].strip()
                res_bash = ejecutar_comando_bash(comando_extraido)
                print(f"   ↳ [Resultado Terminal]: {res_bash[:200]}...")
            else:
                print("   ⚠️ No se pudo extraer el comando limpio de Groq.")
            
            # Marcamos directamente como completada al ser de consola pura sin pasar por QA de código
            with open(ARCHIVO_COMPLETADAS, 'a', encoding='utf-8') as f: f.write(tarea_actual + " (Microtarea Bash exitosa)\n")
            with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f: f.writelines([l + "\n" for l in tareas_pendientes[1:]])
            print("\n✅ Microtarea de consola finalizada. Avanzando backlog...")
            continue
        except Exception as e:
            print(f"   ⚠️ Falló el ejecutor rápido ({e}). Derivando tarea al flujo principal...")

    # --- CAMINO A: FLUJO COMPLEJO (SCOUT + MAKER GEMINI) ---
    print(f"\n🗺️ FASE 0.2: EXPLORADOR GROQ PREPARANDO CONTEXTO...")
    estructura_actual = ver_estructura_proyecto(".")
    prompt_scout = f"""Eres un Analista Técnico. Prepara el terreno para el programador.
Tarea: '{tarea_actual}'
Estructura del proyecto:
{estructura_actual}
¿Qué archivos existentes necesita leer el programador para hacer esto? 
Responde SOLO con las rutas de los archivos separadas por comas. Si es un archivo nuevo o no necesita leer nada, responde NINGUNO."""
    
    contexto_inyectado = ""
    try:
        respuesta_scout = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_scout}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        rutas = respuesta_scout.choices[0].message.content.strip()
        print(f"   ↳ Archivos identificados: {rutas}")
        
        if "NINGUNO" not in rutas.upper():
            for ruta in rutas.split(','):
                ruta_limpia = ruta.strip()
                if os.path.exists(ruta_limpia) and os.path.isfile(ruta_limpia):
                    contenido = leer_archivo(ruta_limpia)
                    contexto_inyectado += f"\n--- Archivo: {ruta_limpia} ---\n{contenido}\n"
                    
        if contexto_inyectado:
            tarea_enriquecida = f"TAREA: {tarea_actual}\n\nCONTEXTO PREVIO (Archivos del proyecto):\n{contexto_inyectado}"
            print("   ↳ Contexto empaquetado con éxito.")
        else:
            tarea_enriquecida = tarea_actual
            
    except Exception as e:
        print(f"⚠️ Explorador falló ({e}). Se enviará la tarea a ciegas.")
        tarea_enriquecida = tarea_actual

    # --- FASE 1: CREADOR TRABAJANDO (GEMINI) ---
    print(f"\n🛠️ FASE 1: CREADOR TRABAJANDO...")
    try:
        response = chat.send_message(tarea_enriquecida)
        
        while response.function_calls:
            respuestas_herramientas = []
            for tool_call in response.function_calls:
                func_name = tool_call.name
                args = tool_call.args if tool_call.args else {}
                res = mapa_funciones[func_name](**args)
                respuestas_herramientas.append(
                    types.Part.from_function_response(name=func_name, response={"resultado": res})
                )
            time.sleep(10)
            response = chat.send_message(respuestas_herramientas)
            
        try: texto_final = response.text
        except: texto_final = "(Sin respuesta de texto)"
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

    # --- FASE 2: INSPECTOR DE CALIDAD (QA GROQ) ---
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
        subprocess.run("git reset --hard", shell=True)
        subprocess.run("git clean -fd", shell=True)
        
        feedback = reporte_qa.split('\n')[0]
        nueva_tarea = f"URGENTE (Fallo QA en tarea anterior): {feedback}. Revisa los archivos y arregla el error."
        tareas_pendientes.insert(0, nueva_tarea)
        with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
            f.writelines([l + "\n" for l in tareas_pendientes])

    print("\n🧹 Limpiando memoria para el siguiente ciclo...")
    chat = crear_chat_creador(modelo_idx)