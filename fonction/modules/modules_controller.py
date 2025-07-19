import os
from PyQt5.QtWidgets import (
    QListWidgetItem, QMenu, QMessageBox, QLineEdit,
    QWidget, QHBoxLayout, QVBoxLayout, QCompleter,
    QDoubleSpinBox, QSpinBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from .gestion_modules import ModuleManager, Module
from .stats_par_type_handler import StatsParTypeHandler

SUBSTATS = [
    "Attaque", "Attaque%", "PV", "PV%", "Defense", "Defense%",
    "Taux crit", "Degats crit", "Resistance", "Precision", "Vitesse"
]

class ModulesController:
    def __init__(self, ui, modules_path):
        self.ui = ui
        self.manager = ModuleManager(modules_path)

        # Charger les stats principales par type/niveau
        stats_file = os.path.join(os.getcwd(), 'data', 'stats_par_type.json')
        self.stats_handler = StatsParTypeHandler(stats_file)

        if self.ui.substatsContainer.layout() is None:
            self.ui.substatsContainer.setLayout(QVBoxLayout())

        self.ui.spinBoxNiveauModule.setRange(1, 15)

        if isinstance(self.ui.spinBoxValeurPrincipale, QDoubleSpinBox):
            self.ui.spinBoxValeurPrincipale.setRange(0.0, 1000.0)
            self.ui.spinBoxValeurPrincipale.setDecimals(0)
        else:
            self.ui.spinBoxValeurPrincipale.setRange(0, 1000)

        self._load_icons()
        self.ui.listIcons.itemClicked.connect(self.on_icon_clicked)

        # Autocomplete pour la stat principale
        stat_completer = QCompleter(SUBSTATS)
        stat_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.lineEditStatPrincipale.setCompleter(stat_completer)

        self.ui.searchModuleBar.textChanged.connect(self.update_list)
        self.ui.moduleList.itemClicked.connect(self.on_module_selected)
        self.ui.moduleList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.moduleList.customContextMenuRequested.connect(self.open_context_menu)

        self.ui.comboTypeModule.currentTextChanged.connect(self.update_main_stat)
        self.ui.spinBoxNiveauModule.valueChanged.connect(self.update_main_stat)

        self.ui.buttonAddSubstat.clicked.connect(lambda: self._add_substat_row())
        self.ui.buttonSaveModule.clicked.connect(lambda: self.save_module())

        self.update_list()
        self.update_main_stat()

    def update_main_stat(self):
        type_module = self.ui.comboTypeModule.currentText().lower()
        niveau = self.ui.spinBoxNiveauModule.value()
        suggestion = self.stats_handler.get_stat_par_type(type_module, niveau)
        if suggestion:
            self.ui.lineEditStatPrincipale.setText(suggestion["stat"])
            self.ui.spinBoxValeurPrincipale.setValue(suggestion["valeur"])

    def _load_icons(self):
        self.ui.listIcons.clear()
        images_dir = os.path.join(os.getcwd(), "images")
        if not os.path.isdir(images_dir):
            return
        for fname in sorted(os.listdir(images_dir)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                path = os.path.join(images_dir, fname)
                set_name = os.path.splitext(fname)[0]
                item = QListWidgetItem(QIcon(path), "")
                item.setData(Qt.UserRole, set_name)
                self.ui.listIcons.addItem(item)

    def on_icon_clicked(self, item):
        effet = item.data(Qt.UserRole)
        self.ui.lineEditNomModule.setText(effet)
        self.ui.searchModuleBar.setText(effet)

    def update_list(self):
        search = self.ui.searchModuleBar.text().strip().lower()
        self.ui.moduleList.clear()
        for idx, m in enumerate(self.manager.modules):
            if search in m.effet.lower() or search in m.type.lower():
                label = f"{m.effet} [{m.type} N{m.niveau}]"
                item = QListWidgetItem(label)
                icon_path = os.path.join("images", f"{m.effet}.png")
                if os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                if m.sous_stats:
                    tooltip = "Sous-stats:\n" + "\n".join(
                        f"{ss['stat']}: {ss['valeur']}" for ss in m.sous_stats
                    )
                    item.setToolTip(tooltip)
                item.setData(Qt.UserRole, idx)
                self.ui.moduleList.addItem(item)

    def on_module_selected(self, item):
        idx = item.data(Qt.UserRole)
        module = self.manager.modules[idx]

        self.ui.lineEditNomModule.setText(module.effet)
        self.ui.comboTypeModule.setCurrentText(module.type)
        self.ui.spinBoxNiveauModule.setValue(module.niveau)
        self.ui.lineEditStatPrincipale.setText(module.stat_principale)
        self.ui.spinBoxValeurPrincipale.setValue(module.valeur_principale)

        layout = self.ui.substatsContainer.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for ss in module.sous_stats:
            self._add_substat_row(ss["stat"], ss["valeur"])

    def _add_substat_row(self, stat_name="", value=0):
        container = QWidget(self.ui.substatsContainer)
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)

        le = QLineEdit(container)
        le.setPlaceholderText("Nom de la sous-stat")
        le.setText(stat_name)
        completer = QCompleter(SUBSTATS)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        le.setCompleter(completer)

        sb = QDoubleSpinBox(container)
        sb.setRange(0.0, 1000.0)
        sb.setDecimals(0)
        sb.setValue(value)

        row_layout.addWidget(le)
        row_layout.addWidget(sb)
        self.ui.substatsContainer.layout().addWidget(container)

    def _read_substats(self):
        substats = []
        layout = self.ui.substatsContainer.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if not widget:
                continue
            le = widget.findChild(QLineEdit)
            sb = widget.findChild(QDoubleSpinBox) or widget.findChild(QSpinBox)
            if le and le.text().strip():
                substats.append({"stat": le.text().strip(), "valeur": sb.value()})
        return substats

    def save_module(self):
        try:
            effet = self.ui.lineEditNomModule.text().strip()
            if not effet:
                QMessageBox.warning(self.ui, "Erreur", "L'effet du module est requis.")
                return
            module = Module(
                effet=effet,
                type_=self.ui.comboTypeModule.currentText(),
                niveau=self.ui.spinBoxNiveauModule.value(),
                stat_principale=self.ui.lineEditStatPrincipale.text().strip(),
                valeur_principale=self.ui.spinBoxValeurPrincipale.value(),
                sous_stats=self._read_substats()
            )
            current = self.ui.moduleList.currentItem()
            if current:
                idx = current.data(Qt.UserRole)
                self.manager.update_module(idx, module)
            else:
                self.manager.add_module(module)
            self.update_list()
        except Exception as e:
            QMessageBox.critical(self.ui, "Erreur inattendue", f"{type(e).__name__}: {e}")

    def open_context_menu(self, pos):
        item = self.ui.moduleList.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        delete_action = menu.addAction("Supprimer ce module")
        action = menu.exec_(self.ui.moduleList.viewport().mapToGlobal(pos))
        if action == delete_action:
            idx = item.data(Qt.UserRole)
            resp = QMessageBox.question(
                self.ui, "Suppression",
                f"Supprimer le module « {item.text()} » ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if resp == QMessageBox.Yes:
                self.manager.delete_module(idx)
                self.update_list()
