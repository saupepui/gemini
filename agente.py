import google.generativeai as genai
import subprocess
import os
import time
from google.api_core.exceptions import ResourceExhausted
import time
import os

# 1. Configuración
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# ==========================================
# 2. HERRAMIENTAS (Sin decoradores)
# ==========================================

def ejecutar_comando_bash(comando: str) -> str:
    print(f"\n[🔧 Bash]: {comando}")
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=90)
        return f"Salida:\n{result.stdout}\nError:\n{result.stderr}" if result.returncode == 0 else f"Error (Código {result.returncode}):\n{result.stderr}"
    except Exception as e:
        return f"Excepción: {str(e)}"

def escribir_archivo(ruta: str, contenido: str) -> str:
    print(f"\n[📝 Crear/Sobrescribir Archivo]: {ruta}")
    try:
        os.makedirs(os.path.dirname(ruta) if os.path.dirname(ruta) else '.', exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return f"Archivo '{ruta}' guardado."
    except Exception as e:
        return f"Error al escribir: {e}"

def leer_archivo(ruta: str) -> str:
    print(f"\n[📖 Leer Archivo]: {ruta}")
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error al leer: {e}"

def ver_estructura_proyecto(directorio: str = ".") -> str:
    print(f"\n[📂 Ver Estructura]: {directorio}")
    resultado = []
    ignorar = {'.git', '__pycache__', 'venv', '.venv'}
    for raiz, dirs, archivos in os.walk(directorio):
        dirs[:] = [d for d in dirs if d not in ignorar]
        nivel = raiz.replace(directorio, '').count(os.sep)
        sangria = ' ' * 4 * (nivel)
        resultado.append(f"{sangria}{os.path.basename(raiz)}/")
        sub_sangria = ' ' * 4 * (nivel + 1)
        for archivo in archivos:
            resultado.append(f"{sub_sangria}{archivo}")
    return "\n".join(resultado)

def reemplazar_en_archivo(ruta: str, texto_antiguo: str, texto_nuevo: str) -> str:
    print(f"\n[✂️ Editar Quirúrgico]: {ruta}")
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        if texto_antiguo not in contenido:
            return f"Error: Texto antiguo no encontrado en '{ruta}'."
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido.replace(texto_antiguo, texto_nuevo, 1))
        return f"Reemplazo exitoso en '{ruta}'."
    except Exception as e:
        return f"Error al editar: {e}"

def buscar_texto_en_proyecto(termino: str, directorio: str = ".") -> str:
    print(f"\n[🔍 Buscar Texto]: '{termino}'")
    coincidencias = []
    ignorar_dirs = {'.git', '__pycache__', 'venv'}
    for raiz, dirs, archivos in os.walk(directorio):
        dirs[:] = [d for d in dirs if d not in ignorar_dirs]
        for archivo in archivos:
            ruta_completa = os.path.join(raiz, archivo)
            try:
                with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                    for num, linea in enumerate(f, 1):
                        if termino in linea:
                            coincidencias.append(f"{ruta_completa}:{num}: {linea.strip()}")
            except: continue
    return "\n".join(coincidencias) if coincidencias else f"No hay coincidencias para '{termino}'."

# Mapeamos los nombres de las funciones a sus referencias en memoria
mapa_funciones = {
    "ejecutar_comando_bash": ejecutar_comando_bash,
    "escribir_archivo": escribir_archivo,
    "leer_archivo": leer_archivo,
    "ver_estructura_proyecto": ver_estructura_proyecto,
    "reemplazar_en_archivo": reemplazar_en_archivo,
    "buscar_texto_en_proyecto": buscar_texto_en_proyecto
}

# ==========================================
# 3. CONFIGURACIÓN DEL SISTEMA DE RESPALDO (CASCADING FALLBACK)
# ==========================================

instrucciones = (
    "Eres un ingeniero de software senior autónomo operando en un contenedor Linux.\n"
    "Cuentas con herramientas para interactuar con el entorno.\n"
    "PROTOCOLO DE INTEGRACIÓN CONTINUA (GIT):\n"
    "  a) Desarrolla el código.\n"
    "  b) Pruébalo usando tu herramienta bash para asegurar que funciona.\n"
    "  c) Si funciona, ejecuta: 'git add .', 'git commit -m \"feat: mensaje\"', y 'git push'.\n"
    "Piensa paso a paso."
)

# Lista de modelos ordenados para el "escuadrón de relevo"
MODELOS_DISPONIBLES = [
    'models/gemini-3.5-flash',
    'models/gemini-2.5-flash',
    'models/gemini-2.0-flash',
    'models/gemini-2.5-pro',
    'models/gemini-pro-latest'
]

modelo_actual_idx = 0

def crear_chat(idx, historial=[]):
    """Inicializa un modelo específico e inyecta el historial anterior."""
    nombre_modelo = MODELOS_DISPONIBLES[idx]
    print(f"\n🔄 [Sistema] Conectando 'cerebro' al modelo: {nombre_modelo}...")
    model = genai.GenerativeModel(
        model_name=nombre_modelo, 
        tools=list(mapa_funciones.values()),
        system_instruction=instrucciones
    )
    # Al pasarle el historial, el nuevo modelo no pierde el contexto de la tarea
    return model.start_chat(history=historial)

# Inicializamos el primer chat
chat = crear_chat(modelo_actual_idx)

print("================================================================")
print("🤖 Super Agente Autónomo (Modo Respaldo en Cascada) Iniciado.")
print("Escribe 'salir' para terminar el programa.")
print("================================================================\n")

while True:
    print("================================================================")
print("🤖 Super Agente Autónomo (Modo BACKLOG INFINITO) Iniciado.")
print("Leyendo tareas de 'backlog.txt'...")
print("================================================================\n")

# Archivo de entrada y archivo de registro de completadas
ARCHIVO_BACKLOG = "backlog.txt"
ARCHIVO_COMPLETADAS = "tareas_completadas.txt"

# Aseguramos que los archivos existan
if not os.path.exists(ARCHIVO_BACKLOG):
    open(ARCHIVO_BACKLOG, 'w').close()
if not os.path.exists(ARCHIVO_COMPLETADAS):
    open(ARCHIVO_COMPLETADAS, 'w').close()

while True:
    # 1. Leemos el backlog
    with open(ARCHIVO_BACKLOG, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    # Filtramos líneas vacías
    tareas_pendientes = [linea.strip() for linea in lineas if linea.strip()]
    
    if not tareas_pendientes:
        print("\n💤 No hay tareas en 'backlog.txt'. Esperando 60 segundos antes de volver a mirar...")
        time.sleep(60)
        continue
        
    # Tomamos la primera tarea de la lista
    tarea_actual = tareas_pendientes[0]
    print(f"\n================================================================")
    print(f"🚀 INICIANDO NUEVA TAREA: {tarea_actual}")
    print(f"================================================================\n")
    
    # --- AQUI EMPIEZA EL BUCLE DE RESPALDO EN CASCADA QUE YA TENÍAMOS ---
    reintentar_tarea = True
    mensaje_a_enviar = tarea_actual 
    
    while reintentar_tarea:
        try:
            print(f"[{MODELOS_DISPONIBLES[modelo_actual_idx]}] está analizando el plan...")
            response = chat.send_message(mensaje_a_enviar)
            
            def extraer_llamadas(resp):
                try:
                    return [part.function_call for part in resp.candidates[0].content.parts if part.function_call]
                except:
                    return []
                    
            llamadas = extraer_llamadas(response)
            
            while llamadas:
                respuestas_herramientas = []
                for tool_call in llamadas:
                    nombre_func = tool_call.name
                    argumentos = {k: v for k, v in tool_call.args.items()}
                    resultado_real = mapa_funciones[nombre_func](**argumentos)
                    
                    respuestas_herramientas.append({
                        "function_response": {
                            "name": nombre_func,
                            "response": {"resultado": resultado_real}
                        }
                    })
                
                print("⏳ Control manual: Pausa de 10 segundos para cuidar la red...")
                time.sleep(10)
                
                mensaje_a_enviar = respuestas_herramientas
                response = chat.send_message(mensaje_a_enviar)
                llamadas = extraer_llamadas(response)
                
            try:
                mensaje_final = response.text
            except Exception:
                mensaje_final = "(El agente completó la tarea en silencio)."
                
            print(f"\n🤖 Reporte Final de la Tarea:\n{mensaje_final}")
            reintentar_tarea = False 
            
            # --- TAREA COMPLETADA CON ÉXITO ---
            # 1. Guardamos la tarea en el registro de completadas
            with open(ARCHIVO_COMPLETADAS, 'a', encoding='utf-8') as f:
                f.write(tarea_actual + "\n")
                
            # 2. La borramos del backlog (reescribiendo el archivo sin la primera línea)
            with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
                f.writelines([linea + "\n" for linea in tareas_pendientes[1:]])
                
            print("\n✅ Tarea tachada del backlog. Limpiando el historial de memoria para el siguiente proyecto...")
            # IMPORTANTE: Reiniciamos el chat para vaciar el contexto y no arrastrar código viejo
            chat = crear_chat(modelo_actual_idx, historial=[]) 
            
        except ResourceExhausted:
            print(f"\n❌ [Alerta 429] Cuota agotada para {MODELOS_DISPONIBLES[modelo_actual_idx]}.")
            modelo_actual_idx += 1
            if modelo_actual_idx >= len(MODELOS_DISPONIBLES):
                print("🚨 Todos los modelos agotados. Pausa de 2 minutos...")
                time.sleep(120)
                modelo_actual_idx = 0 
            chat = crear_chat(modelo_actual_idx, chat.history if chat else [])
            
        except Exception as e:
            print(f"\n❌ Ocurrió un error inesperado: {e}")
            print("Saltando esta tarea problemática para no detener la fábrica...")
            # Si falla de forma crítica, la borramos del backlog para no bloquear la cola infinita
            with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
                f.writelines([linea + "\n" for linea in tareas_pendientes[1:]])
            reintentar_tarea = False 
            chat = crear_chat(modelo_actual_idx, historial=[]) # Limpiamos memoria