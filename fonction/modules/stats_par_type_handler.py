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

    def get_stat_par_type(self, type_module: str, niveau: int) -> Optional[dict]:
        """
        Retourne un dictionnaire {'stat': ..., 'valeur': ...}
        ou None si rien trouvé.
        Cette méthode est utilisée pour l'autoremplissage.
        """
        stat, val = self.get_main_stat(type_module, niveau)
        if stat is not None and val is not None:
            return {"stat": stat, "valeur": val}
        return None
