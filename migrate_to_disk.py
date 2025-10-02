#!/usr/bin/env python3
"""
Script de migration vers le disque persistant
Copie les données existantes vers le nouveau stockage persistant
"""
import os
import shutil
import sqlite3
from datetime import datetime

def migrate_to_persistent_disk():
    """Migrer les données vers le disque persistant"""
    
    # Chemins
    old_db = '/home/ubuntu/pointage-render/database/app.db'
    persistent_dir = '/opt/render/project/data'
    new_db = os.path.join(persistent_dir, 'app.db')
    
    print("🔄 Migration vers le disque persistant")
    print("=" * 40)
    
    # Vérifier si le disque persistant est disponible
    if not os.path.exists(persistent_dir):
        print("❌ Disque persistant non trouvé")
        print("   Assurez-vous que le service utilise un plan payant")
        return False
    
    # Créer le répertoire de sauvegarde
    backup_dir = os.path.join(persistent_dir, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Migrer la base de données si elle existe
    if os.path.exists(old_db):
        print(f"📦 Migration de {old_db} vers {new_db}")
        shutil.copy2(old_db, new_db)
        
        # Créer une sauvegarde immédiate
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'migration_backup_{timestamp}.db')
        shutil.copy2(new_db, backup_file)
        
        print(f"✅ Base de données migrée")
        print(f"✅ Sauvegarde créée : {backup_file}")
        
        # Vérifier l'intégrité
        try:
            conn = sqlite3.connect(new_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees")
            employee_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM time_entries")
            entry_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"📊 Données vérifiées :")
            print(f"   • {employee_count} employés")
            print(f"   • {entry_count} pointages")
            
        except Exception as e:
            print(f"⚠️ Erreur lors de la vérification : {e}")
    
    else:
        print("ℹ️ Aucune base de données existante trouvée")
        print("   Une nouvelle base sera créée automatiquement")
    
    print("✅ Migration terminée avec succès !")
    return True

if __name__ == "__main__":
    migrate_to_persistent_disk()
