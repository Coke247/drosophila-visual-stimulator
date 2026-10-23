import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image, ImageTk

class LinePatternApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controlador de Patrón de Líneas")
        self.root.geometry("1100x650")
        
        self.is_fullscreen = False

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)

        self.width = 1280
        self.height = 720
        self.fps = 60
        self.speed = tk.DoubleVar(value=4.0)
        self.color_width = tk.IntVar(value=30)
        self.black_width = tk.IntVar(value=30)
        self.direction = tk.StringVar(value="RIGHT")

        self.colors = [
            (0, 0, 255),    # Rojo
            (0, 255, 0),    # Verde
            (255, 0, 0),    # Azul
            (0, 255, 255),  # Amarillo
            (255, 0, 255)   # Magenta
        ]

        self.offset_x = 0.0
        self.offset_y = 0.0

        self.setup_ui()
        self.update_pattern()

    def setup_ui(self):
        self.control_frame = ttk.Frame(self.root, padding="15")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(self.control_frame, text="Panel de Control", font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 15))

        self.btn_fullscreen = ttk.Button(self.control_frame, text="Pantalla Completa (F11)", command=self.toggle_fullscreen)
        self.btn_fullscreen.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(self.control_frame, text="Dirección del movimiento:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        direction_combo = ttk.Combobox(
            self.control_frame, 
            textvariable=self.direction, 
            state="readonly",
            values=['RIGHT', 'LEFT', 'DOWN', 'UP', 'DIAG_DOWN_RIGHT', 'DIAG_UP_RIGHT']
        )
        direction_combo.pack(fill=tk.X, pady=(2, 12))

        ttk.Label(self.control_frame, text="Velocidad:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Scale(self.control_frame, from_=0.0, to=30.0, variable=self.speed, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(self.control_frame, textvariable=self.speed).pack(anchor=tk.E, pady=(0, 10))

        ttk.Label(self.control_frame, text="Ancho Líneas Color (px):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Scale(self.control_frame, from_=5, to=100, variable=self.color_width, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(self.control_frame, textvariable=self.color_width).pack(anchor=tk.E, pady=(0, 10))

        ttk.Label(self.control_frame, text="Ancho Líneas Negras (px):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Scale(self.control_frame, from_=5, to=100, variable=self.black_width, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(self.control_frame, textvariable=self.black_width).pack(anchor=tk.E, pady=(0, 15))

        ttk.Label(self.control_frame, text="Colores Activos:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.colors_box = tk.Listbox(self.control_frame, height=5, selectmode=tk.SINGLE)
        self.colors_box.pack(fill=tk.X, pady=(2, 5))
        self.refresh_color_list()

        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(btn_frame, text="Agregar Color", command=self.add_color).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(btn_frame, text="Quitar Color", command=self.remove_color).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        self.video_frame = ttk.Frame(self.root)
        self.video_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(self.video_frame, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

        if self.is_fullscreen:
            self.control_frame.pack_forget()
        else:
            self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

    def end_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.toggle_fullscreen()

    def refresh_color_list(self):
        self.colors_box.delete(0, tk.END)
        for idx, (r, g, b) in enumerate(self.colors):
            self.colors_box.insert(tk.END, f"Color {idx + 1}: RGB({r}, {g}, {b})")

    def add_color(self):
        color_code = colorchooser.askcolor(title="Selecciona un nuevo color")
        if color_code[0]:
            r, g, b = [int(c) for c in color_code[0]]
            self.colors.append((r, g, b))
            self.refresh_color_list()

    def remove_color(self):
        selected = self.colors_box.curselection()
        if selected and len(self.colors) > 1:
            self.colors.pop(selected[0])
            self.refresh_color_list()

    def create_pattern_texture(self, render_w, render_h):
        c_width = max(1, self.color_width.get())
        b_width = max(1, self.black_width.get())
        
        pattern_block_size = len(self.colors) * (c_width + b_width)
        
        # Dimensión mínima requerida para cubrir la vista
        needed_w = render_w + pattern_block_size
        needed_h = render_h + pattern_block_size
        max_dim = max(needed_w, needed_h)
        
        texture = np.zeros((max_dim, max_dim, 3), dtype=np.uint8)
        
        offset = 0
        while offset < max_dim:
            for color_rgb in self.colors:
                color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])
                end_color = min(offset + c_width, max_dim)
                texture[:, offset:end_color] = color_bgr
                offset += c_width
                offset += b_width
                if offset >= max_dim:
                    break
                    
        return texture, pattern_block_size

    def update_pattern(self):
        render_w = self.canvas.winfo_width()
        render_h = self.canvas.winfo_height()

        if render_w <= 1 or render_h <= 1:
            render_w, render_h = self.width, self.height

        texture, pattern_block_size = self.create_pattern_texture(render_w, render_h)
        
        shift_x = int(self.offset_x) % pattern_block_size
        shift_y = int(self.offset_y) % pattern_block_size

        dir_val = self.direction.get()

        if dir_val == 'RIGHT':
            frame = texture[:render_h, shift_x:shift_x + render_w]
        elif dir_val == 'LEFT':
            frame = texture[:render_h, pattern_block_size - shift_x:pattern_block_size - shift_x + render_w]
        elif dir_val == 'DOWN':
            frame = np.transpose(texture[:render_w, shift_y:shift_y + render_h], (1, 0, 2))
        elif dir_val == 'UP':
            frame = np.transpose(texture[:render_w, pattern_block_size - shift_y:pattern_block_size - shift_y + render_h], (1, 0, 2))
        elif dir_val == 'DIAG_DOWN_RIGHT':
            frame = texture[shift_y:shift_y + render_h, shift_x:shift_x + render_w]
        elif dir_val == 'DIAG_UP_RIGHT':
            frame = texture[pattern_block_size - shift_y:pattern_block_size - shift_y + render_h, shift_x:shift_x + render_w]
        else:
            frame = texture[:render_h, shift_x:shift_x + render_w]

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(image=img)

        self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        self.canvas.image = img_tk

        # Escalado dinámico de velocidad según el ancho actual de la pantalla
        # Normalizado respecto a la resolución base de 1280px
        scale_factor = render_w / 1280.0
        effective_speed = self.speed.get() * scale_factor

        self.offset_x += effective_speed
        self.offset_y += effective_speed

        self.root.after(int(1000 / self.fps), self.update_pattern)

if __name__ == "__main__":
    root = tk.Tk()
    app = LinePatternApp(root)
    root.mainloop()