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

# Ajouter les routes de gestion administrative des pointages
from admin_timeentries_api import add_admin_timeentries_routes
from src.models.timeentry import TimeEntry
add_admin_timeentries_routes(app, db, Employee, TimeEntry)

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

@app.route('/admin/timeentries')
def admin_timeentries():
    return send_file(os.path.join(app.static_folder, 'admin_timeentries.html'))

@app.route('/pointage')
def pointage():
    return send_file(os.path.join(app.static_folder, 'pointage.html'))

@app.route('/')
def index():
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/<path:path>')
def serve_static_files(path):
    """Servir les fichiers statiques du frontend"""
    # Éviter de capturer les routes admin spécifiques
    if path.startswith('admin/'):
        return "Route non trouvée", 404
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


# API Routes pour la gestion des pointages (Admin)
@app.route('/api/admin/timeentries', methods=['GET'])
@admin_required
def get_admin_timeentries():
    employee_id = request.args.get('employee_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    entry_type = request.args.get('entry_type')
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)

    query = TimeEntry.query

    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        query = query.filter(func.date(TimeEntry.timestamp) >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        query = query.filter(func.date(TimeEntry.timestamp) <= end_date)
    if entry_type:
        query = query.filter_by(entry_type=entry_type)

    total_count = query.count()
    timeentries = query.order_by(TimeEntry.timestamp.desc()).limit(limit).offset(offset).all()

    results = []
    for entry in timeentries:
        employee = Employee.query.get(entry.employee_id)
        results.append({
            'id': entry.id,
            'employee_id': entry.employee_id,
            'employee_number': employee.employee_number if employee else 'N/A',
            'employee_name': f'{employee.first_name} {employee.last_name}' if employee else 'N/A',
            'entry_type': entry.entry_type,
            'timestamp': entry.timestamp.isoformat(),
            'created_at': entry.created_at.isoformat(),
            'notes': entry.notes
        })
    return jsonify({'success': True, 'timeentries': results, 'total_count': total_count})

@app.route('/api/admin/timeentries', methods=['POST'])
@admin_required
def create_admin_timeentry():
    data = request.get_json()
    employee_id = data.get('employee_id')
    entry_type = data.get('entry_type')
    timestamp_str = data.get('timestamp')
    notes = data.get('notes')

    if not all([employee_id, entry_type, timestamp_str]):
        return jsonify({'success': False, 'error': 'Missing data'}), 400

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid timestamp format'}), 400

    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({'success': False, 'error': 'Employee not found'}), 404

    new_timeentry = TimeEntry(
        employee_id=employee_id,
        entry_type=entry_type,
        timestamp=timestamp,
        notes=notes
    )
    db.session.add(new_timeentry)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Time entry created', 'id': new_timeentry.id}), 201

@app.route('/api/admin/timeentries/<int:timeentry_id>', methods=['PUT'])
@admin_required
def update_admin_timeentry(timeentry_id):
    data = request.get_json()
    timeentry = TimeEntry.query.get(timeentry_id)

    if not timeentry:
        return jsonify({'success': False, 'error': 'Time entry not found'}), 404

    employee_id = data.get('employee_id')
    entry_type = data.get('entry_type')
    timestamp_str = data.get('timestamp')
    notes = data.get('notes')

    if employee_id:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
        timeentry.employee_id = employee_id
    if entry_type:
        timeentry.entry_type = entry_type
    if timestamp_str:
        try:
            timeentry.timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid timestamp format'}), 400
    if notes is not None:
        timeentry.notes = notes

    db.session.commit()
    return jsonify({'success': True, 'message': 'Time entry updated'})

@app.route('/api/admin/timeentries/<int:timeentry_id>', methods=['DELETE'])
@admin_required
def delete_admin_timeentry(timeentry_id):
    timeentry = TimeEntry.query.get(timeentry_id)

    if not timeentry:
        return jsonify({'success': False, 'error': 'Time entry not found'}), 404

    db.session.delete(timeentry)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Time entry deleted'})

@app.route('/api/admin/timeentries/bulk', methods=['POST'])
@admin_required
def bulk_admin_timeentries():
    data = request.get_json()
    action = data.get('action')
    timeentry_ids = data.get('timeentry_ids')

    if not action or not timeentry_ids or not isinstance(timeentry_ids, list):
        return jsonify({'success': False, 'error': 'Invalid bulk operation data'}), 400

    if action == 'delete':
        deleted_count = 0
        for timeentry_id in timeentry_ids:
            timeentry = TimeEntry.query.get(timeentry_id)
            if timeentry:
                db.session.delete(timeentry)
                deleted_count += 1
        db.session.commit()
        return jsonify({'success': True, 'message': f'{deleted_count} time entries deleted', 'deleted_count': deleted_count})
    
    return jsonify({'success': False, 'error': 'Unknown bulk action'}), 400

