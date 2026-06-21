import sqlite3
import os

DB_PATH = "tareas.db"

def obtener_conexion():
    """Obtiene una conexión a la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)

def inicializar_db():
    """Crea la tabla de tareas si no existe."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                completada INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

def agregar_tarea(descripcion):
    """Agrega una nueva tarea a la base de datos."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tareas (descripcion, completada) VALUES (?, 0)", (descripcion,))
        conn.commit()
        return cursor.lastrowid

def listar_tareas():
    """Devuelve todas las tareas de la base de datos."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, descripcion, completada FROM tareas")
        return cursor.fetchall()

def marcar_completada(tarea_id):
    """Marca una tarea como completada dado su ID."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tareas SET completada = 1 WHERE id = ?", (tarea_id,))
        conn.commit()
        return cursor.rowcount > 0

def eliminar_tarea(tarea_id):
    """Elimina una tarea de la base de datos dado su ID."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        return cursor.rowcount > 0
