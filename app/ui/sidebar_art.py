"""Decorative sidebar components for Kritam: Logo & Glowing Wave Footer Art."""

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class SidebarLogoWidget(QWidget):
    """Stylized 3D glowing 'A' / Chevron logo with KRITAM branding."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(115)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        cx = w / 2.0

        # Draw the 3D glowing "A" / Chevron symbol
        logo_top = 10.0
        logo_w = 48.0
        logo_h = 44.0

        # Left leg of "A"
        left_grad = QLinearGradient(cx - logo_w / 2, logo_top + logo_h, cx, logo_top)
        left_grad.setColorAt(0, QColor("#0070ea"))
        left_grad.setColorAt(0.6, QColor("#00c4ff"))
        left_grad.setColorAt(1, QColor("#80e5ff"))

        path_left = QPainterPath()
        path_left.moveTo(cx, logo_top)
        path_left.lineTo(cx - logo_w * 0.44, logo_top + logo_h)
        path_left.lineTo(cx - logo_w * 0.16, logo_top + logo_h)
        path_left.lineTo(cx, logo_top + logo_h * 0.42)
        path_left.closeSubpath()

        p.setPen(Qt.NoPen)
        p.setBrush(left_grad)
        p.drawPath(path_left)

        # Right leg of "A" (darker/3D shaded gradient)
        right_grad = QLinearGradient(cx, logo_top, cx + logo_w / 2, logo_top + logo_h)
        right_grad.setColorAt(0, QColor("#5ad2ff"))
        right_grad.setColorAt(0.5, QColor("#007bfb"))
        right_grad.setColorAt(1, QColor("#0044aa"))

        path_right = QPainterPath()
        path_right.moveTo(cx, logo_top)
        path_right.lineTo(cx + logo_w * 0.44, logo_top + logo_h)
        path_right.lineTo(cx + logo_w * 0.16, logo_top + logo_h)
        path_right.lineTo(cx, logo_top + logo_h * 0.42)
        path_right.closeSubpath()

        p.setBrush(right_grad)
        p.drawPath(path_right)

        # Horizontal crossbar glow
        bar_grad = QLinearGradient(cx - logo_w * 0.32, logo_top + logo_h * 0.64, cx + logo_w * 0.32, logo_top + logo_h * 0.64)
        bar_grad.setColorAt(0, QColor("#00e5ff"))
        bar_grad.setColorAt(1, QColor("#0070ea"))
        p.setBrush(bar_grad)
        p.drawRoundedRect(QRectF(cx - logo_w * 0.28, logo_top + logo_h * 0.64, logo_w * 0.56, 4.5), 2, 2)

        # Ambient glow around logo
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(0, 190, 255, 45), 2))
        p.drawEllipse(QPointF(cx, logo_top + logo_h * 0.5), logo_w * 0.55, logo_h * 0.55)

        # "KRITAM" text below logo
        font_brand = QFont("Segoe UI", 13, QFont.Bold)
        font_brand.setLetterSpacing(QFont.AbsoluteSpacing, 2.5)
        p.setFont(font_brand)
        p.setPen(QColor("#ffffff"))
        p.drawText(QRectF(0, 64, w, 22), Qt.AlignCenter, "KRITAM")

        # Subtitle text
        font_sub = QFont("Segoe UI", 8)
        p.setFont(font_sub)
        p.setPen(QColor("#7e91ad"))
        p.drawText(QRectF(0, 86, w, 18), Qt.AlignCenter, "Your Personal AI Assistant")

        p.end()


class SidebarFooterArtWidget(QWidget):
    """Flowing cyan/blue light ribbons with script text 'More Than a Voice, A Companion'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(175)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Flowing ribbon waves emerging from bottom left corner
        # Outer soft glow wave
        p.setPen(Qt.NoPen)
        outer_wave_grad = QLinearGradient(0, h, w * 0.9, h * 0.4)
        outer_wave_grad.setColorAt(0, QColor(0, 110, 255, 100))
        outer_wave_grad.setColorAt(0.6, QColor(0, 180, 255, 40))
        outer_wave_grad.setColorAt(1, QColor(0, 70, 200, 0))

        path1 = QPainterPath()
        path1.moveTo(0, h * 0.70)
        path1.cubicTo(w * 0.25, h * 0.55, w * 0.60, h * 0.82, w * 0.95, h * 0.65)
        path1.lineTo(w * 0.85, h)
        path1.lineTo(0, h)
        path1.closeSubpath()
        p.setBrush(outer_wave_grad)
        p.drawPath(path1)

        # Core bright cyan wave line
        cyan_pen = QPen(QColor("#00d2ff"), 2.2)
        cyan_pen.setCapStyle(Qt.RoundCap)
        p.setPen(cyan_pen)
        p.setBrush(Qt.NoBrush)

        line_path = QPainterPath()
        line_path.moveTo(0, h * 0.78)
        line_path.cubicTo(w * 0.22, h * 0.68, w * 0.45, h * 0.92, w * 0.75, h * 0.78)
        p.drawPath(line_path)

        # Secondary blue wave
        blue_pen = QPen(QColor(0, 120, 240, 160), 3.0)
        p.setPen(blue_pen)
        line_path2 = QPainterPath()
        line_path2.moveTo(0, h * 0.88)
        line_path2.cubicTo(w * 0.30, h * 0.76, w * 0.55, h * 0.96, w * 0.88, h * 0.84)
        p.drawPath(line_path2)

        # 2. Cursive / handwritten script text
        # "More Than"
        # "a Voice,"
        # "A Companion"
        script_font = QFont("Brush Script MT", 16)
        if not script_font.exactMatch():
            script_font = QFont("Segoe Print", 13)
        if not script_font.exactMatch():
            script_font = QFont("Georgia", 13)
            script_font.setItalic(True)

        p.setFont(script_font)
        p.setPen(QColor("#c5d9f5"))

        text_x = 22.0
        p.drawText(QPointF(text_x, h * 0.52), "More Than")
        p.drawText(QPointF(text_x + 14, h * 0.66), "a Voice,")
        p.drawText(QPointF(text_x, h * 0.81), "A Companion")

        # Stylish cyan flourish / underline under "A Companion"
        flourish_pen = QPen(QColor("#00e5ff"), 2)
        flourish_pen.setCapStyle(Qt.RoundCap)
        p.setPen(flourish_pen)
        p.drawLine(QPointF(text_x + 22, h * 0.85), QPointF(text_x + 72, h * 0.83))

        p.end()
