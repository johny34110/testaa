
import json
import os
import uuid

MODULES_FILE = "modules.json"

class Module:
    def __init__(self, effet, type_, niveau, stat_principale, valeur_principale, sous_stats, id=None):
        self.id = id or self._generate_id()
        self.effet = effet
        self.type = type_
        self.niveau = niveau
        self.stat_principale = stat_principale
        self.valeur_principale = valeur_principale
        self.sous_stats = sous_stats

    def _generate_id(self):
        return f"MOD{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self):
        return {
            "id": self.id,
            "effet": self.effet,
            "type": self.type,
            "niveau": self.niveau,
            "stat_principale": self.stat_principale,
            "valeur_principale": self.valeur_principale,
            "sous_stats": self.sous_stats,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            effet=data["effet"],
            type_=data["type"],
            niveau=data["niveau"],
            stat_principale=data["stat_principale"],
            valeur_principale=data["valeur_principale"],
            sous_stats=data["sous_stats"],
            id=data.get("id")
        )

class ModuleManager:
    def __init__(self, filepath=MODULES_FILE):
        self.filepath = filepath
        self.modules = self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Module.from_dict(m) for m in data]

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in self.modules], f, indent=2, ensure_ascii=False)

    def add_module(self, module):
        self.modules.append(module)
        self.save()

    def update_module(self, index, new_module):
        self.modules[index] = new_module
        self.save()

    def delete_module(self, index):
        if 0 <= index < len(self.modules):
            del self.modules[index]
            self.save()
