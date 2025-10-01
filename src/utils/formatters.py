"""
Utilitaires de formatage pour l'application de pointage
"""

def format_hours(hours):
    """
    Formate les heures pour un affichage lisible
    
    Args:
        hours (float): Nombre d'heures (ex: 7.5)
    
    Returns:
        str: Heures formatées (ex: "7h30" ou "7.5h")
    """
    if hours is None or hours == 0:
        return "0h00"
    
    # Arrondir à 2 décimales
    hours = round(hours, 2)
    
    # Séparer les heures et les minutes
    hours_int = int(hours)
    minutes_decimal = hours - hours_int
    minutes = round(minutes_decimal * 60)
    
    # Si les minutes sont 0, afficher seulement les heures
    if minutes == 0:
        return f"{hours_int}h00"
    
    # Si les minutes sont un multiple de 15, afficher en format h:mm
    if minutes % 15 == 0:
        return f"{hours_int}h{minutes:02d}"
    
    # Sinon, afficher en format décimal avec 2 chiffres max
    if hours == hours_int:
        return f"{hours_int}h00"
    elif hours < 10:
        return f"{hours:.2f}h".rstrip('0').rstrip('.')
    else:
        return f"{hours:.1f}h"

def format_duration(start_time, end_time):
    """
    Calcule et formate la durée entre deux heures
    
    Args:
        start_time (time): Heure de début
        end_time (time): Heure de fin
    
    Returns:
        str: Durée formatée (ex: "4h30")
    """
    if not start_time or not end_time:
        return "0h00"
    
    from datetime import datetime, date
    
    # Convertir en datetime pour calculer la différence
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    
    # Calculer la différence en heures
    delta = end_dt - start_dt
    hours = delta.total_seconds() / 3600
    
    return format_hours(hours)

def format_percentage(value, decimals=1):
    """
    Formate un pourcentage avec un nombre limité de décimales
    
    Args:
        value (float): Valeur en pourcentage
        decimals (int): Nombre de décimales (défaut: 1)
    
    Returns:
        str: Pourcentage formaté (ex: "85.5%")
    """
    if value is None:
        return "0%"
    
    return f"{round(value, decimals)}%"

def format_time_range(start_time, end_time):
    """
    Formate une plage horaire
    
    Args:
        start_time (time): Heure de début
        end_time (time): Heure de fin
    
    Returns:
        str: Plage formatée (ex: "09:00 - 12:30")
    """
    if not start_time and not end_time:
        return "--:-- - --:--"
    
    start_str = start_time.strftime('%H:%M') if start_time else "--:--"
    end_str = end_time.strftime('%H:%M') if end_time else "--:--"
    
    return f"{start_str} - {end_str}"
