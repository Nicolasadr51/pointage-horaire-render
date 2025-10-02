#!/usr/bin/env python3
"""
Application de Pointage - Version Corrigée et Sécurisée
Intègre les améliorations de sécurité recommandées par Claude 4.X
"""

import sys
import os
from datetime import datetime, date, time
from functools import wraps

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, send_from_directory, send_file, session, jsonify, request
from flask_cors import CORS
from src.models.employee import db, Employee, TimeEntry
from src.routes.auth import auth_bp
from src.routes.employee_improved import employee_bp
from src.routes.export import export_bp

app = Flask(__name__, static_folder='static', static_url_path='')

# Configuration sécurisée pour la production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pointeuse_production_key_2024_secure_v3')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'pointeuse:'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS en production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuration de la base de données - SQLite avec améliorations
database_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(database_dir, exist_ok=True)
database_path = os.path.join(database_dir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("🗄️ Application de Pointage - Version Sécurisée")
print("✨ Améliorations de sécurité Claude 4.X intégrées:")
print("   - Protection XSS avec DOMPurify")
print("   - Validation et sanitisation des données")
print("   - Gestion sécurisée des sessions")
print("   - Interface d'administration complète")

# Initialisation des extensions
db.init_app(app)
CORS(app, supports_credentials=True, origins=['*'])

# Décorateur pour vérifier les droits admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return jsonify({'success': False, 'error': 'Non authentifié'}), 401
        
        employee = Employee.query.get(session['employee_id'])
        if not employee or not employee.is_admin:
            return jsonify({'success': False, 'error': 'Accès refusé - droits administrateur requis'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(employee_bp, url_prefix='/api')
app.register_blueprint(export_bp, url_prefix='/api')

# Routes principales
@app.route('/')
def index():
    return send_file(os.path.join(app.static_folder, 'index.html'))

@app.route('/pointage')
def pointage():
    return send_file(os.path.join(app.static_folder, 'pointage.html'))

@app.route('/admin/pointages')
def admin_pointages():
    """Interface d'administration des pointages avec sécurité renforcée"""
    return send_file(os.path.join(app.static_folder, 'admin_timeentries_secure.html'))

# ===== ROUTES API ADMIN POUR GESTION DES POINTAGES =====

@app.route('/api/admin/timeentries', methods=['GET'])
@admin_required
def api_admin_list_timeentries():
    """Lister tous les pointages avec filtres optionnels"""
    try:
        # Paramètres de filtrage sécurisés
        employee_id = request.args.get('employee_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = min(request.args.get('limit', 100, type=int), 1000)  # Limite max pour sécurité
        offset = max(request.args.get('offset', 0, type=int), 0)
        
        # Construire la requête de base avec jointure
        query = db.session.query(TimeEntry).join(Employee)
        
        # Appliquer les filtres avec validation
        if employee_id and employee_id > 0:
            query = query.filter(TimeEntry.employee_id == employee_id)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(TimeEntry.date >= start_dt)
            except ValueError:
                return jsonify({'success': False, 'error': 'Format de date invalide pour start_date'}), 400
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(TimeEntry.date <= end_dt)
            except ValueError:
                return jsonify({'success': False, 'error': 'Format de date invalide pour end_date'}), 400
        
        # Ordonner par date décroissante et appliquer pagination
        query = query.order_by(TimeEntry.date.desc(), TimeEntry.id.desc())
        total_count = query.count()
        results = query.offset(offset).limit(limit).all()
        
        # Formater les résultats de manière sécurisée
        timeentries = []
        for entry in results:
            timeentries.append({
                'id': entry.id,
                'employee_id': entry.employee_id,
                'employee_name': f"{entry.employee.first_name} {entry.employee.last_name}",
                'employee_number': entry.employee.employee_number,
                'date': entry.date.isoformat(),
                'morning_in': entry.morning_in.strftime('%H:%M') if entry.morning_in else None,
                'lunch_out': entry.lunch_out.strftime('%H:%M') if entry.lunch_out else None,
                'lunch_in': entry.lunch_in.strftime('%H:%M') if entry.lunch_in else None,
                'evening_out': entry.evening_out.strftime('%H:%M') if entry.evening_out else None,
                'morning_hours': round(entry.morning_hours, 2),
                'afternoon_hours': round(entry.afternoon_hours, 2),
                'total_hours': round(entry.total_hours, 2),
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'timeentries': timeentries,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des pointages: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

@app.route('/api/admin/timeentries', methods=['POST'])
@admin_required
def api_admin_create_timeentry():
    """Créer un nouveau pointage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON requises'}), 400
        
        # Validation des données requises
        employee_id = data.get('employee_id')
        date_str = data.get('date')
        
        if not employee_id or not date_str:
            return jsonify({'success': False, 'error': 'employee_id et date sont requis'}), 400
        
        # Vérifier que l'employé existe
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'success': False, 'error': 'Employé non trouvé'}), 404
        
        # Valider et parser la date
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Format de date invalide (YYYY-MM-DD attendu)'}), 400
        
        # Vérifier si un pointage existe déjà pour cette date
        existing_entry = TimeEntry.query.filter_by(
            employee_id=employee_id,
            date=entry_date
        ).first()
        
        if existing_entry:
            return jsonify({'success': False, 'error': 'Un pointage existe déjà pour cette date'}), 409
        
        # Créer le nouveau pointage
        new_entry = TimeEntry(
            employee_id=employee_id,
            date=entry_date
        )
        
        # Ajouter les heures optionnelles avec validation
        time_fields = ['morning_in', 'lunch_out', 'lunch_in', 'evening_out']
        for field in time_fields:
            time_str = data.get(field)
            if time_str:
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                    setattr(new_entry, field, time_obj)
                except ValueError:
                    return jsonify({'success': False, 'error': f'Format d\'heure invalide pour {field} (HH:MM attendu)'}), 400
        
        # Calculer les heures travaillées
        new_entry.calculate_hours()
        
        db.session.add(new_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pointage créé avec succès',
            'timeentry': new_entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la création du pointage: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

@app.route('/api/admin/timeentries/<int:timeentry_id>', methods=['PUT'])
@admin_required
def api_admin_update_timeentry(timeentry_id):
    """Modifier un pointage existant"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON requises'}), 400
        
        # Récupérer le pointage
        timeentry = TimeEntry.query.get(timeentry_id)
        if not timeentry:
            return jsonify({'success': False, 'error': 'Pointage non trouvé'}), 404
        
        # Mettre à jour les champs modifiables
        if 'date' in data:
            try:
                new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                # Vérifier qu'il n'y a pas de conflit avec un autre pointage
                existing = TimeEntry.query.filter_by(
                    employee_id=timeentry.employee_id,
                    date=new_date
                ).filter(TimeEntry.id != timeentry_id).first()
                
                if existing:
                    return jsonify({'success': False, 'error': 'Un pointage existe déjà pour cette date'}), 409
                
                timeentry.date = new_date
            except ValueError:
                return jsonify({'success': False, 'error': 'Format de date invalide'}), 400
        
        # Mettre à jour les heures avec validation
        time_fields = ['morning_in', 'lunch_out', 'lunch_in', 'evening_out']
        for field in time_fields:
            if field in data:
                time_str = data[field]
                if time_str:
                    try:
                        time_obj = datetime.strptime(time_str, '%H:%M').time()
                        setattr(timeentry, field, time_obj)
                    except ValueError:
                        return jsonify({'success': False, 'error': f'Format d\'heure invalide pour {field}'}), 400
                else:
                    # Permettre de vider un champ en envoyant null/empty
                    setattr(timeentry, field, None)
        
        # Recalculer les heures
        timeentry.calculate_hours()
        timeentry.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pointage mis à jour avec succès',
            'timeentry': timeentry.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour du pointage: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

@app.route('/api/admin/timeentries/<int:timeentry_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_timeentry(timeentry_id):
    """Supprimer un pointage"""
    try:
        timeentry = TimeEntry.query.get(timeentry_id)
        
        if not timeentry:
            return jsonify({'success': False, 'error': 'Pointage non trouvé'}), 404
        
        db.session.delete(timeentry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pointage supprimé avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la suppression du pointage: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

@app.route('/api/admin/timeentries/bulk', methods=['POST'])
@admin_required
def api_admin_bulk_timeentries():
    """Opérations en lot sur les pointages"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Données JSON requises'}), 400
        
        action = data.get('action')
        timeentry_ids = data.get('timeentry_ids', [])
        
        if not action or not timeentry_ids or not isinstance(timeentry_ids, list):
            return jsonify({'success': False, 'error': 'Action et timeentry_ids requis'}), 400
        
        # Limiter le nombre d'opérations en lot pour la sécurité
        if len(timeentry_ids) > 100:
            return jsonify({'success': False, 'error': 'Maximum 100 opérations en lot autorisées'}), 400
        
        if action == 'delete':
            deleted_count = 0
            for timeentry_id in timeentry_ids:
                if isinstance(timeentry_id, int) and timeentry_id > 0:
                    timeentry = TimeEntry.query.get(timeentry_id)
                    if timeentry:
                        db.session.delete(timeentry)
                        deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'{deleted_count} pointage(s) supprimé(s)',
                'deleted_count': deleted_count
            })
        
        else:
            return jsonify({'success': False, 'error': 'Action non supportée'}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'opération en lot: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

@app.route('/api/employees', methods=['GET'])
@admin_required
def api_list_employees():
    """Lister tous les employés pour les sélecteurs"""
    try:
        employees = Employee.query.filter_by(is_active=True).order_by(Employee.last_name, Employee.first_name).all()
        
        employees_list = []
        for emp in employees:
            employees_list.append({
                'id': emp.id,
                'employee_number': emp.employee_number,
                'first_name': emp.first_name,
                'last_name': emp.last_name,
                'full_name': f"{emp.first_name} {emp.last_name}",
                'email': emp.email,
                'is_admin': emp.is_admin
            })
        
        return jsonify({
            'success': True,
            'employees': employees_list
        })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des employés: {str(e)}")
        return jsonify({'success': False, 'error': 'Erreur interne du serveur'}), 500

# Initialisation de la base de données
def create_tables():
    """Créer les tables et l'admin par défaut"""
    try:
        with app.app_context():
            db.create_all()
            
            # Créer l'admin par défaut s'il n'existe pas
            admin = Employee.query.filter_by(employee_number='ADMIN001').first()
            if not admin:
                from werkzeug.security import generate_password_hash
                
                admin = Employee(
                    employee_number='ADMIN001',
                    first_name='Admin',
                    last_name='Système',
                    email='admin@pointage.local',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    is_active=True
                )
                
                db.session.add(admin)
                db.session.commit()
                print("✅ Administrateur par défaut créé: ADMIN001 / admin123")
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation: {str(e)}")

if __name__ == '__main__':
    # Configuration pour le développement
    app.config['SESSION_COOKIE_SECURE'] = False  # HTTP en dev
    
    # Initialiser la base de données
    create_tables()
    
    print("\n🚀 Démarrage de l'application de pointage")
    print("📊 Interface admin: http://localhost:5000/admin/pointages")
    print("🔑 Connexion: ADMIN001 / admin123")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
