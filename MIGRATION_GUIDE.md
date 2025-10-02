# 🔄 Guide de Migration vers PostgreSQL

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
