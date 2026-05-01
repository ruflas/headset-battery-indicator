"""
headset_battery_indicator.icon_renderer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Icon rendering for battery status display.

This module handles all visual rendering of the battery icon,
separated from the main application logic for easier testing and maintenance.
"""

from typing import Literal

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QBrush


class BatteryIconRenderer:
    """Renders battery status icons with configurable colors and orientation."""
    
    # Canvas size
    CANVAS_SIZE = 128
    
    def __init__(
        self,
        fill_color: str = "#00FF00",
        border_color: str = "#FFFFFF",
        orientation: Literal["Horizontal", "Vertical"] = "Horizontal",
        scale: int = 75,
        show_text: bool = True,
    ):
        """Initialize the renderer with visual settings.
        
        Args:
            fill_color: Hex color for the battery fill (e.g., '#00FF00')
            border_color: Hex color for the battery border (e.g., '#FFFFFF')
            orientation: 'Horizontal' or 'Vertical' battery orientation
            scale: Zoom factor as percentage (50-150)
            show_text: Whether to show percentage/bolt text overlay
        """
        self.fill_color = fill_color
        self.border_color = border_color
        self.orientation = orientation
        self.scale = max(50, min(150, scale))  # Clamp to 50-150%
        self.show_text = show_text

    def render(self, percentage: int, is_charging: bool, error: bool = False) -> QIcon:
        """Render a battery icon with the given parameters.
        
        Args:
            percentage: Battery level (0-100)
            is_charging: Whether the device is charging
            error: Whether to show error state (X symbol)
            
        Returns:
            QIcon with the rendered battery indicator
        """
        s = self.CANVAS_SIZE
        pixmap = QPixmap(s, s)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if error:
            self._paint_error(painter, s)
        else:
            self._paint_battery(painter, s, percentage, is_charging)

        painter.end()
        return QIcon(pixmap)

    def _paint_error(self, painter: QPainter, size: int) -> None:
        """Paint an error state (red X symbol)."""
        painter.setPen(QPen(Qt.red, int(size * 0.15)))
        m = int(size * 0.25)
        painter.drawLine(m, m, size - m, size - m)
        painter.drawLine(size - m, m, m, size - m)

    def _paint_battery(
        self, painter: QPainter, size: int, percentage: int, is_charging: bool
    ) -> None:
        """Paint the battery indicator."""
        scale_factor = self.scale / 100.0

        # Determine colors
        c_fill = QColor(self.fill_color)
        if is_charging:
            c_fill = c_fill.lighter(130)
        c_border = QColor(self.border_color)

        # Set up pen for borders
        pen_width = max(6, int(size * 0.06 * scale_factor))
        pen = QPen(c_border)
        pen.setWidth(pen_width)
        painter.setPen(pen)

        if self.orientation == "Horizontal":
            self._paint_horizontal(painter, size, percentage, c_fill, c_border, pen_width, scale_factor)
        else:
            self._paint_vertical(painter, size, percentage, c_fill, c_border, pen_width, scale_factor)

        # Draw text overlay if enabled
        if self.show_text:
            self._paint_text(painter, size, percentage, is_charging, scale_factor, c_border)

    def _paint_horizontal(
        self,
        painter: QPainter,
        size: int,
        percentage: int,
        fill_color: QColor,
        border_color: QColor,
        pen_width: int,
        scale_factor: float,
    ) -> None:
        """Paint horizontal battery icon."""
        w_total = size * scale_factor
        h_total = (size * 0.80) * scale_factor

        # Center on canvas
        x_start = (size - w_total) / 2
        y_start = (size - h_total) / 2

        # Battery components
        w_body = w_total * 0.90
        w_nub = w_total * 0.10
        h_nub = h_total * 0.50

        body = QRectF(x_start, y_start, w_body, h_total)
        nub = QRectF(x_start + w_body, y_start + (h_total - h_nub) / 2, w_nub, h_nub)

        # Draw body outline
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(body, size // 15, size // 15)

        # Draw nub
        painter.setBrush(border_color)
        painter.drawRoundedRect(nub, size // 30, size // 30)

        # Draw fill
        if percentage > 0:
            pad = pen_width * 1.5
            fill_w = (w_body - 2 * pad) * (percentage / 100.0)
            if fill_w > 0:
                fill_rect = QRectF(
                    body.x() + pad,
                    body.y() + pad,
                    fill_w,
                    body.height() - 2 * pad,
                )
                painter.setBrush(fill_color)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(fill_rect, size // 40, size // 40)

    def _paint_vertical(
        self,
        painter: QPainter,
        size: int,
        percentage: int,
        fill_color: QColor,
        border_color: QColor,
        pen_width: int,
        scale_factor: float,
    ) -> None:
        """Paint vertical battery icon."""
        w_total = (size * 0.80) * scale_factor
        h_total = size * scale_factor

        # Center on canvas
        x_start = (size - w_total) / 2
        y_start = (size - h_total) / 2

        # Battery components
        h_body = h_total * 0.90
        h_nub = h_total * 0.10
        w_nub = w_total * 0.50

        # Nub at top
        nub = QRectF(x_start + (w_total - w_nub) / 2, y_start, w_nub, h_nub)
        # Body below nub
        body = QRectF(x_start, y_start + h_nub, w_total, h_body)

        # Draw body outline
        painter.setPen(QPen(border_color, pen_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(body, size // 15, size // 15)

        # Draw nub
        painter.setBrush(border_color)
        painter.drawRoundedRect(nub, size // 30, size // 30)

        # Draw fill (from bottom)
        if percentage > 0:
            pad = pen_width * 1.5
            fill_h = (h_body - 2 * pad) * (percentage / 100.0)
            if fill_h > 0:
                y_fill = (body.y() + body.height() - pad) - fill_h
                fill_rect = QRectF(body.x() + pad, y_fill, body.width() - 2 * pad, fill_h)
                painter.setBrush(fill_color)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(fill_rect, size // 40, size // 40)

    def _paint_text(
        self,
        painter: QPainter,
        size: int,
        percentage: int,
        is_charging: bool,
        scale_factor: float,
        border_color: QColor,
    ) -> None:
        """Paint text overlay (percentage or charging bolt)."""
        painter.setPen(border_color)

        # Font size based on canvas size and scale
        font_size = int(size * 0.50 * scale_factor)
        font = QFont("Sans Serif", font_size, QFont.Bold)
        painter.setFont(font)

        # Determine text
        txt = "⚡" if is_charging else str(percentage)

        # Draw dark shadow for contrast
        painter.setPen(QColor(0, 0, 0, 255))
        offset = max(2, int(size * 0.03))
        painter.drawText(QRectF(offset, offset, size, size), Qt.AlignCenter, txt)

        # Draw main text in border color
        painter.setPen(border_color)
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, txt)
