import mysql.connector

try:
    print("Conectando a la nube de Aiven...")
    db = mysql.connector.connect(
        host="bd-ligatoto-liga-dominical.h.aivencloud.com",
        port=24214,
        user="avnadmin",
        password="AVNS_WFnpd1c2ax2fvQzCy1v",
        database="defaultdb"
    )
    cursor = db.cursor()

    print("Creando tabla de usuarios...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios_quiniela (
        id_usuario INT AUTO_INCREMENT PRIMARY KEY,
        nombre_completo VARCHAR(100) NOT NULL,
        correo VARCHAR(100) UNIQUE NOT NULL,
        contrasena VARCHAR(255) NOT NULL,
        puntos_totales INT DEFAULT 0
    )
    """)

    print("Creando tabla de predicciones...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predicciones (
        id_prediccion INT AUTO_INCREMENT PRIMARY KEY,
        id_usuario INT,
        id_partido INT,
        pred_goles_local INT,
        pred_goles_visitante INT,
        pred_amarillas INT DEFAULT 0,
        pred_rojas INT DEFAULT 0,
        puntos_obtenidos INT DEFAULT 0,
        procesada BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (id_usuario) REFERENCES usuarios_quiniela(id_usuario),
        FOREIGN KEY (id_partido) REFERENCES partidos(id_partido)
    )
    """)

    db.commit()
    print("¡Éxito! Las tablas de la quiniela ya están listas en tu base de datos.")
    db.close()

except Exception as e:
    print("Ocurrió un error:", e)
