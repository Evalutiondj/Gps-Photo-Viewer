import sys
import os
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QListWidget, QFrame, QSplitter, QFileDialog,
                              QMessageBox, QLineEdit, QRadioButton, QButtonGroup, QScrollArea,
                              QGroupBox, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect, 
                              QComboBox, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QPixmap, QImage, QTransform, QFont, QPainter, QColor, QPalette, QIcon, QAction
from collections import OrderedDict

# Import libraries
try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False

try:
    from PIL import Image, ImageOps
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False


# Windows 11 Fluent Design System QSS
FLUENT_STYLE = """
/* ========== GLOBAL ========== */
* {
    font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 9pt;
    outline: none;
}

QMainWindow {
    background-color: #f3f3f3;
}

QWidget {
    color: #1a1a1a;
    background-color: transparent;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #0067C0;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-weight: 500;
    min-width: 60px;
}

QPushButton:hover {
    background-color: #0078D4;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #e0e0e0;
    color: #949494;
}

/* Secondary Button */
QPushButton#secondaryButton {
    background-color: #f3f3f3;
    color: #1a1a1a;
    border: 1px solid #d0d0d0;
    padding: 6px 10px;
}

QPushButton#secondaryButton:hover {
    background-color: #e8e8e8;
    border-color: #c0c0c0;
}

QPushButton#secondaryButton:pressed {
    background-color: #d8d8d8;
}

/* Filter Button (Default state) */
QPushButton#filterButton {
    background-color: #f3f3f3;
    color: #1a1a1a;
    border: 1px solid #d0d0d0;
    padding: 5px 8px;
}

QPushButton#filterButton:hover {
    background-color: #e8e8e8;
    border-color: #b0b0b0;
}

QPushButton#filterButton:pressed {
    background-color: #d8d8d8;
}

/* Filter Button Active State */
QPushButton#filterButtonActive {
    background-color: #0067C0;
    color: white;
    border: 1px solid #0067C0;
    padding: 5px 8px;
}

QPushButton#filterButtonActive:hover {
    background-color: #0078D4;
    border-color: #0078D4;
}

/* Success Button */
QPushButton#successButton {
    background-color: #0F7B0F;
    padding: 6px 10px;
}

QPushButton#successButton:hover {
    background-color: #107C10;
}

/* Danger Button */
QPushButton#dangerButton {
    background-color: #C42B1C;
    padding: 6px 10px;
}

QPushButton#dangerButton:hover {
    background-color: #D13438;
}

/* Accent Button */
QPushButton#accentButton {
    background-color: #8764B8;
    padding: 6px 10px;
}

QPushButton#accentButton:hover {
    background-color: #9775C4;
}

/* ========== COMBO BOX ========== */
QComboBox {
    background-color: white;
    color: #1a1a1a;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px 12px;
    padding-right: 30px;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #b0b0b0;
}

QComboBox:focus {
    border-color: #0067C0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #d0d0d0;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #606060;
    margin-right: 5px;
}

QComboBox::down-arrow:hover {
    border-top-color: #0067C0;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    selection-background-color: #0067C0;
    selection-color: white;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    min-height: 25px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f0f0f0;
}

/* ========== INPUT FIELDS ========== */
QLineEdit {
    background-color: white;
    color: #1a1a1a;
    border: 1px solid #d0d0d0;
    border-bottom: 2px solid #d0d0d0;
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: #0067C0;
    selection-color: white;
}

QLineEdit:hover {
    border-bottom-color: #b0b0b0;
}

QLineEdit:focus {
    border-bottom-color: #0067C0;
    background-color: #ffffff;
}

/* ========== LIST WIDGET ========== */
QListWidget {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 4px;
    color: #1a1a1a;
}

QListWidget::item {
    border-radius: 4px;
    padding: 8px;
    margin: 1px 0px;
    color: #1a1a1a;
}

QListWidget::item:hover {
    background-color: #f5f5f5;
}

QListWidget::item:selected {
    background-color: #0067C0;
    color: white;
}

QListWidget::item:selected:hover {
    background-color: #0078D4;
}

/* ========== GROUP BOX ========== */
QGroupBox {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 6px;
    padding: 6px 6px 6px 6px;
    font-weight: 600;
    font-size: 8.5pt;
    color: #1a1a1a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    top: 2px;
    padding: 0 6px;
    background-color: white;
    color: #1a1a1a;
}

/* ========== SCROLL AREA ========== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ========== FRAMES ========== */
QFrame#imageFrame {
    background-color: #1a1a1a;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

QFrame#toolbarFrame {
    background-color: #2d2d2d;
    border-radius: 6px;
}

QFrame#statusFrame {
    background-color: #2d2d2d;
    border-radius: 4px;
}

/* ========== LABELS ========== */
QLabel {
    color: #1a1a1a;
}

QLabel#toolLabel {
    color: white;
    background: transparent;
}

QLabel#statusLabel {
    color: #e5e5e5;
    background: transparent;
}

QLabel#infoKeyLabel {
    color: #606060;
    font-weight: 600;
    font-size: 8pt;
}

QLabel#infoValueLabel {
    color: #1a1a1a;
    font-size: 8.5pt;
}

/* ========== SPLITTER ========== */
QSplitter::handle {
    background-color: #e0e0e0;
    width: 1px;
    height: 1px;
}

QSplitter::handle:hover {
    background-color: #0067C0;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #f8f8f8;
    border-bottom: 1px solid #e0e0e0;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: #1a1a1a;
}

QMenuBar::item:selected {
    background-color: #e8e8e8;
}

QMenuBar::item:pressed {
    background-color: #d8d8d8;
}

QMenu {
    background-color: white;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
    color: #1a1a1a;
}

QMenu::item:selected {
    background-color: #0067C0;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #e0e0e0;
    margin: 4px 8px;
}

/* ========== MESSAGE BOX ========== */
QMessageBox {
    background-color: white;
}

QMessageBox QLabel {
    color: #1a1a1a;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""


class AddressLoader(QThread):
    result = pyqtSignal(str)
    
    def __init__(self, lat, lon):
        super().__init__()
        self.lat = lat
        self.lon = lon
        self._is_running = True  # ✅ Thêm flag
    
    def run(self):
        if not GEOPY_AVAILABLE:
            self.result.emit("⚠️ Chưa cài thư viện geopy")
            return
        try:
            if not self._is_running:  # ✅ Check trước khi chạy
                return
            geo = Nominatim(user_agent="geosnap_v2", timeout=10)
            loc = geo.reverse(f"{self.lat}, {self.lon}", language='vi')
            if self._is_running:  # ✅ Check trước khi emit
                self.result.emit(loc.address if loc else "❌ Không tìm thấy địa chỉ")
        except Exception as e:
            if self._is_running:
                self.result.emit(f"❌ Lỗi: {str(e)[:40]}")
    
    def stop(self):
        """Stop thread gracefully"""
        self._is_running = False


class FluentButton(QPushButton):
    """Custom button with hover animation"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


class ImageViewer(QLabel):
    """Fluent Design image viewer"""
    MIN_ZOOM = 0.05  # 5%
    MAX_ZOOM = 20.0  # 2000%
    ZOOM_STEP = 1.15

    def __init__(self):
        super().__init__()
        
        self.original_pixmap = None
        self.scale = 1.0
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False
        self.drag_start = None
        
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        
        self.placeholder_text = "📸 Kéo thả ảnh vào đây\nhoặc nhấn 'Thêm ảnh'"
        
        # Zoom callback
        self.zoom_callback = None
        
        self.setObjectName("imageFrame")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def load_image(self, path):
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            data = img.tobytes('raw', 'RGB')
            qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            self.original_pixmap = QPixmap.fromImage(qimg)
            
            self.rotation = 0
            self.flip_h = False
            self.flip_v = False
            self.fit_to_screen()
            return True
        except Exception as e:
            print(f"Error: {e}")
            self.original_pixmap = None
            self.update()
            return False
    
    def get_transformed_pixmap(self):
        if not self.original_pixmap:
            return None
        
        pixmap = self.original_pixmap
        
        if self.rotation != 0 or self.flip_h or self.flip_v:
            transform = QTransform()
            transform.translate(pixmap.width() / 2, pixmap.height() / 2)
            
            if self.rotation:
                transform.rotate(self.rotation)
            if self.flip_h:
                transform.scale(-1, 1)
            if self.flip_v:
                transform.scale(1, -1)
            
            transform.translate(-pixmap.width() / 2, -pixmap.height() / 2)
            pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        return pixmap
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.original_pixmap:
            painter = QPainter(self)
            painter.setPen(QColor(150, 150, 150))
            font = QFont("Segoe UI Variable", 12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.placeholder_text)
            painter.end()
    
    def render(self):
        if not self.original_pixmap:
            self.setText("")
            self.update()
            return
        
        pixmap = self.get_transformed_pixmap()
        if not pixmap:
            return
        
        scaled_w = int(pixmap.width() * self.scale)
        scaled_h = int(pixmap.height() * self.scale)
        
        if scaled_w > 0 and scaled_h > 0:
            scaled = pixmap.scaled(
                scaled_w, scaled_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)
    
    def fit_to_screen(self):
        if not self.original_pixmap:
            return
        
        pixmap = self.get_transformed_pixmap()
        w_ratio = (self.width() - 30) / pixmap.width()
        h_ratio = (self.height() - 30) / pixmap.height()
        self.scale = min(w_ratio, h_ratio, 1.0)
        self.render()
        if self.zoom_callback:
            self.zoom_callback()
    
    def zoom_in(self):
        self.scale *= 1.15
        self.scale = min(self.scale, 10.0)
        self.render()
        if self.zoom_callback:
            self.zoom_callback()
    
    def zoom_out(self):
        self.scale /= 1.15
        self.scale = max(self.scale, 0.1)
        self.render()
        if self.zoom_callback:
            self.zoom_callback()
    
    def actual_size(self):
        self.scale = 1.0
        self.render()
        if self.zoom_callback:
            self.zoom_callback()
    
    def set_zoom_callback(self, callback):
        """Set callback to update zoom label"""
        self.zoom_callback = callback
    
    def flip_horizontal(self):
        self.flip_h = not self.flip_h
        self.render()
    
    def flip_vertical(self):
        self.flip_v = not self.flip_v
        self.render()
    
    def rotate_right(self):
        self.rotation = (self.rotation + 90) % 360
        self.fit_to_screen()
    
    def rotate_left(self):
        self.rotation = (self.rotation - 90) % 360
        self.fit_to_screen()
    
    def wheelEvent(self, event):
        if not self.original_pixmap:
            return
        
        factor = 1.1 if event.angleDelta().y() > 0 else 1/1.1
        self.scale *= factor
        self.scale = max(0.1, min(self.scale, 10.0))
        self.render()
        if self.zoom_callback:
            self.zoom_callback()
        event.accept()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.original_pixmap:
            self.drag_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        if self.drag_start:
            pass  # Pan functionality can be added here
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = None
            self.setCursor(Qt.CursorShape.CrossCursor)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Don't auto-fit on resize to prevent zoom reset
        pass

class LimitedCache:
    def __init__(self, max_size=500):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key, default=None):
        if key in self.cache:
            self.cache.move_to_end(key)  # Move to end (most recent)
            return self.cache[key]
        return default
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)  # Remove oldest
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()
        
class GeoSnap(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoSnap - GPS Photo Viewer")
        self.setGeometry(80, 40, 1450, 880)
        self.setMinimumSize(1100, 650)
        
        # Set window icon
        icon_path = Path(__file__).parent / "logo.ico"
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.image_list = []
        self.display_list = []
        self.filtered_list = []
        self.current_index = -1
        self.is_filtered = False
        self.gps_cache = LimitedCache(max_size=500)
        self.exif_cache = LimitedCache(max_size=500)
        self.current_gps = None
        self.address_loader = None
        
        # Filter button tracking
        self.active_filter_btn = None
        
        # Theme tracking
        self.is_dark_theme = False
        
        self.init_ui()
        
        # Apply initial theme AFTER UI is created
        self.apply_theme()
    
    def init_ui(self):
        # Create menu bar
        self.create_menu_bar()
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Main splitter (No header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setChildrenCollapsible(False)
        
        # Panels
        left_panel = self.create_left_panel()
        middle_panel = self.create_middle_panel()
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([360, 730, 360])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter, stretch=1)
        
        # Status bar with Fluent style
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 6, 16, 6)
        
        libs_text = f"● exif: {'✓' if EXIFREAD_AVAILABLE else '✗'}  ● heic: {'✓' if HEIC_SUPPORTED else '✗'}  ● map: {'✓' if FOLIUM_AVAILABLE else '✗'}  ● geo: {'✓' if GEOPY_AVAILABLE else '✗'}"
        libs_label = QLabel(libs_text)
        libs_label.setObjectName("statusLabel")
        libs_label.setStyleSheet("color: #b5b5b5; font-size: 8pt;")
        status_layout.addWidget(libs_label)
        
        status_layout.addStretch()
        
        self.status_right = QLabel()
        self.status_right.setObjectName("statusLabel")
        self.status_right.setStyleSheet("color: #e5e5e5; font-size: 8pt; font-weight: 500;")
        status_layout.addWidget(self.status_right)
        
        main_layout.addWidget(status_frame)
        
        self.setAcceptDrops(True)
    
    def create_menu_bar(self):
        """Create professional menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        
        add_action = QAction("➕ Thêm ảnh", self)
        add_action.setShortcut("Ctrl+O")
        add_action.triggered.connect(self.add_images)
        file_menu.addAction(add_action)
        
        folder_action = QAction("📂 Thêm thư mục", self)
        folder_action.setShortcut("Ctrl+Shift+O")
        folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Thoát", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("👁️ View")
        
        self.theme_action = QAction("🌙 Chế độ tối", self)
        self.theme_action.setShortcut("Ctrl+T")
        self.theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.theme_action)
        
        fullscreen_action = QAction("⛶ Toàn màn hình", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        
        about_action = QAction("ℹ️ Về GeoSnap", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()
        
        # Update menu text
        if self.is_dark_theme:
            self.theme_action.setText("☀️ Chế độ sáng")
        else:
            self.theme_action.setText("🌙 Chế độ tối")
        
        # Reapply filter button states if active
        if self.active_filter_btn:
            self.active_filter_btn.setObjectName("filterButtonActive")
            self.active_filter_btn.setStyleSheet("")

        self.update_list_status()
    
    def apply_theme(self):
        """Apply current theme"""
        if self.is_dark_theme:
            self.setStyleSheet(self.get_dark_theme())
            
            # Dark palette
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
            dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(229, 229, 229))
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(229, 229, 229))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor(229, 229, 229))
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(229, 229, 229))
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(0, 103, 192))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 103, 192))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            
            # Disabled
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
            
            self.setPalette(dark_palette)
            QApplication.instance().setPalette(dark_palette)
        else:
            self.setStyleSheet(FLUENT_STYLE)
            
            # Light palette - force it completely
            light_palette = QPalette()
            light_palette.setColor(QPalette.ColorRole.Window, QColor(243, 243, 243))
            light_palette.setColor(QPalette.ColorRole.WindowText, QColor(26, 26, 26))
            light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
            light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
            light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(26, 26, 26))
            light_palette.setColor(QPalette.ColorRole.Text, QColor(26, 26, 26))
            light_palette.setColor(QPalette.ColorRole.Button, QColor(243, 243, 243))
            light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(26, 26, 26))
            light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 103, 192))
            light_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 103, 192))
            light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            
            # Disabled
            light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(148, 148, 148))
            light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(148, 148, 148))
            light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(148, 148, 148))
            light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(235, 235, 235))
            
            self.setPalette(light_palette)
            QApplication.instance().setPalette(light_palette)
        
        # Force repaint
        self.update()
        QApplication.processEvents()
    
    def get_dark_theme(self):
        """Get dark theme stylesheet - matched with light theme structure"""
        return """
/* ========== DARK THEME ========== */
* {
    font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 9pt;
    outline: none;
}

QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    color: #e5e5e5;
    background-color: transparent;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #0067C0;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #0078D4;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #3a3a3a;
    color: #808080;
}

QPushButton#secondaryButton {
    background-color: #3d3d3d;
    color: #e5e5e5;
    border: 1px solid #4d4d4d;
}

QPushButton#secondaryButton:hover {
    background-color: #4d4d4d;
    border-color: #5d5d5d;
}

QPushButton#secondaryButton:pressed {
    background-color: #353535;
}

QPushButton#filterButton {
    background-color: #3d3d3d;
    color: #e5e5e5;
    border: 1px solid #4d4d4d;
}

QPushButton#filterButton:hover {
    background-color: #4d4d4d;
    border-color: #5d5d5d;
}

QPushButton#filterButton:pressed {
    background-color: #353535;
}

QPushButton#filterButtonActive {
    background-color: #0067C0;
    color: white;
    border: 1px solid #0067C0;
}

QPushButton#filterButtonActive:hover {
    background-color: #0078D4;
    border-color: #0078D4;
}

QPushButton#successButton {
    background-color: #0F7B0F;
}

QPushButton#successButton:hover {
    background-color: #107C10;
}

QPushButton#dangerButton {
    background-color: #C42B1C;
}

QPushButton#dangerButton:hover {
    background-color: #D13438;
}

QPushButton#accentButton {
    background-color: #8764B8;
}

QPushButton#accentButton:hover {
    background-color: #9775C4;
}

/* ========== COMBO BOX ========== */
QComboBox {
    background-color: #2d2d2d;
    color: #e5e5e5;
    border: 1px solid #4d4d4d;
    border-radius: 4px;
    padding: 6px 12px;
    padding-right: 30px;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #5d5d5d;
}

QComboBox:focus {
    border-color: #0067C0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #4d4d4d;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #b0b0b0;
    margin-right: 5px;
}

QComboBox::down-arrow:hover {
    border-top-color: #0067C0;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #4d4d4d;
    border-radius: 4px;
    selection-background-color: #0067C0;
    selection-color: white;
    color: #e5e5e5;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    min-height: 25px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #3d3d3d;
}

/* ========== INPUT FIELDS ========== */
QLineEdit {
    background-color: #2d2d2d;
    color: #e5e5e5;
    border: 1px solid #4d4d4d;
    border-bottom: 2px solid #4d4d4d;
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: #0067C0;
    selection-color: white;
}

QLineEdit:hover {
    border-bottom-color: #5d5d5d;
}

QLineEdit:focus {
    border-bottom-color: #0067C0;
    background-color: #2d2d2d;
}

/* ========== LIST WIDGET ========== */
QListWidget {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 4px;
    color: #e5e5e5;
}

QListWidget::item {
    border-radius: 4px;
    padding: 8px;
    margin: 1px 0px;
    color: #e5e5e5;
}

QListWidget::item:hover {
    background-color: #3d3d3d;
}

QListWidget::item:selected {
    background-color: #0067C0;
    color: white;
}

QListWidget::item:selected:hover {
    background-color: #0078D4;
}

/* ========== GROUP BOX ========== */
QGroupBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    margin-top: 6px;
    padding: 6px 6px 6px 6px;
    font-weight: 600;
    font-size: 8.5pt;
    color: #e5e5e5;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    top: 2px;
    padding: 0 6px;
    background-color: #2d2d2d;
    color: #e5e5e5;
}

/* ========== SCROLL AREA ========== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #4d4d4d;
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5d5d5d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ========== FRAMES ========== */
QFrame#imageFrame {
    background-color: #0a0a0a;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
}

QFrame#toolbarFrame {
    background-color: #1a1a1a;
    border-radius: 6px;
}

QFrame#statusFrame {
    background-color: #1a1a1a;
    border-radius: 4px;
}

/* ========== LABELS ========== */
QLabel {
    color: #e5e5e5;
}

QLabel#toolLabel {
    color: white;
    background: transparent;
}

QLabel#statusLabel {
    color: #e5e5e5;
    background: transparent;
}

QLabel#infoKeyLabel {
    color: #b0b0b0;
    font-weight: 600;
    font-size: 8pt;
}

QLabel#infoValueLabel {
    color: #e5e5e5;
    font-size: 8.5pt;
}

/* ========== SPLITTER ========== */
QSplitter::handle {
    background-color: #3d3d3d;
    width: 1px;
    height: 1px;
}

QSplitter::handle:hover {
    background-color: #0067C0;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3d3d3d;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    color: #e5e5e5;
}

QMenuBar::item:selected {
    background-color: #3d3d3d;
}

QMenuBar::item:pressed {
    background-color: #353535;
}

QMenu {
    background-color: #2d2d2d;
    border: 1px solid #4d4d4d;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
    color: #e5e5e5;
}

QMenu::item:selected {
    background-color: #0067C0;
    color: white;
}

QMenu::separator {
    height: 1px;
    background-color: #3d3d3d;
    margin: 4px 8px;
}

/* ========== MESSAGE BOX DARK ========== */
QMessageBox {
    background-color: #2d2d2d;
}

QMessageBox QLabel {
    color: #e5e5e5;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "Về GeoSnap", 
            "📍 <b>GeoSnap</b> v1.0<br><br>"
            "GPS Photo Viewer & Location Analyzer<br><br>"
            "Phát triển bởi PyQt6<br>"
            "© 2025 GeoSnap")
    
    def create_left_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(280)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        add_btn = FluentButton("➕ Thêm ảnh")
        add_btn.clicked.connect(self.add_images)
        add_btn.setMinimumHeight(38)
        btn_layout.addWidget(add_btn)
        
        folder_btn = FluentButton("📂 Thư mục")
        folder_btn.setObjectName("accentButton")
        folder_btn.clicked.connect(self.add_folder)
        folder_btn.setMinimumHeight(38)
        btn_layout.addWidget(folder_btn)
        
        clear_btn = FluentButton("🗑️")
        clear_btn.setObjectName("dangerButton")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setMaximumWidth(45)
        clear_btn.setMinimumHeight(38)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Search card
        search_group = self.create_card("🔍 Tìm kiếm")
        search_layout = QVBoxLayout()
        search_layout.setContentsMargins(8, 10, 8, 8)
        search_layout.setSpacing(0)
        search_group.setLayout(search_layout)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Nhập tên file...")
        self.search_box.textChanged.connect(self.on_search_change)
        self.search_box.setMinimumHeight(32)
        search_layout.addWidget(self.search_box)
        
        layout.addWidget(search_group)
        
        # Filter card
        filter_group = self.create_card("🎯 Bộ lọc")
        filter_layout = QGridLayout()
        filter_layout.setSpacing(6)
        filter_layout.setContentsMargins(8, 10, 8, 8)
        filter_group.setLayout(filter_layout)
        
        self.gps_btn = FluentButton("🌍 Có GPS")
        self.gps_btn.setObjectName("filterButton")
        self.gps_btn.clicked.connect(lambda: self.apply_filter_with_highlight('has_gps', self.gps_btn))
        self.gps_btn.setMinimumHeight(34)
        filter_layout.addWidget(self.gps_btn, 0, 0)
        
        self.no_gps_btn = FluentButton("❌ Không GPS")
        self.no_gps_btn.setObjectName("filterButton")
        self.no_gps_btn.clicked.connect(lambda: self.apply_filter_with_highlight('no_gps', self.no_gps_btn))
        self.no_gps_btn.setMinimumHeight(34)
        filter_layout.addWidget(self.no_gps_btn, 0, 1)
        
        self.camera_btn = FluentButton("📷 Camera")
        self.camera_btn.setObjectName("filterButton")
        self.camera_btn.clicked.connect(self.filter_by_camera)
        self.camera_btn.setMinimumHeight(34)
        filter_layout.addWidget(self.camera_btn, 1, 0)
        
        reset_btn = FluentButton("🔄 Đặt lại")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.clicked.connect(self.clear_filter)
        reset_btn.setMinimumHeight(34)
        filter_layout.addWidget(reset_btn, 1, 1)
        
        layout.addWidget(filter_group)
        
        # Sort card with ComboBox
        sort_group = self.create_card("📊 Sắp xếp")
        sort_layout = QVBoxLayout()
        sort_layout.setContentsMargins(8, 10, 8, 8)
        sort_layout.setSpacing(0)
        sort_group.setLayout(sort_layout)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("📝 Tên file", "name")
        self.sort_combo.addItem("📅 Ngày (mới → cũ)", "date_desc")
        self.sort_combo.addItem("📅 Ngày (cũ → mới)", "date_asc")
        self.sort_combo.addItem("💾 Kích thước", "size")
        self.sort_combo.currentIndexChanged.connect(self.sort_images)
        sort_layout.addWidget(self.sort_combo)
        
        layout.addWidget(sort_group)
        
        # List card
        list_group = self.create_card("📋 Danh sách ảnh")
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(8, 10, 8, 8)
        list_layout.setSpacing(6)
        list_group.setLayout(list_layout)
        
        self.listbox = QListWidget()
        self.listbox.currentRowChanged.connect(self.on_select)
        self.listbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        list_layout.addWidget(self.listbox)
        
        self.list_status = QLabel("0 ảnh")
        self.list_status.setStyleSheet("""
            background-color: #FFF4CE;
            color: #6B5300;
            border-radius: 4px;
            padding: 8px;
            font-weight: 600;
            font-size: 8.5pt;
        """)
        self.list_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        list_layout.addWidget(self.list_status)
        
        layout.addWidget(list_group, stretch=1)
        
        return panel
    
    def create_middle_panel(self):
        panel = QWidget()
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Viewer card
        viewer_group = self.create_card("🖼️ Xem ảnh")
        viewer_layout = QVBoxLayout()
        viewer_layout.setContentsMargins(12, 18, 12, 12)
        viewer_group.setLayout(viewer_layout)
        
        info_label = QLabel("💡 Zoom: Cuộn chuột  |  Di chuyển: Kéo thả  |  Phím tắt: ← →")
        info_label.setStyleSheet("color: #707070; font-size: 8pt; padding: 4px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        viewer_layout.addWidget(info_label)
        
        self.image_viewer = ImageViewer()
        viewer_layout.addWidget(self.image_viewer, stretch=1)
        
        # Set zoom callback
        self.image_viewer.set_zoom_callback(self.update_zoom_label)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setObjectName("toolbarFrame")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        toolbar_layout.setSpacing(10)
        
        toolbar_shadow = QGraphicsDropShadowEffect()
        toolbar_shadow.setBlurRadius(10)
        toolbar_shadow.setColor(QColor(0, 0, 0, 40))
        toolbar_shadow.setOffset(0, 2)
        toolbar.setGraphicsEffect(toolbar_shadow)
        
        tools = [
            ("🔍+", self.image_viewer.zoom_in),
            ("🔍−", self.image_viewer.zoom_out),
            ("⟲ Fit", self.image_viewer.fit_to_screen),
            ("100%", self.image_viewer.actual_size),
            ("↔️", self.image_viewer.flip_horizontal),
            ("↕️", self.image_viewer.flip_vertical),
            ("↻", self.image_viewer.rotate_right),
            ("↺", self.image_viewer.rotate_left)
        ]
        
        for text, func in tools:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
            """)
            btn.clicked.connect(func)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toolbar_layout.addWidget(btn)
        
        toolbar_layout.addStretch()
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("toolLabel")
        self.zoom_label.setStyleSheet("color: white; font-weight: 600; font-size: 10pt;")
        toolbar_layout.addWidget(self.zoom_label)
        
        viewer_layout.addWidget(toolbar)
        layout.addWidget(viewer_group, stretch=1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        self.prev_btn = FluentButton("⬅️ Ảnh trước")
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setMinimumHeight(48)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = FluentButton("Ảnh tiếp theo ➡️")
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setEnabled(False)
        self.next_btn.setMinimumHeight(48)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        return panel
    
    def create_right_panel(self):
        scroll = QScrollArea()
        scroll.setMinimumWidth(280)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File info card (2 columns)
        file_group = self.create_card("📄 Thông tin File")
        file_layout = QGridLayout()
        file_layout.setVerticalSpacing(6)
        file_layout.setHorizontalSpacing(8)
        file_layout.setContentsMargins(8, 10, 8, 8)
        file_group.setLayout(file_layout)
        
        self.file_labels = {}
        file_fields = [
            ("Tên:", 'file_name'),
            ("Kích thước:", 'file_size'),
            ("Định dạng:", 'file_format'),
            ("Độ phân giải:", 'image_dimensions'),
            ("Ngày tạo:", 'file_created'),
            ("Ngày sửa:", 'file_modified')
        ]
        
        for i, (label_text, key) in enumerate(file_fields):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            label.setObjectName("infoKeyLabel")
            file_layout.addWidget(label, row, col, Qt.AlignmentFlag.AlignLeft)
            
            value_label = QLabel("--")
            value_label.setObjectName("infoValueLabel")
            value_label.setWordWrap(True)
            self.file_labels[key] = value_label
            file_layout.addWidget(value_label, row, col + 1, Qt.AlignmentFlag.AlignLeft)
        
        file_layout.setColumnStretch(1, 1)
        file_layout.setColumnStretch(3, 1)
        
        layout.addWidget(file_group)
        
        # Camera info card (2 columns)
        camera_group = self.create_card("📷 Thông tin Camera")
        camera_layout = QGridLayout()
        camera_layout.setVerticalSpacing(6)
        camera_layout.setHorizontalSpacing(8)
        camera_layout.setContentsMargins(8, 10, 8, 8)
        camera_group.setLayout(camera_layout)
        
        self.camera_labels = {}
        camera_fields = [
            ("Camera:", 'camera_model'),
            ("Ống kính:", 'lens_model'),
            ("ISO:", 'iso'),
            ("Tốc độ:", 'shutter_speed'),
            ("Khẩu độ:", 'aperture'),
            ("Tiêu cự:", 'focal_length')
        ]
        
        for i, (label_text, key) in enumerate(camera_fields):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            label.setObjectName("infoKeyLabel")
            camera_layout.addWidget(label, row, col, Qt.AlignmentFlag.AlignLeft)
            
            value_label = QLabel("--")
            value_label.setObjectName("infoValueLabel")
            value_label.setWordWrap(True)
            self.camera_labels[key] = value_label
            camera_layout.addWidget(value_label, row, col + 1, Qt.AlignmentFlag.AlignLeft)
        
        camera_layout.setColumnStretch(1, 1)
        camera_layout.setColumnStretch(3, 1)
        
        layout.addWidget(camera_group)
        
        # GPS info card (2 columns)
        gps_group = self.create_card("📍 Tọa độ GPS")
        gps_layout = QGridLayout()
        gps_layout.setVerticalSpacing(6)
        gps_layout.setHorizontalSpacing(8)
        gps_layout.setContentsMargins(8, 10, 8, 8)
        gps_group.setLayout(gps_layout)
        
        self.gps_labels = {}
        gps_fields = [
            ("Vĩ độ:", 'lat'),
            ("Kinh độ:", 'lon'),
            ("Độ cao:", 'alt'),
            ("Thời gian:", 'time')
        ]
        
        for i, (label_text, key) in enumerate(gps_fields):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            label.setObjectName("infoKeyLabel")
            gps_layout.addWidget(label, row, col, Qt.AlignmentFlag.AlignLeft)
            
            value_label = QLabel("--")
            value_label.setObjectName("infoValueLabel")
            value_label.setWordWrap(True)
            self.gps_labels[key] = value_label
            gps_layout.addWidget(value_label, row, col + 1, Qt.AlignmentFlag.AlignLeft)
        
        gps_layout.setColumnStretch(1, 1)
        gps_layout.setColumnStretch(3, 1)
        
        layout.addWidget(gps_group)
        
        # Address card
        addr_group = self.create_card("🏠 Địa chỉ")
        addr_layout = QVBoxLayout()
        addr_layout.setContentsMargins(8, 10, 8, 8)
        addr_group.setLayout(addr_layout)
        
        self.addr_label = QLabel("--")
        self.addr_label.setObjectName("infoValueLabel")
        self.addr_label.setWordWrap(True)
        self.addr_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        addr_layout.addWidget(self.addr_label)
        
        layout.addWidget(addr_group)
        
        # Map buttons card
        map_group = self.create_card("🗺️ Xem bản đồ")
        map_layout = QGridLayout()
        map_layout.setSpacing(6)
        map_layout.setContentsMargins(8, 10, 8, 8)
        map_group.setLayout(map_layout)
        
        self.google_btn = FluentButton("🌍 Google Maps")
        self.google_btn.clicked.connect(self.open_google_maps)
        self.google_btn.setEnabled(False)
        self.google_btn.setMinimumHeight(40)
        map_layout.addWidget(self.google_btn, 0, 0, 1, 2)
        
        self.html_btn = FluentButton("📍 Bản đồ HTML")
        self.html_btn.setObjectName("successButton")
        self.html_btn.clicked.connect(self.open_html_map)
        self.html_btn.setEnabled(False)
        self.html_btn.setMinimumHeight(38)
        map_layout.addWidget(self.html_btn, 1, 0)
        
        self.all_map_btn = FluentButton("🗺️ Tất cả")
        self.all_map_btn.setObjectName("secondaryButton")
        self.all_map_btn.clicked.connect(self.show_all_on_map)
        self.all_map_btn.setMinimumHeight(38)
        map_layout.addWidget(self.all_map_btn, 1, 1)
        
        layout.addWidget(map_group)
        layout.addStretch()
        
        scroll.setWidget(panel)
        return scroll
    
    def create_card(self, title):
        """Create a Fluent Design card with shadow"""
        card = QGroupBox(title)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)
        return card
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            # ✅ Check file exists và readable
            if os.path.exists(path) and os.path.isfile(path):
                if Path(path).suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                    files.append(path)
        if files:
            self.load_images(files)
        else:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy ảnh hợp lệ")
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh", "",
            "Ảnh (*.jpg *.jpeg *.png *.heic *.heif);;Tất cả (*.*)"
        )
        if files:
            self.load_images(files)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh")
        if folder:
            files = []
            for ext in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                files.extend(Path(folder).rglob(f'*{ext}'))
                files.extend(Path(folder).rglob(f'*{ext.upper()}'))
            if files:
                self.load_images([str(f) for f in files])
            else:
                QMessageBox.information(self, "Thông báo", "Không tìm thấy ảnh nào")
    
    def load_images(self, paths):
        added = 0
        for p in paths:
            if p not in self.image_list:
                self.image_list.append(p)
                added += 1
        
        if added > 0:
            self.sort_images()
            if self.current_index == -1 and self.image_list:
                self.listbox.setCurrentRow(0)
                self.display_image(0)
    
    def sort_images(self):
        if not self.image_list:
            return
        
        current = self.image_list[self.current_index] if self.current_index >= 0 else None
        sort_value = self.sort_combo.currentData()
        
        # ✅ Always sort master list
        if sort_value == "name":
            self.image_list.sort(key=lambda x: Path(x).name.lower())
        elif sort_value in ["date_desc", "date_asc"]:
            def get_date(p):
                tags = self.get_exif(p)
                date_str = str(tags.get('EXIF DateTimeOriginal', ''))
                if not date_str:
                    return os.path.getmtime(p) if os.path.exists(p) else 0
                return date_str
            self.image_list.sort(key=get_date, reverse=(sort_value == "date_desc"))
        elif sort_value == "size":
            def get_size(p):
                return os.path.getsize(p) if os.path.exists(p) else 0
            self.image_list.sort(key=get_size, reverse=True)
        
        # ✅ Update display based on current filter state
        if self.is_filtered:
            # Rebuild filtered list maintaining filter criteria
            self.filtered_list = [p for p in self.image_list if p in self.filtered_list]
            self.update_listbox(self.filtered_list)
        else:
            self.update_listbox(self.image_list)
        
        # ✅ Restore current selection
        if current and current in self.display_list:
            self.current_index = self.image_list.index(current)
            display_idx = self.display_list.index(current)
            self.listbox.setCurrentRow(display_idx)
    
    def apply_filter_with_highlight(self, filter_type, button):
        """Apply filter and highlight active button"""
        if not self.image_list:
            QMessageBox.information(self, "Thông báo", "Chưa có ảnh nào")
            return
        
        # Reset all filter buttons
        self.gps_btn.setObjectName("filterButton")
        self.no_gps_btn.setObjectName("filterButton")
        self.gps_btn.setStyleSheet("")
        self.no_gps_btn.setStyleSheet("")
        
        # Highlight active button
        button.setObjectName("filterButtonActive")
        button.setStyleSheet("")
        self.active_filter_btn = button
        
        self.list_status.setText("⏳ Đang lọc...")
        QApplication.processEvents()
        
        self.filtered_list = []
        for p in self.image_list:
            gps = self.get_gps_data(p)
            if (filter_type == 'has_gps' and gps) or (filter_type == 'no_gps' and not gps):
                self.filtered_list.append(p)
        
        self.is_filtered = True
        self.update_listbox(self.filtered_list)
        
        if self.filtered_list:
            self.listbox.setCurrentRow(0)
    
    def update_listbox(self, items):
        self.display_list = items
        self.listbox.clear()
        for i, p in enumerate(items, 1):
            self.listbox.addItem(f"[{i:03d}] {Path(p).name}")
        self.update_list_status()
    
    def update_list_status(self):
        if self.is_filtered:
            self.list_status.setText(f"🔍 Đã lọc: {len(self.filtered_list)}/{len(self.image_list)} ảnh")
            if self.is_dark_theme:
                self.list_status.setStyleSheet("""
                    background-color: #1a4d2e;
                    color: #90ee90;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: 600;
                    font-size: 8.5pt;
                """)
            else:
                self.list_status.setStyleSheet("""
                    background-color: #D4F4DD;
                    color: #0E5C2F;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: 600;
                    font-size: 8.5pt;
                """)
        else:
            self.list_status.setText(f"📊 Tổng: {len(self.image_list)} ảnh")
            if self.is_dark_theme:
                self.list_status.setStyleSheet("""
                    background-color: #4a4000;
                    color: #ffeb3b;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: 600;
                    font-size: 8.5pt;
                """)
            else:
                self.list_status.setStyleSheet("""
                    background-color: #FFF4CE;
                    color: #6B5300;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: 600;
                    font-size: 8.5pt;
                """)
    
    def on_search_change(self):
        query = self.search_box.text().lower().strip()
        source = self.filtered_list if self.is_filtered else self.image_list
        
        if not query:
            self.update_listbox(source)
            return
        
        results = [p for p in source if query in Path(p).name.lower()]
        self.update_listbox(results)
        
        if results:
            self.listbox.setCurrentRow(0)
    
    def apply_filter(self, filter_type):
        if not self.image_list:
            QMessageBox.information(self, "Thông báo", "Chưa có ảnh nào trong danh sách")
            return
        
        self.list_status.setText("⏳ Đang lọc...")
        QApplication.processEvents()
        
        self.filtered_list = []
        for p in self.image_list:
            gps = self.get_gps_data(p)
            if (filter_type == 'has_gps' and gps) or (filter_type == 'no_gps' and not gps):
                self.filtered_list.append(p)
        
        self.is_filtered = True
        self.update_listbox(self.filtered_list)
        
        if self.filtered_list:
            self.listbox.setCurrentRow(0)
    
    def filter_by_camera(self):
        if not self.image_list:
            QMessageBox.information(self, "Thông báo", "Chưa có ảnh nào")
            return
        
        self.list_status.setText("⏳ Đang quét...")
        QApplication.processEvents()
        
        cameras = set()
        for p in self.image_list:
            tags = self.get_exif(p)
            make = str(tags.get('Image Make', '')).strip()
            model = str(tags.get('Image Model', '')).strip()
            camera = f"{make} {model}".strip()
            if camera:
                cameras.add(camera)
        
        if not cameras:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy thông tin camera")
            self.update_list_status()
            return
        
        from PyQt6.QtWidgets import QInputDialog
        camera, ok = QInputDialog.getItem(
            self, "Lọc theo Camera", "Chọn camera:", 
            sorted(cameras), 0, False
        )
        
        if ok and camera:
            # Reset filter buttons
            self.gps_btn.setObjectName("filterButton")
            self.no_gps_btn.setObjectName("filterButton")
            self.gps_btn.setStyleSheet("")
            self.no_gps_btn.setStyleSheet("")
            
            # Highlight camera button
            self.camera_btn.setObjectName("filterButtonActive")
            self.camera_btn.setStyleSheet("")
            self.active_filter_btn = self.camera_btn
            
            self.filtered_list = []
            for p in self.image_list:
                tags = self.get_exif(p)
                make = str(tags.get('Image Make', '')).strip()
                model = str(tags.get('Image Model', '')).strip()
                if f"{make} {model}".strip() == camera:
                    self.filtered_list.append(p)
            
            self.is_filtered = True
            self.update_listbox(self.filtered_list)
            
            if self.filtered_list:
                self.listbox.setCurrentRow(0)
    
    def clear_filter(self):
        self.is_filtered = False
        self.filtered_list.clear()
        self.search_box.clear()
        
        # Reset all filter button styles
        if hasattr(self, 'gps_btn'):
            self.gps_btn.setObjectName("filterButton")
            self.no_gps_btn.setObjectName("filterButton")
            self.camera_btn.setObjectName("filterButton")
            self.gps_btn.setStyleSheet("")
            self.no_gps_btn.setStyleSheet("")
            self.camera_btn.setStyleSheet("")
        
        self.active_filter_btn = None
        self.update_listbox(self.image_list)
    
    def on_select(self, row):
        if 0 <= row < len(self.display_list):
            path = self.display_list[row]
            if path in self.image_list:
                self.display_image(self.image_list.index(path))
    
    def display_image(self, index):
        if not (0 <= index < len(self.image_list)):
            return
        
        self.current_index = index
        path = self.image_list[index]

        if not os.path.exists(path):
            QMessageBox.warning(self, "Lỗi", 
                f"File không tồn tại hoặc đã bị xóa:\n{Path(path).name}")
            self.image_list.remove(path)
            self.update_listbox(self.display_list)
            return
        
        if not self.image_viewer.load_image(path):
            QMessageBox.warning(self, "Lỗi", f"Không thể tải ảnh:\n{Path(path).name}")
            return
        
        self.update_file_info(path)
        
        gps = self.get_gps_data(path)
        self.current_gps = gps
        
        if gps:
            self.display_gps(gps)
            self.display_camera_info(path)
            self.google_btn.setEnabled(True)
            self.html_btn.setEnabled(True)
            self.load_address_async(gps['lat'], gps['lon'])
        else:
            self.clear_gps()
            self.display_camera_info(path)
            self.addr_label.setText("Ảnh không có GPS")
        
        self.update_nav()
        self.update_zoom_label()
    
    def update_file_info(self, path):
        try:
            stat = os.stat(path)
            self.file_labels['file_name'].setText(Path(path).name)
            self.file_labels['file_size'].setText(self.format_size(stat.st_size))
            self.file_labels['file_format'].setText(Path(path).suffix.upper().replace('.', ''))
            
            try:
                img = Image.open(path)
                self.file_labels['image_dimensions'].setText(f"{img.width} × {img.height} px")
                img.close()
            except:
                self.file_labels['image_dimensions'].setText("--")
            
            self.file_labels['file_created'].setText(
                datetime.fromtimestamp(stat.st_ctime).strftime('%d/%m/%Y %H:%M')
            )
            self.file_labels['file_modified'].setText(
                datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_exif(self, path):
        cached = self.exif_cache.get(path)
        if cached is not None:
            return cached
        
        try:
            if EXIFREAD_AVAILABLE:
                with open(path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                self.exif_cache.set(path, tags)
                return tags
        except Exception as e:
            print(f"EXIF read error for {Path(path).name}: {e}")
        
        self.exif_cache.set(path, {})
        return {}
    
    def get_gps_data(self, path):
        cached = self.gps_cache.get(path)
        if cached is not None:
            return cached
        
        tags = self.get_exif(path)
        
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            try:
                def to_deg(val):
                    d = float(val.values[0].num) / float(val.values[0].den)
                    m = float(val.values[1].num) / float(val.values[1].den)
                    s = float(val.values[2].num) / float(val.values[2].den)
                    return d + m/60 + s/3600
                
                lat = to_deg(tags['GPS GPSLatitude'])
                if str(tags.get('GPS GPSLatitudeRef', '')) == 'S':
                    lat = -lat
                
                lon = to_deg(tags['GPS GPSLongitude'])
                if str(tags.get('GPS GPSLongitudeRef', '')) == 'W':
                    lon = -lon
                
                alt = 'N/A'
                if 'GPS GPSAltitude' in tags:
                    v = tags['GPS GPSAltitude'].values[0]
                    alt = f"{float(v.num)/float(v.den):.1f} m"
                
                dt = str(tags.get('EXIF DateTimeOriginal', 'N/A'))
                
                data = {'lat': lat, 'lon': lon, 'alt': alt, 'time': dt}
                self.gps_cache[path] = data
                return data
            except Exception as e:
                print(f"GPS parsing error for {Path(path).name}: {e}")
                
        self.gps_cache[path] = None
        return None
    
    def display_gps(self, gps):
        self.gps_labels['lat'].setText(f"{gps['lat']:.6f}°")
        self.gps_labels['lon'].setText(f"{gps['lon']:.6f}°")
        self.gps_labels['alt'].setText(gps['alt'])
        self.gps_labels['time'].setText(gps['time'])
    
    def clear_gps(self):
        for lbl in self.gps_labels.values():
            lbl.setText("--")
        self.google_btn.setEnabled(False)
        self.html_btn.setEnabled(False)
    
    def display_camera_info(self, path):
        tags = self.get_exif(path)
        
        make = str(tags.get('Image Make', '')).strip()
        model = str(tags.get('Image Model', '')).strip()
        camera = f"{make} {model}".strip() or "--"
        self.camera_labels['camera_model'].setText(camera[:40])
        
        lens = str(tags.get('EXIF LensModel', '--'))
        self.camera_labels['lens_model'].setText(lens[:40] if lens != '--' else '--')
        
        iso = str(tags.get('EXIF ISOSpeedRatings', '--'))
        self.camera_labels['iso'].setText(f"ISO {iso}" if iso != '--' else '--')
        
        shutter = tags.get('EXIF ExposureTime')
        if shutter:
            try:
                val = shutter.values[0]
                if val.den > val.num:
                    s = f"1/{val.den//val.num}s"
                else:
                    s = f"{float(val.num)/float(val.den):.2f}s"
                self.camera_labels['shutter_speed'].setText(s)
            except:
                self.camera_labels['shutter_speed'].setText("--")
        else:
            self.camera_labels['shutter_speed'].setText("--")
        
        aperture = tags.get('EXIF FNumber')
        if aperture:
            try:
                val = aperture.values[0]
                f_val = float(val.num) / float(val.den)
                self.camera_labels['aperture'].setText(f"f/{f_val:.1f}")
            except:
                self.camera_labels['aperture'].setText("--")
        else:
            self.camera_labels['aperture'].setText("--")
        
        focal = tags.get('EXIF FocalLength')
        if focal:
            try:
                val = focal.values[0]
                fl = float(val.num) / float(val.den)
                self.camera_labels['focal_length'].setText(f"{fl:.0f}mm")
            except:
                self.camera_labels['focal_length'].setText("--")
        else:
            self.camera_labels['focal_length'].setText("--")
    
    def open_google_maps(self):
        if self.current_gps:
            webbrowser.open(
                f"https://www.google.com/maps?q={self.current_gps['lat']},{self.current_gps['lon']}"
            )
    
    def open_html_map(self):
        if not FOLIUM_AVAILABLE:
            QMessageBox.warning(self, "Lỗi", "Cần cài folium:\npip install folium")
            return
        
        if not self.current_gps:
            return
        
        try:
            m = folium.Map(location=[self.current_gps['lat'], self.current_gps['lon']], zoom_start=15)
            
            popup_html = f"""
            <div style='font-family: Segoe UI; width: 270px; padding: 8px;'>
                <h3 style='margin: 0 0 10px 0; color: #0067C0;'>📍 GeoSnap</h3>
                <p style='margin: 5px 0;'><b>File:</b> {Path(self.image_list[self.current_index]).name}</p>
                <p style='margin: 5px 0;'><b>Tọa độ:</b> {self.current_gps['lat']:.6f}, {self.current_gps['lon']:.6f}</p>
                <p style='margin: 5px 0;'><b>Độ cao:</b> {self.current_gps['alt']}</p>
                <p style='margin: 5px 0;'><b>Thời gian:</b> {self.current_gps['time']}</p>
            </div>
            """
            
            folium.Marker(
                [self.current_gps['lat'], self.current_gps['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip="📍 Nhấn xem chi tiết",
                icon=folium.Icon(color='red', icon='camera', prefix='fa')
            ).add_to(m)
            
            folium.Circle(
                [self.current_gps['lat'], self.current_gps['lon']],
                radius=50,
                color='#0067C0',
                fill=True,
                fillOpacity=0.2
            ).add_to(m)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            m.save(temp_file.name)
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            webbrowser.open('file://' + os.path.abspath(temp_file.name))
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tạo bản đồ:\n{str(e)}")

    def show_all_on_map(self):
        if not FOLIUM_AVAILABLE:
            QMessageBox.warning(self, "Lỗi", "Cần cài folium:\npip install folium")
            return
        
        if not self.image_list:
            QMessageBox.information(self, "Thông báo", "Chưa có ảnh nào")
            return
        
        gps_images = []
        for p in self.image_list:
            gps = self.get_gps_data(p)
            if gps:
                gps_images.append((p, gps))
        
        if not gps_images:
            QMessageBox.information(self, "Thông báo", "Không có ảnh nào có GPS")
            return
        
        try:
            lats = [g['lat'] for _, g in gps_images]
            lons = [g['lon'] for _, g in gps_images]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            
            for i, (path, gps) in enumerate(gps_images, 1):
                popup_html = f"""
                <div style='font-family: Segoe UI; width: 250px; padding: 10px;'>
                    <h4 style='margin: 0 0 8px 0; color: #0067C0;'>#{i} - {Path(path).name[:30]}</h4>
                    <p style='margin: 4px 0;'><b>Tọa độ:</b> {gps['lat']:.6f}, {gps['lon']:.6f}</p>
                    <p style='margin: 4px 0;'><b>Độ cao:</b> {gps['alt']}</p>
                    <p style='margin: 4px 0;'><b>Thời gian:</b> {gps['time'][:19]}</p>
                </div>
                """
                
                color = 'red' if i == 1 else ('green' if i == len(gps_images) else 'blue')
                
                folium.Marker(
                    [gps['lat'], gps['lon']],
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"#{i} - {Path(path).name[:28]}",
                    icon=folium.Icon(color=color, icon='camera', prefix='fa')
                ).add_to(m)
            
            if len(gps_images) > 1:
                coordinates = [[g['lat'], g['lon']] for _, g in gps_images]
                folium.PolyLine(
                    coordinates,
                    color='#0067C0',
                    weight=3,
                    opacity=0.7,
                    popup=f"Tuyến đường: {len(gps_images)} ảnh"
                ).add_to(m)
            
            legend_html = f"""
            <div style="position: fixed; bottom: 50px; left: 50px; width: 240px;
                        background: linear-gradient(135deg, white 0%, #f8f9fa 100%);
                        border: 3px solid #0067C0; z-index: 9999;
                        border-radius: 12px; padding: 20px; font-family: 'Segoe UI';
                        box-shadow: 0 8px 24px rgba(0,103,192,0.3);">
                <h3 style="margin: 0 0 14px 0; color: #0067C0; font-size: 18px; font-weight: 600;">
                    📍 GeoSnap Map
                </h3>
                <p style="margin: 8px 0; font-size: 11pt; color: #333;">🔴 Ảnh đầu tiên</p>
                <p style="margin: 8px 0; font-size: 11pt; color: #333;">🔵 Ảnh ở giữa</p>
                <p style="margin: 8px 0; font-size: 11pt; color: #333;">🟢 Ảnh cuối cùng</p>
                <hr style="margin: 14px 0; border: 1px solid #e0e0e0;">
                <p style="margin: 8px 0; font-weight: 600; font-size: 12pt; color: #0067C0;">
                    📊 Tổng: {len(gps_images)} ảnh
                </p>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            m.save(temp_file.name)
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            webbrowser.open('file://' + os.path.abspath(temp_file.name))
            
            # Removed success message dialog
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tạo bản đồ:\n{str(e)}")
    
    def prev_image(self):
        if not self.display_list or self.current_index < 0:
            return
        
        current_path = self.image_list[self.current_index]
        if current_path in self.display_list:
            idx = self.display_list.index(current_path)
            if idx > 0:
                self.listbox.setCurrentRow(idx - 1)
    
    def next_image(self):
        if not self.display_list or self.current_index < 0:
            return
        
        current_path = self.image_list[self.current_index]
        if current_path in self.display_list:
            idx = self.display_list.index(current_path)
            if idx < len(self.display_list) - 1:
                self.listbox.setCurrentRow(idx + 1)
    
    def update_nav(self):
        if not self.display_list or self.current_index < 0:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.status_right.setText("")
            return
        
        current_path = self.image_list[self.current_index]
        if current_path in self.display_list:
            idx = self.display_list.index(current_path)
            self.prev_btn.setEnabled(idx > 0)
            self.next_btn.setEnabled(idx < len(self.display_list) - 1)
            
            total_display = len(self.display_list)
            if self.is_filtered or self.search_box.text().strip():
                self.status_right.setText(
                    f"📸 {idx + 1}/{total_display} (Tổng: {len(self.image_list)})"
                )
            else:
                self.status_right.setText(f"📸 {idx + 1}/{total_display}")
    
    def update_zoom_label(self):
        scale_percent = int(self.image_viewer.scale * 100)
        self.zoom_label.setText(f"{scale_percent}%")
    
    def clear_all(self):
        if not self.image_list:
            return
        
        reply = QMessageBox.question(
            self, "⚠️ Xác nhận",
            f"Xóa tất cả {len(self.image_list)} ảnh khỏi danh sách?\n\n"
            f"(Ảnh gốc không bị xóa)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.image_list.clear()
            self.filtered_list.clear()
            self.display_list.clear()
            self.gps_cache.clear()
            self.exif_cache.clear()
            self.current_index = -1
            self.current_gps = None
            self.is_filtered = False
            
            self.listbox.clear()
            self.search_box.clear()
            
            self.image_viewer.original_pixmap = None
            self.image_viewer.update()
            
            for lbl in self.file_labels.values():
                lbl.setText("--")
            for lbl in self.camera_labels.values():
                lbl.setText("--")
            self.clear_gps()
            self.addr_label.setText("--")
            
            self.update_list_status()
            self.update_nav()
    
    def closeEvent(self, event):
            if self.address_loader and self.address_loader.isRunning():
                self.address_loader.stop()
                self.address_loader.wait(2000)
            
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.prev_image()
        elif event.key() == Qt.Key.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key.Key_Escape:
            if self.image_viewer.original_pixmap:
                self.image_viewer.fit_to_screen()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Don't auto-fit to prevent zoom jumping
        pass


def main():
    # Enable High DPI scaling for PyQt6
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except:
        pass
    
    app = QApplication(sys.argv)
    
    # Force Light Theme - Override Windows Dark Mode
    app.setStyle('Fusion')
    
    # Set Light Palette globally
    light_palette = QPalette()
    light_palette.setColor(QPalette.ColorRole.Window, QColor(243, 243, 243))
    light_palette.setColor(QPalette.ColorRole.WindowText, QColor(26, 26, 26))
    light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(26, 26, 26))
    light_palette.setColor(QPalette.ColorRole.Text, QColor(26, 26, 26))
    light_palette.setColor(QPalette.ColorRole.Button, QColor(243, 243, 243))
    light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(26, 26, 26))
    light_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 103, 192))
    light_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 103, 192))
    light_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Disabled colors
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(148, 148, 148))
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(148, 148, 148))
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(148, 148, 148))
    light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(235, 235, 235))
    
    app.setPalette(light_palette)
    
    # Set modern font
    font = QFont("Segoe UI Variable", 9)
    if not font.exactMatch():
        font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Application metadata
    app.setApplicationName("GeoSnap")
    app.setApplicationDisplayName("GeoSnap - GPS Photo Viewer")
    app.setOrganizationName("GeoSnap")
    app.setOrganizationDomain("geosnap.app")
    
    # Set application icon for taskbar (Windows specific)
    icon_path = Path(__file__).parent / "logo.ico"
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
        
        # For Windows taskbar grouping
        try:
            import ctypes
            myappid = 'geosnap.photogps.viewer.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    
    # Create and show window
    window = GeoSnap()
    
    # Force light theme to apply before showing
    window.apply_theme()
    QApplication.processEvents()
    
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

                
                    