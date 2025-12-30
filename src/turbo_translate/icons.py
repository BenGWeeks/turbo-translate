"""SVG icons for the application."""

from PyQt6.QtCore import QByteArray, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer


def _svg_to_icon(svg_data: str, color: str = "#888888", size: int = 20) -> QIcon:
    """Convert SVG string to QIcon with color replacement."""
    svg_data = svg_data.replace('stroke="currentColor"', f'stroke="{color}"')
    svg_data = svg_data.replace('fill="currentColor"', f'fill="{color}"')

    renderer = QSvgRenderer(QByteArray(svg_data.encode()))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill()

    from PyQt6.QtGui import QPainter
    from PyQt6.QtCore import Qt

    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


# Lucide icons (MIT License)
ICON_SETTINGS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'''

ICON_MIC = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" x2="12" y1="19" y2="22"></line></svg>'''

ICON_MIC_OFF = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="2" x2="22" y1="2" y2="22"></line><path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"></path><path d="M5 10v2a7 7 0 0 0 12 5"></path><path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"></path><path d="M9 9v3a3 3 0 0 0 5.12 2.12"></path><line x1="12" x2="12" y1="19" y2="22"></line></svg>'''

ICON_VOLUME = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>'''

ICON_VOLUME_OFF = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="22" x2="16" y1="9" y2="15"></line><line x1="16" x2="22" y1="9" y2="15"></line></svg>'''

ICON_USER = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'''

ICON_USERS = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'''

ICON_LANGUAGES = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 8 6 6"></path><path d="m4 14 6-6 2-3"></path><path d="M2 5h12"></path><path d="M7 2h1"></path><path d="m22 22-5-10-5 10"></path><path d="M14 18h6"></path></svg>'''

ICON_CLEAR = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>'''

ICON_POWER = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" x2="12" y1="2" y2="12"></line></svg>'''

ICON_CHEVRON_DOWN = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"></path></svg>'''

ICON_CHEVRON_UP = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"></path></svg>'''


def get_settings_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_SETTINGS, color, size)


def get_mic_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_MIC, color, size)


def get_mic_off_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_MIC_OFF, color, size)


def get_volume_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_VOLUME, color, size)


def get_volume_off_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_VOLUME_OFF, color, size)


def get_user_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_USER, color, size)


def get_users_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_USERS, color, size)


def get_languages_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_LANGUAGES, color, size)


def get_clear_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_CLEAR, color, size)


def get_power_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_POWER, color, size)


def get_chevron_down_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_CHEVRON_DOWN, color, size)


def get_chevron_up_icon(color: str = "#888888", size: int = 20) -> QIcon:
    return _svg_to_icon(ICON_CHEVRON_UP, color, size)


def get_tray_icon(listening: bool = False, size: int = 64) -> QIcon:
    """Generate system tray icon - blue orb."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPainter, QRadialGradient, QBrush

    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy = size / 2, size / 2
    radius = size * 0.4

    # Create gradient
    gradient = QRadialGradient(cx, cy, radius)

    if listening:
        # Bright blue when listening
        gradient.setColorAt(0, QColor("#93c5fd"))
        gradient.setColorAt(0.7, QColor("#3b82f6"))
        gradient.setColorAt(1, QColor("#1d4ed8"))
    else:
        # Dimmer blue when idle
        gradient.setColorAt(0, QColor("#60a5fa"))
        gradient.setColorAt(0.7, QColor("#2563eb"))
        gradient.setColorAt(1, QColor("#1e40af"))

    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

    painter.end()

    return QIcon(pixmap)


# Import QColor here to avoid issues
from PyQt6.QtGui import QColor
