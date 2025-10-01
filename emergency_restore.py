#!/usr/bin/env python3
"""
Script de récupération d'urgence pour restaurer l'application
"""
import os
import sys
import hashlib

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def hash_password(password):
    """Hasher un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def emergency_restore():
    """Restauration d'urgence de l'application"""
    try:
        print("🚨 Récupération d'urgence en cours...")
        
        # Créer le dossier database
        database_dir = os.path.join(os.path.dirname(__file__), 'database')
        os.makedirs(database_dir, exist_ok=True)
        print(f"✅ Dossier database créé : {database_dir}")
        
        # Importer l'application
        from app import app, db
        from src.models.employee import Employee
        
        with app.app_context():
            # Créer toutes les tables
            db.create_all()
            print("✅ Tables de base de données créées")
            
            # Vérifier si l'admin existe
            admin = Employee.query.filter_by(employee_number='ADMIN001').first()
            
            if not admin:
                # Créer l'admin par défaut
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
                print("✅ Administrateur existant trouvé")
            
            # Tenter de restaurer depuis une sauvegarde
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.json')]
                if backup_files:
                    print(f"📂 {len(backup_files)} sauvegardes trouvées")
                    print("💡 Pour restaurer les données, exécutez : python backup_data.py restore")
                else:
                    print("⚠️  Aucune sauvegarde trouvée")
            else:
                print("⚠️  Dossier de sauvegarde non trouvé")
            
            print("\n✅ Récupération d'urgence terminée !")
            print("🌐 L'application devrait maintenant fonctionner")
            print("🔑 Identifiants : ADMIN001 / admin123")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération : {e}")
        return False

if __name__ == "__main__":
    emergency_restore()
