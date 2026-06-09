from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi import HTTPException
from fastapi import Form
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import hashlib

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
        # Llamamos al motor de la quiniela para repartir los puntos
        calcular_puntos_quiniela(datos.id_partido, datos.goles_local, datos.goles_visitante)
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

# ==========================================
# MÓDULO QUINIELA: REGISTRO Y LOGIN
# ==========================================

def encriptar_password(password: str):
    # Encripta la contraseña usando SHA-256
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/registro_quiniela")
async def registro_quiniela(nombre: str = Form(...), correo: str = Form(...), password: str = Form(...)):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        pw_hash = encriptar_password(password)
        cursor.execute(
            "INSERT INTO usuarios_quiniela (nombre_completo, correo, contrasena) VALUES (%s, %s, %s)",
            (nombre, correo, pw_hash)
        )
        conexion.commit()
        return {"mensaje": "¡Cuenta creada con éxito!"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado en la quiniela.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.post("/login_quiniela")
async def login_quiniela(correo: str = Form(...), password: str = Form(...)):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        pw_hash = encriptar_password(password)
        cursor.execute(
            "SELECT id_usuario, nombre_completo, puntos_totales FROM usuarios_quiniela WHERE correo = %s AND contrasena = %s",
            (correo, pw_hash)
        )
        usuario = cursor.fetchone()
        
        if usuario:
            return {"mensaje": "Login exitoso", "usuario": usuario}
        else:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

# Modelos para recibir las predicciones en lote
class Prediccion(BaseModel):
    id_partido: int
    goles_local: int
    goles_visitante: int

class PayloadPredicciones(BaseModel):
    id_usuario: int
    predicciones: List[Prediccion]

@app.get("/partidos_quiniela")
async def partidos_quiniela():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Solo traemos los partidos que tienen estatus 'Programado'
        cursor.execute("""
            SELECT p.id_partido, p.jornada, p.dia, p.hora, 
                   el.nombre_equipo AS local, ev.nombre_equipo AS visitante
            FROM partidos p
            JOIN equipos el ON p.id_local = el.id_equipo
            JOIN equipos ev ON p.id_visitante = ev.id_equipo
            WHERE p.estatus = 'Programado'
        """)
        partidos = cursor.fetchall()
        return {"partidos": partidos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.post("/guardar_predicciones")
async def guardar_predicciones(payload: PayloadPredicciones):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        for pred in payload.predicciones:
            # Revisamos si el usuario ya había apostado en este partido (por si quiere cambiar su marcador antes de que empiece)
            cursor.execute("SELECT id_prediccion FROM predicciones WHERE id_usuario = %s AND id_partido = %s", 
                           (payload.id_usuario, pred.id_partido))
            existe = cursor.fetchone()
            
            if existe:
                cursor.execute("""
                    UPDATE predicciones SET pred_goles_local = %s, pred_goles_visitante = %s 
                    WHERE id_prediccion = %s
                """, (pred.goles_local, pred.goles_visitante, existe[0]))
            else:
                cursor.execute("""
                    INSERT INTO predicciones (id_usuario, id_partido, pred_goles_local, pred_goles_visitante)
                    VALUES (%s, %s, %s, %s)
                """, (payload.id_usuario, pred.id_partido, pred.goles_local, pred.goles_visitante))
        conexion.commit()
        return {"mensaje": "¡Pronósticos guardados correctamente!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

def calcular_puntos_quiniela(id_partido, goles_l_real, goles_v_real):
    print("\n--- INICIANDO MOTOR DE QUINIELA ---")
    print(f"Partido ID: {id_partido} | Marcador Oficial: {goles_l_real} - {goles_v_real}")
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Usamos 0 en lugar de FALSE por compatibilidad estricta con MySQL
        cursor.execute("SELECT * FROM predicciones WHERE id_partido = %s AND procesada = 0", (id_partido,))
        predicciones = cursor.fetchall()
        print(f"-> Predicciones encontradas sin procesar: {len(predicciones)}")
        
        for p in predicciones:
            puntos = 0
            print(f"\nRevisando Jugador ID {p['id_usuario']} | Su pronóstico: {p['pred_goles_local']} - {p['pred_goles_visitante']}")
            
            # 1. Marcador exacto
            if p['pred_goles_local'] == goles_l_real and p['pred_goles_visitante'] == goles_v_real:
                puntos = 5
                print("   Resultado: ¡Marcador exacto! (+5 Pts)")
            # 2. Ganador o empate
            elif (p['pred_goles_local'] > p['pred_goles_visitante'] and goles_l_real > goles_v_real) or \
                 (p['pred_goles_local'] < p['pred_goles_visitante'] and goles_l_real < goles_v_real) or \
                 (p['pred_goles_local'] == p['pred_goles_visitante'] and goles_l_real == goles_v_real):
                puntos = 3
                print("   Resultado: ¡Atinó al ganador/empate! (+3 Pts)")
            else:
                print("   Resultado: Falló el pronóstico. (0 Pts)")
                
            # Marcamos como procesada (1) y asignamos puntos
            cursor.execute("UPDATE predicciones SET puntos_obtenidos = %s, procesada = 1 WHERE id_prediccion = %s", 
                           (puntos, p['id_prediccion']))
            cursor.execute("UPDATE usuarios_quiniela SET puntos_totales = puntos_totales + %s WHERE id_usuario = %s", 
                           (puntos, p['id_usuario']))
        
        conexion.commit()
        print("--- MOTOR DE QUINIELA FINALIZADO CORRECTAMENTE ---\n")
    except Exception as e:
        print(f"❌ ERROR en el motor de quiniela: {e}")
    finally:
        cursor.close()
        conexion.close()

@app.get("/ranking_quiniela")
async def ranking_quiniela():
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Traemos a los usuarios ordenados por puntos (el que tenga más va primero)
        cursor.execute("""
            SELECT nombre_completo, puntos_totales 
            FROM usuarios_quiniela 
            ORDER BY puntos_totales DESC, nombre_completo ASC
        """)
        ranking = cursor.fetchall()
        return {"ranking": ranking}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.get("/mis_predicciones/{id_usuario}")
async def mis_predicciones(id_usuario: int):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_partido, pred_goles_local, pred_goles_visitante 
            FROM predicciones 
            WHERE id_usuario = %s
        """, (id_usuario,))
        predicciones = cursor.fetchall()
        return {"predicciones": predicciones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conexion.close()

@app.post("/cerrar_y_reiniciar_jornada/{jornada}")
async def cerrar_y_reiniciar_jornada(jornada: int):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    try:
        # 1. Tomamos la "fotografía" y la mandamos al historial
        cursor.execute("""
            INSERT INTO historial_quiniela (id_usuario, jornada, puntos_jornada)
            SELECT id_usuario, %s, puntos_totales FROM usuarios_quiniela
        """, (jornada,))

        # 2. Reiniciamos a 0 el ranking activo
        cursor.execute("UPDATE usuarios_quiniela SET puntos_totales = 0")

        conexion.commit()
        return {"mensaje": f"Jornada {jornada} respaldada con éxito. Ranking reiniciado a 0."}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la transacción: {e}")
    finally:
        cursor.close()
        conexion.close()
