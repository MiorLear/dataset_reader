import sqlite3
import pandas as pd
import os
from InquirerPy import prompt
import subprocess
import requests  # Para la integración con Ollama 3.1

# Función para crear la base de datos SQLite desde un archivo CSV
def create_sqlite_from_csv(csv_file, db_name):
    df = pd.read_csv(csv_file)

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    table_name = os.path.splitext(os.path.basename(csv_file))[0]
    columns = ', '.join([f'"{col}" TEXT' for col in df.columns])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});")

    for index, row in df.iterrows():
        values = tuple(row)
        placeholders = ', '.join(['?'] * len(values))
        cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders});", values)

    conn.commit()
    conn.close()
    print(f"📊 Base de datos '{db_name}' creada con éxito desde el archivo '{csv_file}'.")

# Función para crear la base de datos SQLite desde un archivo Excel
def create_sqlite_from_excel(excel_file, db_name):
    xls = pd.ExcelFile(excel_file)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        table_name = sheet_name
        columns = ', '.join([f'"{col}" TEXT' for col in df.columns])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});")

        for index, row in df.iterrows():
            values = tuple(row)
            placeholders = ', '.join(['?'] * len(values))
            cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders});", values)

    conn.commit()
    conn.close()
    print(f"📊 Base de datos '{db_name}' creada con éxito desde el archivo '{excel_file}'.")

# Función para mostrar las tablas existentes en la base de datos
def show_tables(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("\nTablas disponibles en la base de datos 📑:")
    if tables:
        table_names = [table[0] for table in tables]
        return table_names
    else:
        print("❌ No hay tablas en la base de datos.")
        return []
    conn.close()

# Función para mostrar ejemplos de consultas SQL
def show_example_queries():
    print("\n📝 Ejemplos de consultas SQL que puedes intentar:")
    print("1️⃣ Obtener todos los registros de una tabla:")
    print("   SELECT * FROM nombre_de_tu_tabla;")
    print("2️⃣ Contar el número de registros en una tabla:")
    print("   SELECT COUNT(*) FROM nombre_de_tu_tabla;")
    print("3️⃣ Filtrar registros con una condición:")
    print("   SELECT * FROM nombre_de_tu_tabla WHERE nombre_columna = 'valor';")
    print("4️⃣ Hacer un agregado (por ejemplo, promedio):")
    print("   SELECT AVG(nombre_columna) FROM nombre_de_tu_tabla;")
    print("5️⃣ Ordenar los registros:")
    print("   SELECT * FROM nombre_de_tu_tabla ORDER BY nombre_columna DESC;")
    print("6️⃣ Limitar el número de resultados:")
    print("   SELECT * FROM nombre_de_tu_tabla LIMIT 5;")

# Función para limpiar la pantalla
def clear_screen():
    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para Unix/Linux/MacOS
        os.system('clear')

# Función para interactuar con Ollama 3.1
def query_with_ollama(query):
    url = "http://localhost:11411/v1/complete"  # URL local donde Ollama está corriendo
    payload = {
        "model": "3.1",  # Usamos el modelo 3.1 de Ollama
        "input": query,  # La consulta que se envía
    }
    
    try:
        # Hacer la solicitud POST a Ollama
        response = requests.post(url, json=payload)
        
        # Comprobar si la respuesta fue exitosa
        response.raise_for_status()

        # Obtener la respuesta de Ollama
        result = response.json()['choices'][0]['text']
        return result

    except Exception as e:
        return f"❌ Error al hacer la consulta con Ollama: {e}"

# Función para el menú interactivo
def interactive_menu(db_name):
    while True:
        tables = show_tables(db_name)  # Mostrar tablas disponibles
        if not tables:
            return  # Si no hay tablas, termina el menú

        table_choices = [{"name": table, "value": table} for table in tables]  # Crear opciones para selectpicker
        table_choices.append({"name": "Ayuda 🆘", "value": "help"})  # Agregar opción de ayuda
        table_choices.append({"name": "Consulta Ollama 3.1 🤖", "value": "ollama"})  # Opción para consulta con Ollama

        # Usamos PyInquirer para mostrar un selectpicker
        questions = [
            {
                'type': 'list',
                'name': 'table',
                'message': '📑 Elige una tabla para consultar:',
                'choices': table_choices,
            }
        ]

        answers = prompt(questions)

        if answers['table'] == "help":
            show_example_queries()  # Mostrar ejemplos de consultas
            continue

        if answers['table'] == "ollama":
            query = input("Introduce tu consulta para Ollama 3.1: ").strip()
            result = query_with_ollama(query)
            print(f"Ollama 3.1 responde: {result}")
            continue

        query = input(f"\nIntroduce tu consulta SQL para la tabla '{answers['table']}': ").strip()
        
        if query.lower() == "exit":
            print("👋 Saliendo del menú...")
            break

        if query.lower() == 'clear':
            clear_screen()
            continue
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()

            cursor.execute(query)
            rows = cursor.fetchall()

            if rows:
                headers = [desc[0] for desc in cursor.description]
                print("\n" + " | ".join(headers))
                for row in rows:
                    print(" | ".join(str(cell) for cell in row))
            else:
                print("✔️ Consulta ejecutada correctamente, pero no hay resultados.")
            
            conn.close()
        except Exception as e:
            print(f"❌ Error en la consulta: {e}")

# Función principal
def main():
    while True:
        print("\n🔄 Bienvenido al sistema de bases de datos interactivo.")
        file_path = input("📂 Introduce la ruta al archivo CSV o Excel: ").strip()

        # Validar que el nombre del archivo para la base de datos tenga la extensión .db
        db_name = input("💾 Introduce el nombre para la base de datos SQLite (por ejemplo, 'mi_base.db'): ").strip()
        if not db_name.endswith('.db'):
            print("❌ El nombre de la base de datos debe terminar con '.db'.")
            continue

        if not os.path.exists(file_path):
            print("❌ No se encontró el archivo, por favor verifica la ruta.")
            continue

        if file_path.endswith('.csv'):
            create_sqlite_from_csv(file_path, db_name)
            break
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            create_sqlite_from_excel(file_path, db_name)
            break
        else:
            print("❌ El archivo debe ser un CSV o un archivo Excel (.csv, .xlsx, .xls).")
            continue

    # Mostrar el menú interactivo para hacer consultas
    interactive_menu(db_name)

if __name__ == "__main__":
    main()
