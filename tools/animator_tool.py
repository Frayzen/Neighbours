import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageChops, ImageDraw, ImageOps
import csv
import os

# Layout Constants
SIDEBAR_WIDTH = 380 

# Material Design 3 Dark Mode Palette
COLORS = {
    "bg_base": "#141218",       # Very dark surface
    "bg_surface": "#1E1E1E",    # Component background
    "bg_surface_variant": "#49454F", # Hover/Input bg
    "primary": "#D0BCFF",       # Lavender accent
    "primary_container": "#4F378B",
    "on_primary": "#381E72",
    "secondary": "#CCC2DC",
    "error": "#F2B8B5",
    "text_main": "#E6E1E5",     # Off-white text
    "text_dim": "#CAC4D0",
    "outline": "#938F99",
    "success": "#B8F2B9"
}

# Standard Animation Names (Mirrors src/config/animation_constants.py)
STANDARD_ANIMATIONS = [
    "idle", "walk", "run", "jump", "dash",
    "closeRangeAttack", "rangeAttack",
    "death", "phaseChange", "hit", "spawn",
    "bossAttack1", "bossAttack2", "bossSpecial"
]

class AnimationNameDialog(tk.Toplevel):
    def __init__(self, parent, options):
        super().__init__(parent)
        self.title("New Animation")
        self.geometry("350x180")
        self.configure(bg=COLORS["bg_base"])
        self.options = options
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        # Center relative to parent
        x = parent.winfo_rootx() + 50
        y = parent.winfo_rooty() + 50
        self.geometry(f"+{x}+{y}")
        
        self._setup_ui()
        self.wait_window(self)

    def _setup_ui(self):
        lbl = tk.Label(self, text="Select or Enter Animation Name:", 
                 bg=COLORS["bg_base"], fg=COLORS["text_main"], font=("Segoe UI", 10))
        lbl.pack(pady=(20, 10))
        
        self.var_name = tk.StringVar()
        
        # Style Combobox
        style = ttk.Style()
        style.theme_use('clam') # Clam allows better color customization
        style.configure("Dark.TCombobox", 
                        fieldbackground=COLORS["bg_surface_variant"],
                        background=COLORS["bg_surface_variant"],
                        foreground=COLORS["text_main"],
                        arrowcolor=COLORS["primary"],
                        borderwidth=0)
        
        self.combo = ttk.Combobox(self, textvariable=self.var_name, values=self.options, style="Dark.TCombobox", font=("Segoe UI", 10))
        self.combo.pack(pady=5, fill=tk.X, padx=30, ipady=4)
        self.combo.focus_set()
        
        btn_frame = tk.Frame(self, bg=COLORS["bg_base"])
        btn_frame.pack(pady=25, fill=tk.X, padx=30)
        
        # Custom Buttons
        self._make_button(btn_frame, "Create", self.confirm, primary=True).pack(side=tk.RIGHT, padx=(10, 0))
        self._make_button(btn_frame, "Cancel", self.cancel, primary=False).pack(side=tk.RIGHT)
        
        self.bind("<Return>", lambda e: self.confirm())
        self.bind("<Escape>", lambda e: self.cancel())

    def _make_button(self, parent, text, cmd, primary=False):
        bg = COLORS["primary"] if primary else COLORS["bg_surface_variant"]
        fg = COLORS["on_primary"] if primary else COLORS["text_main"]
        btn = tk.Button(parent, text=text, command=cmd, 
                        bg=bg, fg=fg, 
                        font=("Segoe UI", 9, "bold"), 
                        relief=tk.FLAT, activebackground=COLORS["primary_container"], activeforeground=COLORS["text_main"],
                        padx=15, pady=5, cursor="hand2")
        return btn

    def confirm(self):
        val = self.var_name.get().strip()
        if val:
            self.result = val
            self.destroy()
        else:
            messagebox.showwarning("Required", "Please enter a name.", parent=self)

    def cancel(self):
        self.destroy()

class AnimationEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Animation Designer")
        self.root.configure(bg=COLORS["bg_base"])
        
        # Fullscreen / Maximized
        try:
            self.root.state('zoomed') 
        except:
            self.root.attributes('-fullscreen', True)

        self.image_path = None
        self.pil_image = None
        self.cached_bg_removed = None
        self.tk_image = None
        self.minimap_image = None
        
        self.animations = [] 
        self.current_preview_frames = []
        self.preview_index = 0
        self.preview_timer = None
        self.remove_bg_var = tk.BooleanVar(value=False)
        self.is_editing = False 
        self.editing_index = -1 
        
        # UI Variables
        self.var_name = tk.StringVar()
        self.var_x = tk.IntVar()
        self.var_y = tk.IntVar()
        self.var_w = tk.IntVar()
        self.var_h = tk.IntVar()
        self.var_count = tk.IntVar()
        self.var_fps = tk.IntVar()
        self.var_loop = tk.BooleanVar()

        self._configure_styles()
        self._setup_ui()
        
        # Global Event Bindings
        self.root.bind('<Key>', self.on_key_press)
        self.root.bind_all('<Button-1>', self._on_global_click)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # General Frame/Label
        style.configure("TFrame", background=COLORS["bg_base"])
        style.configure("TLabel", background=COLORS["bg_base"], foreground=COLORS["text_dim"], font=("Segoe UI", 10))
        
        # Dark Scrollbar
        style.configure("Vertical.TScrollbar", background=COLORS["bg_surface_variant"], troughcolor=COLORS["bg_base"], borderwidth=0, arrowcolor=COLORS["text_dim"])
        style.configure("Horizontal.TScrollbar", background=COLORS["bg_surface_variant"], troughcolor=COLORS["bg_base"], borderwidth=0, arrowcolor=COLORS["text_dim"])
        
        # Dark Combobox
        style.configure("TCombobox", 
                        fieldbackground=COLORS["bg_surface_variant"],
                        background=COLORS["bg_surface_variant"],
                        foreground=COLORS["text_main"],
                        arrowcolor=COLORS["primary"],
                        borderwidth=0)
        
        # Dark Checkbutton
        style.configure("TCheckbutton", background=COLORS["bg_base"], foreground=COLORS["text_main"], font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[('active', COLORS["bg_base"])]) # Prevent hover flicker

    def _setup_ui(self):
        # 1. Top Toolbar (Modern Flat)
        top_bar = tk.Frame(self.root, bg=COLORS["bg_surface"], height=60, padx=20, pady=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        
        # Logo/Title
        tk.Label(top_bar, text="ANIMATOR PRO", bg=COLORS["bg_surface"], fg=COLORS["primary"], font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=(0, 30))
        
        # Tools
        self._make_toolbar_btn(top_bar, "Load Sprite", self.load_image).pack(side=tk.LEFT, padx=5)
        self._make_toolbar_btn(top_bar, "New Animation", self.add_animation_default, primary=True).pack(side=tk.LEFT, padx=5)
        self._make_toolbar_btn(top_bar, "Delete", self.delete_animation, color=COLORS["error"]).pack(side=tk.LEFT, padx=5)
        
        # Spacer
        tk.Frame(top_bar, bg=COLORS["bg_surface"], width=20).pack(side=tk.LEFT)
        
        self._make_toolbar_btn(top_bar, "Export CSV", self.export_csv).pack(side=tk.LEFT, padx=5)
        self._make_toolbar_btn(top_bar, "Import CSV", self.import_csv).pack(side=tk.LEFT, padx=5)
        
        # Toggle Switch style for Remove BG
        f_toggle = tk.Frame(top_bar, bg=COLORS["bg_surface"])
        f_toggle.pack(side=tk.LEFT, padx=20)
        tk.Label(f_toggle, text="Remove BG", bg=COLORS["bg_surface"], fg=COLORS["text_main"], font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        self.chk_bg = ttk.Checkbutton(f_toggle, variable=self.remove_bg_var, command=self._on_bg_toggle, style="TCheckbutton")
        self.chk_bg.pack(side=tk.LEFT)
        
        # Exit Fullscreen
        self._make_toolbar_btn(top_bar, "⛶", lambda: self.root.attributes('-fullscreen', False) or self.root.state('normal')).pack(side=tk.RIGHT)

        # 2. Main Workspace
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=COLORS["bg_base"], sashwidth=4, sashrelief=tk.FLAT)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Left: Canvas Area
        canvas_container = tk.Frame(main_pane, bg=COLORS["bg_base"])
        
        self.canvas = tk.Canvas(canvas_container, bg="#111111", highlightthickness=0)
        h_scroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        main_pane.add(canvas_container)
        
        # Right: Sidebar
        sidebar = tk.Frame(main_pane, width=SIDEBAR_WIDTH, bg=COLORS["bg_surface"])
        main_pane.add(sidebar)
        
        # -- Sidebar Content --
        
        # -- Sidebar Content --
        
        # Animation List
        tk.Label(sidebar, text="ANIMATIONS", bg=COLORS["bg_surface"], fg=COLORS["primary"], font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        list_frame = tk.Frame(sidebar, bg=COLORS["bg_surface"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=0)
        
        self.anim_listbox = tk.Listbox(list_frame, bg=COLORS["bg_base"], fg=COLORS["text_main"],
                                       selectbackground=COLORS["primary_container"], selectforeground=COLORS["text_main"],
                                       relief=tk.FLAT, borderwidth=0, font=("Segoe UI", 10), height=8)
        self.anim_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb_list = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.anim_listbox.yview)
        self.anim_listbox.config(yscrollcommand=sb_list.set)
        sb_list.pack(side=tk.RIGHT, fill=tk.Y)
        self.anim_listbox.bind('<<ListboxSelect>>', self.on_select_animation)

        # Properties Editor
        props_container = tk.Frame(sidebar, bg=COLORS["bg_surface"])
        props_container.pack(fill=tk.X, padx=20, pady=20)
        
        # Edit Button
        self.btn_edit = tk.Button(props_container, text="EDIT SELECTED", command=self.toggle_edit_mode,
                                  bg=COLORS["bg_surface_variant"], fg=COLORS["text_main"],
                                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                                  activebackground=COLORS["primary"], activeforeground=COLORS["on_primary"])
        self.btn_edit.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # Fields Grid
        grid_frame = tk.Frame(props_container, bg=COLORS["bg_surface"])
        grid_frame.pack(fill=tk.X)
        
        self.inputs = []
        
        # Name Row
        self._make_label(grid_frame, "Name").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.combo_name = ttk.Combobox(grid_frame, textvariable=self.var_name, values=STANDARD_ANIMATIONS, style="TCombobox", font=("Segoe UI", 10))
        self.combo_name.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        # Re-bind after creating
        self.combo_name.bind("<<ComboboxSelected>>", self._on_field_change)
        self.combo_name.bind("<FocusOut>", self._on_field_change)
        self.combo_name.bind("<Return>", self._on_field_change)
        self.combo_name.config(state="disabled")

        # Num Rows
        self.inputs.append(self._make_prop_row(grid_frame, "X", self.var_x, 1, 0))
        self.inputs.append(self._make_prop_row(grid_frame, "Y", self.var_y, 1, 2))
        self.inputs.append(self._make_prop_row(grid_frame, "W", self.var_w, 2, 0))
        self.inputs.append(self._make_prop_row(grid_frame, "H", self.var_h, 2, 2))
        self.inputs.append(self._make_prop_row(grid_frame, "Count", self.var_count, 3, 0))
        self.inputs.append(self._make_prop_row(grid_frame, "FPS", self.var_fps, 3, 2))
        
        # Loop Check
        tk.Label(grid_frame, text="Loop", bg=COLORS["bg_surface"], fg=COLORS["text_dim"]).grid(row=4, column=0, sticky="e", padx=5)
        self.chk_loop = ttk.Checkbutton(grid_frame, variable=self.var_loop, command=self._on_field_change, style="TCheckbutton")
        self.chk_loop.grid(row=4, column=1, sticky="w", padx=5)
        self.chk_loop.config(state="disabled")

        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(3, weight=1)

        # Controls & Playback
        playback = tk.Frame(sidebar, bg=COLORS["bg_surface"])
        playback.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(playback, text="LIVE PREVIEW", bg=COLORS["bg_surface"], fg=COLORS["primary"], font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10,5))
        self.preview_label = tk.Label(playback, bg="black")
        self.preview_label.pack(anchor=tk.CENTER)
        
        tk.Label(playback, text="WASD to Move | Arrows to Resize", bg=COLORS["bg_surface"], fg=COLORS["text_dim"], font=("Segoe UI", 8)).pack(pady=(10,0))

    def _make_toolbar_btn(self, parent, text, cmd, primary=False, color=None):
        bg = COLORS["primary"] if primary else COLORS["bg_surface_variant"]
        fg = COLORS["on_primary"] if primary else COLORS["text_main"]
        if color: bg = color; fg = "#330000"
        
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=bg, fg=fg,
                        relief=tk.FLAT, font=("Segoe UI", 9),
                        padx=12, pady=4, cursor="hand2",
                        activebackground=COLORS["primary_container"], activeforeground=COLORS["text_main"])
        # Manual Hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["primary_container"] if not color else "#FF8888"))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _make_label(self, parent, text):
        return tk.Label(parent, text=text, bg=COLORS["bg_surface"], fg=COLORS["text_dim"], font=("Segoe UI", 9))

    def _make_prop_row(self, parent, label_text, var, row, col_start):
        self._make_label(parent, label_text).grid(row=row, column=col_start, sticky="e", padx=(10, 5), pady=5)
        entry = tk.Entry(parent, textvariable=var, 
                         bg=COLORS["bg_surface_variant"], fg=COLORS["text_main"], insertbackground=COLORS["primary"],
                         relief=tk.FLAT, font=("Segoe UI", 10))
        entry.grid(row=row, column=col_start+1, sticky="we", padx=5, pady=5)
        # Bindings
        entry.bind("<FocusOut>", self._on_field_change)
        entry.bind("<Return>", self._on_field_change)
        entry.config(state="disabled", disabledbackground=COLORS["bg_base"], disabledforeground=COLORS["text_dim"])
        return entry

    # --- Logic methods largely unchanged, just ensure they interact with new UI ---
    
    def _on_global_click(self, event):
        try:
            if isinstance(event.widget, (tk.Entry, ttk.Combobox)): return
            cls = event.widget.winfo_class()
            if cls in ('Entry', 'TEntry', 'TCombobox', 'Combobox', 'Listbox', 'TListbox'): return
            self.root.focus_set()
        except: pass

    def toggle_edit_mode(self):
        sel = self.anim_listbox.curselection()
        if not sel: return
        self.is_editing = not self.is_editing
        
        if self.is_editing:
             self.editing_index = sel[0]
        else:
             self.editing_index = -1
             self._update_listbox()
        
        is_active = self.is_editing
        
        # Style update
        bg = COLORS["success"] if is_active else COLORS["bg_surface_variant"]
        fg = "#003300" if is_active else COLORS["text_main"]
        text = "✓ DONE EDITING" if is_active else "✎ EDIT SELECTED"
        self.btn_edit.config(bg=bg, fg=fg, text=text)
        
        # State update
        state = "normal" if is_active else "disabled"
        self.combo_name.config(state=state)
        # Checkbutton state handling in ttk is via state()
        if is_active: self.chk_loop.state(['!disabled'])
        else: self.chk_loop.state(['disabled'])
            
        for entry in self.inputs:
            entry.config(state=state)
            if is_active:
                entry.config(bg=COLORS["bg_surface_variant"], fg=COLORS["text_main"])
            else:
                entry.config(bg=COLORS["bg_base"], fg=COLORS["text_dim"])

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not path: return
        self.image_path = path
        try:
            self.pil_image = Image.open(path).convert("RGBA")
            self.tk_image = ImageTk.PhotoImage(self.pil_image)
            self.cached_bg_removed = None
            if self.remove_bg_var.get(): self._update_bg_cache()
            # self._create_minimap() -> Removed
            self.canvas.delete("all")
            self._draw_checkerboard(self.tk_image.width(), self.tk_image.height())
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW, tags="image")
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    # _create_minimap Removed

    def _on_bg_toggle(self):
        if self.remove_bg_var.get():
             if not self.cached_bg_removed: self._update_bg_cache()
        self.on_select_animation(None)

    def _update_bg_cache(self):
        if not self.pil_image: return
        try: self.cached_bg_removed = self._remove_background_pil_full(self.pil_image)
        except: pass

    def add_animation_default(self):
        if not self.pil_image:
            messagebox.showwarning("Warning", "Load an image first!")
            return
        dialog = AnimationNameDialog(self.root, STANDARD_ANIMATIONS)
        if not dialog.result: return
        
        anim_data = {"name": dialog.result, "x": 0, "y": 0, "w": 64, "h": 64, "count": 1, "fps": 10, "loop": True}
        self.animations.append(anim_data)
        self._update_listbox()
        self.anim_listbox.selection_clear(0, tk.END)
        self.anim_listbox.selection_set(tk.END)
        self.on_select_animation(None)
        if not self.is_editing: self.toggle_edit_mode()

    def delete_animation(self):
        sel = self.anim_listbox.curselection()
        if not sel: return
        if not messagebox.askyesno("Confirm Delete", "Are you sure?"): return
        idx = sel[0]
        del self.animations[idx]
        self._update_listbox()
        self.canvas.delete("overlay")
        if self.is_editing: self.toggle_edit_mode()
        self.on_select_animation(None)

    def _update_listbox(self):
        current_sel = self.anim_listbox.curselection()
        self.anim_listbox.delete(0, tk.END)
        for anim in self.animations:
            self.anim_listbox.insert(tk.END, f"{anim['name']}")
        if current_sel and current_sel[0] < len(self.animations):
            self.anim_listbox.selection_set(current_sel[0])

    def _draw_overlay(self, anim):
        for i in range(anim['count']):
            x = anim['x'] + i * anim['w']
            y = anim['y']
            color = COLORS["success"] if self.is_editing else COLORS["primary"]
            width = 3 if self.is_editing else 2
            self.canvas.create_rectangle(x, y, x + anim['w'], y + anim['h'], outline=color, width=width, tag="overlay")
            self.canvas.create_text(x + 5, y + 5, text=str(i), anchor=tk.NW, fill=color, font=("Segoe UI", 10, "bold"), tag="overlay")

    def on_select_animation(self, event):
        sel = self.anim_listbox.curselection()
        if not sel:
            self.canvas.delete("overlay")
            return
        idx = sel[0]
        if self.is_editing and self.editing_index != -1 and self.editing_index != idx:
             self.toggle_edit_mode()
        if idx >= len(self.animations): return
        anim = self.animations[idx]
        self.var_name.set(anim['name'])
        self.var_x.set(anim['x'])
        self.var_y.set(anim['y'])
        self.var_w.set(anim['w'])
        self.var_h.set(anim['h'])
        self.var_count.set(anim['count'])
        self.var_fps.set(anim['fps'])
        self.var_loop.set(anim['loop'])
        self._refresh_preview(anim)

    def _on_field_change(self, event=None):
        if not self.is_editing: return 
        sel = self.anim_listbox.curselection()
        if not sel: return
        idx = sel[0]
        try:
            self.animations[idx]['name'] = self.var_name.get()
            self.animations[idx]['x'] = self.var_x.get()
            self.animations[idx]['y'] = self.var_y.get()
            self.animations[idx]['w'] = self.var_w.get()
            self.animations[idx]['h'] = self.var_h.get()
            self.animations[idx]['count'] = self.var_count.get()
            self.animations[idx]['fps'] = self.var_fps.get()
            self.animations[idx]['loop'] = self.var_loop.get()
            self._refresh_preview(self.animations[idx])
        except tk.TclError: self._revert_ui_values(idx)
        except Exception: pass

    def _revert_ui_values(self, idx):
        if idx < 0 or idx >= len(self.animations): return
        anim = self.animations[idx]
        self.var_name.set(anim['name'])
        self.var_x.set(anim['x'])
        self.var_y.set(anim['y'])
        self.var_w.set(anim['w'])
        self.var_h.set(anim['h'])
        self.var_count.set(anim['count'])
        self.var_fps.set(anim['fps'])
        self.var_loop.set(anim['loop'])

    def _refresh_preview(self, anim):
        self.canvas.delete("overlay")
        self._draw_overlay(anim)
        self.current_preview_frames = []
        source_sheet = self.pil_image
        if self.remove_bg_var.get():
             if not self.cached_bg_removed: self._update_bg_cache()
             if self.cached_bg_removed: source_sheet = self.cached_bg_removed
        if not source_sheet: return
        try:
            img_w, img_h = source_sheet.size
            for i in range(max(1, anim['count'])): 
                x = anim['x'] + i * anim['w']
                y = anim['y']
                if x >= img_w or y >= img_h: continue 
                crop_w = min(anim['w'], img_w - x)
                crop_h = min(anim['h'], img_h - y)
                if crop_w <= 0 or crop_h <= 0: continue
                crop = source_sheet.crop((x, y, x+crop_w, y+crop_h))
                self.current_preview_frames.append(ImageTk.PhotoImage(crop))
            self.preview_index = 0
            if self.preview_timer: self.root.after_cancel(self.preview_timer)
            self._animate_preview(anim['fps'])
        except Exception as e: print(f"Preview error: {e}")

    def _animate_preview(self, fps):
        if not self.current_preview_frames: return
        frame = self.current_preview_frames[self.preview_index]
        self.preview_label.config(image=frame)
        self.preview_index = (self.preview_index + 1) % len(self.current_preview_frames)
        delay = int(1000 / fps) if fps > 0 else 100
        self.preview_timer = self.root.after(delay, lambda: self._animate_preview(fps))

    def export_csv(self):
        if not self.animations: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path: return
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "StartX", "StartY", "Width", "Height", "Count", "FPS", "Loop"])
                for anim in self.animations:
                    writer.writerow([anim['name'], anim['x'], anim['y'], anim['w'], anim['h'], anim['count'], anim['fps'], anim['loop']])
            messagebox.showinfo("Success", "Exported successfully!")
        except Exception as e: messagebox.showerror("Error", f"Export failed: {e}")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        try:
            with open(path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader) 
                self.animations = []
                for row in reader:
                    if len(row) < 8: continue
                    anim = {"name": row[0], "x": int(row[1]), "y": int(row[2]), "w": int(row[3]), "h": int(row[4]), "count": int(row[5]), "fps": int(row[6]), "loop": row[7] == 'True'}
                    self.animations.append(anim)
            self._update_listbox()
            if self.animations:
                 self.anim_listbox.selection_set(0)
                 self.on_select_animation(None)
            messagebox.showinfo("Success", "Imported successfully!")
        except Exception as e: messagebox.showerror("Error", f"Import failed: {e}")

    def _draw_checkerboard(self, w, h):
        self.canvas.delete("checkerboard")
        pattern = Image.new("RGBA", (20, 20), (20, 20, 20, 255)) # Darker checkerboard
        d = ImageDraw.Draw(pattern)
        d.rectangle((0, 10, 10, 20), fill=(40, 40, 40, 255))
        d.rectangle((10, 0, 20, 10), fill=(40, 40, 40, 255))
        bg = Image.new("RGBA", (w, h))
        for x in range(0, w, 20):
            for y in range(0, h, 20):
                bg.paste(pattern, (x, y))
        self.checkerboard_bg = ImageTk.PhotoImage(bg)
        self.canvas.create_image(0, 0, image=self.checkerboard_bg, anchor=tk.NW, tags="checkerboard")
        self.canvas.tag_lower("checkerboard")

    def on_key_press(self, event):
        if not self.is_editing: return 
        try:
            focused = self.root.focus_get()
            if isinstance(focused, (tk.Entry, ttk.Combobox)): return
        except: pass
        sel = self.anim_listbox.curselection()
        if not sel: return
        step = 10 if (event.state & 0x1) else 1 
        changed = False
        if event.char == 'w': self.var_y.set(self.var_y.get() - step); changed = True
        elif event.char == 's': self.var_y.set(self.var_y.get() + step); changed = True
        elif event.char == 'a': self.var_x.set(self.var_x.get() - step); changed = True
        elif event.char == 'd': self.var_x.set(self.var_x.get() + step); changed = True
        elif event.keysym == 'Up': self.var_h.set(self.var_h.get() - step); changed = True
        elif event.keysym == 'Down': self.var_h.set(self.var_h.get() + step); changed = True
        elif event.keysym == 'Left': self.var_w.set(self.var_w.get() - step); changed = True
        elif event.keysym == 'Right': self.var_w.set(self.var_w.get() + step); changed = True
        if changed: self._on_field_change()

    def _remove_background_pil_full(self, image, threshold=50):
        if image.mode != 'RGBA': image = image.convert('RGBA')
        bg_color = image.getpixel((0,0))
        if isinstance(bg_color, int): bg_color = (bg_color, bg_color, bg_color, 255)
        elif len(bg_color) == 3: bg_color = (bg_color[0], bg_color[1], bg_color[2], 255)
        bg_image = Image.new('RGBA', image.size, bg_color)
        diff = ImageChops.difference(image, bg_image).convert('L')
        mask = diff.point(lambda x: 0 if x < threshold else 255)
        current_alpha = image.split()[3]
        final_mask = ImageChops.multiply(mask, current_alpha)
        result = image.copy()
        result.putalpha(final_mask)
        return result

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimationEditor(root)
    root.mainloop()
