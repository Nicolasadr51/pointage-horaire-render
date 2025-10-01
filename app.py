#!/usr/bin/env python3
import os
import hashlib
from datetime import datetime
from flask import Flask, send_from_directory, send_file, session, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pointeuse_production_key_2024_secure_v2')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

# Configuration base de données
if os.environ.get('DATABASE_URL'):
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("🐘 Utilisation de Neon PostgreSQL (gratuit)")
    database_type = "PostgreSQL (Neon)"
    is_postgresql = True
else:
    database_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(database_dir, exist_ok=True)
    database_path = os.path.join(database_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    print("🗄️ Utilisation de SQLite local")
    database_type = "SQLite (local)"
    is_postgresql = False

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation SQLAlchemy sans imports externes
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Modèles simplifiés
class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_number': self.employee_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

CORS(app, supports_credentials=True, origins=['*'])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Routes essentielles
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    employee_number = data.get('employee_number')
    password = data.get('password')
    
    if not employee_number or not password:
        return jsonify({'error': 'Numéro employé et mot de passe requis'}), 400
    
    password_hash = hash_password(password)
    employee = Employee.query.filter_by(
        employee_number=employee_number,
        password_hash=password_hash,
        is_active=True
    ).first()
    
    if not employee:
        return jsonify({'error': 'Employé non trouvé ou mot de passe incorrect'}), 401
    
    session['employee_id'] = employee.id
    session['is_admin'] = employee.is_admin
    
    return jsonify({
        'message': 'Connexion réussie',
        'employee': employee.to_dict()
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@app.route('/api/employees', methods=['GET'])
def get_employees():
    if 'employee_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    employees = Employee.query.all()
    return jsonify([emp.to_dict() for emp in employees]), 200

@app.route('/api/employees', methods=['POST'])
def create_employee():
    if 'employee_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    current_employee = Employee.query.get(session['employee_id'])
    if not current_employee or not current_employee.is_admin:
        return jsonify({'error': 'Accès refusé'}), 403
    
    data = request.get_json()
    
    # Générer le numéro d'employé
    last_employee = Employee.query.filter(
        Employee.employee_number.like('EMP%')
    ).order_by(Employee.employee_number.desc()).first()
    
    if last_employee:
        last_num = int(last_employee.employee_number[3:])
        new_num = f"EMP{last_num + 1:03d}"
    else:
        new_num = "EMP001"
    
    employee = Employee(
        employee_number=new_num,
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        is_admin=False,
        is_active=True
    )
    
    try:
        db.session.add(employee)
        db.session.commit()
        return jsonify({
            'message': 'Employé créé avec succès',
            'employee': employee.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erreur lors de la création: {str(e)}'}), 500

@app.route('/health')
def health_check():
    return {
        'status': 'healthy', 
        'app': 'pointeuse-horaire',
        'database': database_type,
        'persistent': is_postgresql,
        'free_tier': 'Neon PostgreSQL' if is_postgresql else 'Local SQLite',
        'storage_limit': '512 MB' if is_postgresql else 'Illimité (local)'
    }, 200

@app.route('/')
def serve_frontend():
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/<path:path>')
def serve_static_files(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_file(os.path.join(app.static_folder, 'index.html'))

def init_database():
    """Initialisation simple de la base de données"""
    try:
        print("🔧 Initialisation de la base de données...")
        
        # Créer les tables si elles n'existent pas
        with app.app_context():
            db.create_all()
            print("✅ Tables créées/vérifiées")
            
            # Vérifier si un admin existe
            admin = Employee.query.filter_by(employee_number='ADMIN001').first()
            
            if not admin:
                print("👤 Création de l'administrateur...")
                admin = Employee(
                    employee_number='ADMIN001',
                    first_name='Administrateur',
                    last_name='Système',
                    email='admin@pointage.local',
                    password_hash=hash_password('admin123'),
                    is_admin=True,
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Administrateur créé : ADMIN001 / admin123")
            else:
                print(f"✅ Administrateur existant : {admin.employee_number}")
            
            total = Employee.query.count()
            print(f"📊 {total} employés dans la base")
            print("🎉 Initialisation terminée avec succès !")
            
    except Exception as e:
        print(f"❌ Erreur d'initialisation : {e}")
        try:
            db.session.rollback()
        except:
            pass

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
