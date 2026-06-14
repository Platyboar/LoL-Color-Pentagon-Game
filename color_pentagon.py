import os
import sys
import re
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Set up paths
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS # When built with pyinstaller --add-data
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SYMBOLS_DIR = os.path.join(BASE_DIR, "symbols")
CHAMPS_DIR = os.path.join(BASE_DIR, "champs")

ATTRIBUTES_LIST = [
    "Release date", "Store Price", "Role", "Class", "Legacy class", "Resource", "Range type"
]

class ColorPentagonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Color Pentagon")
        self.root.geometry("1600x1000")
        try:
            self.root.state("zoomed")
        except:
            pass
        self.root.configure(bg="#2b2b2b")
        
        self.champions = self.get_champions()
        self.current_champ = None
        self.champ_attributes = {} # { attr_name: [val1, val2] }
        self.checkbox_vars = {}    # { attr_name: tk.StringVar() } (values: 'none', 'first', 'second', 'both', 'show')
        self.current_image_index = 0
        
        self.scale_factor = 1.0
        self.last_left_h = 0
        self.last_right_size = (0, 0)
        self._resize_timer = None

        # Load a default font
        try:
            self.font_large = font.Font(family="Helvetica", size=24, weight="bold")
            self.pil_font = ImageFont.truetype("arial.ttf", 60)
        except:
            self.pil_font = ImageFont.load_default()
            
        self.setup_ui()
        
        if self.champions:
            self.show_startup_screen()

    def get_champions(self):
        champs = []
        if os.path.exists(CHAMPS_DIR):
            for item in sorted(os.listdir(CHAMPS_DIR)):
                path = os.path.join(CHAMPS_DIR, item)
                if os.path.isdir(path) and not item.startswith("."):
                    md_path = os.path.join(path, f"{item}.md")
                    if os.path.exists(md_path):
                        champs.append(item)
        return champs

    def setup_ui(self):
        # Main layout using PanedWindow for resizability
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = tk.Frame(self.paned, bg="#3c3f41")
        self.paned.add(self.left_frame, weight=1) # Let it scale naturally

        self.right_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(self.right_frame, weight=3) # Right side takes more space
        self.right_frame.bind("<Configure>", self.on_right_configure)

        # --- Left Frame ---
        self.champ_label = tk.Label(self.left_frame, text="Select Champion:", bg="#3c3f41", fg="white", font=("Arial", 16, "bold"))
        self.champ_label.pack(anchor=tk.W, pady=(10, 5))
        self.champ_combo = ttk.Combobox(self.left_frame, values=self.champions, state="readonly", font=("Arial", 14))
        self.champ_combo.pack(fill=tk.X, pady=(0, 10))
        self.champ_combo.bind("<<ComboboxSelected>>", self.on_champ_selected)

        self.hint_label = tk.Label(self.left_frame, text="↑ Select Champion to start", bg="#3c3f41", fg="#00E5FF", font=("Arial", 14, "italic"))
        self.hint_label.pack(anchor=tk.N, pady=(0, 10))

        # Attributes area with Scrollbar
        self.canvas_frame = tk.Frame(self.left_frame, bg="#3c3f41")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#3c3f41", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.attr_container = tk.Frame(self.canvas, bg="#3c3f41")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.attr_container, anchor="nw")
        
        self.attr_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        def _on_mousewheel(event):
            try:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except: pass
            
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        # --- Right Frame ---
        # Main Image Area
        self.main_img_label = tk.Label(self.right_frame, bg="#2b2b2b")
        self.main_img_label.pack(expand=True, fill=tk.BOTH)

        # Bottom Navigation Area
        self.nav_frame = tk.Frame(self.right_frame, bg="#2b2b2b", height=150)
        self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        self.btn_prev = tk.Button(self.nav_frame, text="<", font=("Arial", 20), command=self.prev_image, bg="#555", fg="white")
        self.btn_prev.pack(side=tk.LEFT, padx=20)
        
        self.thumb_frame = tk.Frame(self.nav_frame, bg="#2b2b2b")
        self.thumb_frame.pack(side=tk.LEFT, expand=True)
        
        self.btn_next = tk.Button(self.nav_frame, text=">", font=("Arial", 20), command=self.next_image, bg="#555", fg="white")
        self.btn_next.pack(side=tk.RIGHT, padx=20)
        
        # Background color selector
        self.bg_frame = tk.Frame(self.left_frame, bg="#3c3f41")
        self.bg_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        self.bg_label = tk.Label(self.bg_frame, text="Background Color (OBS):", bg="#3c3f41", fg="white", font=("Arial", 12))
        self.bg_label.pack(anchor=tk.W)
        self.bg_combo = ttk.Combobox(self.bg_frame, values=["Standard", "Green (Chroma)", "Magenta", "Black", "White"], state="readonly", font=("Arial", 12))
        self.bg_combo.current(0)
        self.bg_combo.pack(fill=tk.X, pady=(5,0))
        self.bg_combo.bind("<<ComboboxSelected>>", self.change_bg_color)
        
        self.thumbnails = [] # store references to prevent garbage collection

    def on_right_configure(self, event):
        w, h = event.width, event.height
        if abs(w - self.last_right_size[0]) > 50 or abs(h - self.last_right_size[1]) > 50:
            self.last_right_size = (w, h)
            if self._resize_timer:
                self.root.after_cancel(self._resize_timer)
            self._resize_timer = self.root.after(200, self.update_main_image_if_needed)

    def update_main_image_if_needed(self):
        if self.current_champ:
            self.update_main_image()
        else:
            self.show_startup_screen()

    def change_bg_color(self, event=None):
        val = self.bg_combo.get()
        color = "#2b2b2b" # Standard
        
        # Remove transparency if previously set
        try:
            self.root.attributes("-transparentcolor", "")
        except:
            pass
            
        if val == "Green (Chroma)": color = "#00FF00"
        elif val == "Magenta": color = "#FF00FF"
        elif val == "Black": color = "#000000"
        elif val == "White": color = "#FFFFFF"
        
        self.right_frame.config(bg=color)
        self.main_img_label.config(bg=color)
        self.nav_frame.config(bg=color)
        self.thumb_frame.config(bg=color)

    def parse_markdown(self, champ):
        md_path = os.path.join(CHAMPS_DIR, champ, f"{champ}.md")
        attributes = {key: [] for key in ATTRIBUTES_LIST}
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line in content.split('\n'):
                for key in ATTRIBUTES_LIST:
                    if line.startswith(f"{key}:"):
                        val_str = line.split(":", 1)[1].strip()
                        # Some might be comma separated
                        if key == "Release date" or key == "Store Price":
                            attributes[key] = [val_str]
                        else:
                            vals = [v.strip() for v in val_str.split(",")]
                            attributes[key] = [v for v in vals if v]
        return attributes

    def on_champ_selected(self, event):
        if hasattr(self, 'hint_label') and self.hint_label.winfo_exists():
            self.hint_label.pack_forget()
            
        self.current_champ = self.champ_combo.get()
        self.champ_attributes = self.parse_markdown(self.current_champ)
        self.current_image_index = 0
        self.checkbox_vars = {}
        
        self.build_attributes_ui()
        self.update_main_image()

    def get_symbol_path(self, val):
        clean_val = val.replace(" ", "_").split(" ")[0] # basic cleanup
        path = os.path.join(SYMBOLS_DIR, f"{clean_val}.png")
        if os.path.exists(path):
            return path
        # Fallback check
        for f in os.listdir(SYMBOLS_DIR):
            if val.lower() in f.lower():
                return os.path.join(SYMBOLS_DIR, f)
        return None

    def build_attributes_ui(self):
        for widget in self.attr_container.winfo_children():
            widget.destroy()

        self.attr_images = [] # keep references
        
        for attr in ATTRIBUTES_LIST:
            vals = self.champ_attributes.get(attr, [])
            if not vals:
                continue

            attr_block = tk.Frame(self.attr_container, bg="#3c3f41")
            attr_block.pack(fill=tk.X, pady=(0, 20))
            
            # Line 1: Title with border, horizontally centered
            title_frame = tk.Frame(attr_block, bg="#2b2b2b", highlightbackground="#555", highlightcolor="#555", highlightthickness=2, bd=0)
            title_frame.pack(pady=(0, 10))
            
            tk.Label(title_frame, text=f"{attr}", bg="#2b2b2b", fg="#00E5FF", font=("Arial", 16, "bold"), anchor=tk.CENTER, padx=15, pady=5).pack()
            
            # Line 2: Values + Icons (centered)
            val_wrapper = tk.Frame(attr_block, bg="#3c3f41")
            val_wrapper.pack(pady=5)
            
            for v in vals:
                sym_path = self.get_symbol_path(v)
                if sym_path:
                    try:
                        img = Image.open(sym_path).resize((32, 32), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.attr_images.append(photo)
                        tk.Label(val_wrapper, image=photo, bg="#3c3f41").pack(side=tk.LEFT, padx=5)
                    except:
                        pass
                tk.Label(val_wrapper, text=v, bg="#3c3f41", fg="white", font=("Arial", 15)).pack(side=tk.LEFT, padx=(0, 15))

            # Line 3: Checkboxes (centered)
            cb_wrapper = tk.Frame(attr_block, bg="#3c3f41")
            cb_wrapper.pack()
            
            self.checkbox_vars[attr] = []
            if len(vals) == 1:
                var = tk.BooleanVar(value=False)
                self.checkbox_vars[attr].append(var)
                tk.Checkbutton(cb_wrapper, text="Show", variable=var, bg="#3c3f41", fg="#ddd", selectcolor="#2b2b2b", activebackground="#3c3f41", activeforeground="white", font=("Arial", 13, "bold"), command=self.update_main_image).pack(side=tk.LEFT)
            else:
                for i, v in enumerate(vals):
                    var = tk.BooleanVar(value=False)
                    self.checkbox_vars[attr].append(var)
                    tk.Checkbutton(cb_wrapper, text=f"Show {i+1}", variable=var, bg="#3c3f41", fg="#ddd", selectcolor="#2b2b2b", activebackground="#3c3f41", activeforeground="white", font=("Arial", 13, "bold"), command=self.update_main_image).pack(side=tk.LEFT, padx=(0, 15))

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_main_image()

    def next_image(self):
        if self.current_image_index < 5:
            self.current_image_index += 1
            self.update_main_image()

    def get_image_path(self, index, champ):
        folder = os.path.join(CHAMPS_DIR, champ)
        if index < 5:
            return os.path.join(folder, f"{champ}_Pentagon_{index+1}.png")
        else:
            return None # Composite image is built dynamically

    def draw_text_with_outline(self, draw, pos, text, font, fill, outline):
        x, y = pos
        # draw outline
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    def overlay_attributes(self, base_img):
        # Coordinate map for 890x843 pentagon
        # Scale factor if base_img is different size? Assume base_img is approx 890x843, but we might have scaled it.
        # It's better to overlay on original Pentagon size then scale the result.
        
        # We will assume base_img is the pentagon part. We need to place icons.
        w, h = base_img.size
        # The coordinates mapping on 890x843
        coords = {
            "Release date": (20, 20),         # Top left outside
            "Store Price": (0, 20),           # Top right outside (x is calculated dynamically)
            "Role": (615, 250),               # Adjusted for better 'O' shape
            "Class": (650, 550),              # Bottom right inside
            "Legacy class": (w // 2, 730),    # Exact horizontal center, moved down
            "Resource": (240, 550),           # Bottom left inside
            "Range type": (275, 250)          # Adjusted for better 'O' shape
        }
        
        draw = ImageDraw.Draw(base_img)
        
        for attr in ATTRIBUTES_LIST:
            vars_list = self.checkbox_vars.get(attr, [])
            vals = self.champ_attributes.get(attr, [])
            
            to_draw = []
            for i, var in enumerate(vars_list):
                if var.get() and i < len(vals):
                    to_draw.append(vals[i])
                    
            if not to_draw:
                continue
                
            x, y = coords.get(attr, (w//2, h//2))
            
            # Special handling for text
            if attr == "Store Price":
                text = str(to_draw[0]).replace(" BE", "").replace("BE", "").strip() if to_draw else ""
                bbox = draw.textbbox((0,0), text, font=self.pil_font)
                text_w = bbox[2] - bbox[0]
                
                be_icon = os.path.join(SYMBOLS_DIR, "BE_icon.png")
                if os.path.exists(be_icon):
                    ic_x = w - 70 # 60px icon + 10px padding from right edge
                    text_x = ic_x - text_w - 15
                    self.draw_text_with_outline(draw, (text_x, y), text, self.pil_font, "white", "black")
                    
                    ic = Image.open(be_icon).convert("RGBA").resize((60, 60), Image.Resampling.LANCZOS)
                    base_img.paste(ic, (ic_x, y), ic)
                else:
                    text_x = w - 20 - text_w
                    self.draw_text_with_outline(draw, (text_x, y), text, self.pil_font, "white", "black")
            elif attr == "Release date":
                text = str(to_draw[0]) if to_draw else ""
                self.draw_text_with_outline(draw, (x, y), text, self.pil_font, "white", "black")
            else:
                # Icons centered precisely around x
                total_w = len(to_draw) * 100 + max(0, len(to_draw) - 1) * 20
                start_x = int(x - total_w / 2)
                for val in to_draw:
                    sym_path = self.get_symbol_path(val)
                    if sym_path:
                        try:
                            ic = Image.open(sym_path).convert("RGBA")
                            # Resize to reasonable icon size
                            ic = ic.resize((100, 100), Image.Resampling.LANCZOS)
                            base_img.paste(ic, (start_x, int(y - 50)), ic)
                            start_x += 120
                        except Exception as e:
                            print(e)
                            
        return base_img

    def generate_composite(self):
        champ = self.current_champ
        base_path = os.path.join(CHAMPS_DIR, champ, f"{champ}_Pentagon_5.png")
        if not os.path.exists(base_path):
            base_path = os.path.join(CHAMPS_DIR, champ, f"{champ}_Pentagon.png")
            
        render_path = os.path.join(CHAMPS_DIR, champ, f"{champ}_Render.png")
        if not os.path.exists(render_path):
            render_path = os.path.join(CHAMPS_DIR, champ, f"{champ.replace(' ', '_')}_Render.png")
        
        base_img = Image.open(base_path).convert("RGBA") if os.path.exists(base_path) else Image.new("RGBA", (890, 843), (0,0,0,0))
        
        # Apply overlays to the pentagon first
        base_img = self.overlay_attributes(base_img)
        
        # Now compose with Render
        if os.path.exists(render_path):
            render_img = Image.open(render_path).convert("RGBA")
            
            pent_w, pent_h = base_img.size
            scale = pent_h / render_img.height
            new_w = int(render_img.width * scale)
            render_img = render_img.resize((new_w, pent_h), Image.Resampling.LANCZOS)
            
            canvas_w = new_w + pent_w + 50
            canvas = Image.new("RGBA", (canvas_w, pent_h), (255, 255, 255, 0))
            
            canvas.paste(render_img, (0, 0), render_img)
            canvas.paste(base_img, (new_w + 50, 0), base_img)
            
            return canvas
        return base_img

    def show_startup_screen(self):
        # Load empty pentagon
        pent_path = os.path.join(BASE_DIR, "empty_pentagon", "mathematical_pentagon.png")
        if os.path.exists(pent_path):
            img = Image.open(pent_path).convert("RGBA")
        else:
            img = Image.new("RGBA", (890, 843), (0,0,0,0))
            
        # Text hint moved to UI instead of drawn on image
        
        avail_w = self.right_frame.winfo_width()
        avail_h = self.right_frame.winfo_height() - self.nav_frame.winfo_height()
        if avail_w < 100: avail_w = 1000
        if avail_h < 100: avail_h = 750
        
        img.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)
        self.main_photo = ImageTk.PhotoImage(img)
        self.main_img_label.config(image=self.main_photo)

    def update_main_image(self):
        if not self.current_champ: return
        
        champ = self.current_champ
        
        if self.current_image_index < 5:
            path = self.get_image_path(self.current_image_index, champ)
            if path and os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                img = self.overlay_attributes(img)
            else:
                img = Image.new("RGBA", (800, 600), (0,0,0,0))
        else:
            img = self.generate_composite()

        # Update thumbnails
        self.update_thumbnails()
        
        avail_w = self.right_frame.winfo_width()
        avail_h = self.right_frame.winfo_height() - self.nav_frame.winfo_height()
        if avail_w < 100: avail_w = 1000
        if avail_h < 100: avail_h = 750
        
        img.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)
        
        # Display
        self.main_photo = ImageTk.PhotoImage(img)
        self.main_img_label.config(image=self.main_photo)

    def update_thumbnails(self):
        # Clear old
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        
        champ = self.current_champ
        render_path = os.path.join(CHAMPS_DIR, champ, f"{champ}_Render.png")
        if not os.path.exists(render_path):
            render_path = os.path.join(CHAMPS_DIR, champ, f"{champ.replace(' ', '_')}_Render.png")

        paths = [
            self.get_image_path(0, champ),
            self.get_image_path(1, champ),
            self.get_image_path(2, champ),
            self.get_image_path(3, champ),
            self.get_image_path(4, champ),
            render_path
        ]
        
        for i, p in enumerate(paths):
            if p and os.path.exists(p):
                try:
                    img = Image.open(p)
                    img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.thumbnails.append(photo)
                    
                    bg_color = "red" if i == self.current_image_index else "#2b2b2b"
                    
                    lbl = tk.Label(self.thumb_frame, image=photo, bg=bg_color, bd=2)
                    lbl.pack(side=tk.LEFT, padx=5)
                    
                    # Click to switch
                    lbl.bind("<Button-1>", lambda e, idx=i: self.set_image_index(idx))
                except:
                    pass

    def set_image_index(self, idx):
        self.current_image_index = idx
        self.update_main_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorPentagonApp(root)
    # Delay first update to get correct window size
    root.after(100, app.update_main_image)
    root.mainloop()
