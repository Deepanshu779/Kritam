"""Mascot and Robot visual widgets for Kritam UI matching the reference design."""

import math
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


class KritamRobotWidget(QWidget):
    """3D-style sleek robot mascot with glowing headphones and neon facial expression."""

    def __init__(self, parent=None, compact=False):
        super().__init__(parent)
        self.compact = compact
        self.active = False
        self.glow_phase = 0.0

        if compact:
            self.setFixedSize(56, 56)
        else:
            self.setFixedSize(300, 250)

        # Floating / breathing animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_tick)
        self._anim_timer.start(45)

    def _on_tick(self):
        self.glow_phase += 0.08
        if self.glow_phase > 2 * math.pi:
            self.glow_phase -= 2 * math.pi
        self.update()

    def set_active(self, active):
        self.active = active
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0

        if self.compact:
            self._paint_compact(p, cx, h / 2.0, min(w, h) / 2.0)
        else:
            self._paint_hero(p, cx, h * 0.45, min(w, h) * 0.42)

        p.end()

    def _paint_hero(self, p, cx, cy, radius):
        pulse = math.sin(self.glow_phase)
        float_y = pulse * 4.5 if not self.active else math.sin(self.glow_phase * 2.5) * 7.0
        cy += float_y

        # -------------------------------------------------------------
        # 1. Base Glowing Energy Pedestal & Concentric Rings (Bottom)
        # -------------------------------------------------------------
        base_y = cy + radius * 0.98
        base_w = radius * 2.5
        base_h = radius * 0.52

        # Ambient blue glow spreading across platform
        ambient_grad = QRadialGradient(cx, base_y, base_w * 0.65)
        ambient_grad.setColorAt(0, QColor(0, 160, 255, 75))
        ambient_grad.setColorAt(0.45, QColor(0, 110, 255, 35))
        ambient_grad.setColorAt(1, QColor(0, 40, 140, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(ambient_grad)
        p.drawEllipse(QRectF(cx - base_w * 0.65, base_y - base_h * 0.8, base_w * 1.3, base_h * 1.6))

        # Outer energy ring
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(0, 170, 255, 80), 2))
        p.drawEllipse(QRectF(cx - base_w * 0.50, base_y - base_h * 0.48, base_w * 1.0, base_h * 0.96))

        # Middle bright cyan ring
        p.setPen(QPen(QColor(0, 220, 255, 160), 3))
        p.drawEllipse(QRectF(cx - base_w * 0.38, base_y - base_h * 0.36, base_w * 0.76, base_h * 0.72))

        # Inner vibrant high-glow ring
        inner_alpha = int(210 + 45 * pulse)
        p.setPen(QPen(QColor(0, 245, 255, inner_alpha), 3.5))
        p.drawEllipse(QRectF(cx - base_w * 0.24, base_y - base_h * 0.24, base_w * 0.48, base_h * 0.48))

        # -------------------------------------------------------------
        # 2. Ambient Radiant Aura behind Robot Head
        # -------------------------------------------------------------
        head_r = radius * 0.72
        head_aura = QRadialGradient(cx, cy, head_r * 1.5)
        head_aura.setColorAt(0, QColor(0, 150, 255, int(85 + 25 * pulse)))
        head_aura.setColorAt(0.6, QColor(0, 90, 230, 30))
        head_aura.setColorAt(1, QColor(0, 10, 60, 0))
        p.setBrush(head_aura)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx - head_r * 1.5, cy - head_r * 1.5, head_r * 3.0, head_r * 3.0))

        # -------------------------------------------------------------
        # 3. Futuristic Glowing Headphone Band
        # -------------------------------------------------------------
        band_r = head_r * 1.12
        band_pen = QPen(QColor("#081c34"), head_r * 0.17)
        p.setPen(band_pen)
        p.drawArc(QRectF(cx - band_r, cy - band_r * 1.05, band_r * 2.0, band_r * 2.0), 22 * 16, 136 * 16)

        # Neon illumination line on headband
        band_neon = QPen(QColor("#00d4ff"), 3.2)
        p.setPen(band_neon)
        p.drawArc(QRectF(cx - band_r * 1.01, cy - band_r * 1.06, band_r * 2.02, band_r * 2.02), 26 * 16, 128 * 16)

        # -------------------------------------------------------------
        # 4. Glossy 3D Obsidian Robot Head
        # -------------------------------------------------------------
        head_grad = QRadialGradient(cx - head_r * 0.35, cy - head_r * 0.38, head_r * 1.45)
        head_grad.setColorAt(0.0, QColor("#223958"))
        head_grad.setColorAt(0.35, QColor("#0d2036"))
        head_grad.setColorAt(0.72, QColor("#050f1c"))
        head_grad.setColorAt(1.0, QColor("#020710"))

        p.setBrush(head_grad)
        p.setPen(QPen(QColor("#1b4b80"), 2))
        p.drawEllipse(QPointF(cx, cy), head_r, head_r)

        # 3D Specular Gloss Highlight (curved across upper-right / forehead)
        spec_grad = QLinearGradient(cx - head_r * 0.55, cy - head_r * 0.75, cx + head_r * 0.35, cy - head_r * 0.15)
        spec_grad.setColorAt(0, QColor(255, 255, 255, 60))
        spec_grad.setColorAt(0.4, QColor(0, 200, 255, 30))
        spec_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(spec_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx - head_r * 0.70, cy - head_r * 0.82, head_r * 1.25, head_r * 0.65))

        # -------------------------------------------------------------
        # 5. Glowing Headphones (Ear Cups)
        # -------------------------------------------------------------
        ear_offset_x = head_r * 1.02
        ear_w = head_r * 0.30
        ear_h = head_r * 0.66

        for side in (-1, 1):
            ex = cx + side * ear_offset_x
            ey = cy

            # Outer radiant glow around ear cup
            ear_glow = QRadialGradient(ex, ey, ear_h * 0.95)
            ear_glow.setColorAt(0, QColor(0, 215, 255, int(130 + 35 * pulse)))
            ear_glow.setColorAt(0.55, QColor(0, 110, 255, 45))
            ear_glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(ear_glow)
            p.drawEllipse(QRectF(ex - ear_h * 0.65, ey - ear_h * 0.65, ear_h * 1.3, ear_h * 1.3))

            # Ear cushion dark body
            p.setBrush(QColor("#061322"))
            p.setPen(QPen(QColor("#0088e8"), 2.2))
            p.drawRoundedRect(QRectF(ex - ear_w / 2, ey - ear_h / 2, ear_w, ear_h), ear_w * 0.45, ear_w * 0.45)

            # Glowing cyan capsule / ring on ear cup
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor("#00e5ff"), 3.2))
            p.drawRoundedRect(
                QRectF(ex - ear_w * 0.34, ey - ear_h * 0.38, ear_w * 0.68, ear_h * 0.76),
                ear_w * 0.34,
                ear_w * 0.34,
            )

            # Center bright neon LED indicator
            p.setBrush(QColor("#54f5ff"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey), ear_w * 0.22, ear_w * 0.22)

        # -------------------------------------------------------------
        # 6. Facial Expression: Glowing Cyan Eyes & Smile
        # -------------------------------------------------------------
        cyan_neon = QColor("#00f0ff")

        # Soft glow behind eyes and smile
        p.setPen(QPen(QColor(0, 240, 255, 60), head_r * 0.16, Qt.SolidLine, Qt.RoundCap))
        eye_spacing = head_r * 0.35
        eye_w = head_r * 0.28
        eye_h = head_r * 0.24
        eye_y = cy - head_r * 0.07

        p.drawArc(QRectF(cx - eye_spacing - eye_w / 2, eye_y - eye_h / 2, eye_w, eye_h), 22 * 16, 136 * 16)
        p.drawArc(QRectF(cx + eye_spacing - eye_w / 2, eye_y - eye_h / 2, eye_w, eye_h), 22 * 16, 136 * 16)

        # Crisp core eye arcs
        eye_pen = QPen(cyan_neon, max(3.8, head_r * 0.088), Qt.SolidLine, Qt.RoundCap)
        p.setPen(eye_pen)
        p.drawArc(QRectF(cx - eye_spacing - eye_w / 2, eye_y - eye_h / 2, eye_w, eye_h), 22 * 16, 136 * 16)
        p.drawArc(QRectF(cx + eye_spacing - eye_w / 2, eye_y - eye_h / 2, eye_w, eye_h), 22 * 16, 136 * 16)

        # Cute smiling mouth
        mouth_w = head_r * 0.36
        mouth_h = head_r * 0.24
        mouth_y = cy + head_r * 0.17

        # Soft mouth glow
        p.setPen(QPen(QColor(0, 240, 255, 60), head_r * 0.15, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(QRectF(cx - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h), 205 * 16, 130 * 16)

        # Crisp core mouth
        mouth_pen = QPen(cyan_neon, max(3.4, head_r * 0.078), Qt.SolidLine, Qt.RoundCap)
        p.setPen(mouth_pen)
        p.drawArc(QRectF(cx - mouth_w / 2, mouth_y - mouth_h / 2, mouth_w, mouth_h), 205 * 16, 130 * 16)

    def _paint_compact(self, p, cx, cy, radius):
        """Compact version for sidebar profile card."""
        pulse = math.sin(self.glow_phase)

        # Circular dark backdrop with cyan border
        bg_rect = QRectF(cx - radius + 2, cy - radius + 2, (radius - 2) * 2, (radius - 2) * 2)
        p.setPen(QPen(QColor("#154273"), 1.5))
        p.setBrush(QColor("#071526"))
        p.drawEllipse(bg_rect)

        head_r = radius * 0.52

        # Headphone band
        p.setPen(QPen(QColor("#00b4ff"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(cx - head_r * 1.15, cy - head_r * 1.15, head_r * 2.3, head_r * 2.3), 30 * 16, 120 * 16)

        # Head sphere
        head_grad = QRadialGradient(cx - head_r * 0.3, cy - head_r * 0.3, head_r * 1.4)
        head_grad.setColorAt(0, QColor("#1c3350"))
        head_grad.setColorAt(1, QColor("#040b15"))
        p.setBrush(head_grad)
        p.setPen(QPen(QColor("#15457a"), 1.2))
        p.drawEllipse(QPointF(cx, cy), head_r, head_r)

        # Ear cups
        ear_w = head_r * 0.25
        ear_h = head_r * 0.55
        p.setBrush(QColor("#00d0ff"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(cx - head_r * 1.1 - ear_w / 2, cy - ear_h / 2, ear_w, ear_h), 3, 3)
        p.drawRoundedRect(QRectF(cx + head_r * 1.1 - ear_w / 2, cy - ear_h / 2, ear_w, ear_h), 3, 3)

        # Eyes & mouth
        cyan_pen = QPen(QColor("#00f0ff"), 2.2, Qt.SolidLine, Qt.RoundCap)
        p.setPen(cyan_pen)
        p.setBrush(Qt.NoBrush)

        eye_w = head_r * 0.30
        eye_y = cy - head_r * 0.08
        p.drawArc(QRectF(cx - head_r * 0.46, eye_y - 3, eye_w, 6), 25 * 16, 130 * 16)
        p.drawArc(QRectF(cx + head_r * 0.16, eye_y - 3, eye_w, 6), 25 * 16, 130 * 16)
        p.drawArc(QRectF(cx - head_r * 0.22, cy + head_r * 0.14, head_r * 0.44, 7), 205 * 16, 130 * 16)
