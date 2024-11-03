from flask import Flask, request, jsonify, render_template_string
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import pytz  # Asegúrate de tener instalada esta biblioteca

app = Flask(__name__)

# Función para crear la conexión a la base de datos
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="host",  # Cambia esto por la IP de tu servidor MySQL
            user="usuario",  # Cambia por tu usuario MySQL
            password="password",  # Cambia por tu contraseña MySQL
            database="alarma"  # Cambia por tu base de datos
        )
    except Error as e:
        print(f"Error al conectar con la base de datos: {e}")
    return connection

@app.route('/')
def hello_world():
    return 'Hello from Flask!'


# Ruta para insertar datos en la base de datos
@app.route('/insert', methods=['POST'])
def insert_data():
    data = request.get_json()
    descripcion = data.get('descripcion')

    if descripcion:
        try:
            # Obtener la hora actual en la zona horaria de Argentina
            tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
            argentina_time = datetime.now(tz_argentina)  # Hora de Argentina

            # Crear conexión a la base de datos
            connection = create_connection()
            if connection.is_connected():
                cursor = connection.cursor()
                sql_query = "INSERT INTO movimientos (timestamp, descripcion) VALUES (%s, %s)"
                cursor.execute(sql_query, (argentina_time, descripcion))  # Guardar hora en formato argentino
                connection.commit()
                cursor.close()
                connection.close()
                return jsonify({"status": "success", "message": "Movimiento registrado"}), 200
        except Error as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": "Datos inválidos"}), 400


# Ruta para mostrar los registros en formato HTML con tabla, CSS y filtro de fechas
@app.route('/records', methods=['GET', 'POST'])
def show_records():
    try:
        connection = create_connection()
        if connection.is_connected():
            cursor = connection.cursor()

            # Filtro de fechas basado en la solicitud POST (si existe)
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            query = "SELECT id, timestamp, descripcion FROM movimientos"
            params = []

            if start_date and end_date:
                query += " WHERE timestamp BETWEEN %s AND %s"
                params = [start_date + " 00:00:00", end_date + " 23:59:59"]

            cursor.execute(query, params)
            records = cursor.fetchall()
            cursor.close()
            connection.close()

            # Formatear los registros
            formatted_records = []
            for record in records:
                formatted_timestamp = record[1].strftime('%d/%m/%Y %H:%M:%S')
                formatted_records.append((record[0], formatted_timestamp, record[2]))

            # HTML para mostrar la tabla con filtro de fechas y actualización en tiempo real
            html_template = '''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Registros de Movimientos</title>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; padding: 20px; }
                    table { width: 100%; border-collapse: collapse; font-size: 18px; box-shadow: 0 2px 3px rgba(0,0,0,0.1); }
                    th, td { padding: 12px; border-bottom: 1px solid #ddd; }
                    th { background-color: #333; color: #fff; cursor: pointer; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                    .filter-form { display: flex; justify-content: center; margin-bottom: 20px; }
                    .filter-form input[type="date"] { margin-right: 10px; }
                </style>
            </head>
            <body>
                <h2>Registros de Movimientos</h2>
            
                <!-- Formulario de filtro de fechas -->
                <form class="filter-form" method="POST" action="/records">
                    <input type="date" name="start_date" required max="{{ current_date }}" value="{{ request.form.get('start_date', '') }}">
                    <input type="date" name="end_date" required max="{{ current_date }}" value="{{ request.form.get('end_date', '') }}">
                    <button type="submit">Filtrar</button>
                </form>
            
                <table>
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">ID</th>
                            <th onclick="sortTable(1)">Fecha y Hora</th>
                            <th onclick="sortTable(2)">Descripción</th>
                        </tr>
                    </thead>
                    <tbody id="records-body">
                        {% for record in records %}
                        <tr>
                            <td>{{ record[0] }}</td>
                            <td>{{ record[1] }}</td>
                            <td>{{ record[2] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            
                <script>
                    let previousData = null;
            
                    // Solicitar permiso para las notificaciones
                    function requestNotificationPermission() {
                        if (Notification.permission !== "granted") {
                            Notification.requestPermission().then(permission => {
                                if (permission === "granted") {
                                    console.log("Permiso de notificación concedido.");
                                }
                            });
                        }
                    }
            
                    // Mostrar una notificación de nuevo movimiento
                    function showNotification() {
                        if (Notification.permission === "granted") {
                            new Notification("Nuevo Movimiento Detectado", {
                                body: "¡Se ha detectado un nuevo movimiento en el sistema!",
                                icon: "https://example.com/icon.png" // Opcional: URL de un icono de notificación
                            });
                        }
                    }
            
                    // Consultar datos de la API y comparar con los datos previos
                    function fetchData() {
                        fetch('/api/records')
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    const newData = JSON.stringify(data.records);
            
                                    // Si los datos han cambiado, mostrar notificación
                                    if (previousData && previousData !== newData) {
                                        // alert('¡Se ha detectado un nuevo movimiento!');
                                        showNotification();
                                    }
            
                                    previousData = newData;
                                }
                            })
                            .catch(error => console.error('Error al obtener datos:', error));
                    }
            
                    // Configurar actualización cada 5 segundos y solicitar permiso para notificaciones
                    setInterval(fetchData, 5000);
                    requestNotificationPermission();
            
                    // Función para ordenar la tabla
                    function sortTable(columnIndex) {
                        const table = document.querySelector('table');
                        const tbody = table.querySelector('tbody');
                        const rows = Array.from(tbody.querySelectorAll('tr'));
                        // Cambiar el estado de ordenamiento a 'descending' para mostrar el registro más actual primero
                        let isAscending = table.dataset.sortDirection === 'ascending';
                    
                        // Si no hay estado de ordenamiento establecido, inicialmente ordenamos de forma descendente
                        if (table.dataset.sortDirection === undefined) {
                            isAscending = false; // Mostrar el registro más actual primero
                            table.dataset.sortDirection = 'descending'; // Inicializar el estado
                        }
                    
                        rows.sort((rowA, rowB) => {
                            const cellA = rowA.querySelectorAll('td')[columnIndex].textContent.trim();
                            const cellB = rowB.querySelectorAll('td')[columnIndex].textContent.trim();
                    
                            if (columnIndex === 1) { // Si es la columna de fecha y hora
                                // Convertir las fechas y horas al formato adecuado
                                const [dateA, timeA] = cellA.split(' ');
                                const [dateB, timeB] = cellB.split(' ');
                    
                                const [dayA, monthA, yearA] = dateA.split('/').map(Number);
                                const [dayB, monthB, yearB] = dateB.split('/').map(Number);
                                const [hoursA, minutesA] = timeA.split(':').map(Number);
                                const [hoursB, minutesB] = timeB.split(':').map(Number);
                    
                                // Crear objetos Date para las comparaciones
                                const dateTimeA = new Date(yearA, monthA - 1, dayA, hoursA, minutesA);
                                const dateTimeB = new Date(yearB, monthB - 1, dayB, hoursB, minutesB);
                    
                                return isAscending ? dateTimeA - dateTimeB : dateTimeB - dateTimeA;
                            } else {
                                return isAscending
                                    ? cellA.localeCompare(cellB, 'es', { numeric: true })
                                    : cellB.localeCompare(cellA, 'es', { numeric: true });
                            }
                        });
                    
                        rows.forEach(row => tbody.appendChild(row));
                        table.dataset.sortDirection = isAscending ? 'descending' : 'ascending'; // Alternar el estado para futuras ordenaciones
                        showPage(currentPage); // Actualizar la vista de la página actual después de ordenar
                    }
                    
                    // Al cargar la tabla por primera vez, llamamos a la función de ordenamiento
                    document.addEventListener('DOMContentLoaded', () => {
                        sortTable(1); // Ordenar por fecha y hora inicialmente
                    });

            
                    document.querySelector('input[name="start_date"]').max = document.querySelector('input[name="end_date"]').max = new Date().toISOString().split("T")[0];
                </script>
            </body>
            </html>
            '''

            return render_template_string(html_template, records=formatted_records, request=request), 200

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500




# Nuevo endpoint para obtener registros en formato JSON
@app.route('/api/records', methods=['GET'])
def get_records_json():
    try:
        connection = create_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT id, timestamp, descripcion FROM movimientos")
            records = cursor.fetchall()
            cursor.close()
            connection.close()

            # Formatear los registros en JSON
            json_records = [
                {
                    "id": record[0],
                    "timestamp": record[1].strftime('%d/%m/%Y %H:%M:%S'),  # Formato deseado para JSON
                    "descripcion": record[2]
                }
                for record in records
            ]

            return jsonify({"status": "success", "records": json_records}), 200

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Iniciar la aplicación
#if __name__ == '__main__':
#    app.run(debug=True)
