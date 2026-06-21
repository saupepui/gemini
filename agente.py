import google.generativeai as genai
import subprocess
import os
import time
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# ==========================================
# 2. HERRAMIENTAS (Sin decoradores)
# ==========================================
def ejecutar_comando_bash(comando: str) -> str:
    print(f"\n[🔧 Bash]: {comando}")
    try:
        # Aumentado a 180s para que npm/Astro tengan tiempo de instalarse
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
    print(f"\n[📖 Leer Archivo]: {ruta}")
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error al leer: {e}"

def ver_estructura_proyecto(directorio: str = ".") -> str:
    print(f"\n[📂 Ver Estructura]: {directorio}")
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
    ignorar_dirs = {'.git', '__pycache__', 'venv', 'node_modules'}
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

mapa_funciones = {
    "ejecutar_comando_bash": ejecutar_comando_bash,
    "escribir_archivo": escribir_archivo,
    "leer_archivo": leer_archivo,
    "ver_estructura_proyecto": ver_estructura_proyecto,
    "reemplazar_en_archivo": reemplazar_en_archivo,
    "buscar_texto_en_proyecto": buscar_texto_en_proyecto
}

# ==========================================
# 3. CONFIGURACIÓN DEL SISTEMA IA (DINÁMICO)
# ==========================================
instrucciones = (
    "Eres un ingeniero de software senior autónomo operando en un contenedor Linux.\n"
    "Cuentas con herramientas para interactuar con el entorno.\n"
    "PROTOCOLO DE TRABAJO:\n"
    "  1) Analiza la tarea solicitada.\n"
    "  2) Usa bash o escribe archivos según necesites.\n"
    "  3) Verifica con bash si compila o hay errores.\n"
    "  4) Usa git add, commit y push al terminar.\n"
    "Piensa paso a paso y sé conciso."
)

print("🔍 Consultando a los servidores de Google tu arsenal de modelos...")
MODELOS_DISPONIBLES = []
try:
    for m in genai.list_models():
        nombre = m.name.lower()
        if 'generatecontent' in [metodo.lower() for metodo in m.supported_generation_methods] and 'gemini' in nombre:
            # Filtro vital: Excluir modelos que solo devuelven audio o fallan en texto
            if 'tts' not in nombre and 'audio' not in nombre:
                MODELOS_DISPONIBLES.append(m.name)
    print(f"✅ ¡Arsenal cargado! Tienes {len(MODELOS_DISPONIBLES)} modelos de texto listos para el relevo.")
except Exception as e:
    print(f"❌ Error al consultar modelos: {e}")
    MODELOS_DISPONIBLES = ['models/gemini-2.0-flash', 'models/gemini-1.5-flash']

modelo_actual_idx = 0

def crear_chat(idx, historial=[]):
    nombre_modelo = MODELOS_DISPONIBLES[idx]
    print(f"\n🔄 [Sistema] Conectando 'cerebro' al modelo: {nombre_modelo}...")
    model = genai.GenerativeModel(
        model_name=nombre_modelo, 
        tools=list(mapa_funciones.values()),
        system_instruction=instrucciones
    )
    return model.start_chat(history=historial)

chat = crear_chat(modelo_actual_idx)

# ==========================================
# 4. MOTOR PRINCIPAL (BACKLOG INFINITO)
# ==========================================
print("================================================================")
print("🤖 Super Agente Autónomo (Modo BACKLOG INFINITO) Iniciado.")
print("Leyendo tareas de 'backlog.txt'...")
print("================================================================\n")

ARCHIVO_BACKLOG = "backlog.txt"
ARCHIVO_COMPLETADAS = "tareas_completadas.txt"

if not os.path.exists(ARCHIVO_BACKLOG):
    open(ARCHIVO_BACKLOG, 'w').close()
if not os.path.exists(ARCHIVO_COMPLETADAS):
    open(ARCHIVO_COMPLETADAS, 'w').close()

while True:
    with open(ARCHIVO_BACKLOG, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    tareas_pendientes = [linea.strip() for linea in lineas if linea.strip()]
    
    if not tareas_pendientes:
        print("\n💤 No hay tareas en 'backlog.txt'. Esperando 30 segundos antes de volver a mirar...")
        time.sleep(30)
        continue
        
    tarea_actual = tareas_pendientes[0]
    print(f"\n" + "="*64)
    print(f"🚀 INICIANDO NUEVA TAREA: {tarea_actual[:100]}...")
    print("="*64 + "\n")
    
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
                    
                    # --- AÑADE ESTA LÍNEA AQUÍ ---
                    print(f"   ↳ [Resultado]: {str(resultado_real)[:300]}...")

                    respuestas_herramientas.append({
                        "function_response": {
                            "name": nombre_func,
                            "response": {"resultado": resultado_real}
                        }
                    })
                
                print("⏳ Control manual: Pausa de 30 segundos para cuidar la red...")
                time.sleep(30)
                
                mensaje_a_enviar = respuestas_herramientas
                response = chat.send_message(mensaje_a_enviar)
                llamadas = extraer_llamadas(response)
                
            try:
                mensaje_final = response.text
            except Exception:
                mensaje_final = "(El agente completó la tarea en silencio)."
                
            print(f"\n🤖 Reporte Final de la Tarea:\n{mensaje_final}")
            reintentar_tarea = False 
            
            with open(ARCHIVO_COMPLETADAS, 'a', encoding='utf-8') as f:
                f.write(tarea_actual + "\n")
                
            with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
                f.writelines([linea + "\n" for linea in tareas_pendientes[1:]])
                
            print("\n✅ Tarea tachada del backlog. Limpiando el historial de memoria para el siguiente paso...")
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
            # Blindaje total contra errores de servidor y modalidades de la API
            error_str = str(e).lower()
            if "404" in error_str or "400" in error_str or "api" in error_str or "modalities" in error_str:
                print("🚨 Error crítico de la API de Google. Deteniendo la fábrica para salvar el backlog.")
                exit(1) 
            else:
                print("Saltando esta tarea problemática para no detener la fábrica...")
                with open(ARCHIVO_BACKLOG, 'w', encoding='utf-8') as f:
                    f.writelines([linea + "\n" for linea in tareas_pendientes[1:]])
            reintentar_tarea = False 
            chat = crear_chat(modelo_actual_idx, historial=[])