from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
import os

class AjoutPersonnageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Chargement de l'interface depuis le dossier ui au niveau du projet
        ui_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),  # fonction/personnages
                "..", "..",              # remonte à V2
                "ui", "ajout_personnage.ui"
            )
        )
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Fichier UI non trouvé : {ui_path}")
        uic.loadUi(ui_path, self)

        # Connexion des boutons
        self.buttonValider.clicked.connect(self.on_valider)
        self.buttonAnnuler.clicked.connect(self.reject)

    def remplir_champs(self, data: dict):
        """
        Préremplit les champs du dialogue à partir des données existantes.
        """
        # Nom et niveau
        self.lineEditNom.setText(data.get("nom", ""))
        self.spinBoxNiveau.setValue(data.get("niveau", 1))

        # Stats à gérer dynamiquement
        stats = [
            "PV", "Attaque", "Défense", "Vitesse",
            "Taux crit", "Dégâts crit", "Résistance", "Précision"
        ]
        for stat in stats:
            key = stat.replace(' ', '')  # ex. "Tauxcrit"
            base_widget = getattr(self, f"spinBox{key}Base", None)
            bonus_widget = getattr(self, f"spinBox{key}Bonus", None)
            if base_widget and bonus_widget and stat in data:
                base_widget.setValue(data[stat].get("base", 0))
                bonus_widget.setValue(data[stat].get("bonus", 0))

    def on_valider(self):
        """
        Vérifie que le nom n'est pas vide avant d'accepter.
        """
        if not self.lineEditNom.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du personnage ne peut pas être vide.")
            return
        self.accept()

    def get_data(self) -> dict:
        """
        Récupère les valeurs saisies dans les champs du formulaire.
        """
        data = {
            "nom": self.lineEditNom.text().strip(),
            "niveau": self.spinBoxNiveau.value(),
        }
        # Stats dynamiques
        stats = [
            "PV", "Attaque", "Défense", "Vitesse",
            "Taux crit", "Dégâts crit", "Résistance", "Précision"
        ]
        for stat in stats:
            key = stat.replace(' ', '')
            base_widget = getattr(self, f"spinBox{key}Base")
            bonus_widget = getattr(self, f"spinBox{key}Bonus")
            data[stat] = {
                "base": base_widget.value(),
                "bonus": bonus_widget.value()
            }
        return data
