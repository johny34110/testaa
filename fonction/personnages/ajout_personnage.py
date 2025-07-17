from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton, QWidget
import os
import sys

class AjoutPersonnageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1) Construire le chemin et logguer son état
        ui_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..", "..",
                "ui", "ajout_personnage.ui"
            )
        )
        print("▶ [DEBUG] ui_path =", ui_path)
        print("  exists? ", os.path.exists(ui_path))
        if os.path.exists(ui_path):
            print("  size   ", os.path.getsize(ui_path), "bytes")
        else:
            print("  → le fichier n’existe PAS !")

        # 2) Avant loadUi
        print("▶ [DEBUG] Avant uic.loadUi()")
        try:
            uic.loadUi(ui_path, self)
        except Exception as e:
            print("‼️ Exception levée par loadUi:", e, file=sys.stderr)
            raise
        print("▶ [DEBUG] Après uic.loadUi()")

        # 3) Liste tous les widgets chargés
        names = [w.objectName() for w in self.findChildren(QWidget)]
        print("▶ [DEBUG] Widgets chargés :", names)

        # 4) Redimensionnement
        self.resize(650, 750)
        self.setMinimumSize(650, 750)

        # 5) Connexion des boutons
        btn_valider = self.findChild(QPushButton, "buttonValider")
        btn_annuler = self.findChild(QPushButton, "buttonAnnuler")
        print("▶ [DEBUG] buttonValider trouvé ?", bool(btn_valider))
        print("▶ [DEBUG] buttonAnnuler trouvé ?", bool(btn_annuler))
        if not btn_valider or not btn_annuler:
            raise RuntimeError("Buttons not found, aborting")

        btn_valider.clicked.connect(self.on_valider)
        btn_annuler.clicked.connect(self.reject)

        # 6) Mapping (inchangé)
        self.mapping = {
            "PV": ("spinBoxPVBase", "spinBoxPVBonus"),
            "Attaque": ("spinBoxAttaqueBase", "spinBoxAttaqueBonus"),
            "Defense": ("spinBoxDefenseBase", "spinBoxDefenseBonus"),
            "Vitesse": ("spinBoxVitesseBase", "spinBoxVitesseBonus"),
            "Taux crit": ("spinBoxTauxcritBase", "spinBoxTauxcritBonus"),
            "Degats crit": ("spinBoxDegatsCritBase", "spinBoxDegatsCritBonus"),
            "Resistance": ("spinBoxResistanceBase", "spinBoxResistanceBonus"),
            "Precision": ("spinBoxPrecisionBase", "spinBoxPrecisionBonus"),
        }

    def remplir_champs(self, data: dict):
        """Préremplit les champs à partir des données existantes."""
        self.lineEditNom.setText(data.get("nom", ""))
        self.spinBoxNiveau.setValue(data.get("niveau", 1))
        for stat, (base_name, bonus_name) in self.mapping.items():
            base_widget = getattr(self, base_name, None)
            bonus_widget = getattr(self, bonus_name, None)
            if not base_widget or not bonus_widget:
                print(f"[WARN] Widget manquant pour {stat}")
                continue
            base_val = data.get(stat, {}).get("base", 0.0)
            bonus_val = data.get(stat, {}).get("bonus", 0.0)
            try:
                base_widget.setValue(float(base_val or 0.0))
                bonus_widget.setValue(float(bonus_val or 0.0))
            except Exception as e:
                print(f"[ERREUR] Stat '{stat}' — base={base_val}, bonus={bonus_val}")
                print(f"Exception : {e}")

    def get_data(self) -> dict:
        """Récupère les valeurs du formulaire."""
        data = {
            "nom": self.lineEditNom.text().strip(),
            "niveau": self.spinBoxNiveau.value(),
        }
        for stat, (base_name, bonus_name) in self.mapping.items():
            base_widget = getattr(self, base_name, None)
            bonus_widget = getattr(self, bonus_name, None)
            if base_widget and bonus_widget:
                data[stat] = {
                    "base": base_widget.value(),
                    "bonus": bonus_widget.value()
                }
        return data

    def on_valider(self):
        """Vérifie les champs avant validation."""
        if not self.lineEditNom.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du personnage ne peut pas être vide.")
            return
        self.accept()
