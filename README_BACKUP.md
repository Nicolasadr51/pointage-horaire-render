# 🔄 Système de Sauvegarde et Restauration

## 📋 Vue d'ensemble

L'application de pointage dispose maintenant d'un **système complet de sauvegarde et restauration** qui préserve toutes les données lors des mises à jour.

## 🛡️ Protection des données

### ✅ **Données préservées :**
- **Comptes employés** (identifiants, mots de passe, permissions)
- **Historique des pointages** (tous les pointages passés)
- **Statistiques** (heures travaillées, présences)
- **Configuration** (paramètres de l'application)

### 🔧 **Mécanismes de protection :**

1. **Initialisation intelligente** : Préserve les données existantes
2. **Sauvegarde automatique** : Scripts de sauvegarde avant déploiement
3. **Restauration manuelle** : Interface admin pour restaurer les données
4. **Sauvegardes multiples** : Historique des sauvegardes

## 🚀 Utilisation

### **1. Sauvegarde manuelle (Interface Admin)**

```
1. Se connecter en tant qu'admin
2. Aller dans l'interface d'administration
3. Cliquer sur "Créer une sauvegarde"
4. Confirmation de la sauvegarde créée
```

### **2. Sauvegarde via ligne de commande**

```bash
# Créer une sauvegarde
python backup_data.py backup

# Lister les sauvegardes
python backup_data.py list

# Restaurer la dernière sauvegarde
python backup_data.py restore
```

### **3. Déploiement avec sauvegarde automatique**

```bash
# Déploiement sécurisé avec sauvegarde
python deploy_with_backup.py
```

## 📁 Structure des sauvegardes

```
backups/
├── backup_20241001_143022.json    # Sauvegarde JSON
├── app_20241001_143022.db          # Copie de la base SQLite
├── backup_20241001_120000.json    # Sauvegarde précédente
└── app_20241001_120000.db          # Base précédente
```

## 🔄 Processus de mise à jour

### **Avant chaque déploiement :**

1. ✅ **Sauvegarde automatique** des données existantes
2. ✅ **Déploiement** du nouveau code sur GitHub
3. ✅ **Redéploiement** automatique sur Render
4. ✅ **Préservation** des données existantes
5. ✅ **Restauration** si nécessaire

### **En cas de perte de données :**

1. **Se connecter en admin** sur l'application
2. **Utiliser l'interface de restauration** dans l'admin
3. **Ou exécuter** `python backup_data.py restore`
4. **Vérifier** que les données sont restaurées

## 🎯 Endpoints API

### **Sauvegarde (Admin uniquement)**
```
POST /admin/create-backup
```

### **Restauration (Admin uniquement)**
```
POST /admin/restore-backup
```

### **Liste des sauvegardes (Admin uniquement)**
```
GET /admin/list-backups
```

## ⚡ Avantages

### **🔒 Sécurité des données**
- **Aucune perte** lors des mises à jour
- **Sauvegardes multiples** avec horodatage
- **Restauration rapide** en cas de problème

### **🚀 Déploiement sans risque**
- **Mises à jour transparentes** pour les utilisateurs
- **Rollback possible** en cas de problème
- **Continuité de service** garantie

### **👥 Préservation des comptes**
- **Employés existants** conservés
- **Mots de passe** préservés
- **Permissions** maintenues

## 🔧 Scripts disponibles

| Script | Description |
|--------|-------------|
| `backup_data.py` | Sauvegarde/restauration manuelle |
| `deploy_with_backup.py` | Déploiement sécurisé |
| `init_with_preservation.py` | Initialisation intelligente |

## 📞 Support

En cas de problème avec les sauvegardes :

1. **Vérifier** les logs de l'application
2. **Utiliser** `python backup_data.py list` pour voir les sauvegardes
3. **Restaurer** avec `python backup_data.py restore`
4. **Contacter** l'administrateur système si nécessaire

---

**✅ Vos données sont maintenant protégées lors de chaque mise à jour !**
