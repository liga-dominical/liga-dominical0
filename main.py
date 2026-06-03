from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi import HTTPException
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI(title="API Liga Dominical")

# Dar permisos para que cualquier página web pueda consultar tu API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Función para conectar a la base de datos
def conectar_bd():
    try:
        conexion = mysql.connector.connect(
            host="bd-ligatoto-liga-dominical.h.aivencloud.com",
            port=24214,
            user="avnadmin",
            password="AVNS_WFnpd1c2ax2fvQzCy1v",
            database="defaultdb"
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

class StatJugador(BaseModel):
    id_jugador: int
    goles: int
    asistencias: int
    amarillas: int
    rojas: int
    es_portero: bool = False  # Para saber si actualizamos las estadísticas de portero

class DatosResultado(BaseModel):
    id_partido: int
    goles_local: int
    goles_visitante: int
    stats: List[StatJugador]

@app.get("/")
def leer_raiz():
    return {"mensaje": "¡El servidor de la liga está funcionando correctamente!"}

@app.post("/login")
def login_admin(usuario: str = Form(...), password: str = Form(...)):
    # Aquí definimos tu usuario y contraseña maestro. 
    # (En un futuro lo podemos conectar a la base de datos, por ahora será directo)
    if usuario == "admin" and password == "osone2026":
        return {"mensaje": "Acceso concedido"}
    else:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@app.get("/equipos")
def obtener_equipos():
    conexion = conectar_bd()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    cursor = conexion.cursor(dictionary=True) 
    
    # Esta consulta calcula todo en tiempo real sumando los partidos jugados
    consulta = """
        SELECT 
            e.nombre_equipo, 
            d.nombre AS division,
            COUNT(p.id_partido) AS pj,
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND ((p.id_local = e.id_equipo AND p.goles_local > p.goles_visitante) OR (p.id_visitante = e.id_equipo AND p.goles_visitante > p.goles_local)) THEN 1 
                ELSE 0 
            END), 0) AS pg,
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND p.goles_local = p.goles_visitante THEN 1 
                ELSE 0 
            END), 0) AS pe,
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND ((p.id_local = e.id_equipo AND p.goles_local < p.goles_visitante) OR (p.id_visitante = e.id_equipo AND p.goles_visitante < p.goles_local)) THEN 1 
                ELSE 0 
            END), 0) AS pp,
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND p.id_local = e.id_equipo THEN p.goles_local 
                WHEN p.id_partido IS NOT NULL AND p.id_visitante = e.id_equipo THEN p.goles_visitante 
                ELSE 0 
            END), 0) AS gf,
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND p.id_local = e.id_equipo THEN p.goles_visitante 
                WHEN p.id_partido IS NOT NULL AND p.id_visitante = e.id_equipo THEN p.goles_local 
                ELSE 0 
            END), 0) AS gc,
            (IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND p.id_local = e.id_equipo THEN p.goles_local 
                WHEN p.id_partido IS NOT NULL AND p.id_visitante = e.id_equipo THEN p.goles_visitante 
                ELSE 0 
            END), 0) - 
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND p.id_local = e.id_equipo THEN p.goles_visitante 
                WHEN p.id_partido IS NOT NULL AND p.id_visitante = e.id_equipo THEN p.goles_local 
                ELSE 0 
            END), 0)) AS dg,
            IFNULL(SUM(CASE 
                WHEN p.id_partido IS NOT NULL AND ((p.id_local = e.id_equipo AND p.goles_local > p.goles_visitante) OR (p.id_visitante = e.id_equipo AND p.goles_visitante > p.goles_local)) THEN 3
                WHEN p.id_partido IS NOT NULL AND p.goles_local = p.goles_visitante THEN 1
                ELSE 0 
            END), 0) AS puntos
        FROM equipos e
        JOIN divisiones d ON e.id_division = d.id_division
        LEFT JOIN partidos p ON (e.id_equipo = p.id_local OR e.id_equipo = p.id_visitante) AND p.estatus = 'Jugado'
        GROUP BY e.id_equipo, e.nombre_equipo, d.nombre
        ORDER BY puntos DESC, dg DESC, gf DESC
    """
    
    cursor.execute(consulta)
    equipos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return {"equipos": equipos}

# --- RUTAS PARA LAS ESTADÍSTICAS INDIVIDUALES ---

@app.get("/goleadores")
def obtener_goleadores():
    conexion = conectar_bd()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error al conectar con la BD")
    cursor = conexion.cursor(dictionary=True)
    
    consulta = """
        SELECT j.nombre_completo, e.nombre_equipo, j.goles_totales, d.nombre AS division
        FROM jugadores j
        JOIN equipos e ON j.id_equipo = e.id_equipo
        JOIN divisiones d ON e.id_division = d.id_division
        ORDER BY j.goles_totales DESC
    """
    cursor.execute(consulta)
    goleadores = cursor.fetchall()
    cursor.close()
    conexion.close()
    return {"goleadores": goleadores}

@app.get("/asistencias")
def obtener_asistencias():
    conexion = conectar_bd()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error al conectar con la BD")
    cursor = conexion.cursor(dictionary=True)
    
    consulta = """
        SELECT j.nombre_completo, e.nombre_equipo, j.asistencias, d.nombre AS division
        FROM jugadores j
        JOIN equipos e ON j.id_equipo = e.id_equipo
        JOIN divisiones d ON e.id_division = d.id_division
        ORDER BY j.asistencias DESC
    """
    cursor.execute(consulta)
    asistencias = cursor.fetchall()
    cursor.close()
    conexion.close()
    return {"asistencias": asistencias}

@app.get("/porteros")
def obtener_porteros():
    conexion = conectar_bd()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error al conectar con la BD")
    cursor = conexion.cursor(dictionary=True)
    
    consulta = """
        SELECT j.nombre_completo, e.nombre_equipo, j.goles_recibidos, j.porterias_cero, d.nombre AS division
        FROM jugadores j
        JOIN equipos e ON j.id_equipo = e.id_equipo
        JOIN divisiones d ON e.id_division = d.id_division
        WHERE j.posicion = 'Portero'
        ORDER BY j.goles_recibidos ASC, j.porterias_cero DESC
    """
    cursor.execute(consulta)
    porteros = cursor.fetchall()
    cursor.close()
    conexion.close()
    return {"porteros": porteros}

@app.get("/jornadas")
def obtener_jornadas():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT jornada FROM partidos ORDER BY jornada DESC")
    jornadas = cursor.fetchall()
    conexion.close()
    return {"jornadas": jornadas}

@app.get("/partidos/{division}/{jornada}")
def obtener_partidos(division: str, jornada: int):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    consulta = """
        SELECT p.id_partido, p.id_local, p.id_visitante, p.goles_local, p.goles_visitante, 
               p.id_campo, p.jornada, p.estatus, 
               DATE_FORMAT(p.dia, '%Y-%m-%d') AS dia,
               TIME_FORMAT(p.hora, '%H:%i') AS hora,
               l.nombre_equipo AS local, v.nombre_equipo AS visitante
        FROM partidos p
        JOIN equipos l ON p.id_local = l.id_equipo
        JOIN equipos v ON p.id_visitante = v.id_equipo
        JOIN divisiones d ON l.id_division = d.id_division
        WHERE d.nombre = %s AND p.jornada = %s
    """
    cursor.execute(consulta, (division, jornada))
    partidos = cursor.fetchall()
    conexion.close()
    return {"partidos": partidos}

@app.post("/registrar_partido")
def registrar_partido(
    id_local: int = Form(...),
    id_visitante: int = Form(...),
    goles_local: int = Form(0),
    goles_visitante: int = Form(0),
    id_campo: int = Form(...),
    jornada: int = Form(...),
    dia: str = Form(...),
    hora: str = Form("08:00"),
    estatus: str = Form("Programado"),
    tipo_partido: str = Form("Liga")
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    consulta = """
        INSERT INTO partidos (id_local, id_visitante, goles_local, goles_visitante, id_campo, jornada, dia, hora, estatus, tipo_partido)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(consulta, (id_local, id_visitante, goles_local, goles_visitante, id_campo, jornada, dia, hora, estatus, tipo_partido))
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"mensaje": "Partido registrado con éxito"}

@app.get("/lista_equipos")
def lista_equipos():
    conexion = conectar_bd()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error al conectar con la base de datos")
    
    cursor = conexion.cursor(dictionary=True)
    consulta = """
        SELECT e.id_equipo, e.nombre_equipo, d.nombre AS division 
        FROM equipos e
        JOIN divisiones d ON e.id_division = d.id_division
    """
    cursor.execute(consulta)
    equipos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return {"equipos": equipos}

# ¡AQUÍ ESTÁ EL CAMBIO! Se agregaron p.id_local, p.id_visitante y p.estatus a la consulta SQL
@app.get("/todos_los_partidos")
def todos_los_partidos():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    consulta = """
        SELECT p.id_partido, p.jornada, p.id_local, p.id_visitante, p.estatus,
               DATE_FORMAT(p.dia, '%Y-%m-%d') as dia, 
               TIME_FORMAT(p.hora, '%H:%i') as hora, l.nombre_equipo AS local, v.nombre_equipo AS visitante
        FROM partidos p
        JOIN equipos l ON p.id_local = l.id_equipo
        JOIN equipos v ON p.id_visitante = v.id_equipo
        ORDER BY p.id_partido DESC
    """
    cursor.execute(consulta)
    partidos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return {"partidos": partidos}

@app.delete("/borrar_partido/{id_partido}")
def borrar_partido(id_partido: int):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM partidos WHERE id_partido = %s", (id_partido,))
    conexion.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conexion.close()
    
    if filas_afectadas == 0:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
        
    return {"mensaje": "Partido eliminado correctamente"}

@app.get("/jugadores_equipo/{id_equipo}")
def jugadores_equipo(id_equipo: int):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_jugador, nombre_completo, posicion FROM jugadores WHERE id_equipo = %s", (id_equipo,))
    jugadores = cursor.fetchall()
    conexion.close()
    return {"jugadores": jugadores}

@app.post("/guardar_resultados")
def guardar_resultados(datos: DatosResultado):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        # 1. Actualizar el marcador del partido y cambiar estatus a 'Jugado'
        cursor.execute("""
            UPDATE partidos 
            SET goles_local = %s, goles_visitante = %s, estatus = 'Jugado' 
            WHERE id_partido = %s
        """, (datos.goles_local, datos.goles_visitante, datos.id_partido))
        
        # Necesitamos saber qué equipos jugaron para aplicar las reglas de porteros
        cursor.execute("SELECT id_local, id_visitante FROM partidos WHERE id_partido = %s", (datos.id_partido,))
        partido = cursor.fetchone()
        id_local, id_visitante = partido[0], partido[1]

        # 2. Iterar por cada jugador enviado para sumarle sus estadísticas
        for stat in datos.stats:
            # A todos los que se envíen en la lista se les cuenta como partido jugado
            cursor.execute("""
                UPDATE jugadores 
                SET partidos_jugados = COALESCE(partidos_jugados, 0) + 1,
                    goles_totales = COALESCE(goles_totales, 0) + %s, 
                    asistencias = COALESCE(asistencias, 0) + %s, 
                    amarillas = COALESCE(amarillas, 0) + %s, 
                    rojas = COALESCE(rojas, 0) + %s 
                WHERE id_jugador = %s
            """, (stat.goles, stat.asistencias, stat.amarillas, stat.rojas, stat.id_jugador))
            
            # Si el jugador es guardameta, calculamos sus estadísticas específicas
            if stat.es_portero:
                # Averiguamos si su equipo era local o visitante para saber cuántos goles recibió
                cursor.execute("SELECT id_equipo FROM jugadores WHERE id_jugador = %s", (stat.id_jugador,))
                id_equipo_jugador = cursor.fetchone()[0]
                
                goles_en_contra = datos.goles_visitante if id_equipo_jugador == id_local else datos.goles_local
                
                if goles_en_contra == 0:
                    cursor.execute("""
                        UPDATE jugadores 
                        SET porterias_cero = COALESCE(porterias_cero, 0) + 1 
                        WHERE id_jugador = %s
                    """, (stat.id_jugador,))
                else:
                    cursor.execute("""
                        UPDATE jugadores 
                        SET goles_recibidos = COALESCE(goles_recibidos, 0) + %s 
                        WHERE id_jugador = %s
                    """, (goles_en_contra, stat.id_jugador))
                    
        conexion.commit()
        return {"mensaje": "Resultados y estadísticas del acta guardados con éxito"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    finally:
        cursor.close()
        conexion.close()

@app.get("/lista_divisiones")
def lista_divisiones():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id_division, nombre FROM divisiones")
    divisiones = cursor.fetchall()
    conexion.close()
    return {"divisiones": divisiones}

@app.post("/registrar_equipo")
def registrar_equipo(
    nombre_equipo: str = Form(...),
    id_division: int = Form(...)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "INSERT INTO equipos (nombre_equipo, id_division) VALUES (%s, %s)",
            (nombre_equipo, id_division)
        )
        conexion.commit()
        return {"mensaje": "Equipo registrado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.post("/registrar_jugador")
def registrar_jugador(
    nombre_completo: str = Form(...),
    id_equipo: int = Form(...),
    posicion: str = Form(...)
):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        # Insertamos respetando las columnas exactas de tu tabla 'jugadores'
        consulta = """
            INSERT INTO jugadores (nombre_completo, id_equipo, posicion, partidos_jugados, goles_totales, asistencias, amarillas, rojas, porterias_cero, goles_recibidos)
            VALUES (%s, %s, %s, 0, 0, 0, 0, 0, 0, 0)
        """
        cursor.execute(consulta, (nombre_completo, id_equipo, posicion))
        conexion.commit()
        return {"mensaje": "Jugador registrado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()
