"""
headset_battery_indicator.preferences_dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Preferences dialog for visual icon settings (colors, orientation, scale, text)
and notification/polling configuration.
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
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .i18n import available_languages
from .settings import AppSettings, _is_valid_hex_color


class PreferencesDialog(QDialog):
    """Dialog for visual settings (colors, orientation, scale, text overlay)
    and notification/polling configuration."""

    settings_saved = Signal()

    def __init__(self, app_settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Preferences"))
        self.resize(340, 380)
        self.app_settings = app_settings

        self.temp_fill = app_settings.icon_fill_color
        self.temp_border = app_settings.icon_border_color

        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        fill_row = QHBoxLayout()
        self.btn_fill = QPushButton()
        self.btn_fill.setFixedWidth(32)
        self.btn_fill.clicked.connect(lambda: self._pick_color("fill"))
        self.edit_fill = QLineEdit()
        self.edit_fill.setPlaceholderText("#RRGGBB")
        self.edit_fill.setMaxLength(7)
        self.edit_fill.editingFinished.connect(lambda: self._on_hex_edited("fill"))
        fill_row.addWidget(self.btn_fill)
        fill_row.addWidget(self.edit_fill)
        form.addRow(self.tr("Fill Color:"), fill_row)

        border_row = QHBoxLayout()
        self.btn_border = QPushButton()
        self.btn_border.setFixedWidth(32)
        self.btn_border.clicked.connect(lambda: self._pick_color("border"))
        self.edit_border = QLineEdit()
        self.edit_border.setPlaceholderText("#RRGGBB")
        self.edit_border.setMaxLength(7)
        self.edit_border.editingFinished.connect(lambda: self._on_hex_edited("border"))
        border_row.addWidget(self.btn_border)
        border_row.addWidget(self.edit_border)
        form.addRow(self.tr("Border Color:"), border_row)

        self._orient_values = ["Horizontal", "Vertical"]
        self.combo_orient = QComboBox()
        self.combo_orient.addItems([self.tr("Horizontal"), self.tr("Vertical")])
        form.addRow(self.tr("Orientation:"), self.combo_orient)

        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(50, 150)
        self.spin_scale.setSingleStep(5)
        self.spin_scale.setSuffix("%")
        form.addRow(self.tr("Icon Zoom/Scale:"), self.spin_scale)

        self.chk_show_text = QCheckBox(self.tr("Show percentage/bolt inside icon"))
        form.addRow(self.tr("Overlay Text:"), self.chk_show_text)

        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(5, 95)
        self.spin_threshold.setSingleStep(5)
        self.spin_threshold.setSuffix("%")
        form.addRow(self.tr("Notification Threshold:"), self.spin_threshold)

        self.spin_poll = QSpinBox()
        self.spin_poll.setRange(10, 300)
        self.spin_poll.setSingleStep(10)
        self.spin_poll.setSuffix(self.tr(" sec"))
        form.addRow(self.tr("Poll Interval:"), self.spin_poll)

        self._lang_codes = []
        self.combo_lang = QComboBox()
        for code, name in available_languages():
            self._lang_codes.append(code)
            self.combo_lang.addItem(name)
        form.addRow(self.tr("Language:"), self.combo_lang)

        self.lbl_restart = QLabel(self.tr("⚠ Restart required to apply language change."))
        self.lbl_restart.setVisible(False)
        self.combo_lang.currentIndexChanged.connect(lambda _: self.lbl_restart.setVisible(True))

        layout.addLayout(form)
        layout.addWidget(self.lbl_restart)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save_settings)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_current_settings(self) -> None:
        self.temp_fill = self.app_settings.icon_fill_color
        self.temp_border = self.app_settings.icon_border_color

        self._update_color_row(self.btn_fill, self.edit_fill, self.temp_fill)
        self._update_color_row(self.btn_border, self.edit_border, self.temp_border)
        orient_idx = self._orient_values.index(self.app_settings.icon_orientation) if self.app_settings.icon_orientation in self._orient_values else 0
        self.combo_orient.setCurrentIndex(orient_idx)
        self.spin_scale.setValue(self.app_settings.icon_scale)
        self.chk_show_text.setChecked(self.app_settings.icon_show_text)
        self.spin_threshold.setValue(self.app_settings.notify_threshold)
        self.spin_poll.setValue(self.app_settings.poll_interval)
        lang_idx = self._lang_codes.index(self.app_settings.language) if self.app_settings.language in self._lang_codes else 0
        self.combo_lang.setCurrentIndex(lang_idx)

    def _pick_color(self, target: str) -> None:
        initial = QColor(self.temp_fill if target == "fill" else self.temp_border)
        color = QColorDialog.getColor(initial, self, "Select Color")
        if color.isValid():
            hex_c = color.name()
            if target == "fill":
                self.temp_fill = hex_c
                self._update_color_row(self.btn_fill, self.edit_fill, hex_c)
            else:
                self.temp_border = hex_c
                self._update_color_row(self.btn_border, self.edit_border, hex_c)

    def _on_hex_edited(self, target: str) -> None:
        edit = self.edit_fill if target == "fill" else self.edit_border
        btn = self.btn_fill if target == "fill" else self.btn_border
        value = edit.text().strip()
        if _is_valid_hex_color(value):
            if target == "fill":
                self.temp_fill = value
            else:
                self.temp_border = value
            self._update_color_row(btn, edit, value)
        else:
            edit.setText(self.temp_fill if target == "fill" else self.temp_border)

    def _update_color_row(self, btn: QPushButton, edit: QLineEdit, color_hex: str) -> None:
        btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #555;")
        edit.setText(color_hex)

    def _save_settings(self) -> None:
        self.app_settings.icon_fill_color = self.temp_fill
        self.app_settings.icon_border_color = self.temp_border
        self.app_settings.icon_orientation = self._orient_values[self.combo_orient.currentIndex()]
        self.app_settings.icon_scale = self.spin_scale.value()
        self.app_settings.icon_show_text = self.chk_show_text.isChecked()
        self.app_settings.notify_threshold = self.spin_threshold.value()
        self.app_settings.poll_interval = self.spin_poll.value()
        self.app_settings.language = self._lang_codes[self.combo_lang.currentIndex()]

        self.settings_saved.emit()
        self.accept()
