import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore

class ShellController:
    def __init__(self, ui, json_path, image_dir):
        self.ui = ui
        self.json_path = json_path
        self.image_dir = image_dir  # => "images/shell"
        self.shells_dir = image_dir
        self.effects_dir = os.path.join(self.image_dir, "effets")
        self.shells = []
        self.selected_icon = None
        self.effect_counts = {"x2": None, "x3": []}
        self.effect_widgets = []
        self.selected_x3_buttons = []
        self.selected_x2_button = None

        self.effects_x2 = {
            "eclairdivin", "raidrapide", "gardeducolosse",
            "lameViolente", "etherpeste", "abrievolutif"
        }

        self.stat_options = {
            "Stat1": ["Attaque", "Attaque %", "PV", "PV %", "Defense", "Defense %"],
            "Stat2": ["Vitesse", "Taux crit", "Degats crit", "Precision"],
            "Stat3": ["Resistance", "Precision"]
        }

        self._init_ui()
        self._load_or_create_json()
        self._load_shell_icons()
        self._load_effect_icons()
        self._load_effects_x2_buttons()
        self._load_shells_created()

    def _init_ui(self):
        self.ui.comboStat1.addItems(self.stat_options["Stat1"])
        self.ui.comboStat2.addItems(self.stat_options["Stat2"])
        self.ui.comboStat3.addItems(self.stat_options["Stat3"])

        for spin in [self.ui.valueStat1, self.ui.valueStat2, self.ui.valueStat3]:
            spin.setMinimum(0)
            spin.setMaximum(9999)
            spin.setDecimals(2)

        self.ui.listWidgetShells.itemClicked.connect(self._select_icon)
        self.ui.buttonSauvegarder.clicked.connect(self.save_shell)

    def _load_or_create_json(self):
        if not os.path.exists(self.json_path):
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.shells = json.load(f)

    def _highlight_button(self, button, selected):
        if selected:
            button.setStyleSheet("border: 2px solid #00BFFF; background-color: #e6f7ff;")
        else:
            button.setStyleSheet("")

    def _load_shell_icons(self):
        self.ui.listWidgetShells.clear()
        for file in os.listdir(self.shells_dir):
            if file.endswith(".png") and file != "effets":
                name = os.path.splitext(file)[0]
                icon_path = os.path.join(self.shells_dir, file)
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(icon_path), name)
                item.setData(QtCore.Qt.UserRole, name)
                self.ui.listWidgetShells.addItem(item)

    def _select_icon(self, item):
        self.selected_icon = item.data(QtCore.Qt.UserRole)

    def _load_effect_icons(self):
        layout = self.ui.layoutBoutonsEffets
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for file in os.listdir(self.effects_dir):
            if not file.endswith(".png"):
                continue
            name = os.path.splitext(file)[0]
            if name in self.effects_x2:
                continue
            icon_path = os.path.join(self.effects_dir, file)
            btn = QtWidgets.QPushButton()
            btn.setIcon(QtGui.QIcon(icon_path))
            btn.setIconSize(QtCore.QSize(48, 48))
            btn.setToolTip(name)
            btn.effect_name = name
            btn.clicked.connect(lambda _, b=btn: self._handle_x3_click(b))
            layout.addWidget(btn)
            self.effect_widgets.append(btn)

    def _handle_x3_click(self, button):
        name = button.effect_name
        if name in self.effect_counts["x3"]:
            self.effect_counts["x3"].remove(name)
            self.selected_x3_buttons.remove(button)
            self._highlight_button(button, False)
        elif len(self.effect_counts["x3"]) < 2:
            self.effect_counts["x3"].append(name)
            self.selected_x3_buttons.append(button)
            self._highlight_button(button, True)
        self._update_effect_display()

    def _load_effects_x2_buttons(self):
        boutons = {
            "eclairdivin": self.ui.buttonEclairDivin,
            "raidrapide": self.ui.buttonRaidRapide,
            "gardeducolosse": self.ui.buttonGardeDuColosse,
            "lameViolente": self.ui.buttonLameViolente,
            "etherpeste": self.ui.buttonEtherPeste,
            "abrievolutif": self.ui.buttonAbrievolutif,
        }
        for name, btn in boutons.items():
            icon_path = os.path.join(self.effects_dir, f"{name}.png")
            if os.path.exists(icon_path):
                btn.setIcon(QtGui.QIcon(icon_path))
                btn.setIconSize(QtCore.QSize(48, 48))
                btn.setToolTip(name)
                btn.effect_name = name
                btn.clicked.connect(lambda _, b=btn: self._handle_x2_click(b))

    def _handle_x2_click(self, button):
        name = button.effect_name
        if self.effect_counts["x2"] == name:
            self.effect_counts["x2"] = None
            self._highlight_button(button, False)
            self.selected_x2_button = None
        else:
            if self.selected_x2_button:
                self._highlight_button(self.selected_x2_button, False)
            self.effect_counts["x2"] = name
            self.selected_x2_button = button
            self._highlight_button(button, True)
        self._update_effect_display()

    def _update_effect_display(self):
        lines = []
        for e in self.effect_counts["x3"]:
            lines.append(f"{e} x3")
        if self.effect_counts["x2"]:
            lines.append(f"{self.effect_counts['x2']} x2")
        self.ui.textEditEffets.setText("\n".join(lines))

    def _load_shells_created(self):
        self.ui.listWidgetShellsCreated.clear()
        for shell in self.shells:
            icon_path = os.path.join(self.shells_dir, f"{shell['icon']}.png")
            label = f"{shell['icon']}\nStats: {', '.join(shell['stats'])}\nEffets: {', '.join(shell['effects'])}"
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(icon_path), label)
            self.ui.listWidgetShellsCreated.addItem(item)

    def save_shell(self):
        if not self.selected_icon:
            QtWidgets.QMessageBox.warning(self.ui, "Erreur", "Aucune icône de shell sélectionnée.")
            return

        shell = {
            "icon": self.selected_icon,
            "stats": [
                f"{self.ui.comboStat1.currentText()} {self.ui.valueStat1.value()}",
                f"{self.ui.comboStat2.currentText()} {self.ui.valueStat2.value()}",
                f"{self.ui.comboStat3.currentText()} {self.ui.valueStat3.value()}"
            ],
            "effects": [f"{e} x3" for e in self.effect_counts["x3"]]
        }

        if self.effect_counts["x2"]:
            shell["effects"].append(f"{self.effect_counts['x2']} x2")

        self.shells.append(shell)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.shells, f, indent=4, ensure_ascii=False)

        self._load_shells_created()
        QtWidgets.QMessageBox.information(self.ui, "Succès", "Shell enregistré avec succès.")
