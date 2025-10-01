#!/usr/bin/env python3
"""
Script de déploiement avec sauvegarde automatique des données
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from backup_data import backup_database, restore_database

def deploy_with_backup():
    """Déployer l'application en préservant les données"""
    print("🚀 Déploiement avec préservation des données")
    print("=" * 50)
    
    # 1. Créer une sauvegarde avant déploiement
    print("📦 Étape 1: Sauvegarde des données...")
    if backup_database():
        print("✅ Sauvegarde créée avec succès")
    else:
        print("⚠️  Échec de la sauvegarde, mais on continue...")
    
    print()
    
    # 2. Déployer sur Git
    print("📤 Étape 2: Déploiement sur GitHub...")
    try:
        # Ajouter tous les fichiers
        subprocess.run(['git', 'add', '.'], check=True, cwd=os.path.dirname(__file__))
        
        # Commit avec timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"Déploiement automatique - {timestamp}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, cwd=os.path.dirname(__file__))
        
        # Push vers GitHub
        subprocess.run(['git', 'push'], check=True, cwd=os.path.dirname(__file__))
        
        print("✅ Code déployé sur GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du déploiement Git : {e}")
        return False
    
    print()
    
    # 3. Attendre le redéploiement Render
    print("⏳ Étape 3: Attente du redéploiement Render...")
    print("   Render va automatiquement redéployer l'application.")
    print("   Cela peut prendre 2-5 minutes.")
    print()
    
    # 4. Instructions pour la restauration
    print("🔄 Étape 4: Restauration des données (si nécessaire)")
    print("   Si les données sont perdues après le redéploiement :")
    print("   1. Connectez-vous à l'application")
    print("   2. Exécutez : python backup_data.py restore")
    print("   3. Ou utilisez l'interface web de restauration")
    print()
    
    print("✅ Déploiement terminé !")
    print("🌐 URL de l'application : https://pointage-horaire-render.onrender.com")
    
    return True

def create_restore_endpoint():
    """Créer un endpoint web pour la restauration"""
    restore_code = '''
@app.route('/admin/restore-backup', methods=['POST'])
@admin_required
def restore_backup():
    """Restaurer la dernière sauvegarde (admin seulement)"""
    try:
        from backup_data import restore_database
        
        if restore_database():
            return jsonify({'message': 'Données restaurées avec succès'}), 200
        else:
            return jsonify({'error': 'Échec de la restauration'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la restauration: {str(e)}'}), 500

@app.route('/admin/create-backup', methods=['POST'])
@admin_required
def create_backup():
    """Créer une sauvegarde (admin seulement)"""
    try:
        from backup_data import backup_database
        
        if backup_database():
            return jsonify({'message': 'Sauvegarde créée avec succès'}), 200
        else:
            return jsonify({'error': 'Échec de la sauvegarde'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500
'''
    
    print("📝 Code pour les endpoints de sauvegarde/restauration :")
    print(restore_code)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "endpoints":
        create_restore_endpoint()
    else:
        deploy_with_backup()
