import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, UnidentifiedImageError
import os
import threading

#RAMA testeo1

# Constants for image formats
WEBP_FORMAT = "webp"
JPG_FORMAT = "jpg"
PNG_FORMAT = "png"

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Imágenes")
        self.root.geometry("1200x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.selected_files = []
        self.optimize_var = tk.BooleanVar(value=True)
        self.resize_var = tk.BooleanVar(value=False)
        self.width_var = tk.StringVar(value="0 px")
        self.height_var = tk.StringVar(value="0 px")
        self.new_name_var = tk.StringVar(value="")

        self.preview_image_label = None
        self.conversion_running = False  # Use a boolean flag to control conversion
        self.conversion_thread = None # Store the conversion thread
        self.create_widgets()

    def __del__(self):
        # Limpieza de la imagen de previsualización
        if hasattr(self, "preview_image_label"):
            self.preview_image_label.image = None

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo
        left_frame = ttk.Frame(main_frame, width=500)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Panel derecho
        right_frame = ttk.Frame(main_frame, width=700)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Botones de selección y limpieza de archivos
        ttk.Button(
            left_frame, text="Seleccionar Imágenes", command=self.select_files
        ).pack(fill=tk.X, pady=5)
        ttk.Button(
            left_frame, text="Limpiar Selección", command=self.clear_selection
        ).pack(fill=tk.X, pady=5)

        # Listbox para mostrar los archivos seleccionados
        files_frame = ttk.LabelFrame(
            left_frame, text="Archivos Seleccionados", padding="5"
        )
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.files_listbox = tk.Listbox(files_frame, selectmode=tk.SINGLE, width=50)
        self.files_listbox.bind("<<ListboxSelect>>", self.preview_selected)
        scrollbar = ttk.Scrollbar(
            files_frame, orient=tk.VERTICAL, command=self.files_listbox.yview
        )
        self.files_listbox.configure(yscrollcommand=scrollbar.set)

        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame para la vista previa
        preview_frame = ttk.LabelFrame(right_frame, text="Vista Previa", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        preview_canvas = tk.Canvas(preview_frame, width=380, height=300, bg="lightgray")
        preview_canvas.pack()

        self.preview_image_label = tk.Label(preview_canvas)
        self.preview_image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Opciones de conversión
        options_frame = ttk.LabelFrame(
            right_frame, text="Opciones de Conversión", padding="5"
        )
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            options_frame, text="Optimizar", variable=self.optimize_var
        ).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Redimensionar
        resize_frame = ttk.Frame(options_frame)
        resize_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Checkbutton(
            resize_frame, text="Redimensionar", variable=self.resize_var
        ).pack(side=tk.LEFT)
        ttk.Label(resize_frame, text="Ancho:").pack(side=tk.LEFT, padx=(10, 2))

        entry_width = ttk.Entry(
            resize_frame, textvariable=self.width_var, width=6, foreground="gray"
        )
        entry_width.pack(side=tk.LEFT)
        entry_width.bind(
            "<FocusIn>", lambda event: self.add_placeholder(entry_width, "0 px", False)
        )
        entry_width.bind(
            "<FocusOut>", lambda event: self.add_placeholder(entry_width, "0 px", True)
        )

        ttk.Label(resize_frame, text="Alto:").pack(side=tk.LEFT, padx=(10, 2))

        entry_height = ttk.Entry(
            resize_frame, textvariable=self.height_var, width=6, foreground="gray"
        )
        entry_height.pack(side=tk.LEFT)
        entry_height.bind(
            "<FocusIn>", lambda event: self.add_placeholder(entry_height, "0 px", False)
        )
        entry_height.bind(
            "<FocusOut>", lambda event: self.add_placeholder(entry_height, "0 px", True)
        )

        ttk.Label(options_frame, text="Nombre nuevo:").grid(
            row=2, column=0, padx=5, pady=5
        )
        ttk.Entry(options_frame, textvariable=self.new_name_var).grid(
            row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew"
        )

        # Botones de conversión
        convert_frame = ttk.Frame(right_frame)
        convert_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            convert_frame,
            text="Convertir a WebP",
            command=lambda: self.start_conversion(WEBP_FORMAT),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            convert_frame,
            text="Convertir a JPG",
            command=lambda: self.start_conversion(JPG_FORMAT),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            convert_frame,
            text="Convertir a PNG",
            command=lambda: self.start_conversion(PNG_FORMAT),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            convert_frame, text="Cancelar Conversión", command=self.cancel_conversion
        ).pack(side=tk.LEFT, padx=5)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            right_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Etiqueta de estado
        self.status_label = ttk.Label(right_frame, text="Listo")
        self.status_label.pack()

    def add_placeholder(self, widget, text, focus_out):
        """Función para manejar el placeholder en los Entry de ancho y alto."""
        if focus_out and not widget.get():
            widget.insert(0, text)
            widget.config(foreground="gray")
        elif not focus_out and widget.get() == text:
            widget.delete(0, tk.END)
            widget.config(foreground="black")

    def select_files(self):
        """Permite seleccionar archivos de imagen y los agrega a la lista."""
        filetypes = (
            ("Imágenes", "*.png *.jpg *.jpeg *.webp"),
            ("Todos los archivos", "*.*"),
        )
        filenames = filedialog.askopenfilenames(filetypes=filetypes)

        if filenames:
            self.selected_files.extend(filenames)
            self.update_files_list()
            self.preview_selected()

    def clear_selection(self):
        """Limpia la selección de archivos."""
        self.selected_files = []
        self.update_files_list()
        self.preview_image_label.config(image="", text="")
        self.preview_image_label.image = None

    def update_files_list(self):
        """Actualiza la lista de archivos en el Listbox."""
        self.files_listbox.delete(0, tk.END)
        for file in self.selected_files:
            self.files_listbox.insert(tk.END, os.path.basename(file))

    def preview_selected(self, event=None):
        """Muestra la vista previa de la imagen seleccionada en el listbox."""
        if not self.selected_files:
             self.preview_image_label.config(image="", text="")
             self.preview_image_label.image = None
             return

        # Si no hay selección en el listbox, se muestra la primera imagen
        if event is None:
            file_path = self.selected_files[0]
        else:
            index = self.files_listbox.curselection()
            if not index:
                return
            file_path = self.selected_files[index[0]]

        self._update_preview_image(file_path)

    def _update_preview_image(self, file_path):
        try:
            image = Image.open(file_path)
            width, height = image.size
            max_width, max_height = 380, 300

            # Ajuste de la imagen para encajar en la previsualización
            if width > max_width or height > max_height:
                scaling_factor = min(max_width / width, max_height / height)
                width = int(width * scaling_factor)
                height = int(height * scaling_factor)
            image = image.resize((width, height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)
            self.preview_image_label.config(image=photo, text="")
            self.preview_image_label.image = photo

        except FileNotFoundError:
              self.preview_image_label.config(
                text=f"Error al cargar la imagen: Archivo no encontrado.", image=""
            )
        except UnidentifiedImageError:
             self.preview_image_label.config(
                text=f"Error al cargar la imagen: Formato desconocido.", image=""
            )
        except Exception as e:
            self.preview_image_label.config(
                text=f"Error al cargar la imagen: {str(e)}", image=""
            )

    def _resize_image(self, image, target_width, target_height):
        """Redimensiona la imagen manteniendo proporciones."""
        if target_width <= 0 and target_height <= 0:
            return image # no resize
        original_width, original_height = image.size
        if target_width > 0 and target_height == 0:
                # Calcula el alto manteniendo la proporción
                ratio = original_height / original_width
                target_height = int(target_width * ratio)
        elif target_height > 0 and target_width == 0:
                # Calcula el ancho manteniendo la proporción
                ratio = original_width / original_height
                target_width = int(target_height * ratio)
                
        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)

    def cancel_conversion(self):
        """Marca la bandera de cancelación para detener la conversión."""
        self.conversion_running = False
        self.status_label.config(text="Conversión cancelada")
    
    def on_close(self):
        """Handles window close event."""
        self.cancel_conversion()
        if self.conversion_thread and self.conversion_thread.is_alive():
            self.conversion_thread.join()
        self.root.destroy()


    def _preserve_metadata(self, original_image, new_image):
        """
        Intenta preservar los datos EXIF si existen.
        Retorna el exif (o None) para usarlo al guardar la imagen.
        """
        exif_data = None
        try:
            exif_data = original_image.info["exif"]
            new_image.info["exif"] = exif_data
        except KeyError:
            pass
        return exif_data

    def start_conversion(self, format_type):
        """Inicia la conversión en un hilo separado."""
        if not self.selected_files:
            messagebox.showwarning("Advertencia", "Selecciona archivos primero")
            return

        output_dir = filedialog.askdirectory(title="Selecciona carpeta de destino")
        if not output_dir:
            return

        self.conversion_running = True
        self.conversion_thread = threading.Thread(
            target=self.convert_files, args=(format_type, output_dir)
        )
        self.conversion_thread.start()

    def convert_files(self, format_type, output_dir):
        """Procesa la conversión de archivos uno por uno en un hilo aparte."""
        total_files = len(self.selected_files)
        converted = 0
        errors = []

        for i, file_path in enumerate(self.selected_files):
            if not self.conversion_running:
                break

            try:
                self.root.after(0, self.update_status, f"Convirtiendo: {os.path.basename(file_path)}")
                self.root.after(0, self.update_progress, (i+1) / total_files * 100)
                self.convert_to_format(file_path, output_dir, format_type)
                converted += 1

            except Exception as e:
                errors.append(f"Error en {os.path.basename(file_path)}: {str(e)}")

        self.root.after(0, self.show_conversion_result, converted, total_files, errors)
        self.root.after(0, self.reset_progress)

        if self.conversion_running:
            self.root.after(0, self.update_status, "Listo")
        self.conversion_running = False

    def update_progress(self, progress):
         self.progress_var.set(progress)

    def update_status(self, text):
         self.status_label.config(text=text)

    def reset_progress(self):
        self.progress_var.set(0)

    def convert_to_format(self, file_path, output_dir, format_type):
        """Convierte un archivo de imagen a un formato específico."""
        try:
            image = Image.open(file_path)
            image = self._prepare_image(image, format_type)
            output_path = self._generate_output_path(file_path, output_dir, format_type)
            self._save_image(image, output_path, format_type)
        except (FileNotFoundError, OSError, UnidentifiedImageError) as e:
           raise e
        except Exception as e:
             raise Exception(f"Error during conversion: {str(e)}")

    def _prepare_image(self, image, format_type):
        """Prepares the image for conversion (mode conversion, resizing)."""
        if format_type != PNG_FORMAT and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        if self.resize_var.get():
            width_str = self.width_var.get().replace("px", "").strip()
            height_str = self.height_var.get().replace("px", "").strip()

            try:
                target_width = int(width_str) if width_str.isdigit() else 0
                target_height = int(height_str) if height_str.isdigit() else 0
            except ValueError:
                raise ValueError("Los valores de ancho y alto deben ser números enteros mayores que 0.")
            image = self._resize_image(image, target_width, target_height)

        return image

    def _generate_output_path(self, file_path, output_dir, format_type):
         """Generates the output file path."""
         new_name = self.new_name_var.get().strip()
         if new_name:
              output_filename = new_name + f".{format_type}"
         else:
              output_filename = (
                 os.path.splitext(os.path.basename(file_path))[0] + f".{format_type}"
             )
         return os.path.join(output_dir, output_filename)

    def _save_image(self, image, output_path, format_type):
        """Saves the converted image."""
        save_options = {
            "quality": 100,
            "optimize": self.optimize_var.get(),
        }
        exif_data = self._preserve_metadata(image, image)
        if exif_data:
            image.save(output_path, format_type.upper(), exif=exif_data, **save_options)
        else:
            image.save(output_path, format_type.upper(), **save_options)


    def show_conversion_result(self, converted, total, errors):
        """Muestra el resultado final de la conversión en un mensaje."""
        message = f"Se convirtieron {converted} de {total} imágenes.\n\n"

        if errors:
            message += "Errores encontrados:\n" + "\n".join(errors)
            messagebox.showerror("Resultado de la conversión", message)
        else:
            message += "No se encontraron errores."
            messagebox.showinfo("Resultado de la conversión", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()