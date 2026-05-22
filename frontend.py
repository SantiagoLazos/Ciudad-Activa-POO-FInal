import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import uuid
import csv
from app_backend import *

#Configuración inicial de la apariencia (Light mode según indicaciones)
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class LoginWindow(ctk.CTk):
    #Vista de Inicio de Sesión (Login).
    #Permite autenticar al usuario y redirigirlo a la vista correspondiente.
    def __init__(self):
        super().__init__()
        self.geometry("400x500")
        self.title("Ciudad Activa - Login")
        self.resizable(False, False)

        #Centrar la ventana en la pantalla
        self.eval('tk::PlaceWindow . center')

        #Contenedor principal con estilo moderno
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.pack(expand=True, fill="both", padx=40, pady=40)

        #Título
        self.lbl_title = ctk.CTkLabel(
            self.frame, 
            text="CIUDAD ACTIVA", 
            font=ctk.CTkFont(family="Roboto", size=28, weight="bold"), 
            text_color="#1f538d"
        )
        self.lbl_title.pack(pady=(20, 5))

        self.lbl_subtitle = ctk.CTkLabel(
            self.frame, 
            text="Gestión de Incidencias", 
            font=ctk.CTkFont(family="Roboto", size=16), 
            text_color="gray"
        )
        self.lbl_subtitle.pack(pady=(0, 30))

        #Entradas de texto con placeholders
        self.entry_correo = ctk.CTkEntry(
            self.frame, 
            placeholder_text="Correo Electrónico", 
            height=40, 
            font=("Inter", 14)
        )
        self.entry_correo.pack(fill="x", pady=10)

        self.entry_password = ctk.CTkEntry(
            self.frame, 
            placeholder_text="Contraseña", 
            show="*", 
            height=40, 
            font=("Inter", 14)
        )
        self.entry_password.pack(fill="x", pady=10)

        #Botón de ingreso
        self.btn_login = ctk.CTkButton(
            self.frame, 
            text="Ingresar", 
            height=45, 
            font=ctk.CTkFont(size=15, weight="bold"), 
            command=self.login
        )
        self.btn_login.pack(fill="x", pady=30)

        #Crear archivo usuarios.csv por defecto si no existe
        self._crear_usuarios_default()

    def _crear_usuarios_default(self):
        #Crea credenciales de prueba si el archivo de usuarios no existe.
        ruta = os.path.join(os.path.dirname(__file__), "usuarios.csv")
        if not os.path.exists(ruta):
            with open(ruta, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["correo", "contraseña", "tipo"])
                writer.writerow(["ciudadano@mail.com", "1234", "ciudadano"])
                writer.writerow(["admin@mail.com", "admin", "autoridad"])

    def login(self):
        #Para la validación al iniciar sesión.
        correo = self.entry_correo.get().strip()
        password = self.entry_password.get().strip()

        if not correo or not password:
            messagebox.showerror("Error", "Por favor completa todos los campos.")
            return

        ruta = os.path.join(os.path.dirname(__file__), "usuarios.csv")
        try:
            with open(ruta, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["correo"] == correo and row["contraseña"] == password:
                        tipo = row["tipo"]
                        self.withdraw()  # Ocultar login
                        if tipo == "ciudadano":
                            CitizenWindow(self).mainloop()
                        else:
                            AuthorityWindow(self).mainloop()
                        return
            messagebox.showerror("Error", "Correo o contraseña incorrectos.")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Error al leer usuarios: {e}")


class CitizenWindow(ctk.CTkToplevel):
    #Vista del Ciudadano para reportar incidencias.
    def __init__(self, login_window):
        super().__init__()
        self.login_window = login_window
        self.geometry("600x650")
        self.title("Ciudad Activa - Reportar Incidencia")
        self.protocol("WM_DELETE_WINDOW", self.cerrar_sesion)
        self.backend = Backend()
        
        #Color de fondo profesional y layout
        self.configure(fg_color="#f4f5f7")
        self.frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.frame.pack(expand=True, fill="both", padx=30, pady=30)

        #Título
        self.lbl_title = ctk.CTkLabel(
            self.frame, 
            text="Reportar Nueva Incidencia", 
            font=ctk.CTkFont(size=22, weight="bold"), 
            text_color="#2c3e50"
        )
        self.lbl_title.pack(pady=20)

        #Título del reporte
        self.entry_titulo = ctk.CTkEntry(self.frame, placeholder_text="Título del reporte", height=40)
        self.entry_titulo.pack(fill="x", padx=40, pady=10)

        #Ubicación
        self.entry_ubicacion = ctk.CTkEntry(self.frame, placeholder_text="Ubicación (Ej. Calle Benito Juárez 123)", height=40)
        self.entry_ubicacion.pack(fill="x", padx=40, pady=10)

        #Tipo (Combobox)
        self.combo_tipo = ctk.CTkComboBox(self.frame, values=["bache", "basura", "alumbrado", "emergencia", "otro"], height=40)
        self.combo_tipo.pack(fill="x", padx=40, pady=10)

        #Descripción
        self.textbox_desc = ctk.CTkTextbox(self.frame, height=100)
        self.textbox_desc.insert("1.0", "Descripción de la incidencia...")
        self.textbox_desc.bind("<FocusIn>", self._clear_placeholder)
        self.textbox_desc.pack(fill="x", padx=40, pady=10)

        self.ruta_imagen = "NaN"
        
        #Frame para botones de imagen
        self.img_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.img_frame.pack(fill="x", padx=40, pady=10)
        
        self.btn_imagen = ctk.CTkButton(
            self.img_frame, 
            text="Seleccionar Imagen", 
            command=self.seleccionar_imagen, 
            width=150, 
            fg_color="#3498db", 
            hover_color="#2980b9"
        )
        self.btn_imagen.pack(side="left")

        self.label_imagen = ctk.CTkLabel(self.img_frame, text="Ninguna imagen", text_color="gray")
        self.label_imagen.pack(side="left", padx=20)

        #Frame para botones de acción
        self.action_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=40, pady=20)

        self.btn_enviar = ctk.CTkButton(
            self.action_frame, 
            text="Enviar Reporte", 
            command=self.enviar_reporte, 
            fg_color="#27ae60", 
            hover_color="#2ecc71"
        )
        self.btn_enviar.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.btn_salir = ctk.CTkButton(
            self.action_frame, 
            text="Cerrar Sesión", 
            command=self.cerrar_sesion, 
            fg_color="#e74c3c", 
            hover_color="#c0392b"
        )
        self.btn_salir.pack(side="right", expand=True, fill="x", padx=(10, 0))

    def _clear_placeholder(self, event):
        #Borra el placeholder cuando el campo de descripción gana el foco.
        if self.textbox_desc.get("1.0", "end-1c") == "Descripción de la incidencia...":
            self.textbox_desc.delete("1.0", "end")

    def seleccionar_imagen(self):
        #Abre un cuadro de diálogo para seleccionar una imagen de evidencia.
        archivo = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=[("Imagenes", "*.png *.jpg *.jpeg")])
        if archivo:
            self.ruta_imagen = archivo
            self.label_imagen.configure(text=os.path.basename(archivo))
        else:
            self.ruta_imagen = "NaN"
            self.label_imagen.configure(text="Ninguna imagen")

    def enviar_reporte(self):
        #Crea y guarda el reporte del ciudadano.
        titulo = self.entry_titulo.get().strip()
        ubicacion = self.entry_ubicacion.get().strip()
        tipo = self.combo_tipo.get()
        desc = self.textbox_desc.get("1.0", "end-1c").strip()

        if not titulo or not ubicacion or desc == "" or desc == "Descripción de la incidencia...":
            messagebox.showwarning("Campos incompletos", "Por favor completa el título, ubicación y descripción.")
            return

        nuevo_reporte = Report(
            id=str(uuid.uuid4())[:8],
            title=titulo,
            description=desc,
            location=ubicacion,
            image_path=self.ruta_imagen,
            type_str=tipo,
            frequency=0,
            time_hours=0.0
        )
        
        try:
            self.backend.add_report(nuevo_reporte)
            messagebox.showinfo("Éxito", "Reporte enviado exitosamente.")
            
            #Limpiar campos después del envío exitoso
            self.entry_titulo.delete(0, 'end')
            self.entry_ubicacion.delete(0, 'end')
            self.combo_tipo.set("bache")
            self.textbox_desc.delete("1.0", "end")
            self.textbox_desc.insert("1.0", "Descripción de la incidencia...")
            self.ruta_imagen = "NaN"
            self.label_imagen.configure(text="Ninguna imagen")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el reporte: {e}")

    def cerrar_sesion(self):
        #Cierra la ventana actual y muestra de nuevo el login.
        self.destroy()
        self.login_window.deiconify()
        self.login_window.entry_password.delete(0, 'end')

#Ventana de autoridad, por ahora solo es un placeholder.
#Se puede expandir con funcionalidades específicas para autoridades en el futuro.

class AuthorityWindow(ctk.CTkToplevel):
    #Vista de Autoridad para gestionar incidencias y calcular prioridades.
    def __init__(self, login_window):
        super().__init__()
        self.login_window = login_window
        self.geometry("1100x700")
        self.title("Ciudad Activa - Gestión de Autoridad")
        self.protocol("WM_DELETE_WINDOW", self.cerrar_sesion)
        self.backend = Backend() #Instancia del backend para acceder a los datos de los reportes.

        #grid() para dividir la ventana en dos columnas (izquierda para formulario, derecha para tabla)
        self.configure(fg_color="#f4f5f7")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        #Zona superior (Header y Barra de Búsqueda)
        self.frame_top = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.frame_top.grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")

        lbl_header = ctk.CTkLabel(
            self.frame_top, 
            text="Panel de Autoridad", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            text_color="#1f538d"
        )
        lbl_header.pack(side="left", padx=20)

        self.search_entry = ctk.CTkEntry(self.frame_top, placeholder_text="Buscar incidencia por título...", width=300)
        self.search_entry.pack(side="right", padx=20, pady=15)
        self.search_entry.bind("<KeyRelease>", self.real_time_search) #<KeyRelease> Búsqueda en tiempo real a medida que se escribe.

        #Panel Izquierdo: Lista de reportes y formulario de edición
        self.frame_left = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.frame_left.grid(row=1, column=0, padx=(15, 5), pady=(0, 15), sticky="nsew")
        
        ctk.CTkLabel(
            self.frame_left, 
            text="Gestión de Incidencia", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color="#2c3e50"
        ).pack(pady=20)

        self.selected_id = "" #Para almacenar el ID del reporte seleccionado 
        
        #Campos de entrada
        ctk.CTkLabel(self.frame_left, text="Título:", text_color="gray").pack(anchor="w", padx=20)
        self.entry_title = ctk.CTkEntry(self.frame_left)
        self.entry_title.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(self.frame_left, text="Tipo:", text_color="gray").pack(anchor="w", padx=20)
        self.combo_type = ctk.CTkComboBox(self.frame_left, values=["bache", "basura", "alumbrado", "emergencia", "otro"])
        self.combo_type.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(self.frame_left, text="Frecuencia (Reportes similares):", text_color="gray").pack(anchor="w", padx=20)
        self.entry_freq = ctk.CTkEntry(self.frame_left)
        self.entry_freq.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(self.frame_left, text="Tiempo transcurrido (Horas):", text_color="gray").pack(anchor="w", padx=20)
        self.entry_time = ctk.CTkEntry(self.frame_left)
        self.entry_time.pack(fill="x", padx=20, pady=(0, 25))

        #Botones de acción
        self.btn_actualizar = ctk.CTkButton(
            self.frame_left, 
            text="Actualizar y Recalcular", 
            command=self.update_record, 
            fg_color="#3498db", 
            hover_color="#2980b9"
        )
        self.btn_actualizar.pack(fill="x", padx=20, pady=5)

        self.btn_eliminar = ctk.CTkButton(
            self.frame_left, 
            text="Eliminar Reporte", 
            command=self.delete_record, 
            fg_color="#e74c3c", 
            hover_color="#c0392b"
        )
        self.btn_eliminar.pack(fill="x", padx=20, pady=5)

        self.btn_limpiar = ctk.CTkButton(
            self.frame_left, 
            text="Limpiar Campos", 
            command=self.clear_inputs, 
            fg_color="#95a5a6", 
            hover_color="#7f8c8d"
        )
        self.btn_limpiar.pack(fill="x", padx=20, pady=5)
        
        self.btn_logout = ctk.CTkButton(
            self.frame_left, 
            text="Cerrar Sesión", 
            command=self.cerrar_sesion, 
            fg_color="transparent", 
            text_color="#e74c3c", 
            border_width=1, 
            border_color="#e74c3c"
        )
        self.btn_logout.pack(fill="x", padx=20, pady=(30, 10))

        #Panel Derecho (Tabla/Dashboard)
        self.frame_right = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.frame_right.grid(row=1, column=1, padx=(5, 15), pady=(0, 15), sticky="nsew")

        ctk.CTkLabel(
            self.frame_right, 
            text="Lista de Reportes Priorizados", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color="#2c3e50"
        ).pack(pady=20)

        #Configuración de Treeview estilo moderno
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", 
            background="#f4f5f7", 
            foreground="black", 
            rowheight=30, 
            fieldbackground="#f4f5f7", 
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading", 
            background="#e0e6ed", 
            foreground="#2c3e50", 
            font=("Arial", 11, "bold"), 
            borderwidth=0
        )
        style.map("Treeview", background=[("selected", "#3498db")])

        columns = ("ID", "Título", "Tipo", "Frec.", "Hrs.", "Score Prioridad")
        self.tree = ttk.Treeview(self.frame_right, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            #Ajustar anchos para que se vea estético
            width = 150 if col == "Título" else 80
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        #Event Binding: Clic en la tabla
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)

        self.refresh_table()

    def refresh_table(self, query: str = "") -> None:
        #Actualiza el Treeview con los datos actuales o filtrados.
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if query:
            data = self.backend.search_reports(query)
            #Ordenar búsqueda también por prioridad
            data.sort(key=lambda x: x.priority, reverse=True)
        else:
            data = self.backend.get_all_reports()
            
        for r in data:
            self.tree.insert("", "end", values=(r.id, r.title, r.type_str, r.frequency, r.time_hours, r.priority))

    def real_time_search(self, event) -> None:
        #Filtra la tabla a medida que se escribe en la barra de búsqueda.
        query = self.search_entry.get().strip()
        self.refresh_table(query)

    def on_tree_select(self, event) -> None:
        #Puebla los campos de texto al seleccionar un registro de la tabla.
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected[0])
        values = item['values']
        
        self.selected_id = str(values[0])
        self.clear_inputs_internal()
        
        self.entry_title.insert(0, str(values[1]))
        self.combo_type.set(str(values[2]))
        self.entry_freq.insert(0, str(values[3]))
        self.entry_time.insert(0, str(values[4]))

    def clear_inputs(self) -> None:
        #Limpia todos los campos del panel izquierdo y deselecciona el item en la tabla.
        self.clear_inputs_internal()
        self.selected_id = ""
        #Deseleccionar item en el treeview
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def clear_inputs_internal(self) -> None:
        #Método interno para limpiar solo los campos de entrada.
        self.entry_title.delete(0, 'end')
        self.entry_freq.delete(0, 'end')
        self.entry_time.delete(0, 'end')

    def validate_numbers(self, freq_str: str, time_str: str) -> bool:
        #Validación estricta para evitar crashes por letras o números negativos.
        #Muestra un mensaje de error detallado al usuario.
        if not freq_str or not time_str:
            messagebox.showerror("Error de Validación", "Frecuencia y Tiempo no pueden estar vacíos.")
            return False
            
        try:
            freq = int(freq_str)
            time_val = float(time_str)
            if freq < 0 or time_val < 0:
                messagebox.showerror("Error de Validación", "Los valores numéricos no pueden ser negativos.")
                return False
            return True
        except ValueError:
            messagebox.showerror("Error de Validación", "Frecuencia debe ser un número entero y Tiempo un valor numérico válido (sin letras).")
            return False

    def update_record(self) -> None:
        #Actualiza el reporte y recalcula la prioridad automáticamente.
        if not self.selected_id:
            messagebox.showwarning("Atención", "Selecciona un reporte de la tabla primero.")
            return
            
        title = self.entry_title.get().strip()
        type_str = self.combo_type.get()
        freq_str = self.entry_freq.get().strip()
        time_str = self.entry_time.get().strip()
        
        if not title:
            messagebox.showerror("Error de Validación", "El título no puede estar vacío.")
            return
            
        if self.validate_numbers(freq_str, time_str):
            updated_data = {
                'title': title,
                'type_str': type_str,
                'frequency': freq_str,
                'time_hours': time_str
            }
            if self.backend.update_report(self.selected_id, updated_data):
                messagebox.showinfo("Éxito", "Reporte actualizado y score recalculado.")
                self.refresh_table()
                self.clear_inputs()

    def delete_record(self) -> None:
        #Elimina un registro con confirmación de seguridad.
        if not self.selected_id:
            messagebox.showwarning("Atención", "Selecciona un reporte de la tabla primero.")
            return
            
        confirm = messagebox.askyesno("Confirmar Eliminación", "¿Estás absolutamente seguro de que deseas eliminar permanentemente este reporte?")
        if confirm:
            if self.backend.delete_report(self.selected_id):
                messagebox.showinfo("Éxito", "El reporte ha sido eliminado.")
                self.refresh_table()
                self.clear_inputs()

    def cerrar_sesion(self):
        #Cierra la ventana actual y muestra de nuevo el login.
        self.destroy()
        self.login_window.deiconify()
        self.login_window.entry_password.delete(0, 'end')

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
