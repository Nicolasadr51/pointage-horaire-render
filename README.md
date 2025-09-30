# Pointeuse Horaire - Render Deployment

Application de gestion du temps de travail avec système de pointage pour les employés.

## 🚀 Déploiement sur Render

Cette version est optimisée pour le déploiement gratuit sur Render.com.

## 🔑 Identifiants par défaut

- **Administrateur** : `ADMIN001` / `admin123`

## 🛠️ Technologies

L'application utilise Flask comme framework backend avec SQLAlchemy pour la gestion de la base de données SQLite. Le frontend React est intégré directement dans l'application Flask pour simplifier le déploiement.

## 📋 Fonctionnalités principales

L'application offre un système complet de gestion du temps avec authentification sécurisée et différents niveaux d'accès. Les employés peuvent effectuer leurs pointages quotidiens tandis que les administrateurs disposent d'un tableau de bord complet pour la gestion des équipes.

Le système de pointage permet quatre enregistrements par jour correspondant aux moments clés de la journée de travail. Les données sont exportables dans différents formats pour faciliter les analyses et rapports.

## 🔧 Configuration Render

L'application est configurée pour fonctionner automatiquement sur Render avec les paramètres suivants :

| Paramètre | Valeur |
|-----------|--------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python app.py` |
| Port | Variable d'environnement `PORT` |
| Python Version | 3.11.0 |

## 📊 Structure de l'application

L'architecture suit une approche modulaire avec séparation claire entre les modèles de données, les routes API et l'interface utilisateur. La base de données SQLite assure la persistance des données avec création automatique des tables au premier démarrage.

## 🔐 Sécurité

L'application implémente des mesures de sécurité appropriées incluant le hachage des mots de passe, la gestion des sessions sécurisées et la protection CORS pour les requêtes cross-origin.
