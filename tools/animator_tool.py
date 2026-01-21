import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageChops
import csv
import os

class AnimationEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Animation Frame Editor")
        self.root.geometry("1000x700")

        self.image_path = None
        self.pil_image = None
        self.tk_image = None
        self.sprite_sheet = None
        
        self.animations = [] # List of dicts
        self.current_preview_frames = []
        self.preview_index = 0
        self.preview_timer = None
        self.remove_bg_var = tk.BooleanVar(value=False)
        
        self._setup_ui()

    def _setup_ui(self):
        # Top Bar
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Button(top_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT)
        tk.Button(top_frame, text="Add Animation", command=self.add_animation_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Delete Selected", command=self.delete_animation).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Import CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(top_frame, text="Remove BG", variable=self.remove_bg_var, command=lambda: self.on_select_animation(None)).pack(side=tk.LEFT, padx=5)

        # Main Layout: Left = Canvas/Image, Right = List & Preview
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Left: Canvas
        self.canvas_frame = tk.Frame(main_pane)
        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        
        # Scrollbars for canvas
        h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        main_pane.add(self.canvas_frame)
        
        # Right: Controls
        right_frame = tk.Frame(main_pane, width=300)
        main_pane.add(right_frame)
        
        # Listbox for animations
        tk.Label(right_frame, text="defined Animations:").pack(anchor=tk.W)
        self.anim_listbox = tk.Listbox(right_frame, height=10)
        self.anim_listbox.pack(fill=tk.X, padx=5)
        self.anim_listbox.bind('<<ListboxSelect>>', self.on_select_animation)
        
        # Preview Area
        tk.Label(right_frame, text="Preview:").pack(anchor=tk.W, pady=(10,0))
        self.preview_label = tk.Label(right_frame, bg="black") # Let it autosize
        self.preview_label.pack(padx=5, pady=5)
        
        # Properties Editor (Simple readonly for now, mostly)
        self.props_label = tk.Label(right_frame, text="Details:", justify=tk.LEFT)
        self.props_label.pack(anchor=tk.W, padx=5)

        # Bindings
        self.root.bind('<Key>', self.on_key_press)
        
        # Instructions
        tk.Label(right_frame, text="\nControls:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10,0))
        tk.Label(right_frame, text="WASD: Move Position\nArrows: Resize Frame\nShift: 10x Speed", justify=tk.LEFT).pack(anchor=tk.W, padx=5)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not path:
            return
        
        self.image_path = path
        try:
            self.pil_image = Image.open(path)
            self.tk_image = ImageTk.PhotoImage(self.pil_image)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def add_animation_dialog(self):
        if not self.pil_image:
            messagebox.showwarning("Warning", "Load an image first!")
            return

        # Simple input dialogs for now
        name = simpledialog.askstring("Input", "Animation Name (e.g., Idle):")
        if not name: return
        
        # Default guess
        start_x = simpledialog.askinteger("Input", "Start X:", initialvalue=0)
        start_y = simpledialog.askinteger("Input", "Start Y:", initialvalue=0)
        width = simpledialog.askinteger("Input", "Frame Width:", initialvalue=64)
        height = simpledialog.askinteger("Input", "Frame Height:", initialvalue=64)
        count = simpledialog.askinteger("Input", "Frame Count:", initialvalue=1)
        fps = simpledialog.askinteger("Input", "FPS:", initialvalue=10)
        
        if None in [start_x, start_y, width, height, count, fps]:
            return

        anim_data = {
            "name": name,
            "x": start_x,
            "y": start_y,
            "w": width,
            "h": height,
            "count": count,
            "fps": fps,
            "loop": True # Default
        }
        
        self.animations.append(anim_data)
        self._update_listbox()
        self._draw_overlay(anim_data)

    def delete_animation(self):
        sel = self.anim_listbox.curselection()
        if not sel: return
        idx = sel[0]
        del self.animations[idx]
        self._update_listbox()
        self.canvas.delete("overlay") # Redraw all
        for anim in self.animations:
            self._draw_overlay(anim)

    def _update_listbox(self):
        self.anim_listbox.delete(0, tk.END)
        for anim in self.animations:
            self.anim_listbox.insert(tk.END, f"{anim['name']} ({anim['count']} frames)")

    def _draw_overlay(self, anim):
        # Draw rectangles for frames
        for i in range(anim['count']):
            x = anim['x'] + i * anim['w']
            y = anim['y']
            self.canvas.create_rectangle(x, y, x + anim['w'], y + anim['h'], outline="red", tag="overlay")
            # Text index
            self.canvas.create_text(x + 5, y + 5, text=str(i), anchor=tk.NW, fill="red", tag="overlay")

    def on_select_animation(self, event):
        sel = self.anim_listbox.curselection()
        if not sel: return
        idx = sel[0]
        anim = self.animations[idx]
        
        # Prepare preview
        self.current_preview_frames = []
        try:
            for i in range(anim['count']):
                x = anim['x'] + i * anim['w']
                y = anim['y']
                crop = self.pil_image.crop((x, y, x+anim['w'], y+anim['h']))
                
                if self.remove_bg_var.get():
                     crop = self._remove_background_pil(crop)

                # 1x scale (Final Size)
                self.current_preview_frames.append(ImageTk.PhotoImage(crop))
                
            self.preview_index = 0
            if self.preview_timer:
                self.root.after_cancel(self.preview_timer)
            self._animate_preview(anim['fps'])
            
            # Show details
            details = f"Name: {anim['name']}\nX: {anim['x']}, Y: {anim['y']}\nW: {anim['w']}, H: {anim['h']}\nCount: {anim['count']}\nFPS: {anim['fps']}"
            self.props_label.config(text=details)
            
        except Exception as e:
            print(f"Preview error: {e}")

    def _animate_preview(self, fps):
        if not self.current_preview_frames: return
        
        frame = self.current_preview_frames[self.preview_index]
        self.preview_label.config(image=frame)
        self.preview_index = (self.preview_index + 1) % len(self.current_preview_frames)
        
        delay = int(1000 / fps) if fps > 0 else 100
        self.preview_timer = self.root.after(delay, lambda: self._animate_preview(fps))

    def export_csv(self):
        if not self.animations:
            return
            
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path: return
        
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["Name", "StartX", "StartY", "Width", "Height", "Count", "FPS", "Loop"])
                for anim in self.animations:
                    writer.writerow([
                        anim['name'], anim['x'], anim['y'], anim['w'], anim['h'], 
                        anim['count'], anim['fps'], anim['loop']
                    ])
            messagebox.showinfo("Success", "Exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        
        try:
            with open(path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader) # Add validation?
                
                self.animations = []
                for row in reader:
                    # Name,StartX,StartY,Width,Height,Count,FPS,Loop
                    if len(row) < 8: continue
                    anim = {
                        "name": row[0],
                        "x": int(row[1]),
                        "y": int(row[2]),
                        "w": int(row[3]),
                        "h": int(row[4]),
                        "count": int(row[5]),
                        "fps": int(row[6]),
                        "loop": row[7] == 'True'
                    }
                    self.animations.append(anim)
            
            self._update_listbox()
            self.canvas.delete("overlay")
            for anim in self.animations:
                self._draw_overlay(anim)
                
            messagebox.showinfo("Success", "Imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")

    def on_key_press(self, event):
        sel = self.anim_listbox.curselection()
        if not sel: return
        idx = sel[0]
        anim = self.animations[idx]
        
        step = 10 if (event.state & 0x1) else 1 # Shift check (Simple bitmask)
             
        changed = False
        
        # Position (WASD)
        if event.char == 'w':
            anim['y'] -= step
            changed = True
        elif event.char == 's':
            anim['y'] += step
            changed = True
        elif event.char == 'a':
            anim['x'] -= step
            changed = True
        elif event.char == 'd':
            anim['x'] += step
            changed = True

        # Size (Arrows)
        elif event.keysym == 'Up':
            anim['h'] -= step
            changed = True
        elif event.keysym == 'Down':
            anim['h'] += step
            changed = True
        elif event.keysym == 'Left':
            anim['w'] -= step
            changed = True
        elif event.keysym == 'Right':
            anim['w'] += step
            changed = True
            
        if changed:
            # Refresh overlay
            self.canvas.delete("overlay")
            for a in self.animations:
                self._draw_overlay(a)
            
            # Refresh preview and labels
            # Stop verify timer before restarting to avoid overlap or flicker
            if self.preview_timer:
                self.root.after_cancel(self.preview_timer)
            self.on_select_animation(None)

    def _remove_background_pil(self, image, threshold=50):
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get key color from top-left (0,0) of the *crop*? 
        # Or of the whole sheet?
        # Usually checking (0,0) of the CROP is dangerous if the sprite touches the edge.
        # Better to check (0,0) of the whole image (self.pil_image) or assume specific color.
        # But typically sprite sheets have uniform background.
        # The crop might be in the middle of transparency.
        # Let's use the top-left of the SOURCE IMAGE as key color.
        
        # But wait, image passed here is the crop.
        # I should probably pass the key color or determine it globally.
        # Let's use self.pil_image.getpixel((0,0)).
        
        bg_color = self.pil_image.getpixel((0,0))
        
        # But PIL image might be RGB, crop converted to RGBA.
        # Ensure bg_color matches mode for difference?
        # ImageChops.difference requires images to match.
        
        # Create solid bg image of same size as crop
        # Ensure bg_color acts as RGBA
        if self.pil_image.mode != 'RGBA':
             # Convert color to RGBA tuple if it's int or RGB tuple
             if isinstance(bg_color, int): # Grayscale
                  bg_color = (bg_color, bg_color, bg_color, 255)
             elif len(bg_color) == 3:
                  bg_color = (bg_color[0], bg_color[1], bg_color[2], 255)
        
        bg_image = Image.new('RGBA', image.size, bg_color)
        
        # Difference
        diff = ImageChops.difference(image, bg_image)
        diff = diff.convert('L')
        
        # Threshold to create mask
        # 0 where match (remove), 255 where different (keep)
        mask = diff.point(lambda x: 0 if x < threshold else 255)
        
        image.putalpha(mask)
        return image

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimationEditor(root)
    root.mainloop()
