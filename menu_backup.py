import tkinter as tk
from tkinter import ttk
import sqlite3
import os
from datetime import datetime, timedelta
import json
import subprocess

# ====== ANIMACIONES ======
def animate_element_slide_in(widget, delay=0, direction="right", duration=400):
    """Animación simple de slide in para elementos"""
    if not widget.winfo_exists():
        return
    
    def start_animation():
        try:
            # Para simplificar, solo usamos place con coordenadas
            # Guardar geometría original
            original_place = widget.place_info()
            if not original_place:  # Si no usa place, convertir
                widget.update_idletasks()
                x = widget.winfo_x()
                y = widget.winfo_y()
                widget.place(x=x, y=y)
                original_place = {'x': x, 'y': y}
            
            # Calcular posición inicial
            distance = 30
            if direction == "right":
                start_x = int(original_place.get('x', 0)) - distance
                start_y = int(original_place.get('y', 0))
            elif direction == "left":
                start_x = int(original_place.get('x', 0)) + distance
                start_y = int(original_place.get('y', 0))
            elif direction == "up":
                start_x = int(original_place.get('x', 0))
                start_y = int(original_place.get('y', 0)) + distance
            else:  # down
                start_x = int(original_place.get('x', 0))
                start_y = int(original_place.get('y', 0)) - distance
            
            # Posición inicial
            widget.place(x=start_x, y=start_y)
            
            # Animación
            steps = 15
            for i in range(steps + 1):
                progress = i / steps
                current_x = start_x + (int(original_place.get('x', 0)) - start_x) * progress
                current_y = start_y + (int(original_place.get('y', 0)) - start_y) * progress
                widget.after(int(duration * progress), lambda x=current_x, y=current_y: widget.place(x=x, y=y))
                
        except Exception as e:
            print(f"Error en animación: {e}")
            # Si hay error, al menos mostrar el widget
            try:
                widget.place(x=int(original_place.get('x', 0)), y=int(original_place.get('y', 0)))
            except:
                pass
    
    if delay > 0:
        widget.after(delay, start_animation)
    else:
        start_animation()

def animate_menu_elements(panel):
    """Anima los elementos del menú de inicio"""
    try:
        # Encontrar elementos principales con un pequeño delay
        children = panel.winfo_children()
        for i, child in enumerate(children):
            if isinstance(child, tk.Frame):
                # Agregar un pequeño delay para cada frame
                child.after(i * 50, lambda c=child: c.configure(relief="sunken"))
                child.after(i * 50 + 100, lambda c=child: c.configure(relief="raised"))
    except:
        pass  # Si hay error, continuar sin animaciones

def animate_view_transition(panel, view_func):
    """Transición simple entre vistas con un pequeño delay"""
    def load_new_view():
        view_func(panel)
    
    # Pequeño delay antes de cargar la nueva vista
    panel.after(50, load_new_view)

# ====== MODOS ======
modo_oscuro = False
boton_activo = None

# ====== ESTILOS ======
def obtener_colores():
    if modo_oscuro:
        return {
            "bg": "#2c3e50",
            "panel": "#34495e",
            "sidebar": "#1a252f",
            "btn": "#34495e",
            "btn_hover": "#2c3e50",
            "btn_active": "#e74c3c",
            "text": "#ecf0f1",
            "btn_footer": "#95a5a6"
        }
    else:
        return {
            "bg": "#f5f7fa",
            "panel": "#ffffff",
            "sidebar": "#0a7f5a",
            "btn": "#0a7f5a",
            "btn_hover": "#086a4a",
            "btn_active": "#e67e22",
            "text": "#2c3e50",
            "btn_footer": "#95a5a6"
        }

COLORS = obtener_colores()



FONT_TITULO = ("Segoe UI", 20, "bold")
FONT_SUBTITULO = ("Segoe UI", 16, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_BTN = ("Segoe UI", 10, "bold")

# ====== CONFIGURACIÓN ======
config = {
    "matutino": {
        "entrada_inicio": "07:00",
        "entrada_puntual": "08:05",
        "entrada_retardo": "08:20",
        "salida_inicio": "13:50",
        "salida_fin": "14:30"
    },
    "vespertino": {
        "entrada_inicio": "13:00",
        "entrada_puntual": "14:05",
        "entrada_retardo": "14:20",
        "salida_inicio": "19:50",
        "salida_fin": "20:30"
    },
    "taller": {
        "entrada_inicio": "09:00",
        "entrada_puntual": "10:00",
        "entrada_retardo": "10:15",
        "salida_inicio": "15:00",
        "salida_fin": "16:00"
    }
}

# Cargar config desde archivo
def cargar_config():
    global config
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)

# Guardar config
def guardar_config():
    with open("config.json", "w") as f:
        json.dump(config, f)

cargar_config()

# ====== DETECTAR TURNO ======
def obtener_turno_actual():
    hora = datetime.now().strftime("%H:%M")
    return "matutino" if hora < "12:00" else "vespertino"

# ====== BASE DE DATOS ======
def crear_bd():
    conn = sqlite3.connect("sistema.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            password TEXT
        )
    """)

    # usuario por defecto
    cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario,password) VALUES ('admin','1234')")

    # usuario personal
    cursor.execute("SELECT * FROM usuarios WHERE usuario='personal'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario,password) VALUES ('personal','personal123')")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suspendidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE,
            nombre TEXT,
            ap_paterno TEXT,
            ap_materno TEXT,
            fecha_inicio TEXT,
            duracion_dias INTEGER,
            fecha_fin TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incapacitados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE,
            nombre TEXT,
            ap_paterno TEXT,
            ap_materno TEXT,
            fecha_inicio TEXT,
            duracion_dias INTEGER,
            fecha_fin TEXT
        )
    """)

    # Verificar y agregar columna grupo si no existe
    cursor.execute("PRAGMA table_info(estudiantes)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'grupo' not in columns:
        cursor.execute("ALTER TABLE estudiantes ADD COLUMN grupo TEXT")

    # Verificar y agregar columna telefono si no existe
    if 'telefono' not in columns:
        cursor.execute("ALTER TABLE estudiantes ADD COLUMN telefono TEXT")

    # Insertar estudiantes de ejemplo si no existen
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    if cursor.fetchone()[0] == 0:
        estudiantes_ejemplo = [
            ("Juan", "Pérez", "García", "2024001", "A1", "", "5512345678"),
            ("María", "López", "Hernández", "2024002", "A1", "", "5523456789"),
            ("Carlos", "Ramírez", "Torres", "2024003", "A2", "", "5534567890"),
            ("Ana", "Gómez", "Sánchez", "2024004", "A2", "", "5545678901"),
            ("Luis", "Martínez", "Rodríguez", "2024005", "B1", "", "5556789012"),
        ]
        cursor.executemany("INSERT INTO estudiantes (nombre, ap_paterno, ap_materno, matricula, grupo, estado, telefono) VALUES (?, ?, ?, ?, ?, ?, ?)", estudiantes_ejemplo)

    conn.commit()
    conn.close()

# ====== BD POR DÍA ======
def obtener_bd_dia():
    hoy = datetime.now()
    carpeta = f"asistencias/{hoy.strftime('%Y-%m')}"
    archivo = f"{hoy.strftime('%Y-%m-%d')}.db"
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, archivo)
    conn = sqlite3.connect(ruta)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS control_dia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            ap_paterno TEXT,
            ap_materno TEXT,
            matricula TEXT,
            hora_entrada TEXT,
            estado TEXT,
            hora_salida TEXT
        )
    """)
    conn.commit()
    return conn

# ====== LIMPIAR ROOT ======
def limpiar(root):
    for w in root.winfo_children():
        w.destroy()

# ====== LIMPIAR PANEL ======
def limpiar_panel(panel):
    for widget in panel.winfo_children():
        widget.destroy()

# ====== ESTUDIANTES ======
# ====== ESTUDIANTES ======
def mostrar_estudiantes(panel):
    limpiar_panel(panel)
    
    # Título
    frame_header = tk.Frame(panel, bg=COLORS["bg"])
    frame_header.pack(fill="x", pady=20, padx=20)
    
    tk.Label(frame_header, text="📚 GESTIÓN DE ESTUDIANTES", 
             font=("Segoe UI", 18, "bold"), bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=10)
    tk.Label(frame_header, text="Selecciona el apartado que deseas gestionar", 
             font=("Segoe UI", 11), bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=5)
    
    # Opciones con colores
    frame_opciones = tk.Frame(panel, bg=COLORS["bg"])
    frame_opciones.pack(fill="both", expand=True, pady=30, padx=30)
    
    opciones = [
        {
            "text": "👨‍🎓\nEstudiantes\nActivos",
            "bg": "#0a7f5a",
            "cmd": lambda: vista_estudiantes(panel)
        },
        {
            "text": "🚫\nEstudiantes\nSuspendidos",
            "bg": "#d97706",
            "cmd": lambda: vista_suspendidos(panel)
        },
        {
            "text": "🏥\nEstudiantes\nIncapacitados",
            "bg": "#dc2626",
            "cmd": lambda: vista_incapacitados(panel)
        }
    ]
    
    for i, opcion in enumerate(opciones):
        btn = tk.Button(frame_opciones, text=opcion["text"], font=("Segoe UI", 13, "bold"),
                        bg=opcion["bg"], fg="white", 
                        relief="raised", bd=3, 
                        activebackground=opcion["bg"], activeforeground="white",
                        command=opcion["cmd"], wraplength=120)
        btn.grid(row=i//2, column=i%2, padx=20, pady=25, sticky="nsew", ipady=25)
    
    for i in range(2):
        frame_opciones.grid_columnconfigure(i, weight=1)
    frame_opciones.grid_rowconfigure(0, weight=1)
    frame_opciones.grid_rowconfigure(1, weight=1)

def vista_estudiantes(panel):
    limpiar_panel(panel)
    
    # Frame superior con título decorativo y botón de regresar
    frame_top = tk.Frame(panel, bg=COLORS["panel"], relief="raised", bd=2)
    frame_top.pack(fill="x", padx=20, pady=15)
    
    frame_title = tk.Frame(frame_top, bg=COLORS["panel"])
    frame_title.pack(side="left", expand=True, padx=15, pady=15)
    
    tk.Label(frame_title, text="👨‍🎓 ESTUDIANTES ACTIVOS", bg=COLORS["panel"], fg=COLORS["text"], 
             font=("Segoe UI", 16, "bold")).pack()
    tk.Label(frame_title, text="Gestiona estudiantes registrados", bg=COLORS["panel"], 
             fg=COLORS["text"], font=("Segoe UI", 9)).pack()
    
    btn_regresar = tk.Button(frame_top, text="🔙 Atrás", font=FONT_BTN,
                             bg=COLORS["btn_footer"], fg="white", relief="raised", bd=2,
                             activebackground=COLORS["btn_hover"], activeforeground="white",
                             command=lambda: mostrar_estudiantes(panel), padx=15, pady=8)
    btn_regresar.pack(side="right", padx=15, pady=15)
    
    frame_busqueda = tk.Frame(panel, bg=COLORS["bg"])
    frame_busqueda.pack(pady=10)
    tk.Label(frame_busqueda, text="🔍 Buscar:", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5)
    entrada_busqueda = tk.Entry(frame_busqueda, width=30, font=("Segoe UI", 10), relief="solid", bd=1)
    entrada_busqueda.grid(row=0, column=1, padx=10)
    columnas = ("Nombre", "Ap Paterno", "Ap Materno", "Matrícula", "Grupo", "Estado")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings", selectmode="extended", height=12)
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=120, anchor="center")
    tabla.pack(pady=10)
    
    def cargar_datos(filtro=""):
        for item in tabla.get_children():
            tabla.delete(item)
        try:
            conn = sqlite3.connect("sistema.db")
            cursor = conn.cursor()
            query = """
                SELECT nombre, ap_paterno, ap_materno, matricula, COALESCE(grupo, ''), COALESCE(estado, '')
                FROM estudiantes
                WHERE nombre LIKE ? OR ap_paterno LIKE ? OR ap_materno LIKE ? OR matricula LIKE ? OR grupo LIKE ?
            """
            valores = (f"%{filtro}%", f"%{filtro}%", f"%{filtro}%", f"%{filtro}%", f"%{filtro}%")
            cursor.execute(query, valores)
            for fila in cursor.fetchall():
                tabla.insert("", "end", values=fila)
            conn.close()
        except Exception as e:
            print(f"Error cargando datos: {e}")
    
    def buscar():
        texto = entrada_busqueda.get().strip()
        cargar_datos(texto)
    
    def limpiar_busqueda():
        entrada_busqueda.delete(0, tk.END)
        cargar_datos()
    
    tk.Button(frame_busqueda, text="🔎 Buscar", command=buscar, bg=COLORS["btn"], fg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=5)
    tk.Button(frame_busqueda, text="🗑️ Limpiar", command=limpiar_busqueda, bg="#b91c1c", fg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=3, padx=5)
    
    cargar_datos()

def vista_suspendidos(panel):
    limpiar_panel(panel)
    
    # Frame superior con título y botón de regresar
    frame_header = tk.Frame(panel, bg=COLORS["bg"])
    frame_header.pack(fill="x", padx=20, pady=15)
    
    tk.Label(frame_header, text="🚫 SUSPENDIDOS", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(side="left", expand=True)
    
    btn_regresar = tk.Button(frame_header, text="🔙 Atrás", font=FONT_BTN,
                             bg=COLORS["btn_footer"], fg="white", relief="raised", bd=2,
                             activebackground=COLORS["btn_hover"], activeforeground="white",
                             command=lambda: mostrar_estudiantes(panel), padx=15, pady=5)
    btn_regresar.pack(side="right")
    
    # Frame para búsqueda y agregar
    frame_top = tk.Frame(panel, bg=COLORS["bg"])
    frame_top.pack(pady=10)
    
    tk.Label(frame_top, text="Buscar por matrícula:", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=0, padx=5)
    entrada_matricula = tk.Entry(frame_top, width=20)
    entrada_matricula.grid(row=0, column=1, padx=10)
    
    tk.Label(frame_top, text="Duración (días):", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=2, padx=5)
    entrada_duracion = tk.Entry(frame_top, width=10)
    entrada_duracion.grid(row=0, column=3, padx=10)
    
    label_mensaje = tk.Label(frame_top, text="", bg=COLORS["bg"], fg="green", font=FONT_NORMAL)
    label_mensaje.grid(row=0, column=4, padx=20)
    
    def agregar_suspendido():
        matricula = entrada_matricula.get().strip()
        try:
            duracion = int(entrada_duracion.get().strip())
        except ValueError:
            label_mensaje.config(text="Duración inválida", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            return
        
        if not matricula:
            label_mensaje.config(text="Ingresa matrícula", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            return
        
        # Verificar si existe el estudiante
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, ap_paterno, ap_materno FROM estudiantes WHERE matricula = ?", (matricula,))
        estudiante = cursor.fetchone()
        if not estudiante:
            conn.close()
            label_mensaje.config(text="Estudiante no encontrado", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            return
        
        nombre, ap, am = estudiante
        fecha_inicio = datetime.now().strftime("%Y-%m-%d")
        fecha_fin = (datetime.now() + timedelta(days=duracion)).strftime("%Y-%m-%d")
        
        try:
            cursor.execute("""
                INSERT INTO suspendidos (matricula, nombre, ap_paterno, ap_materno, fecha_inicio, duracion_dias, fecha_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (matricula, nombre, ap, am, fecha_inicio, duracion, fecha_fin))
            conn.commit()
            label_mensaje.config(text=f"✔ Agregado: {nombre}", fg="green")
            entrada_matricula.delete(0, tk.END)
            entrada_duracion.delete(0, tk.END)
            cargar_suspendidos()
            panel.after(3000, lambda: label_mensaje.config(text=""))
        except sqlite3.IntegrityError:
            label_mensaje.config(text="Ya está suspendido", fg="orange")
            panel.after(3000, lambda: label_mensaje.config(text=""))
        conn.close()
    
    tk.Button(frame_top, text="➕ Agregar", command=agregar_suspendido, bg=COLORS["btn"], fg="white").grid(row=0, column=5, padx=10)
    
    # Tabla de suspendidos
    columnas = ("Nombre", "Matrícula", "Fecha Inicio", "Duración", "Fecha Fin")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings", height=12)
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=120, anchor="center")
    tabla.pack(pady=20)
    
    def cargar_suspendidos():
        for item in tabla.get_children():
            tabla.delete(item)
        try:
            conn = sqlite3.connect("sistema.db")
            cursor = conn.cursor()
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT nombre, matricula, fecha_inicio, duracion_dias, fecha_fin
                FROM suspendidos
                WHERE fecha_fin >= ?
                ORDER BY fecha_fin ASC
            """, (hoy,))
            for fila in cursor.fetchall():
                tabla.insert("", "end", values=fila)
            conn.close()
        except Exception as e:
            print(f"Error cargando suspendidos: {e}")
    
    cargar_suspendidos()

def vista_incapacitados(panel):
    limpiar_panel(panel)
    
    # Frame superior con título y botón de regresar
    frame_header = tk.Frame(panel, bg=COLORS["bg"])
    frame_header.pack(fill="x", padx=20, pady=15)
    
    tk.Label(frame_header, text="🏥 INCAPACITADOS", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(side="left", expand=True)
    
    btn_regresar = tk.Button(frame_header, text="🔙 Atrás", font=FONT_BTN,
                             bg=COLORS["btn_footer"], fg="white", relief="raised", bd=2,
                             activebackground=COLORS["btn_hover"], activeforeground="white",
                             command=lambda: mostrar_estudiantes(panel), padx=15, pady=5)
    btn_regresar.pack(side="right")
    
    # Frame para búsqueda y agregar
    frame_top = tk.Frame(panel, bg=COLORS["bg"])
    frame_top.pack(pady=10)
    
    tk.Label(frame_top, text="Buscar por matrícula:", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=0, padx=5)
    entrada_matricula = tk.Entry(frame_top, width=20)
    entrada_matricula.grid(row=0, column=1, padx=10)
    
    tk.Label(frame_top, text="Duración (días):", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=2, padx=5)
    entrada_duracion = tk.Entry(frame_top, width=10)
    entrada_duracion.grid(row=0, column=3, padx=10)
    
    label_mensaje = tk.Label(frame_top, text="", bg=COLORS["bg"], fg="green", font=FONT_NORMAL)
    label_mensaje.grid(row=0, column=4, padx=20)
    
    def agregar_incapacitado():
        matricula = entrada_matricula.get().strip()
        try:
            duracion = int(entrada_duracion.get().strip())
        except ValueError:
            label_mensaje.config(text="Duración inválida", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            return
        
        if not matricula:
            label_mensaje.config(text="Ingresa matrícula", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            return
        
        # Verificar si existe el estudiante
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, ap_paterno, ap_materno FROM estudiantes WHERE matricula = ?", (matricula,))
        estudiante = cursor.fetchone()
        if not estudiante:
            conn.close()
            label_mensaje.config(text="Estudiante no encontrado", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            return
        
        nombre, ap, am = estudiante
        fecha_inicio = datetime.now().strftime("%Y-%m-%d")
        fecha_fin = (datetime.now() + timedelta(days=duracion)).strftime("%Y-%m-%d")
        
        try:
            cursor.execute("""
                INSERT INTO incapacitados (matricula, nombre, ap_paterno, ap_materno, fecha_inicio, duracion_dias, fecha_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (matricula, nombre, ap, am, fecha_inicio, duracion, fecha_fin))
            conn.commit()
            label_mensaje.config(text=f"✔ Agregado: {nombre}", fg="green")
            entrada_matricula.delete(0, tk.END)
            entrada_duracion.delete(0, tk.END)
            cargar_incapacitados()
            panel.after(3000, lambda: label_mensaje.config(text=""))
        except sqlite3.IntegrityError:
            label_mensaje.config(text="Ya está incapacitado", fg="orange")
            panel.after(3000, lambda: label_mensaje.config(text=""))
        conn.close()
    
    tk.Button(frame_top, text="➕ Agregar", command=agregar_incapacitado, bg=COLORS["btn"], fg="white").grid(row=0, column=5, padx=10)
    
    # Tabla de incapacitados
    columnas = ("Nombre", "Matrícula", "Fecha Inicio", "Duración", "Fecha Fin")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings", height=12)
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=120, anchor="center")
    tabla.pack(pady=20)
    
    def cargar_incapacitados():
        for item in tabla.get_children():
            tabla.delete(item)
        try:
            conn = sqlite3.connect("sistema.db")
            cursor = conn.cursor()
            hoy = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT nombre, matricula, fecha_inicio, duracion_dias, fecha_fin
                FROM incapacitados
                WHERE fecha_fin >= ?
                ORDER BY fecha_fin ASC
            """, (hoy,))
            for fila in cursor.fetchall():
                tabla.insert("", "end", values=fila)
            conn.close()
        except Exception as e:
            print(f"Error cargando incapacitados: {e}")
    
    cargar_incapacitados()


# ====== CONTROL DÍA ======
def vista_control_dia(panel):
    limpiar_panel(panel)
    tk.Label(panel, text="📅 CONTROL POR DÍA", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    
    # Función para cargar fecha guardada
    def cargar_fecha_guardada():
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if "ultima_fecha_control" in config:
                    return config["ultima_fecha_control"]
        except:
            pass
        # Si no hay fecha guardada, usar fecha actual
        return datetime.now().strftime("%Y-%m-%d")
    
    # Función para guardar fecha seleccionada
    def guardar_fecha_seleccionada(fecha):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except:
            config = {}
        
        config["ultima_fecha_control"] = fecha
        
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
    
    # Cargar fecha guardada
    fecha_guardada = cargar_fecha_guardada()
    year_default, mes_default, dia_default = fecha_guardada.split("-")
    
    # Frame para selección de fecha
    frame_fecha = tk.Frame(panel, bg=COLORS["bg"])
    frame_fecha.pack(pady=10)
    
    tk.Label(frame_fecha, text="Seleccionar Fecha:", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SUBTITULO).grid(row=0, column=0, padx=10)
    
    # Calendario simple con comboboxes
    frame_cal = tk.Frame(frame_fecha, bg=COLORS["bg"])
    frame_cal.grid(row=0, column=1, padx=10)
    
    tk.Label(frame_cal, text="Año:", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=0)
    year_var = tk.StringVar(value=year_default)
    year_combo = ttk.Combobox(frame_cal, textvariable=year_var, values=[str(y) for y in range(2020, 2031)], width=6, state="readonly")
    year_combo.grid(row=0, column=1, padx=5)
    
    tk.Label(frame_cal, text="Mes:", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=2)
    meses = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    mes_var = tk.StringVar(value=mes_default)
    mes_combo = ttk.Combobox(frame_cal, textvariable=mes_var, values=meses, width=4, state="readonly")
    mes_combo.grid(row=0, column=3, padx=5)
    
    tk.Label(frame_cal, text="Día:", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=4)
    dia_var = tk.StringVar(value=dia_default)
    dia_combo = ttk.Combobox(frame_cal, textvariable=dia_var, values=[str(d).zfill(2) for d in range(1, 32)], width=4, state="readonly")
    dia_combo.grid(row=0, column=5, padx=5)
    
    label_mensaje = tk.Label(frame_fecha, text="", bg=COLORS["bg"], fg="green", font=FONT_NORMAL)
    label_mensaje.grid(row=0, column=2, padx=20)
    
    # Tabla para mostrar datos
    columnas = ("Nombre", "Matrícula", "Entrada", "Estado", "Salida")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings", height=15)
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=130, anchor="center")
    tabla.pack(pady=20, fill="both", expand=True)
    
    def cargar_datos(fecha_str=None):
        for item in tabla.get_children():
            tabla.delete(item)
        if not fecha_str:
            fecha_str = f"{year_var.get()}-{mes_var.get()}-{dia_var.get()}"
        
        try:
            # Construir ruta de la base de datos para esa fecha
            carpeta = f"asistencias/{year_var.get()}-{mes_var.get()}"
            archivo = f"{fecha_str}.db"
            ruta = os.path.join(carpeta, archivo)
            
            if not os.path.exists(ruta):
                label_mensaje.config(text="No hay datos para esta fecha", fg="orange")
                panel.after(3000, lambda: label_mensaje.config(text=""))
                return
            
            conn = sqlite3.connect(ruta)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nombre, matricula, hora_entrada, estado, hora_salida FROM control_dia
                ORDER BY hora_entrada ASC
            """)
            datos = cursor.fetchall()
            conn.close()
            
            for fila in datos:
                tabla.insert("", "end", values=fila)
            
            label_mensaje.config(text=f"✔ {len(datos)} registros cargados", fg="green")
            panel.after(3000, lambda: label_mensaje.config(text=""))
            
        except Exception as e:
            print(f"Error cargando datos: {e}")
            label_mensaje.config(text="Error al cargar datos", fg="red")
            panel.after(3000, lambda: label_mensaje.config(text=""))
    
    def seleccionar_fecha():
        fecha_actual = f"{year_var.get()}-{mes_var.get()}-{dia_var.get()}"
        guardar_fecha_seleccionada(fecha_actual)
        cargar_datos()
    
    tk.Button(frame_fecha, text="📊 Cargar Datos", command=seleccionar_fecha, bg=COLORS["btn"], fg="white", font=FONT_BTN).grid(row=0, column=3, padx=10)
    
    # Cargar datos de la fecha guardada por defecto
    cargar_datos(fecha_guardada)

# ====== REGISTRO ======
def vista_registro(panel):
    limpiar_panel(panel)
    contenedor = tk.Frame(panel, bg=COLORS["bg"])
    contenedor.pack(expand=True)
    frame = tk.Frame(contenedor, bg=COLORS["panel"], padx=40, pady=40)
    frame.grid(row=0, column=0, padx=30)
    tk.Label(frame, text="ESCANEA MATRÍCULA", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    entrada = tk.Entry(frame, font=("Arial", 22), justify="center")
    entrada.pack(pady=20)
    entrada.focus()
    mensaje = tk.Label(frame, bg=COLORS["panel"], fg="green")
    mensaje.pack()
    frame_img = tk.Frame(contenedor, bg=COLORS["bg"])
    frame_img.grid(row=0, column=1, padx=30)
    tk.Label(frame_img, text="FOTO", bg=COLORS["bg"], fg=COLORS["text"], font=("Arial", 14, "bold")).pack(pady=10)
    canvas = tk.Canvas(frame_img, width=200, height=200, bg="white")
    canvas.pack()
    def registrar(event=None):
        mat = entrada.get().strip()
        if not mat:
            return
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, ap_paterno, ap_materno, estado FROM estudiantes WHERE matricula = ?
        """, (mat,))
        res = cursor.fetchone()
        conn.close()
        if not res:
            mensaje.config(text="No existe ❌", fg="red")
            entrada.delete(0, tk.END)
            return
        nombre, ap, am, estado_alumno = res
        if estado_alumno in ["Suspendido", "Incapacitado"]:
            mensaje.config(text=f"{estado_alumno} ❌", fg="red")
            entrada.delete(0, tk.END)
            return
        hora = datetime.now().strftime("%H:%M")
        conn_dia = obtener_bd_dia()
        cur = conn_dia.cursor()
        cur.execute("""
            SELECT id, hora_salida FROM control_dia WHERE matricula = ?
        """, (mat,))
        registro = cur.fetchone()
        if not registro:
            turno = obtener_turno_actual()
            conf = config[turno]
            hora_actual = datetime.now().strftime("%H:%M")
            if not (conf["entrada_inicio"] <= hora_actual <= conf["entrada_retardo"]):
                mensaje.config(text="Fuera de horario de entrada ❌", fg="red")
                entrada.delete(0, tk.END)
                return
            if hora <= conf["entrada_puntual"]:
                estado = "Puntual"
            elif hora <= conf["entrada_retardo"]:
                estado = "Retardo"
            else:
                estado = "Falta"
            cur.execute("""
                INSERT INTO control_dia VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre, ap, am, mat, hora, estado, ""))
            mensaje.config(text=f"ENTRADA ✔ {nombre}", fg="green")
        else:
            id_registro, salida = registro
            if salida:
                mensaje.config(text="YA REGISTRÓ SALIDA ⚠", fg="orange")
            else:
                turno = obtener_turno_actual()
                conf = config[turno]
                hora_actual = datetime.now().strftime("%H:%M")
                if hora_actual < conf["salida_inicio"]:
                    mensaje.config(text="Aún no es hora de salida ❌", fg="red")
                    entrada.delete(0, tk.END)
                    return
                cur.execute("""
                    UPDATE control_dia SET hora_salida = ? WHERE id = ?
                """, (hora, id_registro))
                mensaje.config(text=f"SALIDA ✔ {nombre}", fg="cyan")
        conn_dia.commit()
        conn_dia.close()
        entrada.delete(0, tk.END)
    entrada.bind("<Return>", registrar)

# ====== CONFIGURACIÓN ======
def vista_configuracion(panel):
    limpiar_panel(panel)
    tk.Label(panel, text="CONFIGURACIÓN DE TURNOS", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    contenedor = tk.Frame(panel, bg=COLORS["bg"])
    contenedor.pack()
    turnos = ["matutino", "vespertino"]
    entradas = {}
    for turno in turnos:
        frame = tk.Frame(contenedor, bg=COLORS["panel"], padx=30, pady=20)
        frame.pack(side="left", padx=20, pady=10)
        tk.Label(frame, text=turno.upper(), bg=COLORS["panel"], fg=COLORS["text"], font=("Arial", 14, "bold")).pack(pady=10)
        entradas[turno] = {}
        for clave in config[turno]:
            tk.Label(frame, text=clave, bg=COLORS["panel"], fg=COLORS["text"]).pack()
            e = tk.Entry(frame)
            e.insert(0, config[turno][clave])
            e.pack(pady=5)
            entradas[turno][clave] = e
    # Taller abajo
    frame_taller = tk.Frame(contenedor, bg=COLORS["panel"], padx=30, pady=20)
    frame_taller.pack(pady=20, fill="x")
    tk.Label(frame_taller, text="TALLER", bg=COLORS["panel"], fg=COLORS["text"], font=("Arial", 14, "bold")).pack(pady=10)
    entradas_taller = {}
    for clave in config["taller"]:
        tk.Label(frame_taller, text=clave, bg=COLORS["panel"], fg=COLORS["text"]).pack()
        e = tk.Entry(frame_taller)
        e.insert(0, config["taller"][clave])
        e.pack(pady=5)
        entradas_taller[clave] = e
    def guardar():
        for turno in turnos:
            for clave in entradas[turno]:
                config[turno][clave] = entradas[turno][clave].get()
        for clave in entradas_taller:
            config["taller"][clave] = entradas_taller[clave].get()
        guardar_config()
        tk.Label(panel, text="Guardado ✔", bg=COLORS["bg"], fg="green").pack()
    tk.Button(panel, text="Guardar", bg=COLORS["btn"], fg="white", command=guardar).pack(pady=20)

# ====== CONTROL ======
hora_barrido = "08:30"  # Hora por defecto para marcar faltas

# ====== CONTROL ======
hora_barrido = "08:30"  # Hora por defecto para marcar faltas

def vista_control(panel):
    limpiar_panel(panel)
    
    # Crear notebook para pestañas
    notebook = ttk.Notebook(panel)
    notebook.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Pestaña Control
    tab_control = tk.Frame(notebook, bg=COLORS["bg"])
    notebook.add(tab_control, text="Control Automático")
    
    tk.Label(tab_control, text="CONTROL AUTOMÁTICO", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    frame_hora = tk.Frame(tab_control, bg=COLORS["bg"])
    frame_hora.pack(pady=10)
    tk.Label(frame_hora, text="Hora de Barrido (HH:MM):", bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
    hora_entry = tk.Entry(frame_hora)
    hora_entry.insert(0, hora_barrido)
    hora_entry.pack(side="left", padx=10)
    label_estado = tk.Label(frame_hora, text="", bg=COLORS["bg"], fg="orange", font=("Arial", 10))
    label_estado.pack(side="left", padx=20)
    def actualizar_hora():
        global hora_barrido
        hora_barrido = hora_entry.get().strip()
    tk.Button(frame_hora, text="Actualizar Hora", command=actualizar_hora, bg=COLORS["btn"], fg="white").pack(side="left")
    columnas = ("Nombre", "Matrícula", "Estado")
    tabla = ttk.Treeview(tab_control, columns=columnas, show="headings")
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=150, anchor="center")
    tabla.pack(pady=20)
    
    def cargar_faltas():
        """Carga las faltas existentes en la tabla"""
        for item in tabla.get_children():
            tabla.delete(item)
        try:
            conn_dia = obtener_bd_dia()
            cur = conn_dia.cursor()
            cur.execute("SELECT nombre, matricula, estado FROM control_dia WHERE estado = 'Falta'")
            for fila in cur.fetchall():
                tabla.insert("", "end", values=fila)
            conn_dia.close()
        except:
            pass
    
    def marcar_faltas():
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, ap_paterno, ap_materno, matricula FROM estudiantes")
        estudiantes = cursor.fetchall()
        conn.close()
        conn_dia = obtener_bd_dia()
        cur = conn_dia.cursor()
        for nombre, ap, am, mat in estudiantes:
            cur.execute("SELECT id FROM control_dia WHERE matricula = ?", (mat,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO control_dia VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
                """, (nombre, ap, am, mat, "", "Falta", ""))
        conn_dia.commit()
        # Mostrar faltas
        cargar_faltas()
        conn_dia.close()
        label_estado.config(text="✔ Barrido ejecutado", fg="green")
    
    def verificar_barrido():
        try:
            hora_actual = datetime.now().strftime("%H:%M")
            if hora_actual >= hora_barrido:
                label_estado.config(text="Hora de barrido alcanzada", fg="orange")
            else:
                label_estado.config(text=f"Próximo barrido a {hora_barrido}", fg="gray")
            tab_control.after(60000, verificar_barrido)
        except:
            pass
    verificar_barrido()
    tk.Button(tab_control, text="Marcar Faltas Ahora", command=marcar_faltas, bg=COLORS["btn"], fg="white").pack(pady=10)
    
    # Cargar faltas existentes al inicializar
    cargar_faltas()
    
    # Pestaña Mensajes
    tab_mensajes = tk.Frame(notebook, bg=COLORS["bg"])
    notebook.add(tab_mensajes, text="Mensajes")
    
    tk.Label(tab_mensajes, text="ENVIAR MENSAJES WHATSAPP", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    
    # Frame para mensaje
    frame_mensaje = tk.Frame(tab_mensajes, bg=COLORS["panel"], padx=20, pady=20)
    frame_mensaje.pack(fill="x", padx=20, pady=10)
    tk.Label(frame_mensaje, text="Mensaje a enviar:", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_SUBTITULO).pack(anchor="w")
    text_mensaje = tk.Text(frame_mensaje, height=4, font=FONT_NORMAL, wrap="word")
    text_mensaje.pack(fill="x", pady=10)
    text_mensaje.insert("1.0", "Hola, este es un mensaje de prueba del sistema escolar.")
    
    # Tabla de estudiantes con teléfonos
    frame_tabla = tk.Frame(tab_mensajes, bg=COLORS["bg"])
    frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)
    
    columnas_est = ("Seleccionar", "Nombre", "Matrícula", "Teléfono")
    tabla_est = ttk.Treeview(frame_tabla, columns=columnas_est, show="headings", height=10)
    for col in columnas_est:
        tabla_est.heading(col, text=col)
        if col == "Seleccionar":
            tabla_est.column(col, width=80, anchor="center")
        elif col == "Teléfono":
            tabla_est.column(col, width=120, anchor="center")
        else:
            tabla_est.column(col, width=150, anchor="center")
    tabla_est.pack(fill="both", expand=True)
    
    # Checkboxes para selección
    checks = {}
    
    def cargar_estudiantes():
        for item in tabla_est.get_children():
            tabla_est.delete(item)
        checks.clear()
        try:
            conn = sqlite3.connect("sistema.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nombre || ' ' || ap_paterno || ' ' || ap_materno, matricula, telefono FROM estudiantes WHERE telefono IS NOT NULL AND telefono != ''")
            estudiantes = cursor.fetchall()
            conn.close()
            for est in estudiantes:
                nombre_completo, matricula, telefono = est
                item_id = tabla_est.insert("", "end", values=("", nombre_completo, matricula, telefono))
                checks[item_id] = tk.BooleanVar()
                tabla_est.set(item_id, "Seleccionar", "☐")
        except Exception as e:
            print(f"Error cargando estudiantes: {e}")
    
    def toggle_seleccion(event):
        item = tabla_est.identify_row(event.y)
        if item:
            if checks[item].get():
                checks[item].set(False)
                tabla_est.set(item, "Seleccionar", "☐")
            else:
                checks[item].set(True)
                tabla_est.set(item, "Seleccionar", "☑")
    
    tabla_est.bind("<Button-1>", toggle_seleccion)
    
    # Botón enviar
    def enviar_mensajes():
        mensaje = text_mensaje.get("1.0", "end-1c").strip()
        if not mensaje:
            tk.messagebox.showwarning("Advertencia", "Por favor ingrese un mensaje.")
            return
        seleccionados = [item for item, var in checks.items() if var.get()]
        if not seleccionados:
            tk.messagebox.showwarning("Advertencia", "Por favor seleccione al menos un estudiante.")
            return
        
        import webbrowser
        enviados = 0
        for item in seleccionados:
            telefono = tabla_est.set(item, "Teléfono")
            if telefono:
                url = f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}"
                webbrowser.open(url)
                enviados += 1
        tk.messagebox.showinfo("Éxito", f"Mensajes enviados a {enviados} estudiantes.")
    
    tk.Button(tab_mensajes, text="📱 Enviar Mensajes WhatsApp", command=enviar_mensajes, bg="#25D366", fg="white", font=FONT_BTN, padx=20, pady=10).pack(pady=20)
    
    cargar_estudiantes()

# ====== INICIO ======
def vista_inicio(panel):
    limpiar_panel(panel)
    
    # Header
    frame_header = tk.Frame(panel, bg=COLORS["bg"])
    frame_header.pack(fill="x", pady=(25, 15), padx=20)
    
    tk.Label(frame_header, text="🏫 SIMEC -  Sistema Inteligente de Monitoreo Escolar CONALEP", 
             font=("Segoe UI", 20, "bold"), bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=10)
    tk.Label(frame_header, text="CONALEP - Control de Asistencias y Estudiantes", 
             font=("Segoe UI", 12), bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=5)
    
    # Información del día
    frame_info = tk.Frame(panel, bg=COLORS["bg"])
    frame_info.pack(fill="x", padx=30, pady=15)
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    turno_actual = obtener_turno_actual().capitalize()
    
    # Cards de fecha y turno
    frame_date_turn = tk.Frame(frame_info, bg=COLORS["bg"])
    frame_date_turn.pack(side="left", fill="x", expand=True, padx=10)
    
    card_fecha = tk.Frame(frame_date_turn, bg=COLORS["panel"], relief="raised", bd=2)
    card_fecha.pack(side="left", padx=5, pady=8, fill="both", expand=True)
    tk.Label(card_fecha, text="📅 Fecha", font=("Segoe UI", 11, "bold"), bg=COLORS["panel"], fg=COLORS["text"]).pack(pady=8)
    tk.Label(card_fecha, text=fecha_actual, font=("Segoe UI", 14, "bold"), bg=COLORS["panel"], fg=COLORS["btn"]).pack(pady=8)
    
    card_turno = tk.Frame(frame_date_turn, bg=COLORS["panel"], relief="raised", bd=2)
    card_turno.pack(side="left", padx=5, pady=8, fill="both", expand=True)
    tk.Label(card_turno, text="🕐 Turno", font=("Segoe UI", 11, "bold"), bg=COLORS["panel"], fg=COLORS["text"]).pack(pady=8)
    tk.Label(card_turno, text=turno_actual, font=("Segoe UI", 14, "bold"), bg=COLORS["panel"], fg=COLORS["btn"]).pack(pady=8)
    
    # Estadísticas
    try:
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM estudiantes")
        total_estudiantes = cursor.fetchone()[0]
        
        conn_dia = obtener_bd_dia()
        cur = conn_dia.cursor()
        cur.execute("SELECT COUNT(*) FROM control_dia WHERE estado = 'Puntual'")
        puntuales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM control_dia WHERE estado = 'Retardo'")
        retardos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM control_dia WHERE estado = 'Falta'")
        faltas = cur.fetchone()[0]
        conn.close()
        conn_dia.close()
        
        frame_stats = tk.Frame(frame_info, bg=COLORS["bg"])
        frame_stats.pack(side="left", fill="x", expand=True, padx=10)
        
        # Frame para Total
        card_total = tk.Frame(frame_stats, bg=COLORS["panel"], relief="raised", bd=2)
        card_total.pack(padx=5, pady=8, fill="both", expand=True)
        tk.Label(card_total, text="👥 Total Estudiantes", font=("Segoe UI", 11, "bold"), bg=COLORS["panel"], fg=COLORS["text"]).pack(pady=8)
        tk.Label(card_total, text=str(total_estudiantes), font=("Segoe UI", 18, "bold"), bg=COLORS["panel"], fg=COLORS["btn"]).pack(pady=8)
        
        # Cards de asistencia en fila
        frame_asist = tk.Frame(frame_stats, bg=COLORS["bg"])
        frame_asist.pack(fill="both", expand=True, pady=5)
        
        card_puntual = tk.Frame(frame_asist, bg="#d4edda", relief="raised", bd=2)
        card_puntual.pack(side="left", fill="both", expand=True, padx=3, pady=5)
        tk.Label(card_puntual, text="✅ Puntual", font=("Segoe UI", 10, "bold"), bg="#d4edda", fg="#155724").pack(pady=6)
        tk.Label(card_puntual, text=str(puntuales), font=("Segoe UI", 16, "bold"), bg="#d4edda", fg="#155724").pack(pady=6)
        
        card_retardo = tk.Frame(frame_asist, bg="#fff3cd", relief="raised", bd=2)
        card_retardo.pack(side="left", fill="both", expand=True, padx=3, pady=5)
        tk.Label(card_retardo, text="⏰ Retardo", font=("Segoe UI", 10, "bold"), bg="#fff3cd", fg="#856404").pack(pady=6)
        tk.Label(card_retardo, text=str(retardos), font=("Segoe UI", 16, "bold"), bg="#fff3cd", fg="#856404").pack(pady=6)
        
        card_falta = tk.Frame(frame_asist, bg="#f8d7da", relief="raised", bd=2)
        card_falta.pack(side="left", fill="both", expand=True, padx=3, pady=5)
        tk.Label(card_falta, text="❌ Falta", font=("Segoe UI", 10, "bold"), bg="#f8d7da", fg="#721c24").pack(pady=6)
        tk.Label(card_falta, text=str(faltas), font=("Segoe UI", 16, "bold"), bg="#f8d7da", fg="#721c24").pack(pady=6)
    except:
        pass
    
    # Menú de opciones
    frame_opciones = tk.Frame(panel, bg=COLORS["bg"])
    frame_opciones.pack(fill="both", expand=True, pady=20, padx=30)
    
    opciones = [
        ("👥\nGestión", mostrar_estudiantes),
        ("📝\nRegistro", vista_registro),
        ("📅\nControl Día", vista_control_dia),
        ("🔍\nControl", vista_control),
        ("⚙️\nConfig", vista_configuracion)
    ]
    
    for i, (txt, cmd) in enumerate(opciones):
        btn = tk.Button(frame_opciones, text=txt, font=("Segoe UI", 12, "bold"),
                        bg=COLORS["btn"], fg="white", 
                        relief="raised", bd=3, 
                        activebackground=COLORS["btn_hover"], activeforeground="white",
                        command=lambda c=cmd: c(panel))
        btn.grid(row=i//3, column=i%3, padx=12, pady=12, sticky="nsew", ipady=20)
    
    for i in range(3):
        frame_opciones.grid_columnconfigure(i, weight=1)
    for i in range(2):
        frame_opciones.grid_rowconfigure(i, weight=1)
    
    # Agregar animaciones después de que los widgets estén creados
    panel.after(100, lambda: animate_menu_elements(panel))

# ====== MENÚ ======
def construir_menu(root):
    global boton_activo
    limpiar(root)

    root.title("SIMEC - CONALEP")
    root.geometry("1100x650")
    root.configure(bg=COLORS["bg"])

    # Configurar grid
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    panel_izq = tk.Frame(root, bg=COLORS["sidebar"], width=220)
    panel_izq.grid(row=0, column=0, sticky="ns")

    tk.Label(panel_izq, text="SIMEC",
             bg=COLORS["sidebar"], fg="white",
             font=("Segoe UI", 18, "bold")).pack(pady=25)

    panel = tk.Frame(root, bg=COLORS["bg"])
    panel.grid(row=0, column=1, sticky="nsew")
# --- AQUÍ CONFIGURAMOS EL ESTILO ---
    style = ttk.Style()
    style.theme_use('clam') # 'clam' permite que los colores se apliquen mejor en Treeview
    style.configure("Treeview", 
                    background=COLORS["panel"], 
                    foreground=COLORS["text"], 
                    fieldbackground=COLORS["panel"])
    style.map('Treeview', background=[('selected', COLORS["btn_active"])])
    
    def cambiar_modo():
        global modo_oscuro, COLORS
        modo_oscuro = not modo_oscuro
        COLORS = obtener_colores()
        style.configure("Treeview", background=COLORS["panel"], foreground=COLORS["text"], fieldbackground=COLORS["panel"])
        style.map('Treeview', background=[('selected', COLORS["btn_active"])])
        construir_menu(root)

    def regresar_inicio():
        vista_inicio(panel)

    def terminar_sesion():
        root.destroy()
        subprocess.Popen(["python", "Login.py"])

    # Menú desplegable en el sidebar
    menu_config = tk.Menu(panel_izq, tearoff=0)
    menu_config.add_command(label="🌙 Modo Oscuro", command=cambiar_modo)
    menu_config.add_command(label="🏠 Regresar a Inicio", command=regresar_inicio)
    menu_config.add_command(label="🚪 Terminar Sesión", command=terminar_sesion)

    def mostrar_menu():
        menu_config.post(menubutton.winfo_rootx(), menubutton.winfo_rooty() + menubutton.winfo_height())

    menubutton = tk.Button(panel_izq, text="⚙️ Configuración", bg=COLORS["sidebar"], fg="white", font=FONT_BTN, relief="ridge", bd=3, command=mostrar_menu, width=18, height=2)
    menubutton.pack(side="bottom", fill="x", padx=15, pady=10)

    def btn(txt, cmd):
        b = tk.Button(panel_izq, text=txt,
                      bg=COLORS["sidebar"], fg="white",
                      font=FONT_BTN, bd=3, relief="flat",
                      height=2, width=18,
                      activebackground=COLORS["btn_hover"], activeforeground="white",
                      command=lambda: [cmd(panel), resaltar_boton(b)])
        b.pack(fill="x", padx=15, pady=10)
        return b

    def resaltar_boton(b):
        global boton_activo
        if boton_activo:
            boton_activo.config(bg=COLORS["sidebar"])
        b.config(bg=COLORS["btn_active"])
        boton_activo = b

    btn("👥 Gestión Estudiantes", mostrar_estudiantes)
    btn("📝 Registro Asistencia", vista_registro)
    btn("📅 Control por Día", vista_control_dia)
    btn("⚙️ Configuración", vista_configuracion)
    btn("🔍 Control Automático", vista_control)

    vista_inicio(panel)

def pantalla_inicio(root):
    crear_bd()
    construir_menu(root)
