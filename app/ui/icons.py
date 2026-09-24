"""Vector icon rendering utilities for Kritam UI."""

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)


def create_pixmap(size=24):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    return pm


def render_chrome_icon(size=28):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    w, h = size, size
    cx, cy = w / 2, h / 2
    r = min(w, h) * 0.44

    # Chrome 3-colored sectors around center
    # Top red sector
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#ea4335"))
    p.drawPie(QRectF(cx - r, cy - r, r * 2, r * 2), int(30 * 16), int(120 * 16))

    # Right yellow sector
    p.setBrush(QColor("#fbbc05"))
    p.drawPie(QRectF(cx - r, cy - r, r * 2, r * 2), int(270 * 16), int(120 * 16))

    # Left green sector
    p.setBrush(QColor("#34a853"))
    p.drawPie(QRectF(cx - r, cy - r, r * 2, r * 2), int(150 * 16), int(120 * 16))

    # White ring around center
    p.setBrush(QColor("#ffffff"))
    inner_white_r = r * 0.52
    p.drawEllipse(QPointF(cx, cy), inner_white_r, inner_white_r)

    # Blue inner circle
    blue_grad = QLinearGradient(cx - inner_white_r, cy - inner_white_r, cx + inner_white_r, cy + inner_white_r)
    blue_grad.setColorAt(0, QColor("#4285f4"))
    blue_grad.setColorAt(1, QColor("#1a73e8"))
    p.setBrush(blue_grad)
    p.drawEllipse(QPointF(cx, cy), inner_white_r * 0.76, inner_white_r * 0.76)

    p.end()
    return pm


def render_folder_icon(size=28):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    # Back flap
    p.setBrush(QColor("#0077d4"))
    path_back = QPainterPath()
    path_back.moveTo(size * 0.12, size * 0.32)
    path_back.lineTo(size * 0.44, size * 0.32)
    path_back.lineTo(size * 0.52, size * 0.42)
    path_back.lineTo(size * 0.88, size * 0.42)
    path_back.lineTo(size * 0.88, size * 0.78)
    path_back.lineTo(size * 0.12, size * 0.78)
    path_back.closeSubpath()
    p.drawPath(path_back)

    # Front main body with bright blue gradient
    grad = QLinearGradient(0, size * 0.40, 0, size * 0.86)
    grad.setColorAt(0, QColor("#00a2ff"))
    grad.setColorAt(1, QColor("#0060df"))
    p.setBrush(grad)
    p.drawRoundedRect(QRectF(size * 0.10, size * 0.40, size * 0.80, size * 0.46), 4, 4)

    p.end()
    return pm


def render_camera_icon(size=28):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    # Camera body cyan gradient
    grad = QLinearGradient(0, size * 0.25, 0, size * 0.82)
    grad.setColorAt(0, QColor("#00d2ff"))
    grad.setColorAt(1, QColor("#0077c8"))
    p.setBrush(grad)

    # Top bump
    p.drawRoundedRect(QRectF(size * 0.34, size * 0.22, size * 0.32, size * 0.16), 3, 3)
    # Main body
    p.drawRoundedRect(QRectF(size * 0.12, size * 0.30, size * 0.76, size * 0.52), 6, 6)

    # Flash dot
    p.setBrush(QColor("#ffffff"))
    p.drawEllipse(QPointF(size * 0.74, size * 0.42), size * 0.045, size * 0.045)

    # Lens outer ring
    p.setBrush(QColor("#081728"))
    p.drawEllipse(QPointF(size * 0.50, size * 0.56), size * 0.19, size * 0.19)

    # Lens inner glass
    lens_grad = QRadialGradient(size * 0.48, size * 0.54, size * 0.15)
    lens_grad.setColorAt(0, QColor("#00f0ff"))
    lens_grad.setColorAt(0.6, QColor("#0088cc"))
    lens_grad.setColorAt(1, QColor("#05162b"))
    p.setBrush(lens_grad)
    p.drawEllipse(QPointF(size * 0.50, size * 0.56), size * 0.14, size * 0.14)

    p.end()
    return pm


def render_youtube_icon(size=28):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    # Red rounded rectangle
    grad = QLinearGradient(0, size * 0.25, 0, size * 0.75)
    grad.setColorAt(0, QColor("#ff1133"))
    grad.setColorAt(1, QColor("#cc001b"))
    p.setBrush(grad)
    p.drawRoundedRect(QRectF(size * 0.12, size * 0.25, size * 0.76, size * 0.50), 7, 7)

    # White play triangle
    p.setBrush(QColor("#ffffff"))
    play = QPainterPath()
    play.moveTo(size * 0.42, size * 0.37)
    play.lineTo(size * 0.63, size * 0.50)
    play.lineTo(size * 0.42, size * 0.63)
    play.closeSubpath()
    p.drawPath(play)

    p.end()
    return pm


def render_search_icon(size=28):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Cyan magnifying glass
    pen = QPen(QColor("#00d2ff"), size * 0.11)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    cx, cy = size * 0.42, size * 0.42
    r = size * 0.23
    p.drawEllipse(QPointF(cx, cy), r, r)

    # Handle
    p.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(size * 0.82, size * 0.82))

    p.end()
    return pm


def render_note_icon(size=28):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    # Blue paper sheet
    grad = QLinearGradient(0, size * 0.15, 0, size * 0.85)
    grad.setColorAt(0, QColor("#3ea8ff"))
    grad.setColorAt(1, QColor("#0070ea"))
    p.setBrush(grad)

    doc = QPainterPath()
    doc.moveTo(size * 0.20, size * 0.15)
    doc.lineTo(size * 0.62, size * 0.15)
    doc.lineTo(size * 0.80, size * 0.33)
    doc.lineTo(size * 0.80, size * 0.85)
    doc.lineTo(size * 0.20, size * 0.85)
    doc.closeSubpath()
    p.drawPath(doc)

    # Folded flap
    p.setBrush(QColor("#80caff"))
    flap = QPainterPath()
    flap.moveTo(size * 0.62, size * 0.15)
    flap.lineTo(size * 0.62, size * 0.33)
    flap.lineTo(size * 0.80, size * 0.33)
    flap.closeSubpath()
    p.drawPath(flap)

    # Text lines on note
    pen = QPen(QColor("#ffffff"), size * 0.06)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.drawLine(QPointF(size * 0.32, size * 0.45), QPointF(size * 0.68, size * 0.45))
    p.drawLine(QPointF(size * 0.32, size * 0.58), QPointF(size * 0.68, size * 0.58))
    p.drawLine(QPointF(size * 0.32, size * 0.71), QPointF(size * 0.52, size * 0.71))

    p.end()
    return pm


def render_nav_icon(name, active=False, size=22):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    color = QColor("#ffffff") if active else QColor("#8297b4")
    pen = QPen(color, 2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    if name == "home":
        # Home roof + base
        p.drawLine(QPointF(size * 0.18, size * 0.48), QPointF(size * 0.50, size * 0.20))
        p.drawLine(QPointF(size * 0.50, size * 0.20), QPointF(size * 0.82, size * 0.48))
        p.drawRect(QRectF(size * 0.26, size * 0.48, size * 0.48, size * 0.36))
    elif name == "chat":
        # Speech bubble with dots
        p.drawRoundedRect(QRectF(size * 0.15, size * 0.20, size * 0.70, size * 0.50), 5, 5)
        # Tail
        tail = QPainterPath()
        tail.moveTo(size * 0.32, size * 0.70)
        tail.lineTo(size * 0.24, size * 0.84)
        tail.lineTo(size * 0.46, size * 0.70)
        p.drawPath(tail)
        # Dots
        p.setBrush(color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(size * 0.36, size * 0.45), 1.5, 1.5)
        p.drawEllipse(QPointF(size * 0.50, size * 0.45), 1.5, 1.5)
        p.drawEllipse(QPointF(size * 0.64, size * 0.45), 1.5, 1.5)
    elif name == "tasks":
        # Clipboard with check
        p.drawRoundedRect(QRectF(size * 0.20, size * 0.24, size * 0.60, size * 0.62), 4, 4)
        p.drawRoundedRect(QRectF(size * 0.36, size * 0.14, size * 0.28, size * 0.14), 2, 2)
        # Checkmark
        p.drawLine(QPointF(size * 0.34, size * 0.54), QPointF(size * 0.44, size * 0.64))
        p.drawLine(QPointF(size * 0.44, size * 0.64), QPointF(size * 0.66, size * 0.42))
    elif name == "memory":
        # Brain contours
        p.drawArc(QRectF(size * 0.20, size * 0.24, size * 0.30, size * 0.30), 60 * 16, 180 * 16)
        p.drawArc(QRectF(size * 0.50, size * 0.24, size * 0.30, size * 0.30), -60 * 16, 180 * 16)
        p.drawArc(QRectF(size * 0.18, size * 0.48, size * 0.32, size * 0.32), 120 * 16, 180 * 16)
        p.drawArc(QRectF(size * 0.50, size * 0.48, size * 0.32, size * 0.32), -120 * 16, 180 * 16)
        p.drawLine(QPointF(size * 0.50, size * 0.26), QPointF(size * 0.50, size * 0.74))
    elif name == "settings":
        # Gear
        p.drawEllipse(QPointF(size * 0.5, size * 0.5), size * 0.22, size * 0.22)
        import math
        for i in range(6):
            ang = i * (math.pi / 3)
            x1 = size * 0.5 + math.cos(ang) * (size * 0.26)
            y1 = size * 0.5 + math.sin(ang) * (size * 0.26)
            x2 = size * 0.5 + math.cos(ang) * (size * 0.40)
            y2 = size * 0.5 + math.sin(ang) * (size * 0.40)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    p.end()
    return pm


def render_paperclip_icon(size=20):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#8fa5c2"), 2)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    # Angled paperclip
    path = QPainterPath()
    path.moveTo(size * 0.60, size * 0.32)
    path.lineTo(size * 0.36, size * 0.56)
    path.arcTo(QRectF(size * 0.22, size * 0.48, size * 0.28, size * 0.28), 135, 180)
    path.lineTo(size * 0.64, size * 0.28)
    path.arcTo(QRectF(size * 0.50, size * 0.14, size * 0.32, size * 0.32), -45, 180)
    path.lineTo(size * 0.32, size * 0.60)
    p.drawPath(path)

    p.end()
    return pm


def render_mic_icon(size=20, color="#ffffff"):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))

    # Mic capsule
    p.drawRoundedRect(QRectF(size * 0.36, size * 0.16, size * 0.28, size * 0.46), 4, 4)

    # Mic stand cradle arc
    pen = QPen(QColor(color), 2)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(size * 0.24, size * 0.28, size * 0.52, size * 0.44), 0, -180 * 16)

    # Stand vertical pole and base line
    p.drawLine(QPointF(size * 0.50, size * 0.72), QPointF(size * 0.50, size * 0.86))
    p.drawLine(QPointF(size * 0.35, size * 0.86), QPointF(size * 0.65, size * 0.86))

    p.end()
    return pm


def render_send_icon(size=20, color="#ffffff"):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))

    # Paper airplane
    path = QPainterPath()
    path.moveTo(size * 0.18, size * 0.22)
    path.lineTo(size * 0.84, size * 0.50)
    path.lineTo(size * 0.18, size * 0.78)
    path.lineTo(size * 0.34, size * 0.50)
    path.closeSubpath()
    p.drawPath(path)

    p.end()
    return pm


def render_chevron_right(size=14, color="#6b829e"):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.drawLine(QPointF(size * 0.35, size * 0.22), QPointF(size * 0.65, size * 0.50))
    p.drawLine(QPointF(size * 0.65, size * 0.50), QPointF(size * 0.35, size * 0.78))
    p.end()
    return pm


def render_chevron_down(size=14, color="#6b829e"):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.drawLine(QPointF(size * 0.22, size * 0.35), QPointF(size * 0.50, size * 0.65))
    p.drawLine(QPointF(size * 0.50, size * 0.65), QPointF(size * 0.78, size * 0.35))
    p.end()
    return pm


def render_lightning_icon(size=16, color="#00b4ff"):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))

    path = QPainterPath()
    path.moveTo(size * 0.54, size * 0.10)
    path.lineTo(size * 0.22, size * 0.56)
    path.lineTo(size * 0.50, size * 0.56)
    path.lineTo(size * 0.44, size * 0.90)
    path.lineTo(size * 0.78, size * 0.44)
    path.lineTo(size * 0.52, size * 0.44)
    path.closeSubpath()
    p.drawPath(path)

    p.end()
    return pm


def render_soundwave_icon(size=16, color="#00e5ff"):
    pm = create_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color), 2)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)

    # 4 vertical audio bars
    p.drawLine(QPointF(size * 0.20, size * 0.38), QPointF(size * 0.20, size * 0.62))
    p.drawLine(QPointF(size * 0.40, size * 0.20), QPointF(size * 0.40, size * 0.80))
    p.drawLine(QPointF(size * 0.60, size * 0.30), QPointF(size * 0.60, size * 0.70))
    p.drawLine(QPointF(size * 0.80, size * 0.44), QPointF(size * 0.80, size * 0.56))

    p.end()
    return pm
