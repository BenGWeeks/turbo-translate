"""Global hotkey handling."""

import os
import platform
import threading
from typing import Callable


def is_wayland() -> bool:
    """Check if running on Wayland."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    return session_type == "wayland" or bool(wayland_display)


class HotkeyManager:
    """Cross-platform hotkey manager using pynput."""

    def __init__(self, hotkey: str, callback: Callable[[], None]):
        """
        Initialize the hotkey manager.

        Args:
            hotkey: Hotkey string (e.g., "alt+space", "ctrl+shift+e")
            callback: Function to call when hotkey is pressed
        """
        self.hotkey = hotkey
        self.callback = callback
        self._listener = None
        self._pressed_keys: set = set()
        self._hotkey_keys: set = set()
        self._last_trigger = 0.0

        self._parse_hotkey()

    def _parse_hotkey(self):
        """Parse hotkey string into key set."""
        from pynput import keyboard

        key_map = {
            "alt": keyboard.Key.alt,
            "ctrl": keyboard.Key.ctrl,
            "control": keyboard.Key.ctrl,
            "shift": keyboard.Key.shift,
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "esc": keyboard.Key.esc,
            "escape": keyboard.Key.esc,
        }

        # Add function keys
        for i in range(1, 13):
            key_map[f"f{i}"] = getattr(keyboard.Key, f"f{i}")

        self._hotkey_keys = set()
        for part in self.hotkey.lower().split("+"):
            part = part.strip()
            if part in key_map:
                self._hotkey_keys.add(key_map[part])
            elif len(part) == 1:
                self._hotkey_keys.add(keyboard.KeyCode.from_char(part))

    def start(self):
        """Start listening for hotkey."""
        from pynput import keyboard

        def on_press(key):
            # Normalize key
            if hasattr(key, "value"):
                key = key.value
            self._pressed_keys.add(key)

            # Check if hotkey is pressed
            if self._hotkey_keys.issubset(self._pressed_keys):
                import time

                now = time.time()
                # Debounce
                if now - self._last_trigger > 0.3:
                    self._last_trigger = now
                    self.callback()

        def on_release(key):
            # Normalize key
            if hasattr(key, "value"):
                key = key.value
            self._pressed_keys.discard(key)

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def stop(self):
        """Stop listening for hotkey."""
        if self._listener:
            self._listener.stop()
            self._listener = None


def create_hotkey_manager(hotkey: str, callback: Callable[[], None]) -> HotkeyManager:
    """Create appropriate hotkey manager for the platform."""
    return HotkeyManager(hotkey, callback)
