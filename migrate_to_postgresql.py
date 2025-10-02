#!/usr/bin/env python3
"""
Script de migration vers PostgreSQL (Supabase)
Migre l'application de SQLite vers PostgreSQL pour une persistance robuste
"""
import os
import sys
import json
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_postgresql_config():
    """Créer la configuration PostgreSQL pour Supabase"""
    
    # Configuration pour Supabase
    config = {
        "database_type": "postgresql",
        "supabase_url": "YOUR_SUPABASE_URL",
        "supabase_key": "YOUR_SUPABASE_ANON_KEY",
        "database_url": "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres",
        "migration_date": datetime.now().isoformat(),
        "benefits": [
            "Persistance des données garantie",
            "Pas de perte lors des redéploiements",
            "Sauvegardes automatiques",
            "Scalabilité",
            "500 MB gratuits avec Supabase"
        ]
    }
    
    # Sauvegarder la configuration
    with open('postgresql_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration PostgreSQL créée dans postgresql_config.json")
    return config

def create_updated_app_py():
    """Créer une version mise à jour d'app.py avec PostgreSQL"""
    
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

# Configuration de la base de données PostgreSQL
# Utiliser PostgreSQL (Supabase) en production, SQLite en développement
if os.environ.get('DATABASE_URL'):
    # Production avec PostgreSQL (Supabase)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    print("🐘 Utilisation de PostgreSQL (Supabase) pour la persistance")
else:
    # Développement avec SQLite
    database_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(database_dir, exist_ok=True)
    database_path = os.path.join(database_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    print("🗄️ Utilisation de SQLite pour le développement")

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
        # Avec PostgreSQL, les sauvegardes sont automatiques
        # Mais on peut créer un export JSON pour la compatibilité
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 'backup_data.py', 'backup'
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            return jsonify({'message': 'Sauvegarde créée avec succès (PostgreSQL + JSON)', 'output': result.stdout}), 200
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
        # Avec PostgreSQL, on peut restaurer depuis un export JSON
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
            return jsonify({'backups': [], 'note': 'PostgreSQL assure la persistance automatique'}), 200
        
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
            'database_type': 'PostgreSQL',
            'note': 'Les données sont automatiquement persistées avec PostgreSQL'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la liste des sauvegardes: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    db_type = "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
    return {
        'status': 'healthy', 
        'app': 'pointeuse-horaire',
        'database': db_type,
        'persistent': db_type == "PostgreSQL"
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
    with open('app_postgresql.py', 'w') as f:
        f.write(app_content)
    
    print("✅ Nouveau app.py créé avec support PostgreSQL : app_postgresql.py")

def create_requirements_postgresql():
    """Créer requirements.txt avec psycopg2 pour PostgreSQL"""
    
    requirements = '''Flask==2.3.3
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.21
Werkzeug==2.3.7
python-dateutil==2.8.2
pytz==2023.3
psycopg2-binary==2.9.7
'''
    
    with open('requirements_postgresql.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ Requirements PostgreSQL créés : requirements_postgresql.txt")

def create_migration_guide():
    """Créer un guide de migration"""
    
    guide = '''# 🔄 Guide de Migration vers PostgreSQL

## 📋 Étapes de Migration

### 1. Créer une base de données Supabase

1. Aller sur https://supabase.com
2. Créer un compte gratuit
3. Créer un nouveau projet
4. Noter les informations de connexion :
   - URL du projet
   - Clé API anonyme
   - URL de la base de données

### 2. Configurer les variables d'environnement sur Render

Dans le dashboard Render, ajouter ces variables d'environnement :

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_KEY=[ANON-KEY]
```

### 3. Mettre à jour les fichiers

1. Remplacer `app.py` par `app_postgresql.py`
2. Remplacer `requirements.txt` par `requirements_postgresql.txt`
3. Commit et push sur GitHub

### 4. Redéployer sur Render

Le redéploiement se fera automatiquement avec PostgreSQL.

## ✅ Avantages de PostgreSQL

- **Persistance garantie** : Les données ne sont plus perdues
- **Sauvegardes automatiques** : Supabase gère les sauvegardes
- **Scalabilité** : Peut gérer beaucoup plus d'utilisateurs
- **Gratuit** : 500 MB gratuits avec Supabase
- **Fiabilité** : Base de données professionnelle

## 🔧 Test de la Migration

Après migration, vérifier :

1. L'application démarre correctement
2. La connexion admin fonctionne
3. Création d'employés fonctionne
4. Les données persistent après redéploiement

## 📞 Support

En cas de problème :
1. Vérifier les logs Render
2. Vérifier les variables d'environnement
3. Tester la connexion à Supabase
'''
    
    with open('MIGRATION_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("✅ Guide de migration créé : MIGRATION_GUIDE.md")

def main():
    """Fonction principale de migration"""
    print("🔄 Préparation de la migration vers PostgreSQL")
    print("=" * 50)
    
    # Créer tous les fichiers nécessaires
    create_postgresql_config()
    create_updated_app_py()
    create_requirements_postgresql()
    create_migration_guide()
    
    print("\n✅ Migration préparée avec succès !")
    print("\n📋 Prochaines étapes :")
    print("1. Créer un compte Supabase gratuit")
    print("2. Configurer les variables d'environnement sur Render")
    print("3. Remplacer app.py et requirements.txt")
    print("4. Redéployer l'application")
    print("\n📖 Consultez MIGRATION_GUIDE.md pour les détails")

if __name__ == "__main__":
    main()
