#!/usr/bin/env python3
"""
Analyseur et améliorateur de code utilisant Claude 4.X
"""

import os
import anthropic
import json
from datetime import datetime

class CodeAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = "claude-3-5-sonnet-20241022"  # Version la plus récente disponible
    
    def analyze_code(self, file_path, code_type="web_interface"):
        """Analyse un fichier de code avec Claude 4.X"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé: {file_path}")
            return None
        
        analysis_prompt = f"""
        Tu es un expert en développement web et en analyse de code. Analyse ce code {code_type} et fournis une évaluation détaillée.

        CODE À ANALYSER:
        ```
        {code_content}
        ```

        ANALYSE DEMANDÉE:
        1. **Qualité du code** (structure, lisibilité, maintenabilité)
        2. **Sécurité** (vulnérabilités potentielles, validation des données)
        3. **Performance** (optimisations possibles, bonnes pratiques)
        4. **Accessibilité** (standards WCAG, utilisabilité)
        5. **Compatibilité** (navigateurs, responsive design)
        6. **Erreurs et bugs** potentiels
        7. **Améliorations recommandées** (priorité haute, moyenne, basse)

        FORMAT DE RÉPONSE:
        Fournis une analyse structurée en JSON avec:
        - score_global (0-10)
        - points_forts (array)
        - problemes_critiques (array)
        - problemes_mineurs (array)
        - ameliorations_recommandees (array avec priorité)
        - code_ameliore (si nécessaire)

        Sois précis et constructif dans tes recommandations.
        """
        
        try:
            print(f"🔍 Analyse du code avec Claude 4.X: {file_path}")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )
            
            analysis_result = message.content[0].text
            print(f"✅ Analyse terminée pour {file_path}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
            return None
    
    def improve_code(self, file_path, analysis_result):
        """Améliore le code basé sur l'analyse de Claude 4.X"""
        
        improvement_prompt = f"""
        Basé sur cette analyse précédente, améliore le code en corrigeant tous les problèmes identifiés.

        ANALYSE PRÉCÉDENTE:
        {analysis_result}

        INSTRUCTIONS D'AMÉLIORATION:
        1. Corrige TOUS les problèmes critiques
        2. Implémente les améliorations haute priorité
        3. Optimise les performances
        4. Améliore la sécurité et la validation
        5. Assure la compatibilité cross-browser
        6. Améliore l'accessibilité
        7. Garde le même design et fonctionnalités

        CONTRAINTES:
        - Conserve toutes les fonctionnalités existantes
        - Maintiens la compatibilité avec les API existantes
        - Utilise les mêmes technologies (HTML5, CSS3, JavaScript vanilla)
        - Garde le design moderne et responsive

        Fournis le code amélioré complet et fonctionnel.
        """
        
        try:
            print(f"🔧 Amélioration du code avec Claude 4.X...")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": improvement_prompt
                    }
                ]
            )
            
            improved_code = message.content[0].text
            print(f"✅ Code amélioré généré")
            
            return improved_code
            
        except Exception as e:
            print(f"❌ Erreur lors de l'amélioration: {e}")
            return None
    
    def validate_improvements(self, original_code, improved_code):
        """Valide les améliorations avec Claude 4.X"""
        
        validation_prompt = f"""
        Tu es un expert en assurance qualité logicielle. Compare ces deux versions de code et valide que les améliorations sont correctes.

        CODE ORIGINAL:
        ```
        {original_code[:2000]}...
        ```

        CODE AMÉLIORÉ:
        ```
        {improved_code[:2000]}...
        ```

        VALIDATION DEMANDÉE:
        1. **Fonctionnalités préservées** - Toutes les fonctions originales sont-elles maintenues?
        2. **Améliorations effectives** - Les problèmes identifiés sont-ils résolus?
        3. **Régression** - Y a-t-il de nouveaux problèmes introduits?
        4. **Qualité globale** - Le code est-il objectivement meilleur?
        5. **Recommandations finales** - Autres améliorations suggérées?

        FORMAT DE RÉPONSE:
        Fournis une validation structurée avec:
        - validation_ok (true/false)
        - score_amelioration (0-10)
        - fonctionnalites_preservees (true/false)
        - problemes_resolus (array)
        - nouveaux_problemes (array)
        - recommandation_finale (APPROUVER/REJETER/MODIFIER)
        - commentaires (string)

        Sois rigoureux dans ta validation.
        """
        
        try:
            print(f"✅ Validation des améliorations avec Claude 4.X...")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ]
            )
            
            validation_result = message.content[0].text
            print(f"✅ Validation terminée")
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Erreur lors de la validation: {e}")
            return None

def main():
    """Processus complet d'analyse et d'amélioration"""
    
    analyzer = CodeAnalyzer()
    
    # Fichier à analyser
    target_file = "/home/ubuntu/pointage-render/static/admin_timeentries_generated.html"
    
    print("🚀 PROCESSUS D'AMÉLIORATION AVEC CLAUDE 4.X")
    print("=" * 50)
    
    # Étape 1: Analyse
    print("\n📊 ÉTAPE 1: ANALYSE DU CODE")
    analysis = analyzer.analyze_code(target_file, "interface_web_gestion_pointages")
    
    if not analysis:
        print("❌ Échec de l'analyse")
        return
    
    print(f"📋 Analyse terminée ({len(analysis)} caractères)")
    
    # Étape 2: Amélioration
    print("\n🔧 ÉTAPE 2: AMÉLIORATION DU CODE")
    improved_code = analyzer.improve_code(target_file, analysis)
    
    if not improved_code:
        print("❌ Échec de l'amélioration")
        return
    
    print(f"✨ Code amélioré généré ({len(improved_code)} caractères)")
    
    # Étape 3: Validation
    print("\n✅ ÉTAPE 3: VALIDATION DES AMÉLIORATIONS")
    with open(target_file, 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    validation = analyzer.validate_improvements(original_code, improved_code)
    
    if not validation:
        print("❌ Échec de la validation")
        return
    
    print(f"🎯 Validation terminée")
    
    # Sauvegarde des résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sauvegarder l'analyse
    with open(f"/home/ubuntu/pointage-render/analysis_{timestamp}.txt", 'w', encoding='utf-8') as f:
        f.write(analysis)
    
    # Sauvegarder le code amélioré
    with open(f"/home/ubuntu/pointage-render/static/admin_timeentries_improved_{timestamp}.html", 'w', encoding='utf-8') as f:
        f.write(improved_code)
    
    # Sauvegarder la validation
    with open(f"/home/ubuntu/pointage-render/validation_{timestamp}.txt", 'w', encoding='utf-8') as f:
        f.write(validation)
    
    print(f"\n🎉 PROCESSUS TERMINÉ!")
    print(f"📁 Fichiers générés:")
    print(f"   - analysis_{timestamp}.txt")
    print(f"   - admin_timeentries_improved_{timestamp}.html")
    print(f"   - validation_{timestamp}.txt")
    
    return True

if __name__ == "__main__":
    main()
