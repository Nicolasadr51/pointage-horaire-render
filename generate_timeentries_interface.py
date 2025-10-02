#!/usr/bin/env python3
"""
Générateur d'interface de gestion des pointages utilisant l'API Anthropic
"""

import os
import anthropic
from datetime import datetime

def generate_timeentries_interface():
    """Génère une interface complète de gestion des pointages avec l'API Anthropic"""
    
    # Configuration de l'API Anthropic
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    # Prompt pour générer l'interface complète
    prompt = """
    Crée une interface web complète de gestion des pointages pour une application Flask.
    
    CONTEXTE:
    - Application de pointage horaire avec employés
    - Backend Flask avec API REST déjà implémentée
    - Besoin d'une interface admin pour gérer les pointages
    
    API DISPONIBLES:
    - GET /api/admin/timeentries (liste avec filtres, pagination)
    - POST /api/admin/timeentries (création)
    - PUT /api/admin/timeentries/<id> (modification)
    - DELETE /api/admin/timeentries/<id> (suppression)
    - POST /api/admin/timeentries/bulk (opérations en lot)
    - GET /api/admin/employees (liste des employés)
    
    FONCTIONNALITÉS REQUISES:
    1. Tableau des pointages avec pagination
    2. Filtres par employé, date, type (entrée/sortie)
    3. Formulaire de création de pointage
    4. Modification inline des pointages
    5. Suppression individuelle et en lot
    6. Interface responsive et moderne
    7. Gestion d'erreurs et messages de confirmation
    8. Validation des données côté client
    
    CONTRAINTES TECHNIQUES:
    - HTML5 + CSS3 + JavaScript vanilla (pas de framework)
    - Compatible avec tous les navigateurs modernes
    - Design moderne et professionnel
    - Utilisation d'AJAX pour les appels API
    - Gestion des erreurs réseau
    - Interface intuitive et ergonomique
    
    DESIGN:
    - Couleurs: bleu (#007bff), vert (#28a745), rouge (#dc3545)
    - Typographie moderne et lisible
    - Icônes Font Awesome ou équivalent
    - Layout responsive avec CSS Grid/Flexbox
    - Animations subtiles pour les interactions
    
    Génère un fichier HTML complet avec CSS et JavaScript intégrés.
    """
    
    try:
        print("🤖 Génération de l'interface avec l'API Anthropic...")
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extraire le contenu HTML de la réponse
        html_content = message.content[0].text
        
        # Sauvegarder l'interface générée
        output_file = "/home/ubuntu/pointage-render/static/admin_timeentries_generated.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Interface générée avec succès: {output_file}")
        print(f"📊 Taille du fichier: {len(html_content)} caractères")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        return None

if __name__ == "__main__":
    generate_timeentries_interface()
