import qrcode
import mysql.connector

# Conexión a la base de datos
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="gym_qr"
)
cursor = conn.cursor(dictionary=True)

# Seleccionamos solo los campos que existen
cursor.execute("SELECT id, nombre FROM socios")
socios = cursor.fetchall()

# Generamos los QR por cada socio
for socio in socios:
    data = f"socio:{socio['id']}"
    qr = qrcode.make(data)
    filename = f"{socio['nombre']}_qr.png"
    qr.save(filename)
    print(f"QR generado: {filename}")

cursor.close()
conn.close()
