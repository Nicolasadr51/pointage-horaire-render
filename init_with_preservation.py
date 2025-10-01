#!/usr/bin/env python3
"""
Script d'initialisation qui préserve les données existantes
"""
import os
import sys
from datetime import datetime
import hashlib

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database_with_preservation():
    """Initialiser la base de données en préservant les données existantes"""
    try:
        from app import app, db
        from src.models.employee import Employee, TimeEntry
        
        with app.app_context():
            # Créer les tables si elles n'existent pas
            db.create_all()
            
            # Vérifier si des données existent déjà
            existing_employees = Employee.query.count()
            existing_entries = TimeEntry.query.count()
            
            print(f"📊 Données existantes trouvées :")
            print(f"   • {existing_employees} employés")
            print(f"   • {existing_entries} pointages")
            
            # Si aucun admin n'existe, créer l'admin par défaut
            admin_exists = Employee.query.filter_by(is_admin=True).first()
            
            if not admin_exists:
                print("👤 Création de l'administrateur par défaut...")
                
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
                print(f"✅ Administrateur existant trouvé : {admin_exists.employee_number}")
            
            # Statistiques finales
            total_employees = Employee.query.count()
            total_entries = TimeEntry.query.count()
            
            print(f"\n📈 État final de la base de données :")
            print(f"   • {total_employees} employés au total")
            print(f"   • {total_entries} pointages au total")
            
            if existing_employees > 0 or existing_entries > 0:
                print("✅ Données existantes préservées avec succès !")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        return False

def check_database_integrity():
    """Vérifier l'intégrité de la base de données"""
    try:
        from app import app, db
        from src.models.employee import Employee, TimeEntry
        
        with app.app_context():
            # Vérifier les employés
            employees = Employee.query.all()
            print(f"👥 Employés dans la base :")
            for emp in employees:
                print(f"   • {emp.employee_number} - {emp.first_name} {emp.last_name} ({'Admin' if emp.is_admin else 'Employé'})")
            
            # Vérifier les pointages récents
            recent_entries = TimeEntry.query.order_by(TimeEntry.date.desc()).limit(5).all()
            print(f"\n⏰ Pointages récents :")
            for entry in recent_entries:
                employee = Employee.query.get(entry.employee_id)
                print(f"   • {entry.date} - {employee.first_name} {employee.last_name} ({entry.total_hours}h)")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    
    if command == "init":
        print("🔧 Initialisation avec préservation des données")
        print("=" * 50)
        init_database_with_preservation()
    elif command == "check":
        print("🔍 Vérification de l'intégrité de la base de données")
        print("=" * 50)
        check_database_integrity()
    else:
        print("Usage:")
        print("  python init_with_preservation.py init   # Initialiser en préservant les données")
        print("  python init_with_preservation.py check  # Vérifier l'intégrité des données")
