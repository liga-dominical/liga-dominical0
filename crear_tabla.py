from main import conectar_bd

conexion = conectar_bd()
cursor = conexion.cursor()
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_quiniela (
            id_historial INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT,
            jornada INT,
            puntos_jornada INT,
            fecha_cierre TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios_quiniela(id_usuario)
        )
    """)
    conexion.commit()
    print("¡Tabla de historial creada con éxito en Aiven!")
except Exception as e:
    print(f"Error: {e}")
finally:
    cursor.close()
    conexion.close()
