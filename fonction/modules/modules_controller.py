import os
import json
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
    "Attaque", "Attaque %", "PV", "PV %", "Défense", "Défense %",
    "Taux crit", "Dégâts crit", "Résistance", "Précision", "Vitesse"
]
FIXED_TYPES = ('casque', 'transitor', 'bracelet')

class ModulesController:
    def __init__(self, ui, modules_path):
        self.ui = ui
        self.manager = ModuleManager(modules_path)
        # Handler pour les main stats selon type/niveau
        stats_file = os.path.join(os.getcwd(), 'data', 'stats_par_type.json')
        self.stats_handler = StatsParTypeHandler(stats_file)

        # Layout du container de sous‑stats
        if self.ui.substatsContainer.layout() is None:
            self.ui.substatsContainer.setLayout(QVBoxLayout())

        # Niveau limité à 1‐15
        self.ui.spinBoxNiveauModule.setRange(1, 15)

        # Ajustement plage du spinBox de la stat principale
        if isinstance(self.ui.spinBoxValeurPrincipale, QDoubleSpinBox):
            self.ui.spinBoxValeurPrincipale.setRange(0.0, 1000.0)
            self.ui.spinBoxValeurPrincipale.setDecimals(0)
        else:
            self.ui.spinBoxValeurPrincipale.setRange(0, 1000)

        # Chargement icônes + clic
        self._load_icons()
        self.ui.listIcons.itemClicked.connect(self.on_icon_clicked)

        # Autocomplete pour la stat principale comme pour les sous-stats
        stat_completer = QCompleter(SUBSTATS)
        stat_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.lineEditStatPrincipale.setCompleter(stat_completer)

        # Recherche
        self.ui.searchModuleBar.textChanged.connect(self.update_list)

        # Liste modules
        self.ui.moduleList.itemClicked.connect(self.on_module_selected)
        self.ui.moduleList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.moduleList.customContextMenuRequested.connect(self.open_context_menu)

        # Mise à jour auto main stat au changement type/niveau
        self.ui.comboTypeModule.currentTextChanged.connect(self.update_main_stat)
        self.ui.spinBoxNiveauModule.valueChanged.connect(self.update_main_stat)

        # Boutons
        self.ui.buttonAddSubstat.clicked.connect(lambda: self._add_substat_row())
        self.ui.buttonSaveModule.clicked.connect(lambda: self.save_module())

        # Initialisation
        self.update_list()
        self.update_main_stat()

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
        set_name = item.data(Qt.UserRole)
        self.ui.lineEditNomModule.setText(set_name)
        self.ui.searchModuleBar.setText(set_name)

    def update_list(self):
        search = self.ui.searchModuleBar.text().strip().lower()
        self.ui.moduleList.clear()
        for idx, m in enumerate(self.manager.modules):
            if search in m.nom.lower() or search in m.type.lower():
                label = f"{m.nom} [{m.type} N{m.niveau}]"
                item = QListWidgetItem(label)
                icon_path = os.path.join("images", f"{m.nom}.png")
                if os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                # aperçu sous-stats
                if m.sous_stats:
                    tip = "Sous-stats:\n" + "\n".join(f"{ss['stat']}: {ss['valeur']}" for ss in m.sous_stats)
                    item.setToolTip(tip)
                item.setData(Qt.UserRole, idx)
                self.ui.moduleList.addItem(item)

    def on_module_selected(self, item):
        idx = item.data(Qt.UserRole)
        module = self.manager.modules[idx]
        # remplir formulaire
        self.ui.lineEditNomModule.setText(module.nom)
        self.ui.comboTypeModule.setCurrentText(module.type)
        self.ui.spinBoxNiveauModule.setValue(module.niveau)
        self.ui.lineEditStatPrincipale.setText(module.stat_principale)
        self.ui.spinBoxValeurPrincipale.setValue(module.valeur_principale)
        # sous‑stats
        layout = self.ui.substatsContainer.layout()
        while layout.count():
            w = layout.takeAt(0).widget()
            if w: w.deleteLater()
        for ss in module.sous_stats:
            self._add_substat_row(ss["stat"], ss["valeur"])
        self.update_main_stat()

    def update_main_stat(self):
        t = self.ui.comboTypeModule.currentText().lower()
        lvl = self.ui.spinBoxNiveauModule.value()
        stat, val = self.stats_handler.get_main_stat(t, lvl)
        # Toujours mettre à jour le champ Stat principale
        self.ui.lineEditStatPrincipale.setText(stat or "")
        # Types fixes: stat désactivée, valeur figée si connue
        if t in FIXED_TYPES:
            self.ui.lineEditStatPrincipale.setDisabled(True)
            if val is not None:
                self.ui.spinBoxValeurPrincipale.setValue(val)
                self.ui.spinBoxValeurPrincipale.setDisabled(True)
            else:
                self.ui.spinBoxValeurPrincipale.setDisabled(False)
        # Noyau: tout éditable, préremplissage si existant
        elif t == 'noyau':
            self.ui.lineEditStatPrincipale.setDisabled(False)
            self.ui.spinBoxValeurPrincipale.setDisabled(False)
            if val is not None:
                self.ui.spinBoxValeurPrincipale.setValue(val)
        # Autres types: tout éditable
        else:
            self.ui.lineEditStatPrincipale.setDisabled(False)
            self.ui.spinBoxValeurPrincipale.setDisabled(False)

    def _add_substat_row(self, stat_name="", value=0):
        cont = QWidget(self.ui.substatsContainer)
        hl = QHBoxLayout(cont); hl.setContentsMargins(0,0,0,0)
        le = QLineEdit(cont); le.setPlaceholderText("Nom de la sous-stat"); le.setText(stat_name)
        completer = QCompleter(SUBSTATS); completer.setCaseSensitivity(Qt.CaseInsensitive); le.setCompleter(completer)
        sb = QDoubleSpinBox(cont); sb.setRange(0.0,1000.0); sb.setDecimals(0); sb.setValue(value)
        hl.addWidget(le); hl.addWidget(sb)
        self.ui.substatsContainer.layout().addWidget(cont)

    def _read_substats(self):
        subs = []
        for i in range(self.ui.substatsContainer.layout().count()):
            w = self.ui.substatsContainer.layout().itemAt(i).widget()
            if not w: continue
            le = w.findChild(QLineEdit); sb = w.findChild(QDoubleSpinBox) or w.findChild(QSpinBox)
            if le and le.text().strip(): subs.append({"stat": le.text().strip(), "valeur": sb.value()})
        return subs

    def save_module(self):
        try:
            t = self.ui.comboTypeModule.currentText().lower()
            nom = self.ui.lineEditNomModule.text().strip()
            if not nom:
                QMessageBox.warning(self.ui, "Erreur", "Le nom du module est requis.")
                return
            lvl = self.ui.spinBoxNiveauModule.value()
            stat_princ = self.ui.lineEditStatPrincipale.text().strip()
            val_princ = self.ui.spinBoxValeurPrincipale.value()
            module = Module(nom=nom, type_=t, niveau=lvl,
                            stat_principale=stat_princ, valeur_principale=val_princ,
                            sous_stats=self._read_substats())
            # dynamique: noyau ou valeur fixe manquante
            existing_stat, existing_val = self.stats_handler.get_main_stat(t, lvl)
            if t == 'noyau':
                if existing_stat != stat_princ or existing_val != val_princ:
                    self.stats_handler.set_noyau_stat(stat_princ, lvl, val_princ)
            elif t in FIXED_TYPES and existing_val is None:
                # ajouter par_niveau pour fixed types
                entry = self.stats_handler.data[t]['par_niveau']
                entry[str(lvl)] = val_princ
                self.stats_handler.save()
            # ajout/màj module
            cur = self.ui.moduleList.currentItem()
            if cur:
                idx = cur.data(Qt.UserRole); self.manager.update_module(idx, module)
            else:
                self.manager.add_module(module)
            self.update_list()
        except Exception as e:
            QMessageBox.critical(self.ui, "Erreur inattendue", f"{type(e).__name__}: {e}")

    def open_context_menu(self, pos):
        item = self.ui.moduleList.itemAt(pos)
        if not item: return
        menu = QMenu(); delete_action = menu.addAction("Supprimer ce module")
        action = menu.exec_(self.ui.moduleList.viewport().mapToGlobal(pos))
        if action == delete_action:
            idx = item.data(Qt.UserRole)
            if QMessageBox.question(self.ui, "Suppression",
                f"Supprimer le module « {item.text()} » ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                self.manager.delete_module(idx); self.update_list()
