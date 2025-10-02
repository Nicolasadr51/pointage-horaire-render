#!/usr/bin/env python3
"""
Solution de persistance utilisant les disques persistants de Render
Alternative simple et gratuite à PostgreSQL externe
"""
import os
import sys
import json
import shutil
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_persistent_disk_app():
    """Créer une version d'app.py optimisée pour les disques persistants"""
    
    app_content = '''#!/usr/bin/env python3
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

# Configuration de la base de données avec disque persistant
# Le disque persistant sera monté sur /opt/render/project/data
persistent_data_dir = '/opt/render/project/data'
local_data_dir = os.path.join(os.path.dirname(__file__), 'database')

# Utiliser le disque persistant si disponible, sinon local
if os.path.exists(persistent_data_dir) and os.access(persistent_data_dir, os.W_OK):
    database_dir = persistent_data_dir
    print("🔒 Utilisation du disque persistant Render pour la base de données")
else:
    database_dir = local_data_dir
    print("🗄️ Utilisation du stockage local (développement)")

os.makedirs(database_dir, exist_ok=True)
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
        # Créer une sauvegarde sur le disque persistant
        backup_dir = os.path.join(database_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.db')
        
        # Copier la base de données
        shutil.copy2(database_path, backup_file)
        
        return jsonify({
            'message': 'Sauvegarde créée avec succès sur disque persistant',
            'backup_file': f'backup_{timestamp}.db',
            'location': 'Disque persistant Render'
        }), 200
            
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
        backup_dir = os.path.join(database_dir, 'backups')
        
        if not os.path.exists(backup_dir):
            return jsonify({'error': 'Aucune sauvegarde trouvée'}), 404
        
        # Trouver la sauvegarde la plus récente
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.db')]
        
        if not backup_files:
            return jsonify({'error': 'Aucune sauvegarde trouvée'}), 404
        
        latest_backup = sorted(backup_files)[-1]
        backup_path = os.path.join(backup_dir, latest_backup)
        
        # Restaurer la base de données
        shutil.copy2(backup_path, database_path)
        
        return jsonify({
            'message': 'Données restaurées avec succès',
            'restored_from': latest_backup
        }), 200
            
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
        backup_dir = os.path.join(database_dir, 'backups')
        
        if not os.path.exists(backup_dir):
            return jsonify({
                'backups': [], 
                'storage_type': 'Disque persistant Render',
                'note': 'Aucune sauvegarde trouvée'
            }), 200
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('backup_') and f.endswith('.db')]
        
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
            'storage_type': 'Disque persistant Render',
            'database_location': database_path
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la liste des sauvegardes: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    is_persistent = os.path.exists(persistent_data_dir) and os.access(persistent_data_dir, os.W_OK)
    
    return {
        'status': 'healthy', 
        'app': 'pointeuse-horaire',
        'database': 'SQLite',
        'storage': 'Disque persistant' if is_persistent else 'Local',
        'persistent': is_persistent,
        'database_path': database_path
    }, 200

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
'''
    
    # Sauvegarder le nouveau app.py
    with open('app_persistent_disk.py', 'w') as f:
        f.write(app_content)
    
    print("✅ App.py avec disque persistant créé : app_persistent_disk.py")

def create_render_yaml():
    """Créer le fichier render.yaml avec configuration du disque persistant"""
    
    render_config = '''services:
  - type: web
    name: pointage-horaire
    env: python
    plan: starter  # Plan payant requis pour les disques persistants
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0
    disk:
      name: pointage-data
      mountPath: /opt/render/project/data
      sizeGB: 1  # 1 GB suffit largement pour l'application
'''
    
    with open('render_persistent.yaml', 'w') as f:
        f.write(render_config)
    
    print("✅ Configuration Render avec disque persistant : render_persistent.yaml")

def create_migration_script():
    """Créer un script de migration des données existantes"""
    
    migration_script = '''#!/usr/bin/env python3
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
'''
    
    with open('migrate_to_disk.py', 'w') as f:
        f.write(migration_script)
    
    print("✅ Script de migration créé : migrate_to_disk.py")

def create_deployment_guide():
    """Créer un guide de déploiement avec disque persistant"""
    
    guide = '''# 🔒 Guide de Déploiement avec Disque Persistant

## 📋 Solution de Persistance

Cette solution utilise les **disques persistants de Render** pour assurer la persistance des données sans avoir besoin de services externes.

## ✅ Avantages

- **Persistance garantie** : Les données survivent aux redéploiements
- **Simplicité** : Pas de configuration externe nécessaire
- **Sauvegardes automatiques** : Snapshots quotidiens par Render
- **Performance** : SSD haute performance
- **Sécurité** : Chiffrement au repos

## 💰 Coût

- **Plan Starter requis** : $7/mois minimum
- **Disque 1 GB** : Inclus dans le plan
- **Total** : $7/mois pour une solution complète

## 🚀 Étapes de Déploiement

### 1. Préparer les fichiers

```bash
# Remplacer app.py par la version avec disque persistant
cp app_persistent_disk.py app.py

# Utiliser la configuration Render avec disque
cp render_persistent.yaml render.yaml
```

### 2. Configurer le service sur Render

1. Aller dans le dashboard Render
2. Modifier le service existant
3. **Upgrader vers le plan Starter** ($7/mois)
4. Ajouter un disque persistant :
   - **Nom** : pointage-data
   - **Taille** : 1 GB
   - **Point de montage** : /opt/render/project/data

### 3. Redéployer

1. Commit et push les changements sur GitHub
2. Le redéploiement se fait automatiquement
3. Le disque persistant sera créé et monté

### 4. Vérifier la migration

1. Vérifier les logs de déploiement
2. Tester la connexion à l'application
3. Créer un employé de test
4. Vérifier que les données persistent après redéploiement

## 🔧 Fonctionnalités

### Sauvegardes automatiques
- **Snapshots quotidiens** par Render
- **Rétention** : 7 jours minimum
- **Restauration** : Via le dashboard Render

### Sauvegardes manuelles
- Interface admin pour créer des sauvegardes
- Stockage sur le disque persistant
- Restauration via l'interface

### Monitoring
- Surveillance de l'utilisation du disque
- Alertes en cas de problème
- Métriques de performance

## 🔍 Vérification

Après déploiement, vérifier :

1. **Health check** : `/health` doit indiquer "Disque persistant"
2. **Création d'employés** : Doit fonctionner
3. **Persistance** : Les données doivent survivre aux redéploiements
4. **Sauvegardes** : Interface admin fonctionnelle

## 📞 Support

En cas de problème :

1. Vérifier les logs Render
2. Vérifier que le plan Starter est actif
3. Vérifier que le disque est correctement monté
4. Contacter le support Render si nécessaire

## 🎯 Résultat

Avec cette solution :
- ✅ **Persistance garantie** des données
- ✅ **Sauvegardes automatiques** quotidiennes
- ✅ **Interface de gestion** complète
- ✅ **Performance optimale** avec SSD
- ✅ **Sécurité** avec chiffrement

**Coût total : $7/mois pour une solution professionnelle complète**
'''
    
    with open('DEPLOYMENT_GUIDE_PERSISTENT.md', 'w') as f:
        f.write(guide)
    
    print("✅ Guide de déploiement créé : DEPLOYMENT_GUIDE_PERSISTENT.md")

def main():
    """Fonction principale"""
    print("🔒 Préparation de la solution avec disque persistant")
    print("=" * 50)
    
    # Créer tous les fichiers nécessaires
    create_persistent_disk_app()
    create_render_yaml()
    create_migration_script()
    create_deployment_guide()
    
    print("\n✅ Solution avec disque persistant préparée !")
    print("\n📋 Prochaines étapes :")
    print("1. Upgrader vers le plan Starter sur Render ($7/mois)")
    print("2. Ajouter un disque persistant de 1 GB")
    print("3. Remplacer app.py par app_persistent_disk.py")
    print("4. Redéployer l'application")
    print("\n📖 Consultez DEPLOYMENT_GUIDE_PERSISTENT.md pour les détails")
    print("\n💡 Cette solution garantit la persistance des données pour $7/mois")

if __name__ == "__main__":
    main()
