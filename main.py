"""
HOE Billing Software - Main Entry Point
Version 1.0
Hari Om Electric, Lalpura Mode, Jaipur
"""
import sys
import os
import traceback

# Project root ko path mein add karo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt


def main():
    # ── High DPI support ──────────────────────────────────────────────────
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("HOE Billing Software")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Hari Om Electric")

    # ── Default font ──────────────────────────────────────────────────────
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── App icon set karo ─────────────────────────────────────────────────
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.ico")

    # Agar icon nahi hai to create karo
    if not os.path.exists(icon_path):
        try:
            os.makedirs(os.path.join(base_dir, "assets"), exist_ok=True)
            _create_icon(icon_path)
        except Exception:
            pass

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # ── Folders ensure karo ───────────────────────────────────────────────
    for folder in ["invoices", "backups", "assets"]:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    # ── Database initialize ───────────────────────────────────────────────
    try:
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.initialize()
    except Exception as e:
        QMessageBox.critical(None, "Database Error",
                             f"Database initialize nahi ho saki:\n\n{str(e)}\n\n"
                             f"Software band ho raha hai.")
        sys.exit(1)

    # ── Theme apply karo ──────────────────────────────────────────────────
    try:
        from utils.theme_manager import ThemeManager
        theme_mgr = ThemeManager()
        theme_mgr.apply_theme(app, db.get_setting("theme", "light"))
    except Exception:
        pass  # Theme error pe crash mat karo

    # ── Login window dikhao ───────────────────────────────────────────────
    try:
        from views.login_window import LoginWindow
        login = LoginWindow(db)
        login.show()
    except Exception as e:
        QMessageBox.critical(None, "Startup Error",
                             f"Login window nahi khuli:\n\n{str(e)}")
        sys.exit(1)

    sys.exit(app.exec_())


def _create_icon(path):
    """Runtime pe simple HOE icon banao — koi extra library nahi chahiye."""
    import struct

    width, height = 32, 32
    pixels = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = 26, 42, 74, 255          # Navy background
            if 3 <= x <= 28 and 3 <= y <= 28:
                r, g, b = 255, 255, 255            # White area
                # H
                if 5 <= x <= 7 and 7 <= y <= 24:  r,g,b = 26,42,74
                if 14 <= x <= 16 and 7 <= y <= 24: r,g,b = 26,42,74
                if 5 <= x <= 16 and 14 <= y <= 16: r,g,b = 26,42,74
                # O
                if 18 <= x <= 26 and 7 <= y <= 24:  r,g,b = 26,42,74
                if 20 <= x <= 24 and 9 <= y <= 22:  r,g,b = 255,255,255
            pixels.append((r, g, b, a))

    bmp = bytearray()
    bmp += struct.pack('<I', 40)
    bmp += struct.pack('<i', width)
    bmp += struct.pack('<i', height * 2)
    bmp += struct.pack('<H', 1)
    bmp += struct.pack('<H', 32)
    bmp += struct.pack('<I', 0)
    bmp += struct.pack('<I', width * height * 4)
    bmp += struct.pack('<i', 0) * 4

    for y in range(height - 1, -1, -1):
        for x in range(width):
            r, g, b, a = pixels[y * width + x]
            bmp += struct.pack('BBBB', b, g, r, a)

    mask_row = ((width + 31) // 32) * 4
    bmp += bytes(mask_row * height)

    ico_header = struct.pack('<HHH', 0, 1, 1)
    offset = 6 + 16
    dir_entry = struct.pack('<BBBBHHII', width, height, 0, 0, 1, 32, len(bmp), offset)

    with open(path, 'wb') as f:
        f.write(ico_header + dir_entry + bytes(bmp))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Last resort error — console pe print karo
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Critical Error", str(e))
        except Exception:
            pass
        sys.exit(1)
