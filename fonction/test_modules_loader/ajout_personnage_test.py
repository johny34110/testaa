import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from v4.fonction.personnages.ajout_personnage import AjoutPersonnageDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Chemins vers les fichiers de test
    base_path = Path(__file__).resolve().parent.parent  # ← adapte au besoin
    modules_path = base_path / "data" / "modules.json"
    shells_path = base_path / "data" / "shells.json"

    # Crée et affiche la fenêtre d’ajout
    dialog = AjoutPersonnageDialog(None, str(modules_path), str(shells_path))
    if dialog.exec_():
        data = dialog.get_data()
        print("\n=== Données récupérées ===")
        for k, v in data.items():
            print(f"{k}: {v}")
    else:
        print("Ajout annulé.")

    sys.exit()
