from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import uuid
import qrcode
import base64
from io import BytesIO


app = Flask(__name__)
CORS(app)

# 🔧 Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'gym_qr'
}

# 🧠 Utilidad para formatear fecha en español
def formatear_fecha_espanol(fecha):
    fecha_formateada = fecha.strftime("%A %d de %B de %Y, %H:%M")
    fecha_formateada = fecha_formateada.replace("Monday", "lunes") \
        .replace("Tuesday", "martes") \
        .replace("Wednesday", "miércoles") \
        .replace("Thursday", "jueves") \
        .replace("Friday", "viernes") \
        .replace("Saturday", "sábado") \
        .replace("Sunday", "domingo") \
        .replace("January", "enero") \
        .replace("February", "febrero") \
        .replace("March", "marzo") \
        .replace("April", "abril") \
        .replace("May", "mayo") \
        .replace("June", "junio") \
        .replace("July", "julio") \
        .replace("August", "agosto") \
        .replace("September", "septiembre") \
        .replace("October", "octubre") \
        .replace("November", "noviembre") \
        .replace("December", "diciembre")
    return fecha_formateada[0].upper() + fecha_formateada[1:]

@app.route('/verificar_qr', methods=['POST'])
def verificar_qr():
    data = request.get_json()
    token = data.get('token')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM socios WHERE qr_token = %s", (token,))
        socio = cursor.fetchone()

        if socio:
            if socio['cuota_pagada']:
                cursor_asistencia = conn.cursor()
                cursor_asistencia.execute("INSERT INTO asistencias (socio_id) VALUES (%s)", (socio['id'],))
                conn.commit()
                cursor_asistencia.close()
                cursor.close()
                conn.close()
                return jsonify({'status': 'aceptado', 'nombre': socio['nombre']})
            else:
                cursor.close()
                conn.close()
                return jsonify({'status': 'rechazado', 'razon': 'cuota impaga'})
        else:
            cursor.close()
            conn.close()
            return jsonify({'status': 'rechazado', 'razon': 'token inválido'})

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/historial_asistencias/<int:socio_id>', methods=['GET'])
def historial_asistencias(socio_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT fecha_hora FROM asistencias WHERE socio_id = %s ORDER BY fecha_hora DESC", (socio_id,))
        asistencias_raw = cursor.fetchall()
        asistencias_formateadas = [formatear_fecha_espanol(fila['fecha_hora']) for fila in asistencias_raw]

        cursor.close()
        conn.close()

        response = make_response(jsonify({'socio_id': socio_id, 'asistencias': asistencias_formateadas}))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/asistencias_hoy', methods=['GET'])
def asistencias_hoy():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        hoy = datetime.now().date()
        cursor.execute("""
            SELECT a.fecha_hora, s.nombre
            FROM asistencias a
            JOIN socios s ON a.socio_id = s.id
            WHERE DATE(a.fecha_hora) = %s
            ORDER BY a.fecha_hora DESC
        """, (hoy,))
        registros = cursor.fetchall()

        for r in registros:
            r["fecha_hora"] = formatear_fecha_espanol(r["fecha_hora"])

        cursor.close()
        conn.close()

        response = make_response(jsonify({'asistencias_hoy': registros}))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/asistencias_semana', methods=['GET'])
def asistencias_semana():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        hoy = datetime.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())

        cursor.execute("""
            SELECT a.fecha_hora, s.nombre
            FROM asistencias a
            JOIN socios s ON a.socio_id = s.id
            WHERE DATE(a.fecha_hora) >= %s
            ORDER BY a.fecha_hora DESC
        """, (inicio_semana,))
        registros = cursor.fetchall()

        for r in registros:
            r["fecha_hora"] = formatear_fecha_espanol(r["fecha_hora"])

        cursor.close()
        conn.close()

        response = make_response(jsonify({'asistencias_semana': registros}))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/total_socios', methods=['GET'])
def total_socios():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM socios")
        total = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({'total': total})

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/ranking_asistencias', methods=['GET'])
def ranking_asistencias():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT s.nombre, COUNT(a.id) AS cantidad
            FROM asistencias a
            JOIN socios s ON a.socio_id = s.id
            GROUP BY s.nombre
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        ranking = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'ranking': ranking})

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/socio/<int:socio_id>', methods=['GET'])
def obtener_socio(socio_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, nombre, apellido, direccion, altura, peso, cuota_pagada FROM socios WHERE id = %s", (socio_id,))
        socio = cursor.fetchone()

        cursor.close()
        conn.close()

        if socio:
            return jsonify(socio)
        else:
            return jsonify({'status': 'error', 'mensaje': 'Socio no encontrado'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/socios', methods=['GET'])
def listar_socios():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, nombre, apellido, direccion, altura, peso, cuota_pagada FROM socios")
        socios = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'socios': socios})

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})

@app.route('/socio', methods=['POST'])
def agregar_socio():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        direccion = data.get('direccion')
        altura = data.get('altura')
        peso = data.get('peso')
        email = data.get('email')  # ✅ leer el email
        cuota_pagada = data.get('cuota_pagada', True)

        if not nombre:
            return jsonify({'status': 'error', 'mensaje': 'Falta el nombre del socio'}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Insertar socio incluyendo email
        cursor.execute("""
            INSERT INTO socios (nombre, apellido, direccion, altura, peso, email, cuota_pagada)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, direccion, altura, peso, email, cuota_pagada))
        conn.commit()

        socio_id = cursor.lastrowid
        qr_token = f"socio:{socio_id}"

        # Actualizar el qr_token
        cursor.execute("UPDATE socios SET qr_token = %s WHERE id = %s", (qr_token, socio_id))
        conn.commit()

        cursor.close()
        conn.close()

        # Generar imagen QR en memoria
        qr = qrcode.make(qr_token)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify({
            'status': 'ok',
            'mensaje': 'Socio agregado correctamente',
            'qr_token': qr_token,
            'qr_base64': img_base64
        })

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)})



@app.route('/verificar_acceso_qr/<string:qr_data>', methods=['GET'])
def verificar_acceso_qr(qr_data):
    if not qr_data.startswith("socio:"):
        return jsonify({"acceso": False, "mensaje": "QR inválido"}), 400

    try:
        socio_id = int(qr_data.split(":")[1])
    except ValueError:
        return jsonify({"acceso": False, "mensaje": "ID inválido"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT nombre, cuota_pagada FROM socios WHERE id = %s", (socio_id,))
        socio = cursor.fetchone()

        cursor.close()
        conn.close()

        if not socio:
            return jsonify({"acceso": False, "mensaje": "Socio no encontrado"}), 404

        if not socio["cuota_pagada"]:
            return jsonify({"acceso": False, "mensaje": f"{socio['nombre']} tiene la cuota impaga"}), 403

        return jsonify({"acceso": True, "mensaje": f"{socio['nombre']} puede ingresar ✅"}), 200

    except Exception as e:
        return jsonify({"acceso": False, "mensaje": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
