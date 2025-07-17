'''
Module: stats_par_type_handler.py

📊 Système de stats_par_type.json – fonctionnement détaillé

🎯 Objectif:
Ce module gère la lecture, l'écriture et l'initialisation du fichier data/stats_par_type.json qui contient:
  - Pour chaque type de module (casque, transitor, bracelet, noyau):
    • La stat principale (main_stat) pour les types fixes.
    • Le mapping "par_niveau" des valeurs associées à chaque niveau.
  - Pour les noyaux, un mapping flexible de sous-stats principales selon le niveau.

Fonctionnalités:
  1. Initialisation automatique du fichier JSON s'il n'existe pas ou est vide.
  2. Lecture des données existantes pour préremplir l'interface:
     - casque, transitor, bracelet: stat et valeur fixe selon niveau.
     - noyau: aucune stat forcée, l'utilisateur choisit.
  3. Sauvegarde dynamique pour les noyaux:
     - Si l'utilisateur crée un noyau avec une stat principale/niveau non présent,
       on ajoute l'entrée dans le JSON pour usage futur.

Structure attendue (exemple):
{
  "casque": {
    "main_stat": "Attaque",
    "par_niveau": {"12": 270, "15": 330}
  },
  "transitor": {
    "main_stat": "PV",
    "par_niveau": {"12": 2700, "15": 3300}
  },
  "bracelet": {
    "main_stat": "Défense",
    "par_niveau": {"12": 205, "15": 250}
  },
  "noyau": {
    "Attaque %": {"12": 5, "15": 6},
    "Défense %": {"12": 5, "15": 6},
    ...
  }
}

Usage:
    handler = StatsParTypeHandler('data/stats_par_type.json')
    # Obtenir stat principale
    stat, valeur = handler.get_main_stat('casque', 12)
    # Pour noyau: si absent, valeur par défaut None
    stat, valeur = handler.get_main_stat('noyau', 13)

    # Enregistrer dynamiquement une nouvelle statistique de noyau
    handler.set_noyau_stat('Crit%', 14, 7)

    # Sauvegarde du fichier JSON
    handler.save()
'''

import json
import os
from typing import Tuple, Optional

class StatsParTypeHandler:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = {}
        self._load_or_initialize()

    def _load_or_initialize(self):
        """
        Charge le fichier JSON existant ou crée la structure de base.
        """
        if not os.path.exists(self.filepath) or os.stat(self.filepath).st_size == 0:
            # Structure de base
            self.data = {
                "casque": {"main_stat": "Attaque", "par_niveau": {}},
                "transitor": {"main_stat": "PV", "par_niveau": {}},
                "bracelet": {"main_stat": "Défense", "par_niveau": {}},
                "noyau": {}
            }
            self._save_json()
        else:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def get_main_stat(self, module_type: str, niveau: int) -> Tuple[Optional[str], Optional[int]]:
        """
        Retourne (stat_principale, valeur) pour le type et niveau donnés.
        Pour les types fixes (casque, transitor, bracelet), renvoie toujours main_stat défini,
        et valeur via par_niveau.get(niveau.
        Pour noyau, renvoie (None, None) si inexistant.
        """
        t = module_type.lower()
        niveau_str = str(niveau)
        if t in ('casque', 'transitor', 'bracelet'):
            entry = self.data.get(t, {})
            stat = entry.get('main_stat')
            valeur = entry.get('par_niveau', {}).get(niveau_str)
            return stat, valeur
        elif t == 'noyau':
            # cherche une stat présente pour ce niveau
            for stat_name, levels in self.data['noyau'].items():
                if niveau_str in levels:
                    return stat_name, levels[niveau_str]
            return None, None
        else:
            return None, None

    def set_noyau_stat(self, stat_name: str, niveau: int, valeur: int):
        """
        Pour un noyau, ajoute ou met à jour la valeur de stat_name au niveau donné.
        """
        niveaux = self.data.setdefault('noyau', {})
        entry = niveaux.setdefault(stat_name, {})
        entry[str(niveau)] = valeur
        self._save_json()

    def _save_json(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def save(self):
        """Exporte la structure actuelle vers le fichier JSON."""
        self._save_json()
