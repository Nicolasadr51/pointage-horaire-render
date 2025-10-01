#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, send_from_directory, send_file, session, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration pour la production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pointeuse_production_key_2024_secure_v2')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'pointeuse:'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS en production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuration de la base de données
if os.environ.get('DATABASE_URL'):
    # Production avec Neon PostgreSQL (gratuit)
    database_url = os.environ.get('DATABASE_URL')
    # Neon utilise parfois postgres:// au lieu de postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print("🐘 Utilisation de Neon PostgreSQL (gratuit) pour la persistance")
    database_type = "PostgreSQL (Neon)"
else:
    # Développement avec SQLite
    database_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(database_dir, exist_ok=True)
    database_path = os.path.join(database_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    print("🗄️ Utilisation de SQLite pour le développement")
    database_type = "SQLite (local)"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation manuelle de SQLAlchemy pour éviter les conflits
from flask_sqlalchemy import SQLAlchemy
import hashlib

db = SQLAlchemy()
db.init_app(app)

# Redéfinition des modèles pour PostgreSQL
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
    
    def __repr__(self):
        return f'<Employee {self.employee_number}: {self.first_name} {self.last_name}>'

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

class TimeEntry(db.Model):
    __tablename__ = 'time_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # Les 4 créneaux de pointage
    morning_in = db.Column(db.Time, nullable=True)
    lunch_out = db.Column(db.Time, nullable=True)
    lunch_in = db.Column(db.Time, nullable=True)
    evening_out = db.Column(db.Time, nullable=True)
    
    # Heures calculées
    morning_hours = db.Column(db.Float, default=0.0)
    afternoon_hours = db.Column(db.Float, default=0.0)
    total_hours = db.Column(db.Float, default=0.0)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    employee = db.relationship('Employee', backref='time_entries')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat() if self.date else None,
            'morning_in': self.morning_in.strftime('%H:%M') if self.morning_in else None,
            'lunch_out': self.lunch_out.strftime('%H:%M') if self.lunch_out else None,
            'lunch_in': self.lunch_in.strftime('%H:%M') if self.lunch_in else None,
            'evening_out': self.evening_out.strftime('%H:%M') if self.evening_out else None,
            'morning_hours': round(self.morning_hours, 2),
            'afternoon_hours': round(self.afternoon_hours, 2),
            'total_hours': round(self.total_hours, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

CORS(app, supports_credentials=True, origins=['*'])

# Routes simplifiées pour tester
@app.route('/api/auth/login', methods=['POST'])
def login():
    from flask import request
    data = request.get_json()
    
    employee_number = data.get('employee_number')
    password = data.get('password')
    
    if not employee_number or not password:
        return jsonify({'error': 'Numéro employé et mot de passe requis'}), 400
    
    # Hash du mot de passe
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Recherche de l'employé
    employee = Employee.query.filter_by(
        employee_number=employee_number,
        password_hash=password_hash,
        is_active=True
    ).first()
    
    if not employee:
        return jsonify({'error': 'Employé non trouvé ou mot de passe incorrect'}), 401
    
    # Créer la session
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
    
    from flask import request
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
    
    # Hash du mot de passe
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    employee = Employee(
        employee_number=new_num,
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password_hash=password_hash,
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
    """Point de contrôle de santé pour le déploiement"""
    is_postgresql = os.environ.get('DATABASE_URL') is not None
    
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
    """Servir la page d'accueil du frontend"""
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/<path:path>')
def serve_static_files(path):
    """Servir les fichiers statiques du frontend"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_file(os.path.join(app.static_folder, 'index.html'))

def init_clean_database():
    """Initialisation propre de la base de données PostgreSQL"""
    try:
        print("🔧 Initialisation propre de la base de données PostgreSQL...")
        
        # Supprimer toutes les tables existantes
        db.drop_all()
        print("🗑️ Tables existantes supprimées")
        
        # Créer les nouvelles tables
        db.create_all()
        print("✅ Nouvelles tables créées")
        
        # Créer l'administrateur par défaut
        admin = Employee(
            employee_number='ADMIN001',
            first_name='Administrateur',
            last_name='Système',
            email='admin@pointage.local',
            password_hash=hashlib.sha256('admin123'.encode()).hexdigest(),
            is_admin=True,
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Administrateur créé : ADMIN001 / admin123")
        print("🎉 Base de données PostgreSQL initialisée avec succès !")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False

if __name__ == '__main__':
    with app.app_context():
        init_clean_database()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
