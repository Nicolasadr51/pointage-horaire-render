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
from src.routes.employee import employee_bp
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

# Configuration de la base de données
database_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(database_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
database_path = os.path.join(database_dir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation des extensions
db.init_app(app)
CORS(app, supports_credentials=True, origins=['*'])

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(employee_bp, url_prefix='/api')
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
        # Importer et exécuter la fonction de sauvegarde
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'backup_data.py', 'backup'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            return jsonify({'message': 'Sauvegarde créée avec succès', 'output': result.stdout}), 200
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
        # Importer et exécuter la fonction de restauration
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'backup_data.py', 'restore'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            return jsonify({'message': 'Données restaurées avec succès', 'output': result.stdout}), 200
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
            return jsonify({'backups': []}), 200
        
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
        
        return jsonify({'backups': backups}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la liste des sauvegardes: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    return {'status': 'healthy', 'app': 'pointeuse-horaire'}, 200

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
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
