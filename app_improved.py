#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, send_from_directory, send_file, session, jsonify
from flask_cors import CORS
from src.models.employee import db, Employee
from src.routes.auth import auth_bp
from src.routes.employee_improved import employee_bp  # Version améliorée
from src.routes.timeentry import timeentry_bp
from src.routes.export import export_bp

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

# Configuration de la base de données - SQLite temporaire
database_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(database_dir, exist_ok=True)
database_path = os.path.join(database_dir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("🗄️ Utilisation de SQLite avec améliorations UX")
print("✨ Nouvelles fonctionnalités:")
print("   - Numéro d'employé libre (Munier, EMP001, etc.)")
print("   - Connexion insensible à la casse")
print("   - Interface de pointage avec liste déroulante")

# Initialisation des extensions
db.init_app(app)
CORS(app, supports_credentials=True, origins=['*'])

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(employee_bp, url_prefix='/api')  # Version améliorée
app.register_blueprint(timeentry_bp, url_prefix='/api')
app.register_blueprint(export_bp, url_prefix='/api')

# Routes de sauvegarde/restauration (admin seulement)
@app.route('/admin/create-backup', methods=['POST'])
def create_backup():
    """Créer une sauvegarde (admin seulement)"""
    if 'employee_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    employee = Employee.query.get(session['employee_id'])
    if not employee or not employee.is_admin:
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'backup_data.py', 'backup'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            return jsonify({
                'message': 'Sauvegarde créée avec succès',
                'output': result.stdout,
                'database_type': 'SQLite (amélioré)',
                'improvements': [
                    'Numéro d\'employé libre',
                    'Connexion insensible à la casse',
                    'Interface pointage avec liste'
                ]
            }), 200
        else:
            return jsonify({'error': 'Échec de la sauvegarde', 'output': result.stderr}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500

@app.route('/admin/restore-backup', methods=['POST'])
def restore_backup():
    """Restaurer la dernière sauvegarde (admin seulement)"""
    if 'employee_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    employee = Employee.query.get(session['employee_id'])
    if not employee or not employee.is_admin:
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'backup_data.py', 'restore'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            return jsonify({
                'message': 'Données restaurées avec succès',
                'output': result.stdout,
                'database_type': 'SQLite (amélioré)'
            }), 200
        else:
            return jsonify({'error': 'Échec de la restauration', 'output': result.stderr}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la restauration: {str(e)}'}), 500

@app.route('/admin/list-backups', methods=['GET'])
def list_backups():
    """Lister les sauvegardes disponibles (admin seulement)"""
    if 'employee_id' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    employee = Employee.query.get(session['employee_id'])
    if not employee or not employee.is_admin:
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        
        if not os.path.exists(backup_dir):
            return jsonify({
                'backups': [],
                'database_type': 'SQLite (amélioré)',
                'improvements': [
                    'Numéro d\'employé libre',
                    'Connexion insensible à la casse',
                    'Interface pointage avec liste'
                ]
            }), 200
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.json')]
        
        backups = []
        for backup_file in sorted(backup_files, reverse=True):
            file_path = os.path.join(backup_dir, backup_file)
            file_size = os.path.getsize(file_path)
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            backups.append({
                'filename': backup_file,
                'size': file_size,
                'date': file_date.isoformat(),
                'date_formatted': file_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'backups': backups,
            'database_type': 'SQLite (amélioré)',
            'improvements': [
                'Numéro d\'employé libre',
                'Connexion insensible à la casse',
                'Interface pointage avec liste'
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la liste des sauvegardes: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    return {
        'status': 'healthy', 
        'app': 'pointeuse-horaire',
        'database': 'SQLite (amélioré)',
        'persistent': False,
        'improvements': [
            'Numéro d\'employé libre (Munier, EMP001, etc.)',
            'Connexion insensible à la casse',
            'Interface pointage avec liste déroulante'
        ],
        'database_path': database_path
    }, 200

# NOUVELLE ROUTE: Interface de pointage améliorée
@app.route('/pointage')
def pointage_interface():
    """Interface de pointage avec liste déroulante"""
    return send_file(os.path.join(app.static_folder, 'pointage.html'))

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
        # Si le fichier n'existe pas, servir index.html pour le routing côté client
        return send_file(os.path.join(app.static_folder, 'index.html'))

if __name__ == '__main__':
    with app.app_context():
        # Utiliser le script d'initialisation avec préservation
        from init_with_preservation import init_database_with_preservation
        init_database_with_preservation()
        
        print("\n🎯 AMÉLIORATIONS DÉPLOYÉES:")
        print("   📝 Numéro d'employé libre: Munier, munier, EMP001, etc.")
        print("   🔤 Connexion insensible à la casse")
        print("   📋 Interface pointage: /pointage (liste déroulante)")
        print("   🔧 Interface admin: / (gestion complète)")
        print("\n✅ Application prête avec toutes les améliorations UX!")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
