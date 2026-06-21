import sys
import os

# Añadir el directorio actual al path para importar db.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db

def mostrar_menu():
    print("\n=== GESTOR DE TAREAS PENDIENTES ===")
    print("1. Añadir tarea")
    print("2. Listar tareas")
    print("3. Marcar tarea como completada")
    print("4. Eliminar una tarea")
    print("5. Salir")
    print("===================================")

def agregar():
    descripcion = input("Ingrese la descripción de la tarea: ").strip()
    if descripcion:
        id_tarea = db.agregar_tarea(descripcion)
        print(f"¡Tarea agregada exitosamente con ID: {id_tarea}!")
    else:
        print("La descripción no puede estar vacía.")

def listar():
    tareas = db.listar_tareas()
    if not tareas:
        print("\nNo hay tareas registradas.")
        return
    
    print("\n--- LISTA DE TAREAS ---")
    for tarea in tareas:
        id_tarea, descripcion, completada = tarea
        estado = "[✔] Completada" if completada == 1 else "[ ] Pendiente"
        print(f"{id_tarea}. {descripcion} {estado}")
    print("----------------------")

def completar():
    listar()
    tareas = db.listar_tareas()
    if not tareas:
        return
    try:
        id_tarea = int(input("Ingrese el ID de la tarea que desea marcar como completada: "))
        if db.marcar_completada(id_tarea):
            print(f"¡Tarea con ID {id_tarea} marcada como completada!")
        else:
            print(f"No se encontró ninguna tarea con el ID {id_tarea}.")
    except ValueError:
        print("Por favor, ingrese un número ID válido.")

def eliminar():
    listar()
    tareas = db.listar_tareas()
    if not tareas:
        return
    try:
        id_tarea = int(input("Ingrese el ID de la tarea que desea eliminar: "))
        if db.eliminar_tarea(id_tarea):
            print(f"¡Tarea con ID {id_tarea} eliminada exitosamente!")
        else:
            print(f"No se encontró ninguna tarea con el ID {id_tarea}.")
    except ValueError:
        print("Por favor, ingrese un número ID válido.")

def main():
    db.inicializar_db()
    
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción (1-5): ").strip()
        
        if opcion == "1":
            agregar()
        elif opcion == "2":
            listar()
        elif opcion == "3":
            completar()
        elif opcion == "4":
            eliminar()
        elif opcion == "5":
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    main()
