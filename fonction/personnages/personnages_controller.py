# --- personnages_controller.py ---

import os
import json
import math
from pathlib import Path

from PyQt5.QtWidgets import (
    QComboBox, QMessageBox, QMenu, QWidget, QApplication
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSortFilterProxyModel

from .ajout_personnage import AjoutPersonnageDialog

class PersonnagesController:
    def __init__(self, ui: QWidget, data_path: str, modules_path: str, shells_path: str):
        self.ui            = ui
        self.data_path     = data_path
        self.modules_path  = modules_path
        self.shells_path   = shells_path

        # Modèle/proxy
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Nom","Niveau","PV","Attaque","Defense","Vitesse",
            "Taux crit","Degats crit","Resistance","Precision"
        ])
        self.proxy = QSortFilterProxyModel(self.ui)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.characterTable.setModel(self.proxy)
        self.ui.characterTable.setSortingEnabled(True)
        self.ui.characterTable.sortByColumn(0, Qt.AscendingOrder)

        # Actions
        self.ui.addCharacterButton.clicked.connect(self.open_add_dialog)
        self.ui.searchBar.textChanged.connect(self.proxy.setFilterFixedString)
        self.enable_context_menu()

        # Pagination
        self.all_characters = []
        self.currentPage    = 1
        self._setup_pagination()

        # Charger modules.json
        self._load_modules_data()

        # Charger & afficher
        self.load_characters()
        self.update_table()

    def _setup_pagination(self):
        self.pageSizeCombo = QComboBox(self.ui)
        for size in ["10","20","50","100"]:
            self.pageSizeCombo.addItem(size)
        self.pageSizeCombo.setCurrentIndex(0)
        self.ui.paginationLayout.insertWidget(1, self.pageSizeCombo)
        self.ui.prevPageButton.clicked.connect(self.prev_page)
        self.ui.nextPageButton.clicked.connect(self.next_page)
        self.pageSizeCombo.currentTextChanged.connect(self.on_page_size_changed)

    def _load_modules_data(self):
        """Charge modules.json pour calcul stats."""
        if os.path.exists(self.modules_path):
            try:
                with open(self.modules_path, "r", encoding="utf-8") as f:
                    self.modules_data = json.load(f)
            except json.JSONDecodeError:
                QMessageBox.warning(self.ui, "Erreur", "modules.json est corrompu.")
                self.modules_data = []
        else:
            QMessageBox.warning(self.ui, "Erreur", f"modules.json introuvable : {self.modules_path}")
            self.modules_data = []

    def load_characters(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.all_characters = json.load(f)
            except json.JSONDecodeError:
                QMessageBox.warning(self.ui, "Erreur", "JSON personnages corrompu.")
                self.all_characters = []
        else:
            self.all_characters = []
        self.currentPage = 1

    def save_characters(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.all_characters, f, indent=2, ensure_ascii=False)

    def update_table(self):
        self.model.removeRows(0, self.model.rowCount())
        term = self.ui.searchBar.text().lower()
        filt = [p for p in self.all_characters if term in p["nom"].lower()]
        pageSize = int(self.pageSizeCombo.currentText())
        pages = max(1, math.ceil(len(filt)/pageSize))
        self.currentPage = min(self.currentPage, pages)
        start = (self.currentPage-1)*pageSize
        for p in filt[start:start+pageSize]:
            self._append_row(p)
        self.ui.pageLabel.setText(f"Page {self.currentPage} / {pages}")
        self.ui.prevPageButton.setEnabled(self.currentPage>1)
        self.ui.nextPageButton.setEnabled(self.currentPage<pages)

    def _append_row(self, data):
        # calc base+bonus + modules + %
        def total_char(stat): return stat["base"]+stat["bonus"]
        keys = ["PV","Attaque","Defense","Vitesse","Taux crit","Degats crit","Resistance","Precision"]
        agg = {k: total_char(data[k]) for k in keys}
        base = {k: data[k]["base"] for k in keys}

        for mid in data.get("modules",[]):
            m = next((m for m in self.modules_data if m.get("id")==mid),None)
            if not m: continue
            # stat principale flat
            ms = m.get("stat_principale"); mv = m.get("valeur_principale",0)
            if ms in agg: agg[ms]+=mv
            # sous-stats
            for sub in m.get("sous_stats",[]):
                k = sub.get("stat"); v=sub.get("valeur",0)
                if k in ("PV%","Attaque%","Defense%"):
                    col = k.rstrip("%")
                    agg[col]+= base[col]*(v/100)
                elif k in agg:
                    agg[k]+=v

        row = [
            QStandardItem(data["nom"]),
            QStandardItem(str(data["niveau"])),
            QStandardItem(str(int(agg["PV"]))),
            QStandardItem(str(int(agg["Attaque"]))),
            QStandardItem(str(int(agg["Defense"]))),
            QStandardItem(str(int(agg["Vitesse"]))),
            QStandardItem(str(int(agg["Taux crit"]))),
            QStandardItem(str(int(agg["Degats crit"]))),
            QStandardItem(str(int(agg["Resistance"]))),
            QStandardItem(str(int(agg["Precision"])))
        ]
        for it in row: it.setEditable(False)
        row[0].setData(data["nom"], Qt.UserRole)
        self.model.appendRow(row)

    def _update_row(self, source_row, data):
        """Met à jour in-place la ligne source_row."""
        # Refaire le même calcul que _append_row
        def total_char(stat): return stat["base"]+stat["bonus"]
        keys=["PV","Attaque","Defense","Vitesse","Taux crit","Degats crit","Resistance","Precision"]
        agg={k: total_char(data[k]) for k in keys}
        base={k:data[k]["base"] for k in keys}
        for mid in data.get("modules",[]):
            m=next((m for m in self.modules_data if m.get("id")==mid),None)
            if not m: continue
            ms, mv = m.get("stat_principale"), m.get("valeur_principale",0)
            if ms in agg: agg[ms]+=mv
            for sub in m.get("sous_stats",[]):
                k,v=sub.get("stat"),sub.get("valeur",0)
                if k in ("PV%","Attaque%","Defense%"):
                    col=k.rstrip("%"); agg[col]+=base[col]*(v/100)
                elif k in agg:
                    agg[k]+=v
        vals = [
            data["nom"], str(data["niveau"]),
            str(int(agg["PV"])), str(int(agg["Attaque"])),
            str(int(agg["Defense"])), str(int(agg["Vitesse"])),
            str(int(agg["Taux crit"])), str(int(agg["Degats crit"])),
            str(int(agg["Resistance"])), str(int(agg["Precision"]))
        ]
        for col, v in enumerate(vals):
            self.model.item(source_row, col).setText(v)

    def on_page_size_changed(self, text):
        self.currentPage=1; self.update_table()

    def prev_page(self):
        if self.currentPage>1:
            self.currentPage-=1; self.update_table()

    def next_page(self):
        term=self.ui.searchBar.text().lower()
        total=len([p for p in self.all_characters if term in p["nom"].lower()])
        pages=max(1,math.ceil(total/int(self.pageSizeCombo.currentText())))
        if self.currentPage<pages:
            self.currentPage+=1; self.update_table()

    def open_add_dialog(self):
        dlg=AjoutPersonnageDialog(QApplication.activeWindow(),
                                  self.modules_path,self.shells_path)
        dlg.modulesChanged.connect(lambda d, r=None:None)  # pas utile ici
        if dlg.exec_():
            new=dlg.get_data()
            self.all_characters.append(new)
            self.save_characters()
            self.currentPage=math.ceil(len(self.all_characters)/int(self.pageSizeCombo.currentText()))
            self.update_table()

    def edit_character(self, index):
        src = self.proxy.mapToSource(index)
        row = src.row()
        term = self.ui.searchBar.text().lower()
        filt = [p for p in self.all_characters if term in p["nom"].lower()]
        idx = (self.currentPage-1)*int(self.pageSizeCombo.currentText())+row
        if not (0 <= idx < len(filt)): return
        actual = filt[idx]

        dlg=AjoutPersonnageDialog(QApplication.activeWindow(),
                                  self.modules_path,self.shells_path)
        dlg.remplir_champs(actual)
        # connexion live update
        dlg.modulesChanged.connect(lambda data, r=row: self._update_row(r,data))

        if dlg.exec_():
            updated=dlg.get_data()
            for i,p in enumerate(self.all_characters):
                if p["nom"]==actual["nom"]:
                    self.all_characters[i]=updated; break
            self.save_characters()
            self.update_table()

    def open_context_menu(self,pos):
        index=self.ui.characterTable.indexAt(pos)
        if not index.isValid(): return
        menu=QMenu(self.ui)
        m=menu.addAction("Modifier"); d=menu.addAction("Supprimer")
        act=menu.exec_(self.ui.characterTable.viewport().mapToGlobal(pos))
        if act==m: self.edit_character(index)
        elif act==d:
            src=self.proxy.mapToSource(index); row=src.row()
            nom=self.model.item(row,0).text()
            if QMessageBox.question(self.ui,"Suppression",
               f"Supprimer '{nom}' ?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
                self.all_characters=[p for p in self.all_characters if p["nom"]!=nom]
                self.save_characters(); self.update_table()

    def enable_context_menu(self):
        self.ui.characterTable.doubleClicked.connect(self.edit_character)
        self.ui.characterTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.characterTable.customContextMenuRequested.connect(self.open_context_menu)
