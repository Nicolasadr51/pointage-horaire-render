# 🔒 Guide de Déploiement avec Disque Persistant

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
