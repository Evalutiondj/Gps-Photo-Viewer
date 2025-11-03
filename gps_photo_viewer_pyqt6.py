import sys
import os
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QListWidget, QFrame, QSplitter, QFileDialog,
                              QMessageBox, QLineEdit, QRadioButton, QButtonGroup, QScrollArea,
                              QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QImage, QTransform, QCursor, QFont, QPainter, QColor

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


# Windows 11 Modern Stylesheet
WIN11_STYLE = """
QMainWindow {
    background-color: #f3f3f3;
}

QWidget {
    font-family: 'Segoe UI', Arial;
    font-size: 9pt;
}

QPushButton {
    background-color: #005FB8;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #0067C0;
}

QPushButton:pressed {
    background-color: #004275;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #888888;
}

QPushButton#secondaryButton {
    background-color: #e0e0e0;
    color: #1a1a1a;
}

QPushButton#secondaryButton:hover {
    background-color: #d0d0d0;
}

QPushButton#dangerButton {
    background-color: #d13438;
}

QPushButton#dangerButton:hover {
    background-color: #c42b1c;
}

QPushButton#accentButton {
    background-color: #8764B8;
}

QPushButton#accentButton:hover {
    background-color: #744DA9;
}

QLineEdit {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
}

QLineEdit:focus {
    border: 2px solid #005FB8;
}

QListWidget {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: white;
    outline: none;
}

QListWidget::item {
    padding: 6px;
    border-radius: 4px;
    margin: 1px;
}

QListWidget::item:selected {
    background-color: #005FB8;
    color: white;
}

QListWidget::item:hover {
    background-color: #f0f0f0;
}

QGroupBox {
    border: 1px solid #d1d1d1;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: white;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QRadioButton {
    spacing: 5px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #8a8a8a;
}

QRadioButton::indicator:checked {
    background-color: #005FB8;
    border: 2px solid #005FB8;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QFrame#imageFrame {
    background-color: #1a1a1a;
    border: 1px solid #d1d1d1;
    border-radius: 6px;
}

QLabel#statusLabel {
    background-color: #fef7cd;
    border-radius: 4px;
    padding: 6px;
}
"""


class AddressLoader(QThread):
    result = pyqtSignal(str)
    
    def __init__(self, lat, lon):
        super().__init__()
        self.lat = lat
        self.lon = lon
    
    def run(self):
        if not GEOPY_AVAILABLE:
            self.result.emit("Không có dịch vụ")
            return
        try:
            geo = Nominatim(user_agent="gps_viewer", timeout=10)
            loc = geo.reverse(f"{self.lat}, {self.lon}", language='vi')
            self.result.emit(loc.address if loc else "Không tìm thấy")
        except Exception as e:
            self.result.emit(f"Lỗi: {str(e)[:30]}")


class ImageViewer(QLabel):
    """Modern image viewer with zoom/pan"""
    def __init__(self):
        super().__init__()
        self.setObjectName("imageFrame")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        
        self.original_pixmap = None
        self.display_pixmap = None
        self.scale = 1.0
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False
        self.offset = QPoint(0, 0)
        self.drag_start = None
        self.mouse_pos = QPoint(0, 0)
        
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        
        self.placeholder_text = "Kéo thả ảnh vào đây hoặc nhấn 'Thêm'"
    
    def load_image(self, path):
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to QPixmap
            data = img.tobytes('raw', 'RGB')
            qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            self.original_pixmap = QPixmap.fromImage(qimg)
            
            self.rotation = 0
            self.flip_h = False
            self.flip_v = False
            self.offset = QPoint(0, 0)
            self.fit_to_screen()
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            self.original_pixmap = None
            self.update()
            return False
    
    def get_transformed_pixmap(self):
        if not self.original_pixmap:
            return None
        
        pixmap = self.original_pixmap
        
        # Apply transformations
        if self.rotation != 0 or self.flip_h or self.flip_v:
            transform = QTransform()
            
            # Move to center for rotation
            transform.translate(pixmap.width() / 2, pixmap.height() / 2)
            
            if self.rotation:
                transform.rotate(self.rotation)
            
            if self.flip_h:
                transform.scale(-1, 1)
            
            if self.flip_v:
                transform.scale(1, -1)
            
            # Move back
            transform.translate(-pixmap.width() / 2, -pixmap.height() / 2)
            
            pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        return pixmap
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.original_pixmap:
            painter = QPainter(self)
            painter.setPen(QColor(160, 160, 160))
            font = QFont("Segoe UI", 12)
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
        
        # Scale pixmap
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
        w_ratio = (self.width() - 20) / pixmap.width()
        h_ratio = (self.height() - 20) / pixmap.height()
        self.scale = min(w_ratio, h_ratio, 1.0)
        self.offset = QPoint(0, 0)
        self.render()
    
    def zoom_in(self):
        self.scale *= 1.2
        self.scale = min(self.scale, 10.0)
        self.render()
    
    def zoom_out(self):
        self.scale /= 1.2
        self.scale = max(self.scale, 0.1)
        self.render()
    
    def actual_size(self):
        self.scale = 1.0
        self.render()
    
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
        old_scale = self.scale
        self.scale *= factor
        self.scale = max(0.1, min(self.scale, 10.0))
        
        self.render()
        event.accept()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.original_pixmap:
            self.drag_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        if self.drag_start:
            delta = event.pos() - self.drag_start
            self.offset += delta
            self.drag_start = event.pos()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = None
            self.setCursor(Qt.CursorShape.CrossCursor)


class GPSPhotoViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📍 GPS Photo Viewer Professional")
        self.setGeometry(100, 50, 1600, 900)
        
        self.image_list = []
        self.display_list = []
        self.filtered_list = []
        self.current_index = -1
        self.is_filtered = False
        self.gps_cache = {}
        self.exif_cache = {}
        self.current_gps = None
        self.address_loader = None
        
        self.init_ui()
        self.setStyleSheet(WIN11_STYLE)
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #0078D4, stop:1 #00BCF2);
            border-radius: 8px;
        """)
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        
        title = QLabel("📍 GPS Photo Viewer Professional")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Windows 11 Modern Edition")
        subtitle.setStyleSheet("font-size: 10pt; color: rgba(255,255,255,180);")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #d1d1d1; }")
        
        # Left panel (25%)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Middle panel (50%)
        middle_panel = self.create_middle_panel()
        splitter.addWidget(middle_panel)
        
        # Right panel (25%)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial sizes
        splitter.setSizes([350, 700, 350])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        
        # Status bar
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #2b2b2b; border-radius: 4px;")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 4, 10, 4)
        
        libs = f"exif:{'✓' if EXIFREAD_AVAILABLE else '✗'} heic:{'✓' if HEIC_SUPPORTED else '✗'} map:{'✓' if FOLIUM_AVAILABLE else '✗'} geo:{'✓' if GEOPY_AVAILABLE else '✗'}"
        libs_label = QLabel(libs)
        libs_label.setStyleSheet("color: #b0b0b0; font-size: 8pt;")
        status_layout.addWidget(libs_label)
        
        status_layout.addStretch()
        
        self.status_right = QLabel()
        self.status_right.setStyleSheet("color: #b0b0b0; font-size: 8pt;")
        status_layout.addWidget(self.status_right)
        
        main_layout.addWidget(status_frame)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def create_left_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(280)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        add_btn = QPushButton("➕ Thêm")
        add_btn.clicked.connect(self.add_images)
        btn_layout.addWidget(add_btn)
        
        folder_btn = QPushButton("📂 Folder")
        folder_btn.setObjectName("accentButton")
        folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(folder_btn)
        
        clear_btn = QPushButton("🗑️")
        clear_btn.setObjectName("dangerButton")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setMaximumWidth(45)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Search box
        search_group = QGroupBox("🔍 Tìm kiếm")
        search_layout = QVBoxLayout(search_group)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Nhập tên file...")
        self.search_box.textChanged.connect(self.on_search_change)
        search_layout.addWidget(self.search_box)
        
        layout.addWidget(search_group)
        
        # Filter buttons
        filter_group = QGroupBox("🎯 Lọc nhanh")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setSpacing(6)
        
        btn_style_sec = "secondaryButton"
        
        gps_btn = QPushButton("🌍 Có GPS")
        gps_btn.setObjectName(btn_style_sec)
        gps_btn.clicked.connect(lambda: self.apply_filter('has_gps'))
        filter_layout.addWidget(gps_btn, 0, 0)
        
        no_gps_btn = QPushButton("❌ Không GPS")
        no_gps_btn.setObjectName(btn_style_sec)
        no_gps_btn.clicked.connect(lambda: self.apply_filter('no_gps'))
        filter_layout.addWidget(no_gps_btn, 0, 1)
        
        camera_btn = QPushButton("📷 Camera")
        camera_btn.setObjectName(btn_style_sec)
        camera_btn.clicked.connect(self.filter_by_camera)
        filter_layout.addWidget(camera_btn, 1, 0)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.clear_filter)
        filter_layout.addWidget(reset_btn, 1, 1)
        
        layout.addWidget(filter_group)
        
        # Sort options
        sort_group = QGroupBox("📊 Sắp xếp")
        sort_layout = QVBoxLayout(sort_group)
        
        self.sort_group = QButtonGroup()
        sorts = [("📝 Tên file", "name"), ("📅 Ngày giảm dần", "date_desc"), 
                 ("📅 Ngày tăng dần", "date_asc"), ("💾 Kích thước", "size")]
        
        for text, value in sorts:
            rb = QRadioButton(text)
            rb.setProperty("value", value)
            rb.toggled.connect(lambda checked, v=value: self.sort_images() if checked else None)
            self.sort_group.addButton(rb)
            sort_layout.addWidget(rb)
            if value == "name":
                rb.setChecked(True)
        
        layout.addWidget(sort_group)
        
        # Image list
        list_label = QLabel("📋 Danh sách ảnh")
        list_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(list_label)
        
        self.listbox = QListWidget()
        self.listbox.currentRowChanged.connect(self.on_select)
        layout.addWidget(self.listbox)
        
        # Status label
        self.list_status = QLabel("0 ảnh")
        self.list_status.setObjectName("statusLabel")
        self.list_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.list_status)
        
        return panel
    
    def create_middle_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        
        # Image viewer
        viewer_label = QLabel("🖼️ Xem ảnh (Zoom: Cuộn chuột | Di chuyển: Kéo thả)")
        viewer_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(viewer_label)
        
        self.image_viewer = ImageViewer()
        layout.addWidget(self.image_viewer, stretch=1)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #2b2b2b; border-radius: 6px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 8, 8, 8)
        toolbar_layout.setSpacing(6)
        
        tool_btn_style = """
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """
        
        for text, func in [("🔍+", self.image_viewer.zoom_in), 
                           ("🔍-", self.image_viewer.zoom_out),
                           ("⟲ Fit", self.image_viewer.fit_to_screen), 
                           ("100%", self.image_viewer.actual_size),
                           ("↔️", self.image_viewer.flip_horizontal), 
                           ("↕️", self.image_viewer.flip_vertical),
                           ("↻", self.image_viewer.rotate_right), 
                           ("↺", self.image_viewer.rotate_left)]:
            btn = QPushButton(text)
            btn.setStyleSheet(tool_btn_style)
            btn.clicked.connect(func)
            toolbar_layout.addWidget(btn)
        
        toolbar_layout.addStretch()
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: white; font-weight: bold;")
        toolbar_layout.addWidget(self.zoom_label)
        
        layout.addWidget(toolbar)
        
        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        self.prev_btn = QPushButton("⬅️ Ảnh trước")
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setMinimumHeight(45)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Ảnh tiếp ➡️")
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setEnabled(False)
        self.next_btn.setMinimumHeight(45)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        return panel
    
    def create_right_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(280)
        
        scroll = QScrollArea()
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        
        # File info
        file_group = QGroupBox("📄 Thông tin File")
        file_layout = QGridLayout(file_group)
        file_layout.setVerticalSpacing(8)
        file_layout.setHorizontalSpacing(10)
        
        self.file_labels = {}
        file_fields = [
            ("Tên:", 'file_name'), ("Kích thước:", 'file_size'), 
            ("Định dạng:", 'file_format'), ("Độ phân giải:", 'image_dimensions'),
            ("Ngày tạo:", 'file_created'), ("Ngày sửa:", 'file_modified')
        ]
        
        for i, (label_text, key) in enumerate(file_fields):
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #666;")
            file_layout.addWidget(label, i, 0, Qt.AlignmentFlag.AlignRight)
            
            value_label = QLabel("--")
            value_label.setWordWrap(True)
            self.file_labels[key] = value_label
            file_layout.addWidget(value_label, i, 1)
        
        layout.addWidget(file_group)
        
        # Camera info
        camera_group = QGroupBox("📷 Thông tin Camera")
        camera_layout = QGridLayout(camera_group)
        camera_layout.setVerticalSpacing(8)
        camera_layout.setHorizontalSpacing(10)
        
        self.camera_labels = {}
        camera_fields = [
            ("Camera:", 'camera_model'), ("Ống kính:", 'lens_model'),
            ("ISO:", 'iso'), ("Tốc độ:", 'shutter_speed'),
            ("Khẩu độ:", 'aperture'), ("Tiêu cự:", 'focal_length')
        ]
        
        for i, (label_text, key) in enumerate(camera_fields):
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #666;")
            camera_layout.addWidget(label, i, 0, Qt.AlignmentFlag.AlignRight)
            
            value_label = QLabel("--")
            value_label.setWordWrap(True)
            self.camera_labels[key] = value_label
            camera_layout.addWidget(value_label, i, 1)
        
        layout.addWidget(camera_group)
        
        # GPS info
        gps_group = QGroupBox("📍 Thông tin GPS")
        gps_layout = QGridLayout(gps_group)
        gps_layout.setVerticalSpacing(8)
        gps_layout.setHorizontalSpacing(10)
        
        self.gps_labels = {}
        gps_fields = [
            ("Vĩ độ:", 'lat'), ("Kinh độ:", 'lon'),
            ("Độ cao:", 'alt'), ("Thời gian:", 'time')
        ]
        
        for i, (label_text, key) in enumerate(gps_fields):
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #666;")
            gps_layout.addWidget(label, i, 0, Qt.AlignmentFlag.AlignRight)
            
            value_label = QLabel("--")
            value_label.setWordWrap(True)
            self.gps_labels[key] = value_label
            gps_layout.addWidget(value_label, i, 1)
        
        layout.addWidget(gps_group)
        
        # Address
        addr_group = QGroupBox("🏠 Địa chỉ")
        addr_layout = QVBoxLayout(addr_group)
        
        self.addr_label = QLabel("--")
        self.addr_label.setWordWrap(True)
        self.addr_label.setStyleSheet("padding: 5px;")
        addr_layout.addWidget(self.addr_label)
        
        layout.addWidget(addr_group)
        
        # Map buttons
        map_group = QGroupBox("🗺️ Bản đồ")
        map_layout = QGridLayout(map_group)
        map_layout.setSpacing(8)
        
        self.google_btn = QPushButton("🌍 Google Maps")
        self.google_btn.clicked.connect(self.open_google_maps)
        self.google_btn.setEnabled(False)
        self.google_btn.setMinimumHeight(40)
        map_layout.addWidget(self.google_btn, 0, 0, 1, 2)
        
        self.html_btn = QPushButton("📍 Xem HTML")
        self.html_btn.clicked.connect(self.open_html_map)
        self.html_btn.setEnabled(False)
        self.html_btn.setMinimumHeight(40)
        map_layout.addWidget(self.html_btn, 1, 0)
        
        self.all_map_btn = QPushButton("🗺️ Tất cả")
        self.all_map_btn.setObjectName("accentButton")
        self.all_map_btn.clicked.connect(self.show_all_on_map)
        self.all_map_btn.setMinimumHeight(40)
        map_layout.addWidget(self.all_map_btn, 1, 1)
        
        layout.addWidget(map_group)
        
        layout.addStretch()
        
        return scroll
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                files.append(path)
        if files:
            self.load_images(files)
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh", "",
            "Images (*.jpg *.jpeg *.png *.heic *.heif);;All Files (*.*)"
        )
        if files:
            self.load_images(files)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
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
        sort_value = next((btn.property("value") for btn in self.sort_group.buttons() if btn.isChecked()), "name")
        
        if sort_value == "name":
            self.image_list.sort(key=lambda x: Path(x).name.lower())
        elif sort_value in ["date_desc", "date_asc"]:
            def get_date(p):
                tags = self.get_exif(p)
                return str(tags.get('EXIF DateTimeOriginal', os.path.getmtime(p)))
            self.image_list.sort(key=get_date, reverse=(sort_value == "date_desc"))
        elif sort_value == "size":
            self.image_list.sort(key=lambda x: os.path.getsize(x), reverse=True)
        
        # Update display
        if self.is_filtered:
            self.filtered_list = [p for p in self.image_list if p in self.filtered_list]
            self.update_listbox(self.filtered_list)
        else:
            self.update_listbox(self.image_list)
        
        # Restore selection
        if current and current in self.image_list:
            self.current_index = self.image_list.index(current)
            if current in self.display_list:
                display_idx = self.display_list.index(current)
                self.listbox.setCurrentRow(display_idx)
    
    def update_listbox(self, items):
        self.display_list = items
        self.listbox.clear()
        for i, p in enumerate(items, 1):
            self.listbox.addItem(f"[{i:03d}] {Path(p).name}")
        self.update_list_status()
    
    def update_list_status(self):
        if self.is_filtered:
            self.list_status.setText(f"🔍 {len(self.filtered_list)}/{len(self.image_list)} ảnh")
            self.list_status.setStyleSheet("background-color: #d1fae5; border-radius: 4px; padding: 6px;")
        else:
            self.list_status.setText(f"📊 {len(self.image_list)} ảnh")
            self.list_status.setStyleSheet("background-color: #fef7cd; border-radius: 4px; padding: 6px;")
    
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
            QMessageBox.information(self, "Thông báo", "Chưa có ảnh nào")
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
        
        self.list_status.setText("⏳ Đang quét camera...")
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
            self, "Chọn Camera", "Chọn camera để lọc:", 
            sorted(cameras), 0, False
        )
        
        if ok and camera:
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
        
        if not self.image_viewer.load_image(path):
            QMessageBox.warning(self, "Lỗi", f"Không thể tải ảnh:\n{Path(path).name}")
            return
        
        # Update file info
        self.update_file_info(path)
        
        # Update GPS and camera
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
            self.addr_label.setText("Không có GPS")
        
        self.update_nav()
        self.update_zoom_label()
    
    def update_file_info(self, path):
        try:
            stat = os.stat(path)
            self.file_labels['file_name'].setText(Path(path).name)
            self.file_labels['file_size'].setText(self.format_size(stat.st_size))
            self.file_labels['file_format'].setText(Path(path).suffix.upper())
            
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
            print(f"Error updating file info: {e}")
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_exif(self, path):
        if path in self.exif_cache:
            return self.exif_cache[path]
        
        try:
            if EXIFREAD_AVAILABLE:
                with open(path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                self.exif_cache[path] = tags
                return tags
        except:
            pass
        
        self.exif_cache[path] = {}
        return {}
    
    def get_gps_data(self, path):
        if path in self.gps_cache:
            return self.gps_cache[path]
        
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
                print(f"GPS parsing error: {e}")
        
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
        self.camera_labels['camera_model'].setText(camera[:35])
        
        lens = str(tags.get('EXIF LensModel', '--'))
        self.camera_labels['lens_model'].setText(lens[:35] if lens != '--' else '--')
        
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
    
    def load_address_async(self, lat, lon):
        self.addr_label.setText("🔄 Đang tải địa chỉ...")
        
        if self.address_loader and self.address_loader.isRunning():
            self.address_loader.terminate()
        
        self.address_loader = AddressLoader(lat, lon)
        self.address_loader.result.connect(self.addr_label.setText)
        self.address_loader.start()
    
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
            <div style='font-family: Segoe UI; width: 250px;'>
                <h4 style='margin: 0 0 10px 0;'>📍 Vị trí ảnh</h4>
                <p><b>File:</b> {Path(self.image_list[self.current_index]).name}</p>
                <p><b>Tọa độ:</b> {self.current_gps['lat']:.6f}, {self.current_gps['lon']:.6f}</p>
                <p><b>Độ cao:</b> {self.current_gps['alt']}</p>
                <p><b>Thời gian:</b> {self.current_gps['time']}</p>
            </div>
            """
            
            folium.Marker(
                [self.current_gps['lat'], self.current_gps['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip="📍 Nhấn để xem chi tiết",
                icon=folium.Icon(color='red', icon='camera', prefix='fa')
            ).add_to(m)
            
            folium.Circle(
                [self.current_gps['lat'], self.current_gps['lon']],
                radius=50,
                color='red',
                fill=True,
                fillOpacity=0.2
            ).add_to(m)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            m.save(temp_file.name)
            temp_file.close()
            
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
        
        # Collect GPS images
        gps_images = []
        for p in self.image_list:
            gps = self.get_gps_data(p)
            if gps:
                gps_images.append((p, gps))
        
        if not gps_images:
            QMessageBox.information(self, "Thông báo", "Không có ảnh nào có GPS")
            return
        
        try:
            # Calculate center
            lats = [g['lat'] for _, g in gps_images]
            lons = [g['lon'] for _, g in gps_images]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            
            # Add markers
            for i, (path, gps) in enumerate(gps_images, 1):
                popup_html = f"""
                <div style='font-family: Segoe UI; width: 220px;'>
                    <h4 style='margin: 0 0 8px 0;'>#{i} - {Path(path).name[:30]}</h4>
                    <p><b>Tọa độ:</b> {gps['lat']:.6f}, {gps['lon']:.6f}</p>
                    <p><b>Độ cao:</b> {gps['alt']}</p>
                    <p><b>Thời gian:</b> {gps['time'][:16]}</p>
                </div>
                """
                
                color = 'red' if i == 1 else ('green' if i == len(gps_images) else 'blue')
                
                folium.Marker(
                    [gps['lat'], gps['lon']],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"#{i} - {Path(path).name[:25]}",
                    icon=folium.Icon(color=color, icon='camera', prefix='fa')
                ).add_to(m)
            
            # Add route line
            if len(gps_images) > 1:
                coordinates = [[g['lat'], g['lon']] for _, g in gps_images]
                folium.PolyLine(
                    coordinates,
                    color='#0078D4',
                    weight=3,
                    opacity=0.7,
                    popup=f"Tuyến đường: {len(gps_images)} ảnh"
                ).add_to(m)
            
            # Add legend
            legend_html = f"""
            <div style="position: fixed; bottom: 50px; left: 50px; width: 200px;
                        background-color: white; border: 2px solid #0078D4; z-index: 9999;
                        border-radius: 8px; padding: 15px; font-family: 'Segoe UI';
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                <h4 style="margin: 0 0 10px 0; color: #0078D4;">📍 Bản đồ tổng quan</h4>
                <p style="margin: 5px 0;">🔴 Ảnh đầu tiên</p>
                <p style="margin: 5px 0;">🔵 Ảnh ở giữa</p>
                <p style="margin: 5px 0;">🟢 Ảnh cuối cùng</p>
                <hr style="margin: 10px 0;">
                <p style="margin: 5px 0; font-weight: bold;">📊 Tổng: {len(gps_images)} ảnh</p>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            m.save(temp_file.name)
            temp_file.close()
            
            webbrowser.open('file://' + os.path.abspath(temp_file.name))
            
            QMessageBox.information(
                self, "Thành công", 
                f"Đã tạo bản đồ với {len(gps_images)} ảnh có GPS!"
            )
            
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
            
            # Update status
            total_display = len(self.display_list)
            if self.is_filtered or self.search_box.text().strip():
                self.status_right.setText(
                    f"Đang xem: {idx + 1}/{total_display} (Tổng: {len(self.image_list)})"
                )
            else:
                self.status_right.setText(f"Đang xem: {idx + 1}/{total_display}")
    
    def update_zoom_label(self):
        scale_percent = int(self.image_viewer.scale * 100)
        self.zoom_label.setText(f"{scale_percent}%")
    
    def clear_all(self):
        if not self.image_list:
            return
        
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Bạn có chắc muốn xóa {len(self.image_list)} ảnh khỏi danh sách?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
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
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.prev_image()
        elif event.key() == Qt.Key.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key.Key_Escape:
            if self.image_viewer.original_pixmap:
                self.image_viewer.fit_to_screen()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set Windows 11 font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = GPSPhotoViewer()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()