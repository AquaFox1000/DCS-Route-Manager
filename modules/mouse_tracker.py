try:
    from pynput.mouse import Controller
    _mouse = Controller()
    HAS_MOUSE = True
except ImportError:
    _mouse = None
    HAS_MOUSE = False
    print("⚠️ pynput not found. Mouse tracking disabled.")

class MouseTracker:
    @staticmethod
    def get_cursor_position():
        """
        Returns the global (x, y) screen coordinates of the mouse.
        Returns None if pynput is not active.
        """
        if HAS_MOUSE and _mouse:
            return _mouse.position
        return None