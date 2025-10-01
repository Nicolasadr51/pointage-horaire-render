#!/usr/bin/env python3
"""
Script de sauvegarde et restauration des données de l'application de pointage
"""
import os
import sys
import json
import sqlite3
from datetime import datetime
import shutil

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def backup_database():
    """Sauvegarder la base de données en JSON"""
    try:
        database_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
        
        if not os.path.exists(database_path):
            print("❌ Base de données non trouvée")
            return False
        
        # Connexion à la base de données
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row  # Pour avoir des dictionnaires
        cursor = conn.cursor()
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'employees': [],
            'time_entries': []
        }
        
        # Sauvegarder les employés
        cursor.execute("SELECT * FROM employee")
        employees = cursor.fetchall()
        for emp in employees:
            backup_data['employees'].append(dict(emp))
        
        # Sauvegarder les pointages
        cursor.execute("SELECT * FROM time_entry")
        entries = cursor.fetchall()
        for entry in entries:
            entry_dict = dict(entry)
            # Convertir les dates/heures en string pour JSON
            if entry_dict['date']:
                entry_dict['date'] = entry_dict['date']
            if entry_dict['morning_in']:
                entry_dict['morning_in'] = entry_dict['morning_in']
            if entry_dict['lunch_out']:
                entry_dict['lunch_out'] = entry_dict['lunch_out']
            if entry_dict['lunch_in']:
                entry_dict['lunch_in'] = entry_dict['lunch_in']
            if entry_dict['evening_out']:
                entry_dict['evening_out'] = entry_dict['evening_out']
            if entry_dict['created_at']:
                entry_dict['created_at'] = entry_dict['created_at']
            if entry_dict['updated_at']:
                entry_dict['updated_at'] = entry_dict['updated_at']
            
            backup_data['time_entries'].append(entry_dict)
        
        conn.close()
        
        # Créer le dossier de sauvegarde
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Sauvegarder en JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Copier aussi la base de données SQLite
        db_backup_file = os.path.join(backup_dir, f'app_{timestamp}.db')
        shutil.copy2(database_path, db_backup_file)
        
        print(f"✅ Sauvegarde créée : {backup_file}")
        print(f"✅ Base de données copiée : {db_backup_file}")
        print(f"📊 {len(backup_data['employees'])} employés sauvegardés")
        print(f"📊 {len(backup_data['time_entries'])} pointages sauvegardés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return False

def restore_database(backup_file=None):
    """Restaurer la base de données depuis un fichier JSON"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        
        if backup_file is None:
            # Prendre la sauvegarde la plus récente
            if not os.path.exists(backup_dir):
                print("❌ Aucune sauvegarde trouvée")
                return False
            
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.json')]
            if not backup_files:
                print("❌ Aucune sauvegarde JSON trouvée")
                return False
            
            backup_file = os.path.join(backup_dir, sorted(backup_files)[-1])
        
        print(f"📂 Restauration depuis : {backup_file}")
        
        # Charger les données de sauvegarde
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Initialiser l'application Flask pour accéder aux modèles
        from app import app, db
        from src.models.employee import Employee, TimeEntry
        
        with app.app_context():
            # Supprimer toutes les données existantes
            TimeEntry.query.delete()
            Employee.query.delete()
            db.session.commit()
            
            # Restaurer les employés
            for emp_data in backup_data['employees']:
                employee = Employee(
                    employee_number=emp_data['employee_number'],
                    first_name=emp_data['first_name'],
                    last_name=emp_data['last_name'],
                    email=emp_data['email'],
                    password_hash=emp_data['password_hash'],
                    is_admin=emp_data['is_admin'],
                    is_active=emp_data['is_active']
                )
                if emp_data.get('created_at'):
                    employee.created_at = datetime.fromisoformat(emp_data['created_at'].replace('Z', '+00:00'))
                
                db.session.add(employee)
            
            db.session.commit()
            
            # Restaurer les pointages
            for entry_data in backup_data['time_entries']:
                # Trouver l'employé correspondant
                employee = Employee.query.filter_by(employee_number=entry_data.get('employee_number')).first()
                if not employee:
                    # Fallback sur l'ID si le numéro n'est pas disponible
                    employee = Employee.query.get(entry_data['employee_id'])
                
                if employee:
                    time_entry = TimeEntry(
                        employee_id=employee.id,
                        date=datetime.strptime(entry_data['date'], '%Y-%m-%d').date() if entry_data['date'] else None,
                        morning_in=datetime.strptime(entry_data['morning_in'], '%H:%M:%S').time() if entry_data.get('morning_in') else None,
                        lunch_out=datetime.strptime(entry_data['lunch_out'], '%H:%M:%S').time() if entry_data.get('lunch_out') else None,
                        lunch_in=datetime.strptime(entry_data['lunch_in'], '%H:%M:%S').time() if entry_data.get('lunch_in') else None,
                        evening_out=datetime.strptime(entry_data['evening_out'], '%H:%M:%S').time() if entry_data.get('evening_out') else None,
                        morning_hours=entry_data.get('morning_hours', 0.0),
                        afternoon_hours=entry_data.get('afternoon_hours', 0.0),
                        total_hours=entry_data.get('total_hours', 0.0)
                    )
                    
                    if entry_data.get('created_at'):
                        time_entry.created_at = datetime.fromisoformat(entry_data['created_at'].replace('Z', '+00:00'))
                    if entry_data.get('updated_at'):
                        time_entry.updated_at = datetime.fromisoformat(entry_data['updated_at'].replace('Z', '+00:00'))
                    
                    db.session.add(time_entry)
            
            db.session.commit()
        
        print(f"✅ Restauration terminée")
        print(f"📊 {len(backup_data['employees'])} employés restaurés")
        print(f"📊 {len(backup_data['time_entries'])} pointages restaurés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration : {e}")
        return False

def list_backups():
    """Lister toutes les sauvegardes disponibles"""
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    
    if not os.path.exists(backup_dir):
        print("❌ Aucun dossier de sauvegarde trouvé")
        return
    
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("❌ Aucune sauvegarde trouvée")
        return
    
    print("📂 Sauvegardes disponibles :")
    for backup_file in sorted(backup_files, reverse=True):
        file_path = os.path.join(backup_dir, backup_file)
        file_size = os.path.getsize(file_path)
        file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        print(f"  • {backup_file} ({file_size} bytes, {file_date.strftime('%Y-%m-%d %H:%M:%S')})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup_data.py backup          # Créer une sauvegarde")
        print("  python backup_data.py restore         # Restaurer la dernière sauvegarde")
        print("  python backup_data.py restore <file>  # Restaurer une sauvegarde spécifique")
        print("  python backup_data.py list            # Lister les sauvegardes")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        backup_database()
    elif command == "restore":
        backup_file = sys.argv[2] if len(sys.argv) > 2 else None
        restore_database(backup_file)
    elif command == "list":
        list_backups()
    else:
        print(f"❌ Commande inconnue : {command}")
        sys.exit(1)
