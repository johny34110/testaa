import os
import json

class Module:
    def __init__(self, nom, type_, niveau, stat_principale, valeur_principale, sous_stats=None):
        self.nom = nom
        self.type = type_
        self.niveau = niveau
        self.stat_principale = stat_principale
        self.valeur_principale = valeur_principale
        self.sous_stats = sous_stats if sous_stats else []

    def to_dict(self):
        return {
            "nom": self.nom,
            "type": self.type,
            "niveau": self.niveau,
            "stat_principale": self.stat_principale,
            "valeur_principale": self.valeur_principale,
            "sous_stats": self.sous_stats
        }

    @staticmethod
    def from_dict(d):
        return Module(
            nom=d.get("nom"),
            type_=d.get("type"),
            niveau=d.get("niveau"),
            stat_principale=d.get("stat_principale"),
            valeur_principale=d.get("valeur_principale"),
            sous_stats=d.get("sous_stats", [])
        )

    def __str__(self):
        return f"{self.nom} [{self.type} N{self.niveau}]"


class ModuleManager:
    def __init__(self, filepath="data/modules.json"):
        self.filepath = filepath
        self.modules = self.load_modules()

    def load_modules(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Module.from_dict(d) for d in data] if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError):
            return []

    def save_modules(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.modules], f, indent=2, ensure_ascii=False)

    def add_module(self, module):
        self.modules.append(module)
        self.save_modules()

    def update_module(self, index, new_module):
        if 0 <= index < len(self.modules):
            self.modules[index] = new_module
            self.save_modules()

    def delete_module(self, index):
        if 0 <= index < len(self.modules):
            del self.modules[index]
            self.save_modules()

    def search_modules(self, nom=None, type_=None, sous_stat=None, valeur_exacte=None):
        result = self.modules
        if nom:
            result = [m for m in result if nom.lower() in m.nom.lower()]
        if type_:
            result = [m for m in result if m.type == type_]
        if sous_stat:
            result = [
                m for m in result
                if any(sous_stat.lower() in s["stat"].lower() for s in m.sous_stats)
            ]
        if valeur_exacte is not None:
            result = [m for m in result if m.valeur_principale == valeur_exacte]
        return result
