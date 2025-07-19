from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QComboBox, QSpinBox, QLabel, QMessageBox
from pathlib import Path
import json

class AjoutPersonnageDialog(QDialog):
    def __init__(self, parent=None, modules_path=None, shells_path=None):
        super().__init__(parent)

        # --- Calcul du chemin vers le .ui à partir de la racine du projet ---
        # Si votre arborescence est :
        # v4/
        # ├── main.py
        # ├── ui/
        # │   └── ajout_personnage.ui
        # └── fonction/
        #     └── personnages/
        #         └── ajout_personnage.py
        #
        # alors il faut remonter de 'fonction/personnages' jusqu'à 'v4',
        # puis descendre dans 'ui'.
        base_dir = Path(__file__).resolve().parent.parent.parent
        ui_path  = base_dir / "ui" / "ajout_personnage.ui"

        # Charge la fenêtre depuis le .ui
        uic.loadUi(str(ui_path), self)

        # === DEBUG : vérifier le bon .ui et la présence des QComboBox ===
        print(f"[DEBUG] ui_path.exists()? {ui_path.exists()} -> {ui_path}")
        combos = [w.objectName() for w in self.findChildren(QComboBox)]
        print(f"[DEBUG] Combos trouvés : {combos}")
        # =================================================================

        # Stockage des chemins JSON
        self.modules_path = modules_path
        self.shells_path  = shells_path

        # Chargement des modules et shells
        self._load_modules_shells()

        # Limites des valeurs
        self.spinBoxNiveau.setMaximum(50)
        for spin in self.findChildren(QSpinBox):
            if spin.objectName().startswith("spinBox") and "Niveau" not in spin.objectName():
                spin.setMaximum(9999999)

        # Connexion des boutons
        self.buttonValider.clicked.connect(self.on_valider)
        self.buttonAnnuler.clicked.connect(self.reject)

    def _load_modules_shells(self):
        from pathlib import Path
        import json

        # 1) Lecture des deux JSON
        self.modules = []
        self.shells = []

        # Modules
        if self.modules_path and Path(self.modules_path).exists():
            print(f"[DEBUG] Lecture de {self.modules_path}")
            with open(self.modules_path, encoding="utf-8") as f:
                try:
                    self.modules = json.load(f)
                    print(f"[DEBUG] {len(self.modules)} modules chargés.")
                except json.JSONDecodeError as e:
                    print(f"[ERREUR] JSON modules invalide : {e}")
        else:
            print(f"[ERREUR] Chemin modules introuvable : {self.modules_path}")

        # Affichage rapide du contenu
        for m in self.modules:
            print(f"→ Module: effet='{m.get('effet')}', type='{m.get('type')}', id='{m.get('id')}'")

        # Shells
        if self.shells_path and Path(self.shells_path).exists():
            print(f"[DEBUG] Lecture de {self.shells_path}")
            with open(self.shells_path, encoding="utf-8") as f:
                try:
                    self.shells = json.load(f)
                    print(f"[DEBUG] {len(self.shells)} shells chargés.")
                except json.JSONDecodeError as e:
                    print(f"[ERREUR] JSON shells invalide : {e}")
        else:
            print(f"[ERREUR] Chemin shells introuvable : {self.shells_path}")

        # 2) Préparation du filtre par slot
        types_par_slot = {
            0: "casque",
            1: "transitor",
            2: "noyau",
            3: "noyau",
            4: "noyau",
            5: "noyau",
        }

        # 3) Pour chaque comboModule{i}, on vide, on ajoute "Aucun" puis les modules
        for i in range(6):
            combo: QComboBox = getattr(self, f"comboModule{i}", None)
            label: QLabel = getattr(self, f"labelTypeModule{i}", None)
            type_attendu = types_par_slot[i]

            print(f"\n[Slot {i}] Type attendu : {type_attendu}")

            if combo is None:
                print(f"  ❌ widget comboModule{i} introuvable")
                continue

            # On efface et on ajoute "Aucun"
            combo.clear()
            combo.addItem("Aucun", None)
            ajoutés = 0

            # On parcourt tous les modules chargés
            for m in self.modules:
                m_type = str(m.get("type", "")).strip().lower()
                if m_type == type_attendu:
                    texte = f"{m.get('effet')} ({m_type})"
                    combo.addItem(texte, m.get("id"))
                    ajoutés += 1
                    print(f"   ✅ Ajouté à {combo.objectName()}: {texte}")

            print(f"   → {combo.objectName()} contient {combo.count()} items (dont 'Aucun')")

            # On met à jour le label « casque (Slot 1) », etc.
            if label:
                label.setText(f"{type_attendu.capitalize()} (Slot {i + 1})")

        # 4) Pour la comboShell
        if hasattr(self, "comboShell"):
            self.comboShell.clear()
            self.comboShell.addItem("Aucun", None)
            for s in self.shells:
                effet = s.get("effet", "Sans effet")
                sid = s.get("id", "")
                self.comboShell.addItem(effet, sid)
                print(f"[Shell] Ajouté : {effet} (id={sid})")

        print("===== [DEBUG] FIN CHARGEMENT MODULES/SHELLS =====\n")

    def get_data(self):
        data = {
            "nom": self.lineEditNom.text().strip(),
            "niveau": self.spinBoxNiveau.value(),
        }

        # Stats
        for stat in ["PV", "Attaque", "Defense", "Vitesse", "Taux crit", "Degats crit", "Resistance", "Precision"]:
            base = getattr(self, f"spinBox{stat.replace(' ', '')}Base").value()
            bonus = getattr(self, f"spinBox{stat.replace(' ', '')}Bonus").value()
            data[stat] = {"base": base, "bonus": bonus}

        # Modules équipés
        modules = []
        for i in range(6):
            combo: QComboBox = getattr(self, f"comboModule{i}", None)
            if combo:
                module_id = combo.currentData()
                if module_id:
                    modules.append(module_id)
        data["modules"] = modules

        # Shell sélectionné
        if hasattr(self, "comboShell"):
            shell_id = self.comboShell.currentData()
            data["shell"] = shell_id if shell_id else None

        return data

    def remplir_champs(self, data):
        self.lineEditNom.setText(data.get("nom", ""))
        self.spinBoxNiveau.setValue(data.get("niveau", 1))

        for stat in ["PV", "Attaque", "Defense", "Vitesse", "Taux crit", "Degats crit", "Resistance", "Precision"]:
            base = data.get(stat, {}).get("base", 0)
            bonus = data.get(stat, {}).get("bonus", 0)
            getattr(self, f"spinBox{stat.replace(' ', '')}Base").setValue(base)
            getattr(self, f"spinBox{stat.replace(' ', '')}Bonus").setValue(bonus)

        # Modules
        for i in range(6):
            combo: QComboBox = getattr(self, f"comboModule{i}", None)
            if combo:
                module_id = data.get("modules", [None]*6)[i] if i < len(data.get("modules", [])) else None
                index = combo.findData(module_id)
                if index >= 0:
                    combo.setCurrentIndex(index)

        # Shell
        if hasattr(self, "comboShell"):
            shell_id = data.get("shell", None)
            index = self.comboShell.findData(shell_id)
            if index >= 0:
                self.comboShell.setCurrentIndex(index)

    def on_valider(self):
        # Vérification du nom
        if not self.lineEditNom.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom du personnage est requis.")
            return

        # (Optionnel) Vérifier qu'au moins un module ou shell est sélectionné
        # si c'est une règle métier, sinon retirer ce bloc
        if not any(getattr(self, f"comboModule{i}").currentData() for i in range(6)) \
           and (not hasattr(self, "comboShell") or not self.comboShell.currentData()):
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Aucun module ni shell sélectionné. Voulez-vous continuer ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Tout est OK : on accepte et ferme le dialogue
        self.accept()
