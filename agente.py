import google.generativeai as genai
import subprocess
import os
import time
from google.api_core.exceptions import ResourceExhausted

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
    user_input = input("\nTú (Jefe de Proyecto): ")
    if user_input.lower() in ['salir', 'exit', 'quit']:
        break
    
    reintentar_tarea = True
    mensaje_a_enviar = user_input # Puede ser texto o los resultados de una función
    
    while reintentar_tarea:
        try:
            print(f"\n[{MODELOS_DISPONIBLES[modelo_actual_idx]}] está analizando el plan...")
            
            # 1. Enviamos el mensaje
            response = chat.send_message(mensaje_a_enviar)
            
            # Función auxiliar para extraer llamadas (el SDK de Google las esconde en 'parts')
            def extraer_llamadas(resp):
                try:
                    return [part.function_call for part in resp.candidates[0].content.parts if part.function_call]
                except:
                    return []
                    
            llamadas = extraer_llamadas(response)
            
            # 2. Bucle de interceptación de herramientas
            while llamadas:
                respuestas_herramientas = []
                
                for tool_call in llamadas:
                    nombre_func = tool_call.name
                    # Convertimos los argumentos (que vienen en formato Protobuf) a un diccionario de Python
                    argumentos = {k: v for k, v in tool_call.args.items()}
                    
                    # Ejecutamos la función de la herramienta
                    resultado_real = mapa_funciones[nombre_func](**argumentos)
                    
                    # Estructura estricta que exige Google para devolver la respuesta
                    respuestas_herramientas.append({
                        "function_response": {
                            "name": nombre_func,
                            "response": {"resultado": resultado_real}
                        }
                    })
                
                print("⏳ Control manual: Pausa de 10 segundos para cuidar la red...")
                time.sleep(10)
                
                # Actualizamos el mensaje para la siguiente iteración
                mensaje_a_enviar = respuestas_herramientas
                response = chat.send_message(mensaje_a_enviar)
                llamadas = extraer_llamadas(response)
                
            # Si el bucle termina, la IA nos habló en texto normal
            print(f"\n🤖 Reporte Final:\n{response.text}")
            reintentar_tarea = False # Salimos del bucle de reintento con éxito
            
        except ResourceExhausted:
            print(f"\n❌ [Alerta 429] Cuota agotada para el modelo actual.")
            
            # Pasamos al siguiente modelo
            modelo_actual_idx += 1
            
            if modelo_actual_idx >= len(MODELOS_DISPONIBLES):
                print("🚨 ¡Alerta Crítica! Se han agotado todos los modelos del escuadrón.")
                print("Pausa obligatoria de 2 minutos para reiniciar cuotas de los servidores...")
                time.sleep(120)
                modelo_actual_idx = 0 
            
            # Rescatamos el historial y creamos el nuevo chat
            historial_rescatado = chat.history if chat else []
            chat = crear_chat(modelo_actual_idx, historial_rescatado)
            
            print("🔄 Reintentando exactamente donde nos quedamos...")
            # Al no cambiar 'reintentar_tarea', el bucle repite la iteración principal
            
        except Exception as e:
            print(f"\n❌ Ocurrió un error inesperado (no es de cuota): {e}")
            reintentar_tarea = False # Rompemos el bucle si es un error crítico    