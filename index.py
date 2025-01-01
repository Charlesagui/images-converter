import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, UnidentifiedImageError
from pathlib import Path
import threading
import cv2
import numpy as np
import svgwrite

WEBP_FORMAT = "webp"
JPG_FORMAT = "jpg"
PNG_FORMAT = "png"
SVG_FORMAT = "svg"

PIL_FORMATS = {
    "jpg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "svg": None  # Pillow no soporta SVG, pero está manejado por otra parte del código
}


def imread_unicode_path(path_obj):
    """Lee una imagen desde una ruta con caracteres especiales."""
    try:
        with open(path_obj, "rb") as f:
            file_bytes = f.read()
        # Convertimos los bytes a un array de numpy
        arr = np.frombuffer(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
        return img
    except Exception as e:
        print(f"Error al leer la imagen desde la ruta {path_obj}: {e}")
        return None

class ImageConverterApp:
    """Aplicación de conversión de imágenes con vectorizado a SVG.
    - Extrae contornos (canales RGB) y los dibuja con svgwrite.
    - Aplica un gradiente radial en el mismo SVG.
    - Redimensiona si se selecciona esa opción.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imágenes")
        self.root.geometry("1200x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Variables de control
        self.selected_files = []
        self.optimize_var = tk.BooleanVar(value=True)
        self.resize_var = tk.BooleanVar(value=False)
        self.width_var = tk.StringVar(value="0")
        self.height_var = tk.StringVar(value="0")
        self.new_name_var = tk.StringVar(value="")
        self.threshold_var = tk.IntVar(value=128)  # Umbral para binarización (0-255)

        self.preview_image_label = None
        self.conversion_running = False
        self.conversion_thread = None
        self.create_widgets()

    def create_widgets(self):
        """Crea y dispone los widgets de la interfaz gráfica."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo
        left_frame = ttk.Frame(main_frame, width=500)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Panel derecho
        right_frame = ttk.Frame(main_frame, width=700)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Botones principales
        ttk.Button(left_frame, text="Seleccionar Imágenes", command=self.select_files).pack(fill=tk.X, pady=5)
        ttk.Button(left_frame, text="Limpiar Selección", command=self.clear_selection).pack(fill=tk.X, pady=5)

        # Lista de archivos
        files_frame = ttk.LabelFrame(left_frame, text="Archivos Seleccionados", padding="5")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.files_listbox = tk.Listbox(files_frame, selectmode=tk.SINGLE, width=50)
        self.files_listbox.bind("<<ListboxSelect>>", self.preview_selected)
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Vista previa
        preview_frame = ttk.LabelFrame(right_frame, text="Vista Previa", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        preview_canvas = tk.Canvas(preview_frame, width=380, height=300, bg="lightgray")
        preview_canvas.pack()
        self.preview_image_label = tk.Label(preview_canvas)
        self.preview_image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Opciones
        options_frame = ttk.LabelFrame(right_frame, text="Opciones de Conversión", padding="5")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(options_frame, text="Optimizar", variable=self.optimize_var).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Opciones de redimensión
        resize_frame = ttk.Frame(options_frame)
        resize_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        ttk.Checkbutton(resize_frame, text="Redimensionar", variable=self.resize_var).pack(side=tk.LEFT)
        ttk.Label(resize_frame, text="Ancho:").pack(side=tk.LEFT, padx=(10, 2))
        width_entry = ttk.Entry(resize_frame, textvariable=self.width_var, width=6)
        width_entry.pack(side=tk.LEFT)

        ttk.Label(resize_frame, text="Alto:").pack(side=tk.LEFT, padx=(10, 2))
        height_entry = ttk.Entry(resize_frame, textvariable=self.height_var, width=6)
        height_entry.pack(side=tk.LEFT)

        # Umbral para SVG
        threshold_frame = ttk.Frame(options_frame)
        threshold_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        ttk.Label(threshold_frame, text="Umbral (0-255):").pack(side=tk.LEFT)
        ttk.Entry(threshold_frame, textvariable=self.threshold_var, width=5).pack(side=tk.LEFT, padx=5)

        # Nombre nuevo
        ttk.Label(options_frame, text="Nombre nuevo:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(options_frame, textvariable=self.new_name_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Botones de conversión
        convert_frame = ttk.Frame(right_frame)
        convert_frame.pack(fill=tk.X, pady=(0, 10))

        self.conversion_buttons = {}
        for format_type, text in [(WEBP_FORMAT, "WebP"), (JPG_FORMAT, "JPG"),
                                  (PNG_FORMAT, "PNG"), (SVG_FORMAT, "SVG")]:
            button = ttk.Button(
                convert_frame,
                text=f"Convertir a {text}",
                command=lambda ft=format_type: self.start_conversion(ft)
            )
            button.pack(side=tk.LEFT, padx=5)
            self.conversion_buttons[format_type] = button


        ttk.Button(convert_frame, text="Cancelar", command=self.cancel_conversion).pack(side=tk.LEFT, padx=5)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(right_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(right_frame, text="Listo")
        self.status_label.pack()

    def _image_to_svg_with_colors(self, input_path, output_path, threshold):
        """Convierte una imagen a SVG con contornos por canal (RGB) y agrega un gradiente radial."""
        print("========== _image_to_svg_with_colors DEBUG INFO ==========")
        print(f"Ruta recibida: {input_path}")
        print("Existe la ruta?", input_path.exists())
        print("Es archivo?", input_path.is_file())

        img = imread_unicode_path(input_path)
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen con OpenCV: {input_path}")

        # Redimensionamiento usando OpenCV, si está activado
        if self.resize_var.get():
            try:
                width = int(self.width_var.get().strip() or "0")
                height = int(self.height_var.get().strip() or "0")
                if width > 0 and height > 0:
                    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
                    print(f"Redimensionado a: {width} x {height}")
            except ValueError:
                print("Valor no numérico en anchura o altura, se omite redimensionamiento.")

        # Convertimos a RGB (OpenCV -> BGR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, _ = img_rgb.shape

        # Crear el objeto Drawing de svgwrite
        dwg = svgwrite.Drawing(filename=str(output_path),
                               profile='tiny',
                               size=(f"{width}px", f"{height}px"))

        # Extraer contornos por cada canal R, G, B
        for i, color in enumerate(['red', 'green', 'blue']):
            channel = img_rgb[:, :, i]
            _, binary = cv2.threshold(channel, threshold, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                if cv2.contourArea(contour) > 100:
                    path_data = "M " + " L ".join([f"{p[0][0]},{p[0][1]}" for p in contour]) + " Z"
                    dwg.add(dwg.path(d=path_data, fill=color, opacity=0.6))

        # Agregar un gradiente radial con svgwrite
        grad_id = "myRadialGradient"
        radial_grad = dwg.defs.add(
            dwg.radialGradient(
                id_=grad_id,
                center=("50%", "50%"),
                r="50%"
            )
        )
        radial_grad.add_stop_color(offset=0.0, color="red", opacity=1.0)
        radial_grad.add_stop_color(offset=1.0, color="blue", opacity=1.0)

        dwg.add(dwg.rect(
            insert=(0, 0),
            size=(width, height),
            fill=f"url(#{grad_id})",
            opacity=0.3
        ))

        dwg.save()
        print("SVG guardado correctamente:", output_path)

    def _load_image(self, file_path):
        """Carga una imagen usando imread_unicode_path o PIL, dependiendo del contexto."""
        try:
             if file_path.suffix.lower() == ".svg":
                 return None
             img = imread_unicode_path(file_path)
             if img is not None:
                return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
             else:
                return Image.open(file_path)

        except (UnidentifiedImageError, FileNotFoundError) as e:
            raise Exception(f"Error al cargar imagen: {str(e)}")
        except Exception as e:
            raise Exception(f"Error Inesperado al cargar imagen: {str(e)}")


    def convert_files(self, format_type, output_dir):
        total_files = len(self.selected_files)
        converted = 0
        errors = []

        for i, file_path in enumerate(self.selected_files):
            if not self.conversion_running:
                break

            try:
                self.root.after(0, self.update_status, f"Convirtiendo: {file_path.name}")
                self.root.after(0, self.update_progress, (i + 1) / total_files * 100)

                output_path = self._generate_output_path(file_path, output_dir, format_type, i)
                print(f"Ruta de salida: {output_path}")

                if format_type == SVG_FORMAT:
                    self._image_to_svg_with_colors(file_path, output_path, self.threshold_var.get())
                else:
                    print(f"Intentando convertir {file_path} a {format_type}")
                    try:
                        image = self._load_image(file_path)
                        if image is None:
                            errors.append(f"Error en {file_path.name}: No se pudo procesar la imagen para convertir a {format_type.upper()}.")
                            continue

                        # Redimensionar si está activado
                        if self.resize_var.get():
                            w = int(self.width_var.get().strip() or "0")
                            h = int(self.height_var.get().strip() or "0")
                            if w > 0 and h > 0:
                                image = image.resize((w, h), Image.Resampling.LANCZOS)

                        # Obtener el formato compatible con Pillow
                        pil_format = PIL_FORMATS.get(format_type.lower())
                        if pil_format is None:
                            errors.append(f"Formato no soportado por Pillow: {format_type.upper()}")
                            continue

                        print(f"Guardando imagen en: {output_path}, formato Pillow: {pil_format}")
                        image.save(str(output_path), format=pil_format, optimize=self.optimize_var.get())
                        print(f"Convertido {file_path} a {output_path}")
                    except Exception as e:
                        errors.append(f"Error al convertir {file_path.name} a {format_type}: {str(e)}")
                        print(f"Error al convertir {file_path} a {format_type}: {e}, tipo de error: {type(e)}")

                converted += 1

            except Exception as e:
                errors.append(f"Error general al procesar {file_path}: {str(e)}")
                print(f"Error general al procesar {file_path}: {e}, tipo de error: {type(e)}")

        self.root.after(0, self.show_conversion_result, converted, total_files, errors)
        self.root.after(0, self.reset_progress)
        self.root.after(0, self.enable_conversion_buttons)
        self.conversion_running = False

    def _generate_output_path(self, file_path, output_dir, format_type, index):
        new_name = self.new_name_var.get().strip()
        if new_name:
            output_filename = f"{new_name}_{index}.{format_type}"
        else:
            output_filename = f"{file_path.stem}.{format_type}"
        return Path(output_dir) / output_filename

    def select_files(self):
        filetypes = (("Imágenes", "*.png *.jpg *.jpeg *.webp *.svg"), ("Todos los archivos", "*.*"))
        filenames = filedialog.askopenfilenames(filetypes=filetypes)
        if filenames:
            self.selected_files.extend([Path(f).resolve() for f in filenames])
            self.update_files_list()
            self.preview_selected()

    def clear_selection(self):
        self.selected_files = []
        self.files_listbox.delete(0, tk.END)
        if self.preview_image_label:
            self.preview_image_label.config(image="")
            self.preview_image_label.image = None

    def update_files_list(self):
        self.files_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.files_listbox.insert(tk.END, file.name)

    def preview_selected(self, event=None):
        if not self.selected_files:
            return
        try:
            if event:
                index = self.files_listbox.curselection()
                if not index:
                    return
                file_path = self.selected_files[index[0]]
            else:
                file_path = self.selected_files[0]

            image = self._load_image(file_path)
            if image:
              width, height = image.size
              max_size = (380, 300)
              ratio = min(max_size[0] / width, max_size[1] / height)
              new_size = (int(width * ratio), int(height * ratio))
              image = image.resize(new_size, Image.Resampling.LANCZOS)
              photo = ImageTk.PhotoImage(image)
              self.preview_image_label.config(image=photo, text="")
              self.preview_image_label.image = photo
            else:
              self.preview_image_label.config(text="Vista previa no disponible para SVG", image="")
              self.preview_image_label.image = None

        except Exception as e:
            self.preview_image_label.config(text=f"Error: {str(e)}", image="")
            self.preview_image_label.image = None

    def start_conversion(self, format_type):
        if not self.selected_files:
            messagebox.showwarning("Advertencia", "Selecciona archivos primero")
            return

        output_dir = filedialog.askdirectory(title="Selecciona carpeta de destino")
        if not output_dir:
            return
        
        self.disable_conversion_buttons()
        self.conversion_running = True
        self.conversion_thread = threading.Thread(
            target=self.convert_files,
            args=(format_type, output_dir)
        )
        self.conversion_thread.start()

    def cancel_conversion(self):
        self.conversion_running = False
        self.status_label.config(text="Conversión cancelada")
        self.enable_conversion_buttons()


    def on_close(self):
        self.cancel_conversion()
        if self.conversion_thread and self.conversion_thread.is_alive():
            self.conversion_thread.join()
        self.root.destroy()

    def update_progress(self, progress):
        self.progress_var.set(progress)

    def update_status(self, text):
        self.status_label.config(text=text)

    def reset_progress(self):
        self.progress_var.set(0)

    def show_conversion_result(self, converted, total, errors):
        message = f"Se convirtieron {converted} de {total} imágenes."
        if errors:
            message += "\n\nErrores:\n" + "\n".join(errors)
            messagebox.showerror("Resultado", message)
        else:
            messagebox.showinfo("Resultado", message)
        self.status_label.config(text="Listo")

    def disable_conversion_buttons(self):
       for button in self.conversion_buttons.values():
            button.config(state=tk.DISABLED)

    def enable_conversion_buttons(self):
        for button in self.conversion_buttons.values():
            button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()