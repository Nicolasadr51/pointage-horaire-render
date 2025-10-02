"""
Routes API pour la gestion administrative des pointages
Permet de créer, modifier, supprimer et lister les pointages depuis l'interface admin
"""

from flask import request, jsonify
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def add_admin_timeentries_routes(app, db, Employee, TimeEntry):
    """Ajouter les routes API de gestion des pointages à l'application Flask"""
    
    @app.route('/api/admin/timeentries', methods=['GET'])
    def api_admin_list_timeentries():
        """Lister tous les pointages avec filtres optionnels"""
        try:
            # Paramètres de filtrage optionnels
            employee_id = request.args.get('employee_id', type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            entry_type = request.args.get('entry_type')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Construire la requête de base
            query = db.session.query(TimeEntry, Employee).join(Employee)
            
            # Appliquer les filtres
            if employee_id:
                query = query.filter(TimeEntry.employee_id == employee_id)
            
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(TimeEntry.timestamp >= start_dt)
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(TimeEntry.timestamp < end_dt)
            
            if entry_type and entry_type in ['in', 'out']:
                query = query.filter(TimeEntry.entry_type == entry_type)
            
            # Ordonner par timestamp décroissant et appliquer pagination
            query = query.order_by(TimeEntry.timestamp.desc())
            total_count = query.count()
            results = query.offset(offset).limit(limit).all()
            
            # Formater les résultats
            timeentries = []
            for time_entry, employee in results:
                timeentries.append({
                    'id': time_entry.id,
                    'employee_id': time_entry.employee_id,
                    'employee_number': employee.employee_number,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'entry_type': time_entry.entry_type,
                    'timestamp': time_entry.timestamp.isoformat(),
                    'notes': time_entry.notes or '',
                    'created_at': time_entry.timestamp.strftime('%d/%m/%Y %H:%M:%S')
                })
            
            return jsonify({
                'success': True,
                'timeentries': timeentries,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des pointages : {e}")
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la récupération des pointages'
            }), 500
    
    @app.route('/api/admin/timeentries', methods=['POST'])
    def api_admin_create_timeentry():
        """Créer un nouveau pointage manuellement"""
        try:
            data = request.get_json()
            
            # Validation des données requises
            required_fields = ['employee_id', 'entry_type', 'timestamp']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Champ requis manquant : {field}'
                    }), 400
            
            employee_id = data['employee_id']
            entry_type = data['entry_type']
            timestamp_str = data['timestamp']
            notes = data.get('notes', '')
            
            # Validation du type de pointage
            if entry_type not in ['in', 'out']:
                return jsonify({
                    'success': False,
                    'error': 'Type de pointage invalide (in ou out requis)'
                }), 400
            
            # Validation de l'employé
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({
                    'success': False,
                    'error': 'Employé non trouvé'
                }), 404
            
            # Conversion du timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Format de date/heure invalide (ISO 8601 requis)'
                }), 400
            
            # Créer le pointage
            time_entry = TimeEntry(
                employee_id=employee_id,
                entry_type=entry_type,
                timestamp=timestamp,
                notes=notes
            )
            
            db.session.add(time_entry)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Pointage créé avec succès',
                'timeentry': {
                    'id': time_entry.id,
                    'employee_id': time_entry.employee_id,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'entry_type': time_entry.entry_type,
                    'timestamp': time_entry.timestamp.isoformat(),
                    'notes': time_entry.notes,
                    'created_at': time_entry.timestamp.strftime('%d/%m/%Y %H:%M:%S')
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du pointage : {e}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la création du pointage'
            }), 500
    
    @app.route('/api/admin/timeentries/<int:timeentry_id>', methods=['PUT'])
    def api_admin_update_timeentry(timeentry_id):
        """Modifier un pointage existant"""
        try:
            time_entry = TimeEntry.query.get(timeentry_id)
            if not time_entry:
                return jsonify({
                    'success': False,
                    'error': 'Pointage non trouvé'
                }), 404
            
            data = request.get_json()
            
            # Mise à jour des champs modifiables
            if 'entry_type' in data:
                if data['entry_type'] not in ['in', 'out']:
                    return jsonify({
                        'success': False,
                        'error': 'Type de pointage invalide'
                    }), 400
                time_entry.entry_type = data['entry_type']
            
            if 'timestamp' in data:
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    time_entry.timestamp = timestamp
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Format de date/heure invalide'
                    }), 400
            
            if 'notes' in data:
                time_entry.notes = data['notes']
            
            if 'employee_id' in data:
                employee = Employee.query.get(data['employee_id'])
                if not employee:
                    return jsonify({
                        'success': False,
                        'error': 'Employé non trouvé'
                    }), 404
                time_entry.employee_id = data['employee_id']
            
            db.session.commit()
            
            # Récupérer les informations de l'employé pour la réponse
            employee = Employee.query.get(time_entry.employee_id)
            
            return jsonify({
                'success': True,
                'message': 'Pointage modifié avec succès',
                'timeentry': {
                    'id': time_entry.id,
                    'employee_id': time_entry.employee_id,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'entry_type': time_entry.entry_type,
                    'timestamp': time_entry.timestamp.isoformat(),
                    'notes': time_entry.notes,
                    'created_at': time_entry.timestamp.strftime('%d/%m/%Y %H:%M:%S')
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du pointage : {e}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la modification du pointage'
            }), 500
    
    @app.route('/api/admin/timeentries/<int:timeentry_id>', methods=['DELETE'])
    def api_admin_delete_timeentry(timeentry_id):
        """Supprimer un pointage"""
        try:
            time_entry = TimeEntry.query.get(timeentry_id)
            if not time_entry:
                return jsonify({
                    'success': False,
                    'error': 'Pointage non trouvé'
                }), 404
            
            # Sauvegarder les informations pour la réponse
            employee = Employee.query.get(time_entry.employee_id)
            deleted_info = {
                'id': time_entry.id,
                'employee_name': f"{employee.first_name} {employee.last_name}",
                'entry_type': time_entry.entry_type,
                'timestamp': time_entry.timestamp.strftime('%d/%m/%Y %H:%M:%S')
            }
            
            db.session.delete(time_entry)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Pointage supprimé avec succès',
                'deleted_timeentry': deleted_info
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du pointage : {e}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la suppression du pointage'
            }), 500
    
    @app.route('/api/admin/timeentries/bulk', methods=['POST'])
    def api_admin_bulk_timeentries():
        """Opérations en lot sur les pointages (suppression multiple, etc.)"""
        try:
            data = request.get_json()
            action = data.get('action')
            timeentry_ids = data.get('timeentry_ids', [])
            
            if not action or not timeentry_ids:
                return jsonify({
                    'success': False,
                    'error': 'Action et IDs de pointages requis'
                }), 400
            
            if action == 'delete':
                # Suppression en lot
                deleted_count = 0
                for timeentry_id in timeentry_ids:
                    time_entry = TimeEntry.query.get(timeentry_id)
                    if time_entry:
                        db.session.delete(time_entry)
                        deleted_count += 1
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'{deleted_count} pointages supprimés avec succès',
                    'deleted_count': deleted_count
                })
            
            else:
                return jsonify({
                    'success': False,
                    'error': 'Action non supportée'
                }), 400
                
        except Exception as e:
            logger.error(f"Erreur lors de l'opération en lot : {e}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'opération en lot'
            }), 500
