from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
import os

# Liste des effets simples (3 fois possible) et effets spéciaux (2 fois max)
EFFETS_SHELL = {
    "normaux": ["celerite", "baindesang", "fauche"],
    "speciaux": ["eclairdivin", "raidrapide", "gardeducolosse", "lameViolente", "etherpeste", "abrievolutif"]
}

def create_effect_buttons(callback, image_dir="images/modules/"):
    """Crée une rangée de boutons avec les icônes des effets disponibles"""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setSpacing(5)

    for effect_type in EFFETS_SHELL.values():
        for effect in effect_type:
            icon_path = os.path.join(image_dir, f"{effect}.png")
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(40, 40))
            btn.setToolTip(effect)
            btn.setObjectName(effect)
            btn.clicked.connect(lambda _, e=effect: callback(e))
            layout.addWidget(btn)

    return container
