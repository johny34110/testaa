import os
import json
import math
from PyQt5.QtWidgets import (
    QComboBox, QMessageBox, QMenu, QWidget
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from .ajout_personnage import AjoutPersonnageDialog


class PersonnagesController:
    def __init__(self, ui: QWidget, data_path: str):
        self.ui = ui
        self.data_path = data_path

        # Modèle principal
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Nom", "Niveau", "PV", "Attaque", "Défense", "Vitesse",
            "Taux crit", "Dégâts crit", "Résistance", "Précision"
        ])

        # Proxy pour recherche
        self.proxy = QSortFilterProxyModel(self.ui)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(0)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Table de personnages
        self.ui.characterTable.setModel(self.proxy)
        self.ui.characterTable.setSortingEnabled(True)
        self.ui.characterTable.sortByColumn(0, Qt.AscendingOrder)

        # Connexions
        self.ui.addCharacterButton.clicked.connect(self.open_add_dialog)
        self.ui.searchBar.textChanged.connect(self.proxy.setFilterFixedString)
        self.enable_context_menu()

        # Pagination
        self.all_characters = []
        self.currentPage = 1
        self._setup_pagination()

        self.load_characters()
        self.update_table()

    def _setup_pagination(self):
        self.pageSizeCombo = QComboBox(self.ui)
        for size in ["10", "20", "50", "100"]:
            self.pageSizeCombo.addItem(size)
        self.pageSizeCombo.setCurrentIndex(0)
        self.ui.paginationLayout.insertWidget(1, self.pageSizeCombo)
        self.ui.prevPageButton.clicked.connect(self.prev_page)
        self.ui.nextPageButton.clicked.connect(self.next_page)
        self.pageSizeCombo.currentTextChanged.connect(self.on_page_size_changed)

    def load_characters(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.all_characters = json.load(f)
            except json.JSONDecodeError:
                QMessageBox.warning(self.ui, "Erreur", "Le fichier JSON est corrompu.")
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
        filtered = [p for p in self.all_characters if term in p['nom'].lower()]
        pageSize = int(self.pageSizeCombo.currentText())
        pages = max(1, math.ceil(len(filtered) / pageSize))
        self.currentPage = min(self.currentPage, pages)
        start = (self.currentPage - 1) * pageSize
        for p in filtered[start:start + pageSize]:
            self._append_row(p)

        self.ui.pageLabel.setText(f"Page {self.currentPage} / {pages}")
        self.ui.prevPageButton.setEnabled(self.currentPage > 1)
        self.ui.nextPageButton.setEnabled(self.currentPage < pages)

    def _append_row(self, data):
        t = lambda s: s['base'] + s['bonus']
        row = [
            QStandardItem(data['nom']),
            QStandardItem(str(data['niveau'])),
            QStandardItem(str(t(data['PV']))),
            QStandardItem(str(t(data['Attaque']))),
            QStandardItem(str(t(data['Défense']))),
            QStandardItem(str(t(data['Vitesse']))),
            QStandardItem(str(t(data['Taux crit']))),
            QStandardItem(str(t(data['Dégâts crit']))),
            QStandardItem(str(t(data['Résistance']))),
            QStandardItem(str(t(data['Précision'])))
        ]
        for item in row:
            item.setEditable(False)
        row[0].setData(data['nom'], Qt.UserRole)
        self.model.appendRow(row)

    def on_page_size_changed(self, text):
        self.currentPage = 1
        self.update_table()

    def prev_page(self):
        if self.currentPage > 1:
            self.currentPage -= 1
            self.update_table()

    def next_page(self):
        term = self.ui.searchBar.text().lower()
        total = len([p for p in self.all_characters if term in p['nom'].lower()])
        pages = max(1, math.ceil(total / int(self.pageSizeCombo.currentText())))
        if self.currentPage < pages:
            self.currentPage += 1
            self.update_table()

    def open_add_dialog(self):
        dlg = AjoutPersonnageDialog(self.ui)
        if dlg.exec_():
            new = dlg.get_data()
            self.all_characters.append(new)
            self.save_characters()
            self.currentPage = math.ceil(len(self.all_characters) / int(self.pageSizeCombo.currentText()))
            self.update_table()

    def edit_character(self, index):
        src = self.proxy.mapToSource(index)
        row = src.row()
        term = self.ui.searchBar.text().lower()
        filtered = [p for p in self.all_characters if term in p['nom'].lower()]
        try:
            actual = filtered[(self.currentPage - 1) * int(self.pageSizeCombo.currentText()) + row]
        except IndexError:
            return
        dlg = AjoutPersonnageDialog(self.ui)
        dlg.remplir_champs(actual)
        if dlg.exec_():
            updated = dlg.get_data()
            for i, p in enumerate(self.all_characters):
                if p['nom'] == actual['nom']:
                    self.all_characters[i] = updated
                    break
            self.save_characters()
            self.update_table()

    def open_context_menu(self, pos):
        index = self.ui.characterTable.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self.ui)
        mod = menu.addAction("Modifier")
        suppr = menu.addAction("Supprimer")
        action = menu.exec_(self.ui.characterTable.viewport().mapToGlobal(pos))
        if action == mod:
            self.edit_character(index)
        elif action == suppr:
            src = self.proxy.mapToSource(index)
            row = src.row()
            nom = self.model.item(row, 0).text()
            confirm = QMessageBox.question(self.ui, "Suppression", f"Supprimer « {nom} » ?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.all_characters = [p for p in self.all_characters if p['nom'] != nom]
                self.save_characters()
                self.update_table()

    def enable_context_menu(self):
        self.ui.characterTable.doubleClicked.connect(self.edit_character)
        self.ui.characterTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.characterTable.customContextMenuRequested.connect(self.open_context_menu)
