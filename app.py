from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "rental.db")

class DatabaseManager:
    def __init__(self, db_name=DATABASE_NAME):
        """Initializes the database connection and creates tables if they don't exist."""
        self.db_name = db_name
        self.create_table()

    def _get_connection(self):
        """Helper method to get a database connection."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self):
        """Creates a 'vehicles' table."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id TEXT PRIMARY KEY,
            model TEXT NOT NULL,
            price_per_day REAL NOT NULL,
            is_available INTEGER DEFAULT 1
        );
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
        print("✅ Database initialization complete (Table checked/created).")

    def add_vehicle(self, vehicle_id, model, price_per_day):
        """Inserts a new vehicle into the database."""
        insert_query = "INSERT OR IGNORE INTO vehicles (vehicle_id, model, price_per_day) VALUES (?, ?, ?);"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, (vehicle_id, model, price_per_day))
                conn.commit()
                if cursor.rowcount > 0:
                    print(f"🚗 Added: {model} ({vehicle_id})")
                else:
                    print(f"⚠️ Vehicle ID {vehicle_id} already exists.")
        except sqlite3.Error as e:
            print(f"❌ Error adding vehicle: {e}")

    def fetch_all_vehicles(self):
        """Retrieves and returns all rows from the vehicles table."""
        select_query = "SELECT * FROM vehicles;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(select_query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_vehicle(self, vehicle_id):
        """Retrieves a single vehicle by ID."""
        select_query = "SELECT * FROM vehicles WHERE vehicle_id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(select_query, (vehicle_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_availability(self, vehicle_id, status):
        """Updates whether a vehicle is available (1) or rented (0)."""
        update_query = "UPDATE vehicles SET is_available = ? WHERE vehicle_id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(update_query, (status, vehicle_id))
            conn.commit()
            print(f"🔄 Updated status for ID {vehicle_id}")

    def delete_vehicle(self, vehicle_id):
        """Deletes a specific vehicle record."""
        delete_query = "DELETE FROM vehicles WHERE vehicle_id = ?;"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(delete_query, (vehicle_id,))
            conn.commit()
            print(f"🗑️ Deleted vehicle ID {vehicle_id}")


db = DatabaseManager()
app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/vehicles', methods=['GET'])
def api_vehicles():
    vehicles = db.fetch_all_vehicles()
    return jsonify(vehicles)

@app.route('/api/rent', methods=['POST'])
def api_rent():
    payload = request.get_json(silent=True) or {}
    vehicle_id = payload.get('vehicle_id')
    days = payload.get('days')

    if not vehicle_id or not isinstance(days, (int, float)) or days < 1:
        return jsonify({'error': 'Invalid rental request. Please provide a vehicle ID and rental days.'}), 400

    vehicle = db.get_vehicle(vehicle_id)
    if vehicle is None:
        return jsonify({'error': 'Vehicle not found.'}), 404
    if not vehicle['is_available']:
        return jsonify({'error': 'Vehicle is already rented.'}), 400

    db.update_availability(vehicle_id, 0)
    return jsonify({'message': f"{vehicle['model']} rented successfully for {int(days)} day(s)."})

@app.route('/api/return', methods=['POST'])
def api_return():
    payload = request.get_json(silent=True) or {}
    vehicle_id = payload.get('vehicle_id')

    if not vehicle_id:
        return jsonify({'error': 'Invalid return request. Please provide a vehicle ID.'}), 400

    vehicle = db.get_vehicle(vehicle_id)
    if vehicle is None:
        return jsonify({'error': 'Vehicle not found.'}), 404
    if vehicle['is_available']:
        return jsonify({'error': 'Vehicle is already available.'}), 400

    db.update_availability(vehicle_id, 1)
    return jsonify({'message': f"{vehicle['model']} returned successfully."})

if __name__ == '__main__':
    if len(db.fetch_all_vehicles()) == 0:
        # Budget/Simple Cars
        db.add_vehicle('V101', 'Hyundai i10', 800.0)
        db.add_vehicle('V102', 'Tata Nano', 600.0)
        db.add_vehicle('V103', 'Maruti Swift', 1200.0)
        db.add_vehicle('V104', 'Renault Kwid', 900.0)
        
        # Mid-Range Cars
        db.add_vehicle('V105', 'Mahindra Thar', 2500.0)
        db.add_vehicle('V106', 'Honda City', 1800.0)
        db.add_vehicle('V107', 'Hyundai Creta', 2200.0)
        
        # Premium/Luxury Cars
        db.add_vehicle('V108', 'BMW 3 Series', 8500.0)
        db.add_vehicle('V109', 'Mercedes-Benz C-Class', 9500.0)
        db.add_vehicle('V110', 'Audi A4', 8800.0)
        db.add_vehicle('V111', 'Range Rover Sport', 12000.0)
        db.add_vehicle('V112', 'Tesla Model 3', 7500.0)
        db.add_vehicle('V113', 'Jaguar XF', 9000.0)
        db.add_vehicle('V114', 'Aston Martin Vantage', 15000.0)
    app.run(host='0.0.0.0', port=5000, debug=True)
