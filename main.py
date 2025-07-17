import faulthandler
faulthandler.enable()

import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget

from fonction.personnages.personnages_controller import PersonnagesController
from fonction.modules.modules_controller import ModulesController
#yozde
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(__file__)

        # === Charger l'UI principale
        main_ui = os.path.join(base_dir, "ui", "etheria_optimizer_main.ui")
        uic.loadUi(main_ui, self)
        self.resize(1000, 720)

        # === Connexion sidebar
        self.sidebar.currentRowChanged.connect(self.mainStack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        # === Onglet Personnages
        tab_characters_ui = os.path.join(base_dir, "ui", "tab_characters.ui")
        tab_characters = uic.loadUi(tab_characters_ui)
        self.mainStack.insertWidget(0, tab_characters)
        personnages_json = os.path.join(base_dir, "data", "personnages.json")
        self.personnages_controller = PersonnagesController(tab_characters, personnages_json)

        # === Onglet Modules
        module_tab_ui = os.path.join(base_dir, "ui", "module_tab.ui")
        self.tabModules = uic.loadUi(module_tab_ui)  # bien stocké dans self
        self.mainStack.insertWidget(1, self.tabModules)
        modules_json = os.path.join(base_dir, "data", "modules.json")
        self.modules_controller = ModulesController(self.tabModules, modules_json)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
