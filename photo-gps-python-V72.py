import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import webbrowser
import os
import tempfile
import datetime

# Import thư viện
try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False
    print("⚠️ exifread chưa cài: pip install exifread")

try:
    from PIL import Image, ExifTags, ImageTk, ImageOps
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False
    print("⚠️ HEIC chưa hỗ trợ: pip install pillow pillow-heif")

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("⚠️ folium chưa cài: pip install folium")

try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("⚠️ geopy chưa cài: pip install geopy")

class ImageViewer:
    """Image viewer with zoom, pan, flip - OPTIMIZED"""
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg='#1f2937')
        self.frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(self.frame, bg='#1f2937', highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill='both', expand=True)
        
        # Toolbar
        toolbar = tk.Frame(self.frame, bg='#374151', height=40)
        toolbar.pack(side='bottom', fill='x')
        
        btn_style = {'font': ('Arial', 9), 'bg': '#4b5563', 'fg': 'white', 
                    'relief': 'flat', 'padx': 8, 'pady': 5, 'cursor': 'hand2'}
        
        tk.Button(toolbar, text="🔍+", command=self.zoom_in, **btn_style).pack(side='left', padx=1, pady=5)
        tk.Button(toolbar, text="🔍-", command=self.zoom_out, **btn_style).pack(side='left', padx=1)
        tk.Button(toolbar, text="⟲ Fit", command=self.fit_to_screen, **btn_style).pack(side='left', padx=1)
        tk.Button(toolbar, text="100%", command=self.actual_size, **btn_style).pack(side='left', padx=1)
        tk.Button(toolbar, text="↔️", command=self.flip_horizontal, **btn_style).pack(side='left', padx=1)
        tk.Button(toolbar, text="↕️", command=self.flip_vertical, **btn_style).pack(side='left', padx=1)
        tk.Button(toolbar, text="↻", command=self.rotate_right, **btn_style).pack(side='left', padx=1)
        tk.Button(toolbar, text="↺", command=self.rotate_left, **btn_style).pack(side='left', padx=1)
        
        self.zoom_label = tk.Label(toolbar, text="100%", font=('Arial', 9), bg='#374151', fg='white')
        self.zoom_label.pack(side='right', padx=10)
        
        # Variables
        self.original_image = None
        self.display_image = None
        self.photo = None
        self.scale = 1.0
        self.canvas_image = None
        self.img_x = 0
        self.img_y = 0
        self.drag_data = {'x': 0, 'y': 0}
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False
        self._render_scheduled = False
        self._mouse_x = 0
        self._mouse_y = 0
        
        # Bindings
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-4>', self.on_mousewheel)
        self.canvas.bind('<Button-5>', self.on_mousewheel)
        self.canvas.bind('<Motion>', self.on_mouse_move)
    
    def load_image(self, file_path):
        try:
            self.original_image = Image.open(file_path)
            self.rotation = 0
            self.flip_h = False
            self.flip_v = False
            self.original_image = ImageOps.exif_transpose(self.original_image)
            self._update_display_image()
            self.fit_to_screen()
            return True
        except Exception as e:
            print(f"Lỗi load ảnh: {e}")
            self.show_placeholder("Không thể tải ảnh")
            return False
    
    def _update_display_image(self):
        if not self.original_image:
            return
        img = self.original_image.copy()
        if self.rotation:
            img = img.rotate(-self.rotation, expand=True)
        if self.flip_h:
            img = ImageOps.mirror(img)
        if self.flip_v:
            img = ImageOps.flip(img)
        self.display_image = img
    
    def show_placeholder(self, text="Chọn ảnh"):
        self.canvas.delete('all')
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text=text, font=('Arial', 14), fill='#9ca3af'
        )
    
    def fit_to_screen(self):
        if not self.display_image:
            return
        self.canvas.update()
        canvas_w = max(self.canvas.winfo_width(), 400)
        canvas_h = max(self.canvas.winfo_height(), 300)
        img_w, img_h = self.display_image.size
        self.scale = min(canvas_w / img_w, canvas_h / img_h) * 0.95
        self.img_x = canvas_w // 2
        self.img_y = canvas_h // 2
        self.schedule_render()
    
    def actual_size(self):
        if not self.display_image:
            return
        self.scale = 1.0
        self.canvas.update()
        self.img_x = self.canvas.winfo_width() // 2
        self.img_y = self.canvas.winfo_height() // 2
        self.schedule_render()
    
    def zoom_in(self):
        self._zoom_at_center(1.2)
    
    def zoom_out(self):
        self._zoom_at_center(1/1.2)
    
    def _zoom_at_center(self, factor):
        if not self.display_image:
            return
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        center_x = canvas_w // 2
        center_y = canvas_h // 2
        dx = center_x - self.img_x
        dy = center_y - self.img_y
        self.scale *= factor
        self.img_x = center_x - dx * factor
        self.img_y = center_y - dy * factor
        self.schedule_render()
    
    def flip_horizontal(self):
        self.flip_h = not self.flip_h
        self._update_display_image()
        self.schedule_render()
    
    def flip_vertical(self):
        self.flip_v = not self.flip_v
        self._update_display_image()
        self.schedule_render()
    
    def rotate_right(self):
        self.rotation = (self.rotation + 90) % 360
        self._update_display_image()
        self.fit_to_screen()
    
    def rotate_left(self):
        self.rotation = (self.rotation - 90) % 360
        self._update_display_image()
        self.fit_to_screen()
    
    def schedule_render(self):
        if not self._render_scheduled:
            self._render_scheduled = True
            self.canvas.after(10, self._do_render)
    
    def _do_render(self):
        self._render_scheduled = False
        if not self.display_image:
            return
        img_w, img_h = self.display_image.size
        new_w = int(img_w * self.scale)
        new_h = int(img_h * self.scale)
        
        max_dim = 4000
        if new_w > max_dim or new_h > max_dim:
            scale_down = min(max_dim / new_w, max_dim / new_h)
            new_w = int(new_w * scale_down)
            new_h = int(new_h * scale_down)
        
        if new_w > 0 and new_h > 0:
            resample = Image.Resampling.LANCZOS if new_w < 3000 else Image.Resampling.BILINEAR
            resized = self.display_image.resize((new_w, new_h), resample)
            self.photo = ImageTk.PhotoImage(resized)
            self.canvas.delete('all')
            self.canvas_image = self.canvas.create_image(
                self.img_x, self.img_y, image=self.photo, anchor='center'
            )
            self.zoom_label.config(text=f"{int(self.scale * 100)}%")
    
    def on_mouse_move(self, event):
        self._mouse_x = event.x
        self._mouse_y = event.y
    
    def on_press(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.canvas.config(cursor='fleur')  # Cross arrows - compatible with Windows
    
    def on_drag(self, event):
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        self.img_x += dx
        self.img_y += dy
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        if self.canvas_image:
            self.canvas.move(self.canvas_image, dx, dy)
    
    def on_release(self, event):
        self.canvas.config(cursor='crosshair')
    
    def on_mousewheel(self, event):
        if not self.display_image:
            return
        mouse_x = self._mouse_x
        mouse_y = self._mouse_y
        
        if event.num == 4 or event.delta > 0:
            factor = 1.1
        elif event.num == 5 or event.delta < 0:
            factor = 1/1.1
        else:
            return
        
        dx = mouse_x - self.img_x
        dy = mouse_y - self.img_y
        old_scale = self.scale
        self.scale *= factor
        self.scale = max(0.05, min(self.scale, 20.0))
        actual_factor = self.scale / old_scale
        self.img_x = mouse_x - dx * actual_factor
        self.img_y = mouse_y - dy * actual_factor
        self.schedule_render()

class PhotoGPSViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("📍 GPS Photo Viewer Professional")
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        window_w = min(1600, int(screen_w * 0.9))
        window_h = min(900, int(screen_h * 0.9))
        x = (screen_w - window_w) // 2
        y = (screen_h - window_h) // 2
        self.root.geometry(f"{window_w}x{window_h}+{x}+{y}")
        self.root.configure(bg='#f0f4f8')
        self.root.minsize(1200, 700)
        
        self.image_list = []
        self.current_index = -1
        self.current_image_data = None
        self.map_file = None
        self.gps_cache = {}
        self.exif_cache = {}
        
        # Advanced features
        self.filtered_list = []  # For search/filter
        self.is_filtered = False
        self.display_list = []  # Current displayed list (for indexing)
        
        self.create_widgets()
        self.setup_drag_drop()
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
    
    def setup_drag_drop(self):
        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        except:
            pass
    
    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        valid = []
        for f in files:
            f = f.strip('{}')
            if os.path.isfile(f) and os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                valid.append(f)
        if valid:
            self.load_images(valid)
    
    def on_window_resize(self, event):
        if event.widget == self.root:
            if hasattr(self, 'image_viewer') and self.image_viewer.original_image:
                self.root.after(100, self.image_viewer.fit_to_screen)
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg='#4f46e5', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="📍 GPS Photo Viewer", font=('Arial', 18, 'bold'),
                bg='#4f46e5', fg='white').pack(pady=8)
        tk.Label(header, text="Professional Edition", font=('Arial', 9),
                bg='#4f46e5', fg='#e0e7ff').pack()
        
        # Main
        main = tk.PanedWindow(self.root, orient='horizontal', sashwidth=5, bg='#cbd5e1')
        main.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Get current window size for initial proportions
        self.root.update_idletasks()
        current_width = self.root.winfo_width()
        if current_width < 800:  # Fallback if not rendered yet
            current_width = 1400
        
        # Left panel - 1/4
        left = tk.Frame(main, bg='#f0f4f8')
        main.add(left, minsize=250, width=int(current_width * 0.25))
        
        # Middle panel - 2/4 (50%)
        middle = tk.Frame(main, bg='#f0f4f8')
        main.add(middle, minsize=500, width=int(current_width * 0.5))
        
        # Right panel - 1/4
        right = tk.Frame(main, bg='#f0f4f8')
        main.add(right, minsize=250, width=int(current_width * 0.25))
        
        self.create_left_panel(left)
        self.create_middle_panel(middle)
        self.create_right_panel(right)
        
        # Status
        status = tk.Frame(self.root, bg='#1f2937', height=22)
        status.pack(side='bottom', fill='x')
        libs = f"exif:{'✓' if EXIFREAD_AVAILABLE else '✗'} heic:{'✓' if HEIC_SUPPORTED else '✗'} map:{'✓' if FOLIUM_AVAILABLE else '✗'} geo:{'✓' if GEOPY_AVAILABLE else '✗'}"
        tk.Label(status, text=libs, font=('Arial', 8), bg='#1f2937', fg='#9ca3af').pack(side='left', padx=10)
        self.status_right = tk.Label(status, text="", font=('Arial', 8), bg='#1f2937', fg='#9ca3af')
        self.status_right.pack(side='right', padx=10)
    
    def create_left_panel(self, parent):
        # Buttons
        bf = tk.Frame(parent, bg='#f0f4f8')
        bf.pack(fill='x', padx=5, pady=5)
        bs = {'font': ('Arial', 9, 'bold'), 'fg': 'white', 'relief': 'flat', 'cursor': 'hand2', 'pady': 6}
        tk.Button(bf, text="➕ Thêm", bg='#4f46e5', command=self.add_images, **bs).pack(side='left', fill='x', expand=True, padx=(0,2))
        tk.Button(bf, text="📂 Folder", bg='#7c3aed', command=self.add_folder, **bs).pack(side='left', fill='x', expand=True, padx=2)
        tk.Button(bf, text="🗑️", bg='#dc2626', command=self.clear_all, **bs).pack(side='left', padx=(2,0))
        
        # Search bar - NEW
        search_frame = tk.Frame(parent, bg='#ffffff', relief='solid', borderwidth=1)
        search_frame.pack(fill='x', padx=5, pady=(0,5))
        
        tk.Label(search_frame, text="🔍", font=('Arial', 10), bg='#ffffff').pack(side='left', padx=(5,0))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.on_search_change())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=('Arial', 9), bg='#f9fafb', relief='flat')
        search_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        self.clear_search_btn = tk.Button(search_frame, text="✕", font=('Arial', 8),
                                         bg='#ffffff', fg='#6b7280', relief='flat',
                                         cursor='hand2', command=self.clear_search)
        self.clear_search_btn.pack(side='right', padx=5)
        
        # Filter bar - NEW
        filter_frame = tk.Frame(parent, bg='#ffffff', relief='solid', borderwidth=1)
        filter_frame.pack(fill='x', padx=5, pady=(0,5))
        
        tk.Label(filter_frame, text="Lọc:", font=('Arial', 8, 'bold'),
                bg='#ffffff', fg='#374151').pack(side='left', padx=5)
        
        filter_btn_style = {'font': ('Arial', 8), 'bg': '#e5e7eb', 'fg': '#374151',
                           'relief': 'flat', 'cursor': 'hand2', 'padx': 6, 'pady': 3}
        
        tk.Button(filter_frame, text="🌍 Có GPS", command=lambda: self.apply_filter('has_gps'),
                 **filter_btn_style).pack(side='left', padx=2)
        tk.Button(filter_frame, text="❌ Không GPS", command=lambda: self.apply_filter('no_gps'),
                 **filter_btn_style).pack(side='left', padx=2)
        tk.Button(filter_frame, text="📷 Camera", command=self.filter_by_camera,
                 **filter_btn_style).pack(side='left', padx=2)
        
        # Reset button with different color
        reset_style = filter_btn_style.copy()
        reset_style['bg'] = '#fbbf24'
        tk.Button(filter_frame, text="🔄 Reset", command=self.clear_filter,
                 **reset_style).pack(side='right', padx=5)
        
        # Sort
        sf = tk.Frame(parent, bg='#ffffff', relief='solid', borderwidth=1)
        sf.pack(fill='x', padx=5, pady=(0,5))
        tk.Label(sf, text="Sắp xếp:", font=('Arial', 8, 'bold'), bg='#ffffff', fg='#374151').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.sort_var = tk.StringVar(value="name")
        sorts = [("Tên", "name"), ("Ngày↓", "date_desc"), ("Ngày↑", "date_asc"), ("Size", "size"), ("Type", "type")]
        for i, (t, v) in enumerate(sorts):
            tk.Radiobutton(sf, text=t, variable=self.sort_var, value=v, font=('Arial', 8),
                          bg='#ffffff', fg='#374151', selectcolor='#dbeafe',
                          command=self.sort_images).grid(row=0, column=i+1, padx=2, sticky='w')
        
        # List
        lf = tk.LabelFrame(parent, text="📋 Danh Sách", font=('Arial', 9, 'bold'),
                          bg='#ffffff', fg='#1f2937')
        lf.pack(fill='both', expand=True, padx=5, pady=(0,5))
        scroll = tk.Scrollbar(lf)
        scroll.pack(side='right', fill='y')
        self.listbox = tk.Listbox(lf, font=('Arial', 9), yscrollcommand=scroll.set,
                                  bg='#f9fafb', fg='#1f2937', selectbackground='#4f46e5',
                                  selectforeground='white', relief='flat', highlightthickness=0)
        self.listbox.pack(side='left', fill='both', expand=True)
        scroll.config(command=self.listbox.yview)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        self.list_status = tk.Label(parent, text="0 ảnh", font=('Arial', 8),
                                    bg='#fef3c7', fg='#92400e', pady=3)
        self.list_status.pack(fill='x', padx=5)
    
    def create_middle_panel(self, parent):
        frame = tk.LabelFrame(parent, text="🖼️ Xem Ảnh (Zoom: Chuột | Pan: Kéo)", 
                             font=('Arial', 10, 'bold'), bg='#ffffff', fg='#1f2937')
        frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.image_viewer = ImageViewer(frame)
        
        nav = tk.Frame(parent, bg='#f0f4f8')
        nav.pack(fill='x', padx=5, pady=5)
        bs = {'font': ('Arial', 10, 'bold'), 'fg': 'white', 'relief': 'flat',
             'cursor': 'hand2', 'pady': 10}
        self.prev_btn = tk.Button(nav, text="⬅️ Trước", bg='#6b7280', 
                                  command=self.prev_image, state='disabled', **bs)
        self.prev_btn.pack(side='left', fill='x', expand=True, padx=(0,3))
        self.next_btn = tk.Button(nav, text="Tiếp ➡️", bg='#6b7280',
                                  command=self.next_image, state='disabled', **bs)
        self.next_btn.pack(side='right', fill='x', expand=True, padx=(3,0))
    
    def create_right_panel(self, parent):
        # File info
        ff = tk.LabelFrame(parent, text="📄 File", font=('Arial', 9, 'bold'),
                          bg='#ffffff', fg='#1f2937', padx=10, pady=8)
        ff.pack(fill='x', padx=5, pady=5)
        ig = tk.Frame(ff, bg='#ffffff')
        ig.pack(fill='x')
        file_labels = [("Tên:", 'file_name'), ("Size:", 'file_size'), ("Format:", 'file_format'),
                      ("Dimensions:", 'image_dimensions'), ("Created:", 'file_created'), ("Modified:", 'file_modified')]
        self.file_info_labels = {}
        for i, (lt, attr) in enumerate(file_labels):
            tk.Label(ig, text=lt, font=('Arial', 7, 'bold'), bg='#ffffff', fg='#6b7280', anchor='w').grid(row=i, column=0, sticky='w', pady=1)
            lbl = tk.Label(ig, text="--", font=('Arial', 8), bg='#ffffff', fg='#374151', anchor='w')
            lbl.grid(row=i, column=1, sticky='w', padx=(5,0), pady=1)
            self.file_info_labels[attr] = lbl
        ig.columnconfigure(1, weight=1)
        
        # Camera
        cf = tk.LabelFrame(parent, text="📷 Camera", font=('Arial', 9, 'bold'),
                          bg='#ffffff', fg='#1f2937', padx=10, pady=8)
        cf.pack(fill='x', padx=5, pady=5)
        cg = tk.Frame(cf, bg='#ffffff')
        cg.pack(fill='x')
        cam_labels = [("Camera:", 'camera_model'), ("Lens:", 'lens_model'), ("ISO:", 'iso'),
                     ("Shutter:", 'shutter_speed'), ("Aperture:", 'aperture'), ("Focal:", 'focal_length')]
        self.camera_info_labels = {}
        for i, (lt, attr) in enumerate(cam_labels):
            r = i // 2
            c = (i % 2) * 2
            tk.Label(cg, text=lt, font=('Arial', 7, 'bold'), bg='#ffffff', fg='#6b7280', anchor='w').grid(row=r, column=c, sticky='w', pady=1, padx=(0,2))
            lbl = tk.Label(cg, text="--", font=('Arial', 8), bg='#ffffff', fg='#374151', anchor='w')
            lbl.grid(row=r, column=c+1, sticky='w', pady=1)
            self.camera_info_labels[attr] = lbl
        cg.columnconfigure(1, weight=1)
        cg.columnconfigure(3, weight=1)
        
        # Address
        af = tk.LabelFrame(parent, text="🏠 Địa Chỉ", font=('Arial', 9, 'bold'),
                          bg='#ffffff', fg='#1f2937', padx=10, pady=8)
        af.pack(fill='x', padx=5, pady=5)
        self.addr_label = tk.Label(af, text="--", font=('Arial', 8),
                                   bg='#ffffff', fg='#374151', anchor='w', 
                                   justify='left', wraplength=300)
        self.addr_label.pack(fill='x')
        
        # GPS
        gf = tk.LabelFrame(parent, text="📍 GPS", font=('Arial', 9, 'bold'),
                          bg='#ffffff', fg='#1f2937', padx=10, pady=8)
        gf.pack(fill='both', expand=True, padx=5, pady=5)
        gg = tk.Frame(gf, bg='#ffffff')
        gg.pack(fill='both', expand=True)
        gps_labels = [("Vĩ độ:", 'lat'), ("Kinh độ:", 'lon'), ("Độ cao:", 'alt'), ("Thời gian:", 'time')]
        for i, (lt, attr) in enumerate(gps_labels):
            f = tk.Frame(gg, bg='#f0fdf4' if i<2 else '#eff6ff', relief='solid', borderwidth=1)
            f.grid(row=i//2, column=(i%2)*2, columnspan=2, sticky='ew', padx=2, pady=2)
            tk.Label(f, text=lt, font=('Arial', 7, 'bold'),
                    bg=f['bg'], fg='#15803d' if i<2 else '#1e40af').pack(anchor='w', padx=5, pady=1)
            lbl = tk.Label(f, text="--", font=('Arial', 8), bg=f['bg'], fg='#1f2937')
            lbl.pack(anchor='w', padx=5, pady=1)
            setattr(self, f'{attr}_label', lbl)
        gg.columnconfigure(0, weight=1)
        gg.columnconfigure(2, weight=1)
        
        # Map buttons
        mf = tk.Frame(gf, bg='#ffffff')
        mf.pack(fill='x', pady=8)
        bs = {'font': ('Arial', 10, 'bold'), 'fg': 'white', 'relief': 'flat',
             'cursor': 'hand2', 'pady': 11}
        self.google_btn = tk.Button(mf, text="🗺️ Google", bg='#2563eb',
                                    command=self.open_google_maps, state='disabled', **bs)
        self.google_btn.pack(side='left', fill='x', expand=True, padx=(0,2))
        self.html_btn = tk.Button(mf, text="🌐 HTML", bg='#059669',
                                  command=self.open_html_map, state='disabled', **bs)
        self.html_btn.pack(side='left', fill='x', expand=True, padx=2)
        
        # Advanced map button - NEW
        self.advanced_map_btn = tk.Button(mf, text="🗺️ All", bg='#7c3aed',
                                          command=self.show_all_on_map, state='normal', **bs)
        self.advanced_map_btn.pack(side='left', fill='x', expand=True, padx=(2,0))
    
    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Chọn ảnh",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.heic *.heif"), ("All", "*.*")]
        )
        if files:
            self.load_images(list(files))
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục")
        if folder:
            files = []
            for f in os.listdir(folder):
                if os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.png', '.heic', '.heif']:
                    files.append(os.path.join(folder, f))
            if files:
                self.load_images(files)
            else:
                messagebox.showinfo("Thông báo", "Không có ảnh")
    
    def load_images(self, paths):
        added = 0
        for p in paths:
            if p not in self.image_list:
                self.image_list.append(p)
                added += 1
        if added > 0:
            if added > 20:
                self.list_status.config(text=f"⏳ Đang sắp xếp {added} ảnh...")
                self.root.update()
            self.sort_images()
            self.update_list_status()
            if self.current_index == -1 and self.image_list:
                self.listbox.selection_set(0)
                self.display_image(0)
    
    def sort_images(self):
        if not self.image_list:
            return
        current = self.image_list[self.current_index] if self.current_index >= 0 else None
        sort_by = self.sort_var.get()
        
        if len(self.image_list) > 50:
            self.list_status.config(text="⏳ Đang sắp xếp...")
            self.root.update()
        
        if sort_by == "name":
            self.image_list.sort(key=lambda x: os.path.basename(x).lower())
        elif sort_by in ["date_desc", "date_asc"]:
            def get_date(p):
                if p in self.exif_cache:
                    tags = self.exif_cache[p]
                else:
                    try:
                        if EXIFREAD_AVAILABLE:
                            with open(p, 'rb') as f:
                                tags = exifread.process_file(f, details=False, stop_tag='DateTimeOriginal')
                            self.exif_cache[p] = tags
                        else:
                            tags = {}
                    except:
                        tags = {}
                if 'EXIF DateTimeOriginal' in tags:
                    return str(tags['EXIF DateTimeOriginal'])
                return str(os.path.getmtime(p))
            self.image_list.sort(key=get_date, reverse=(sort_by == "date_desc"))
        elif sort_by == "size":
            self.image_list.sort(key=lambda x: os.path.getsize(x), reverse=True)
        elif sort_by == "type":
            self.image_list.sort(key=lambda x: os.path.splitext(x)[1].lower())
        
        # Update display based on current state
        if self.is_filtered:
            # Re-apply filter on sorted list
            temp_filtered = [p for p in self.image_list if p in self.filtered_list]
            self.filtered_list = temp_filtered
            self.update_listbox(self.filtered_list)
        else:
            self.update_listbox(self.image_list)
        
        # Restore selection
        if current and current in self.image_list:
            idx = self.image_list.index(current)
            self.current_index = idx
            # Find in display list
            if current in self.display_list:
                display_idx = self.display_list.index(current)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(display_idx)
                self.listbox.see(display_idx)
        
        self.update_list_status()
    
    def on_select(self, event):
        sel = self.listbox.curselection()
        if sel:
            # Get the actual index from display_list
            display_index = sel[0]
            if display_index < len(self.display_list):
                selected_path = self.display_list[display_index]
                # Find actual index in full image_list
                if selected_path in self.image_list:
                    actual_index = self.image_list.index(selected_path)
                    self.display_image(actual_index)
    
    def display_image(self, index):
        if index < 0 or index >= len(self.image_list):
            return
        self.current_index = index
        path = self.image_list[index]
        
        if self.image_viewer.load_image(path):
            stat = os.stat(path)
            self.file_info_labels['file_name'].config(text=os.path.basename(path))
            self.file_info_labels['file_size'].config(text=self.format_size(stat.st_size))
            self.file_info_labels['file_format'].config(text=os.path.splitext(path)[1].upper())
            
            try:
                img = Image.open(path)
                self.file_info_labels['image_dimensions'].config(text=f"{img.width} × {img.height} px")
                img.close()
            except:
                self.file_info_labels['image_dimensions'].config(text="--")
            
            self.file_info_labels['file_created'].config(
                text=datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M'))
            self.file_info_labels['file_modified'].config(
                text=datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'))
            
            self.current_image_data = self.get_gps_data_cached(path)
            
            if self.current_image_data:
                self.display_gps()
                self.display_camera_info(path)
                self.google_btn.config(state='normal')
                self.html_btn.config(state='normal')
                self.addr_label.config(text="🔄 Đang tải...")
                self.root.after(200, self.load_address)
                if FOLIUM_AVAILABLE:
                    self.create_map()
            else:
                self.clear_gps()
                self.clear_camera_info()
                self.addr_label.config(text="Không có GPS")
        
        self.update_nav()
        self.update_status()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_gps_data_cached(self, path):
        if path in self.gps_cache:
            return self.gps_cache[path]
        data = self.get_gps_data(path)
        self.gps_cache[path] = data
        return data
    
    def get_gps_data(self, path):
        if EXIFREAD_AVAILABLE:
            try:
                with open(path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                    def to_deg(val):
                        d = float(val.values[0].num) / float(val.values[0].den)
                        m = float(val.values[1].num) / float(val.values[1].den)
                        s = float(val.values[2].num) / float(val.values[2].den)
                        return d + m/60 + s/3600
                    lat = to_deg(tags['GPS GPSLatitude'])
                    if 'GPS GPSLatitudeRef' in tags and str(tags['GPS GPSLatitudeRef']) == 'S':
                        lat = -lat
                    lon = to_deg(tags['GPS GPSLongitude'])
                    if 'GPS GPSLongitudeRef' in tags and str(tags['GPS GPSLongitudeRef']) == 'W':
                        lon = -lon
                    alt = 'N/A'
                    if 'GPS GPSAltitude' in tags:
                        v = tags['GPS GPSAltitude'].values[0]
                        alt = f"{float(v.num)/float(v.den):.1f} m"
                    dt = 'N/A'
                    if 'EXIF DateTimeOriginal' in tags:
                        dt = str(tags['EXIF DateTimeOriginal'])
                    return {'lat': lat, 'lon': lon, 'alt': alt, 'time': dt}
            except:
                pass
        return None
    
    def display_gps(self):
        if self.current_image_data:
            self.lat_label.config(text=f"{self.current_image_data['lat']:.6f}°")
            self.lon_label.config(text=f"{self.current_image_data['lon']:.6f}°")
            self.alt_label.config(text=self.current_image_data['alt'])
            self.time_label.config(text=self.current_image_data['time'])
    
    def clear_gps(self):
        self.lat_label.config(text="--")
        self.lon_label.config(text="--")
        self.alt_label.config(text="--")
        self.time_label.config(text="--")
        self.google_btn.config(state='disabled')
        self.html_btn.config(state='disabled')
    
    def display_camera_info(self, path):
        try:
            if not EXIFREAD_AVAILABLE:
                return
            if path in self.exif_cache:
                tags = self.exif_cache[path]
            else:
                with open(path, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                self.exif_cache[path] = tags
            
            make = str(tags.get('Image Make', '')).strip()
            model = str(tags.get('Image Model', '')).strip()
            camera = f"{make} {model}".strip() if make or model else "--"
            self.camera_info_labels['camera_model'].config(text=camera[:25])
            
            lens = str(tags.get('EXIF LensModel', '--'))
            self.camera_info_labels['lens_model'].config(text=lens[:25] if lens != '--' else '--')
            
            iso = str(tags.get('EXIF ISOSpeedRatings', '--'))
            self.camera_info_labels['iso'].config(text=f"ISO {iso}" if iso != '--' else '--')
            
            shutter = tags.get('EXIF ExposureTime', None)
            if shutter:
                try:
                    val = shutter.values[0]
                    if val.den > val.num:
                        self.camera_info_labels['shutter_speed'].config(text=f"1/{val.den//val.num}s")
                    else:
                        self.camera_info_labels['shutter_speed'].config(text=f"{float(val.num)/float(val.den):.2f}s")
                except:
                    self.camera_info_labels['shutter_speed'].config(text="--")
            else:
                self.camera_info_labels['shutter_speed'].config(text="--")
            
            aperture = tags.get('EXIF FNumber', None)
            if aperture:
                try:
                    val = aperture.values[0]
                    f_val = float(val.num) / float(val.den)
                    self.camera_info_labels['aperture'].config(text=f"f/{f_val:.1f}")
                except:
                    self.camera_info_labels['aperture'].config(text="--")
            else:
                self.camera_info_labels['aperture'].config(text="--")
            
            focal = tags.get('EXIF FocalLength', None)
            if focal:
                try:
                    val = focal.values[0]
                    fl = float(val.num) / float(val.den)
                    self.camera_info_labels['focal_length'].config(text=f"{fl:.0f}mm")
                except:
                    self.camera_info_labels['focal_length'].config(text="--")
            else:
                self.camera_info_labels['focal_length'].config(text="--")
        except Exception as e:
            print(f"Lỗi camera info: {e}")
            self.clear_camera_info()
    
    def clear_camera_info(self):
        for lbl in self.camera_info_labels.values():
            lbl.config(text="--")
    
    def load_address(self):
        if not self.current_image_data or not GEOPY_AVAILABLE:
            self.addr_label.config(text="Không có dịch vụ")
            return
        try:
            geo = Nominatim(user_agent="gps_viewer", timeout=10)
            loc = geo.reverse(f"{self.current_image_data['lat']}, {self.current_image_data['lon']}", language='vi')
            if loc:
                self.addr_label.config(text=loc.address)
            else:
                self.addr_label.config(text="Không tìm thấy")
        except Exception as e:
            self.addr_label.config(text=f"Lỗi: {str(e)[:30]}")
    
    def create_map(self):
        if not FOLIUM_AVAILABLE or not self.current_image_data:
            return
        try:
            lat = self.current_image_data['lat']
            lon = self.current_image_data['lon']
            m = folium.Map(location=[lat, lon], zoom_start=15)
            popup = f"""<b>📍 Vị trí</b><br><b>File:</b> {os.path.basename(self.image_list[self.current_index])}<br>
            <b>Tọa độ:</b> {lat:.6f}, {lon:.6f}<br><b>Độ cao:</b> {self.current_image_data['alt']}<br>
            <b>Thời gian:</b> {self.current_image_data['time']}"""
            folium.Marker([lat, lon], popup=folium.Popup(popup, max_width=300),
                         tooltip="📍 Click", icon=folium.Icon(color='red', icon='camera', prefix='fa')).add_to(m)
            folium.Circle([lat, lon], radius=50, color='red', fill=True, fillColor='red', fillOpacity=0.2).add_to(m)
            if self.map_file:
                try:
                    os.unlink(self.map_file.name)
                except:
                    pass
            self.map_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            m.save(self.map_file.name)
            self.map_file.close()
        except Exception as e:
            print(f"Lỗi map: {e}")
    
    def open_google_maps(self):
        if self.current_image_data:
            webbrowser.open(f"https://www.google.com/maps?q={self.current_image_data['lat']},{self.current_image_data['lon']}")
    
    def open_html_map(self):
        if self.map_file:
            webbrowser.open('file://' + os.path.abspath(self.map_file.name))
    
    def prev_image(self):
        if self.current_index > 0:
            idx = self.current_index - 1
            # Find in display list
            path = self.image_list[idx]
            if path in self.display_list:
                display_idx = self.display_list.index(path)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(display_idx)
                self.listbox.see(display_idx)
            self.display_image(idx)
    
    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            idx = self.current_index + 1
            # Find in display list
            path = self.image_list[idx]
            if path in self.display_list:
                display_idx = self.display_list.index(path)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(display_idx)
                self.listbox.see(display_idx)
            self.display_image(idx)
    
    def update_nav(self):
        if len(self.image_list) == 0:
            self.prev_btn.config(state='disabled')
            self.next_btn.config(state='disabled')
        else:
            self.prev_btn.config(state='normal' if self.current_index > 0 else 'disabled')
            self.next_btn.config(state='normal' if self.current_index < len(self.image_list) - 1 else 'disabled')
    
    def update_list_status(self):
        if self.is_filtered:
            self.list_status.config(text=f"🔍 {len(self.filtered_list)}/{len(self.image_list)} ảnh", bg='#d1fae5')
        else:
            self.list_status.config(text=f"📊 {len(self.image_list)} ảnh", bg='#fef3c7')
    
    def update_status(self):
        if self.current_index >= 0 and self.image_list:
            self.status_right.config(text=f"Đang xem: {self.current_index + 1}/{len(self.image_list)}")
        else:
            self.status_right.config(text="")
    
    def clear_all(self):
        if not self.image_list:
            return
        if messagebox.askyesno("Xác nhận", f"Xóa {len(self.image_list)} ảnh?"):
            self.image_list.clear()
            self.filtered_list.clear()
            self.is_filtered = False
            self.listbox.delete(0, tk.END)
            self.current_index = -1
            self.current_image_data = None
            self.gps_cache.clear()
            self.exif_cache.clear()
            self.image_viewer.show_placeholder()
            for lbl in self.file_info_labels.values():
                lbl.config(text="--")
            self.clear_camera_info()
            self.addr_label.config(text="--")
            self.clear_gps()
            self.update_list_status()
            self.update_nav()
            self.update_status()
            if self.map_file:
                try:
                    os.unlink(self.map_file.name)
                except:
                    pass
                self.map_file = None
    
    # ==================== SEARCH & FILTER ====================
    
    def on_search_change(self):
        """Search as you type"""
        query = self.search_var.get().lower().strip()
        
        # Get source list
        source_list = self.filtered_list if self.is_filtered else self.image_list
        
        if not query:
            # Show all from source
            self.update_listbox(source_list)
            return
        
        # Search in current list
        results = [p for p in source_list if query in os.path.basename(p).lower()]
        
        self.update_listbox(results)
        self.list_status.config(text=f"🔍 Tìm thấy: {len(results)}/{len(source_list)}",bg='#dbeafe')
        
        # Auto-select first result if available
        if results:
            self.listbox.selection_set(0)
            self.listbox.see(0)
            # Display first result
            if results[0] in self.image_list:
                actual_index = self.image_list.index(results[0])
                self.display_image(actual_index)
    
    def clear_search(self):
        """Clear search box"""
        self.search_var.set("")
        source_list = self.filtered_list if self.is_filtered else self.image_list
        self.update_listbox(source_list)
        self.update_list_status()
    
    # ✅ ĐÚNG - Thêm progress indicator
    def apply_filter(self, filter_type):
        if not self.image_list:
            messagebox.showinfo("Thông báo", "Chưa có ảnh nào")
            return
        
        self.list_status.config(text="⏳ Đang lọc...", bg='#fef3c7')
        self.root.update_idletasks()
        
        self.filtered_list = []
        total = len(self.image_list)
        
        for i, p in enumerate(self.image_list):
            # Progress indicator every 10 items
            if i % 10 == 0 and total > 50:
                self.list_status.config(text=f"⏳ Đang lọc... {i}/{total}")
                self.root.update_idletasks()
            
            gps = self.get_gps_data_cached(p)
            if filter_type == 'has_gps' and gps:
                self.filtered_list.append(p)
            elif filter_type == 'no_gps' and not gps:
                self.filtered_list.append(p)
        
        filter_name = "có GPS" if filter_type == 'has_gps' else "không có GPS"
        self.is_filtered = True
        self.update_listbox(self.filtered_list)
        self.list_status.config(text=f"🌍 Lọc: {len(self.filtered_list)} ảnh {filter_name}", bg='#d1fae5')
        
        # Auto-select first
        if self.filtered_list:
            self.listbox.selection_set(0)
            self.listbox.see(0)
            if self.filtered_list[0] in self.image_list:
                actual_index = self.image_list.index(self.filtered_list[0])
                self.display_image(actual_index)
    
    def filter_by_camera(self):
        """Filter by camera model"""
        if not self.image_list:
            messagebox.showinfo("Thông báo", "Chưa có ảnh nào")
            return
        
        # Get unique cameras
        self.list_status.config(text="⏳ Đang tải camera...", bg='#fef3c7')
        self.root.update_idletasks()

        cameras = set()
        total = len(self.image_list)

        for i, p in enumerate(self.image_list):
            # Progress every 10 items for large lists
            if i % 10 == 0 and total > 50:
                self.list_status.config(text=f"⏳ Đang quét... {i}/{total}")
                self.root.update_idletasks()
            # Load EXIF nếu chưa có
            if p not in self.exif_cache:
                try:
                    if EXIFREAD_AVAILABLE:
                        with open(p, 'rb') as f:
                            tags = exifread.process_file(f, details=False)
                        self.exif_cache[p] = tags
                except:
                    self.exif_cache[p] = {}
            if p in self.exif_cache:
                tags = self.exif_cache[p]
                make = str(tags.get('Image Make', '')).strip()
                model = str(tags.get('Image Model', '')).strip()
                camera = f"{make} {model}".strip()
                if camera:
                    cameras.add(camera)
        
        if not cameras:
            messagebox.showinfo("Thông báo", "Không tìm thấy thông tin camera")
            return
        self.update_list_status()
        # Show selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Chọn Camera")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Chọn camera để lọc:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=('Arial', 9))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        for cam in sorted(cameras):
            listbox.insert(tk.END, cam)
        
        def apply():
            sel = listbox.curselection()
            if sel:
                selected_cam = listbox.get(sel[0])
                self.filtered_list = []
                for p in self.image_list:
                    if p in self.exif_cache:
                        tags = self.exif_cache[p]
                        make = str(tags.get('Image Make', '')).strip()
                        model = str(tags.get('Image Model', '')).strip()
                        camera = f"{make} {model}".strip()
                        if camera == selected_cam:
                            self.filtered_list.append(p)
                
                self.is_filtered = True
                self.update_listbox(self.filtered_list)
                self.list_status.config(text=f"📷 {len(self.filtered_list)} ảnh - {selected_cam}")
                dialog.destroy()
                
                # Auto-select first
                if self.filtered_list:
                    self.listbox.selection_set(0)
                    self.listbox.see(0)
                    if self.filtered_list[0] in self.image_list:
                        actual_index = self.image_list.index(self.filtered_list[0])
                        self.display_image(actual_index)
        
        tk.Button(dialog, text="Áp dụng", command=apply, bg='#4f46e5', fg='white',
                 font=('Arial', 10, 'bold'), cursor='hand2').pack(pady=10)
    
    def clear_filter(self):
        """Reset filter"""
        self.is_filtered = False
        self.filtered_list.clear()
        self.search_var.set("")
        self.update_listbox(self.image_list)
        self.update_list_status()
    
    def update_listbox(self, items):
        """Update listbox with items - WITH NUMBERING"""
        self.display_list = items  # Store current display list
        self.listbox.delete(0, tk.END)
        
        # Add items with numbering
        for i, p in enumerate(items, 1):
            # Format: [001] filename.jpg
            display_text = f"[{i:03d}] {os.path.basename(p)}"
            self.listbox.insert(tk.END, display_text)
    
    # ==================== ADVANCED MAP ====================
    
    def show_all_on_map(self):
        """Show all images with GPS on one map"""
        if not self.image_list:
            messagebox.showinfo("Thông báo", "Chưa có ảnh nào")
            return
        
        if not FOLIUM_AVAILABLE:
            messagebox.showerror("Lỗi", "Cần cài folium: pip install folium")
            return
        
        # Collect all GPS points
        self.list_status.config(text="⏳ Đang tạo bản đồ...")
        self.root.update()
        
        gps_images = []
        for p in self.image_list:
            gps = self.get_gps_data_cached(p)
            if gps:
                gps_images.append((p, gps))
        
        if not gps_images:
            messagebox.showinfo("Thông báo", "Không có ảnh nào có GPS")
            self.update_list_status()
            return
        
        try:
            # Calculate center
            lats = [g['lat'] for _, g in gps_images]
            lons = [g['lon'] for _, g in gps_images]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # Create map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            
            # Add markers
            for i, (path, gps) in enumerate(gps_images, 1):
                popup_html = f"""
                <div style='width:200px'>
                <b>#{i} - {os.path.basename(path)}</b><br>
                <b>Tọa độ:</b> {gps['lat']:.6f}, {gps['lon']:.6f}<br>
                <b>Độ cao:</b> {gps['alt']}<br>
                <b>Thời gian:</b> {gps['time'][:16] if len(gps['time']) > 16 else gps['time']}
                </div>
                """
                
                # Use different colors for markers
                color = 'red' if i == 1 else ('green' if i == len(gps_images) else 'blue')
                
                folium.Marker(
                    [gps['lat'], gps['lon']],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"#{i} - {os.path.basename(path)[:20]}",
                    icon=folium.Icon(color=color, icon='camera', prefix='fa')
                ).add_to(m)
            
            # Add polyline if more than 1 point (route)
            if len(gps_images) > 1:
                coordinates = [[g['lat'], g['lon']] for _, g in gps_images]
                folium.PolyLine(
                    coordinates,
                    color='red',
                    weight=2,
                    opacity=0.7,
                    popup=f"Route: {len(gps_images)} photos"
                ).add_to(m)
            
            # Add legend
            legend_html = f"""
            <div style="position: fixed; bottom: 50px; left: 50px; width: 180px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <b>📍 Bản đồ tổng quan</b><br>
            🔴 Ảnh đầu tiên<br>
            🔵 Ảnh ở giữa<br>
            🟢 Ảnh cuối cùng<br>
            📊 Tổng: {len(gps_images)} ảnh
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Save and open
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            m.save(temp_file.name)
            temp_file.close()
            
            webbrowser.open('file://' + os.path.abspath(temp_file.name))
            
            self.update_list_status()
            messagebox.showinfo("Thành công", f"Đã tạo bản đồ với {len(gps_images)} ảnh!")
            
        except Exception as e:
            print(f"Lỗi tạo advanced map: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Lỗi", f"Không thể tạo bản đồ: {str(e)}")
            self.update_list_status()

def main():
    try:
        root = TkinterDnD.Tk()
    except:
        root = tk.Tk()
    app = PhotoGPSViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
