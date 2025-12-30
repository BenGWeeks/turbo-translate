"""Animated waveform orb widget with blue theme."""

import math
import random

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Animated blob-style waveform visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)

        # Colors - Blue theme
        self._primary_color = QColor("#3b82f6")  # Blue
        self._glow_color = QColor("#60a5fa")  # Light blue
        self._bg_color = QColor("#0f172a")  # Dark blue

        # Animation state
        self._level = 0.0
        self._target_level = 0.0
        self._phase = 0.0
        self._is_listening = False
        self._is_processing = False

        # Blob parameters
        self._num_points = 32
        self._base_radius = 0.35
        self._noise_offsets = [random.random() * 100 for _ in range(self._num_points)]

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(16)  # ~60 FPS

    def set_colors(self, primary: str, glow: str, background: str):
        """Set the color scheme."""
        self._primary_color = QColor(primary)
        self._glow_color = QColor(glow)
        self._bg_color = QColor(background)
        self.update()

    def set_level(self, level: float):
        """Set the audio level (0.0 to 1.0)."""
        self._target_level = max(0.0, min(1.0, level))

    def set_listening(self, listening: bool):
        """Set whether actively listening."""
        self._is_listening = listening
        self.update()

    def set_processing(self, processing: bool):
        """Set whether processing audio."""
        self._is_processing = processing
        self.update()

    def _update_animation(self):
        """Update animation state."""
        # Smooth level transition
        self._level += (self._target_level - self._level) * 0.15

        # Decay level if not listening
        if not self._is_listening:
            self._target_level *= 0.95

        # Advance phase
        self._phase += 0.02
        if self._phase > math.pi * 2:
            self._phase -= math.pi * 2

        self.update()

    def _noise(self, x: float, offset: float) -> float:
        """Simple noise function for organic movement."""
        return math.sin(x + offset) * 0.5 + math.sin(x * 2.3 + offset * 1.7) * 0.3

    def paintEvent(self, event):
        """Paint the waveform visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get dimensions
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        size = min(w, h)

        # Fill background
        painter.fillRect(self.rect(), self._bg_color)

        # Calculate blob points
        points = []
        for i in range(self._num_points):
            angle = (i / self._num_points) * math.pi * 2

            # Base radius
            radius = self._base_radius * size

            # Add audio-reactive deformation
            if self._is_listening:
                # Multiple frequency components
                wave1 = math.sin(angle * 3 + self._phase * 2) * self._level * 0.15
                wave2 = math.sin(angle * 5 - self._phase * 3) * self._level * 0.1
                wave3 = self._noise(self._phase * 2 + i * 0.5, self._noise_offsets[i]) * 0.05

                radius *= 1 + wave1 + wave2 + wave3

                # Breathing effect
                radius *= 1 + math.sin(self._phase) * 0.02
            elif self._is_processing:
                # Pulsing effect when processing
                pulse = math.sin(self._phase * 3) * 0.1
                radius *= 1 + pulse
            else:
                # Subtle idle animation
                radius *= 1 + math.sin(self._phase + i * 0.2) * 0.02

            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            points.append(QPointF(x, y))

        # Create smooth path through points
        path = self._create_smooth_path(points)

        # Draw layers for depth effect
        layers = [
            (1.3, 0.1),  # Outer glow
            (1.15, 0.2),  # Mid glow
            (1.0, 1.0),  # Main blob
        ]

        for scale, alpha in layers:
            scaled_path = self._scale_path(path, cx, cy, scale)

            if scale == 1.0:
                # Main blob with gradient
                gradient = QRadialGradient(cx, cy, size * 0.4)
                gradient.setColorAt(0, self._lighten(self._primary_color, 0.3))
                gradient.setColorAt(0.7, self._primary_color)
                gradient.setColorAt(1, self._darken(self._primary_color, 0.3))

                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
            else:
                # Glow layers
                glow = QColor(self._glow_color)
                glow.setAlphaF(alpha * 0.3)
                painter.setBrush(QBrush(glow))
                painter.setPen(Qt.PenStyle.NoPen)

            painter.drawPath(scaled_path)

        # Draw status indicator
        if self._is_listening:
            self._draw_status_dot(painter, cx, cy + size * 0.25, "#22c55e")  # Green
        elif self._is_processing:
            self._draw_status_dot(painter, cx, cy + size * 0.25, "#f59e0b")  # Orange

    def _create_smooth_path(self, points: list[QPointF]) -> QPainterPath:
        """Create a smooth closed path through points using Bezier curves."""
        if len(points) < 3:
            return QPainterPath()

        path = QPainterPath()
        n = len(points)

        # Start at first point
        path.moveTo(points[0])

        for i in range(n):
            p0 = points[(i - 1) % n]
            p1 = points[i]
            p2 = points[(i + 1) % n]
            p3 = points[(i + 2) % n]

            # Calculate control points
            tension = 0.3
            cp1 = QPointF(
                p1.x() + (p2.x() - p0.x()) * tension,
                p1.y() + (p2.y() - p0.y()) * tension,
            )
            cp2 = QPointF(
                p2.x() - (p3.x() - p1.x()) * tension,
                p2.y() - (p3.y() - p1.y()) * tension,
            )

            path.cubicTo(cp1, cp2, p2)

        path.closeSubpath()
        return path

    def _scale_path(self, path: QPainterPath, cx: float, cy: float, scale: float) -> QPainterPath:
        """Scale a path around a center point."""
        from PyQt6.QtGui import QTransform

        transform = QTransform()
        transform.translate(cx, cy)
        transform.scale(scale, scale)
        transform.translate(-cx, -cy)
        return transform.map(path)

    def _draw_status_dot(self, painter: QPainter, x: float, y: float, color: str):
        """Draw a small status indicator dot."""
        dot_color = QColor(color)
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x, y), 5, 5)

    def _lighten(self, color: QColor, amount: float) -> QColor:
        """Lighten a color."""
        h, s, l, a = color.getHslF()
        l = min(1.0, l + amount)
        result = QColor()
        result.setHslF(h, s, l, a)
        return result

    def _darken(self, color: QColor, amount: float) -> QColor:
        """Darken a color."""
        h, s, l, a = color.getHslF()
        l = max(0.0, l - amount)
        result = QColor()
        result.setHslF(h, s, l, a)
        return result
