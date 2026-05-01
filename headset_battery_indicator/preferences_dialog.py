"""
headset_battery_indicator.preferences_dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Preferences dialog for visual icon settings (colors, orientation, scale, text).
"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .settings import AppSettings


class PreferencesDialog(QDialog):
    """Dialog for visual settings (colors, orientation, scale, text overlay)."""

    settings_saved = Signal()

    def __init__(self, app_settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(300, 250)
        self.app_settings = app_settings

        self.temp_fill = app_settings.icon_fill_color
        self.temp_border = app_settings.icon_border_color

        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.btn_fill = QPushButton()
        self.btn_fill.clicked.connect(lambda: self._pick_color("fill"))
        form.addRow("Fill Color:", self.btn_fill)

        self.btn_border = QPushButton()
        self.btn_border.clicked.connect(lambda: self._pick_color("border"))
        form.addRow("Border Color:", self.btn_border)

        self.combo_orient = QComboBox()
        self.combo_orient.addItems(["Horizontal", "Vertical"])
        form.addRow("Orientation:", self.combo_orient)

        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(50, 150)
        self.spin_scale.setSingleStep(5)
        self.spin_scale.setSuffix("%")
        form.addRow("Icon Zoom/Scale:", self.spin_scale)

        self.chk_show_text = QCheckBox("Show percentage/bolt inside icon")
        form.addRow("Overlay Text:", self.chk_show_text)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save_settings)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_current_settings(self) -> None:
        self.temp_fill = self.app_settings.icon_fill_color
        self.temp_border = self.app_settings.icon_border_color

        self._update_btn_style(self.btn_fill, self.temp_fill)
        self._update_btn_style(self.btn_border, self.temp_border)
        self.combo_orient.setCurrentText(self.app_settings.icon_orientation)
        self.spin_scale.setValue(self.app_settings.icon_scale)
        self.chk_show_text.setChecked(self.app_settings.icon_show_text)

    def _pick_color(self, target: str) -> None:
        initial = QColor(self.temp_fill if target == "fill" else self.temp_border)
        color = QColorDialog.getColor(initial, self, "Select Color")
        if color.isValid():
            hex_c = color.name()
            if target == "fill":
                self.temp_fill = hex_c
                self._update_btn_style(self.btn_fill, hex_c)
            else:
                self.temp_border = hex_c
                self._update_btn_style(self.btn_border, hex_c)

    def _update_btn_style(self, btn: QPushButton, color_hex: str) -> None:
        fg = "black" if QColor(color_hex).lightness() > 128 else "white"
        btn.setText(color_hex)
        btn.setStyleSheet(
            f"background-color: {color_hex}; color: {fg}; border: 1px solid #555;"
        )

    def _save_settings(self) -> None:
        self.app_settings.icon_fill_color = self.temp_fill
        self.app_settings.icon_border_color = self.temp_border
        self.app_settings.icon_orientation = self.combo_orient.currentText()
        self.app_settings.icon_scale = self.spin_scale.value()
        self.app_settings.icon_show_text = self.chk_show_text.isChecked()

        self.settings_saved.emit()
        self.accept()
