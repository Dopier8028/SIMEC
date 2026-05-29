import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import csv
import shutil
from datetime import datetime, timedelta
import json
import subprocess

CARPETA_ALUMNOS = "alumnos"
ARCHIVO_ALUMNOS = os.path.join(CARPETA_ALUMNOS, "alumnos.xlsx")

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

# ====== ALUMNOS DESDE EXCEL (fuente principal) ======
def _mapear_columnas_excel(columnas):
    col_map = {}
    for c in columnas:
        cl = str(c).strip().lower()
        if "matr" in cl:
            col_map["matricula"] = c
        elif "tel" in cl or "cel" in cl or "móvil" in cl or "movil" in cl:
            col_map["telefono"] = c
        elif "grupo" in cl:
            col_map["grupo"] = c
        elif "segundo" in cl and "apell" in cl:
            col_map["ap_materno"] = c
        elif "primer" in cl and "apell" in cl:
            col_map["ap_paterno"] = c
        elif cl == "nombre" or (cl.startswith("nombre") and "apell" not in cl):
            col_map["nombre"] = c
    return col_map


def _valor_celda(val):
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _registro_desde_dict(fila, col_map):
    mat = _valor_celda(fila.get(col_map.get("matricula", ""), ""))
    if not mat:
        return None
    nombre = _valor_celda(fila.get(col_map.get("nombre", ""), "")).title()
    ap_p = _valor_celda(fila.get(col_map.get("ap_paterno", ""), "")).title()
    ap_m = _valor_celda(fila.get(col_map.get("ap_materno", ""), "")).title()
    grupo = _valor_celda(fila.get(col_map.get("grupo", ""), ""))
    telefono = _valor_celda(fila.get(col_map.get("telefono", ""), ""))
    return (nombre, ap_p, ap_m, mat, grupo, "Activo", telefono)


def leer_registros_excel(ruta):
    registros = []
    if ruta.lower().endswith(".csv"):
        with open(ruta, newline="", encoding="utf-8-sig") as f:
            lector = csv.DictReader(f)
            col_map = _mapear_columnas_excel(lector.fieldnames or [])
            for fila in lector:
                reg = _registro_desde_dict(fila, col_map)
                if reg:
                    registros.append(reg)
        return registros

    try:
        import pandas as pd
        df = pd.read_excel(ruta)
        df.columns = [str(c).strip() for c in df.columns]
        col_map = _mapear_columnas_excel(df.columns)
        if "matricula" not in col_map:
            raise ValueError("No se encontró columna de matrícula en el Excel")
        for _, row in df.iterrows():
            fila = {c: row[c] for c in df.columns}
            reg = _registro_desde_dict(fila, col_map)
            if reg:
                registros.append(reg)
        return registros
    except ImportError:
        pass

    import openpyxl
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    hoja = wb.active
    filas = list(hoja.iter_rows(values_only=True))
    wb.close()
    if not filas:
        return registros
    encabezados = [str(c).strip() if c is not None else "" for c in filas[0]]
    col_map = _mapear_columnas_excel(encabezados)
    if "matricula" in col_map:
        idx = {k: encabezados.index(v) for k, v in col_map.items()}
        for fila in filas[1:]:
            if not fila or not any(fila):
                continue
            fila_dict = {}
            for clave, i in idx.items():
                if i < len(fila):
                    fila_dict[col_map[clave]] = fila[i]
            reg = _registro_desde_dict(fila_dict, col_map)
            if reg:
                registros.append(reg)
    else:
        for fila in filas[1:]:
            if not fila or not fila[0]:
                continue
            mat = _valor_celda(fila[0])
            nombre = _valor_celda(fila[1] if len(fila) > 1 else "").title()
            ap_p = _valor_celda(fila[2] if len(fila) > 2 else "").title()
            ap_m = _valor_celda(fila[3] if len(fila) > 3 else "").title()
            grupo = _valor_celda(fila[5] if len(fila) > 5 else "")
            telefono = _valor_celda(fila[6] if len(fila) > 6 else "")
            registros.append((nombre, ap_p, ap_m, mat, grupo, "Activo", telefono))
    return registros


def buscar_archivo_alumnos():
    os.makedirs(CARPETA_ALUMNOS, exist_ok=True)
    if os.path.isfile(ARCHIVO_ALUMNOS):
        return ARCHIVO_ALUMNOS
    for nombre in sorted(os.listdir(CARPETA_ALUMNOS)):
        if nombre.lower().endswith((".xlsx", ".xls", ".csv")):
            return os.path.join(CARPETA_ALUMNOS, nombre)
    return None


def sincronizar_alumnos_desde_excel(ruta=None, mostrar_error=False):
    if ruta is None:
        ruta = buscar_archivo_alumnos()
    if not ruta or not os.path.isfile(ruta):
        return 0, None
    try:
        registros = leer_registros_excel(ruta)
        if not registros:
            msg = "El archivo no contiene alumnos válidos (revisa matrículas y encabezados)."
            if mostrar_error:
                messagebox.showwarning("Importar alumnos", msg)
            return 0, msg
        conn = sqlite3.connect("sistema.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM estudiantes")
        cursor.executemany(
            """INSERT INTO estudiantes
               (nombre, ap_paterno, ap_materno, matricula, grupo, estado, telefono)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            registros,
        )
        conn.commit()
        conn.close()
        return len(registros), f"Se cargaron {len(registros)} alumnos desde Excel."
    except Exception as e:
        msg = f"No se pudo leer el Excel: {e}"
        if mostrar_error:
            messagebox.showerror("Importar alumnos", msg)
        return 0, msg


def importar_alumnos_archivo(tabla_widget=None, recargar=None):
    ruta = filedialog.askopenfilename(
        title="Seleccionar lista de alumnos (Excel o CSV)",
        filetypes=[
            ("Excel", "*.xlsx *.xls"),
            ("CSV", "*.csv"),
            ("Todos", "*.*"),
        ],
    )
    if not ruta:
        return
    os.makedirs(CARPETA_ALUMNOS, exist_ok=True)
    ext = os.path.splitext(ruta)[1].lower()
    destino = ARCHIVO_ALUMNOS if ext in (".xlsx", ".xls") else os.path.join(CARPETA_ALUMNOS, f"alumnos{ext}")
    if os.path.abspath(ruta) != os.path.abspath(destino):
        shutil.copy2(ruta, destino)
    total, msg = sincronizar_alumnos_desde_excel(destino, mostrar_error=True)
    if total and msg:
        messagebox.showinfo("Importar alumnos", f"{msg}\n\nArchivo guardado en:\n{destino}")
        if recargar:
            recargar()
        elif tabla_widget:
            for item in tabla_widget.get_children():
                tabla_widget.delete(item)
            conn = sqlite3.connect("sistema.db")
            cur = conn.cursor()
            cur.execute(
                "SELECT nombre, ap_paterno, ap_materno, matricula, COALESCE(grupo,''), COALESCE(estado,'') FROM estudiantes ORDER BY grupo, ap_paterno"
            )
            for nombre, ap, am, mat, grupo, estado in cur.fetchall():
                tabla_widget.insert(
                    "",
                    "end",
                    values=(nombre, ap, am, mat, grupo, turno_nombre_grupo(grupo), estado),
                )
            conn.close()

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            ap_paterno TEXT,
            ap_materno TEXT,
            matricula TEXT UNIQUE,
            grupo TEXT,
            estado TEXT DEFAULT 'Activo',
            telefono TEXT DEFAULT ''
        )
    """)

    cursor.execute("PRAGMA table_info(estudiantes)")
    columns = [col[1] for col in cursor.fetchall()]
    if "grupo" not in columns:
        cursor.execute("ALTER TABLE estudiantes ADD COLUMN grupo TEXT")
    if "telefono" not in columns:
        cursor.execute("ALTER TABLE estudiantes ADD COLUMN telefono TEXT")

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

# ====== TURNO Y FALTAS EN TXT ======
def turno_digit_grupo(grupo):
    """ 2261 → Matutino 
2262 → Vespertino"""
    g = str(grupo or "").strip()
    if len(g) >= 4 and g[:3].isdigit():
        d = g[3]
        if d in ("1", "2"):
            return d
    if len(g) >= 2:
        d = g[1]
        if d in ("1", "2"):
            return d
    return None


def sql_filtro_turno(turno_sel):
    if turno_sel == "Matutino (1)":
        return (
            "(CASE WHEN LENGTH(COALESCE(grupo,'')) >= 4 AND SUBSTR(grupo,1,3) GLOB '[0-9][0-9][0-9]' "
            "THEN SUBSTR(grupo,4,1) ELSE SUBSTR(grupo,2,1) END) = '1'"
        )
    if turno_sel == "Vespertino (2)":
        return (
            "(CASE WHEN LENGTH(COALESCE(grupo,'')) >= 4 AND SUBSTR(grupo,1,3) GLOB '[0-9][0-9][0-9]' "
            "THEN SUBSTR(grupo,4,1) ELSE SUBSTR(grupo,2,1) END) = '2'"
        )
    return None


def turno_nombre_grupo(grupo):
    d = turno_digit_grupo(grupo)
    if d == "1":
        return "Matutino"
    if d == "2":
        return "Vespertino"
    return "—"


def hora_a_minutos(hhmm):
    try:
        h, m = hhmm.strip().split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return 0


def obtener_hora_cierre_dia():
    return config.get("hora_cierre_dia", config.get("vespertino", {}).get("salida_fin", "20:30"))


def ruta_bd_dia(fecha_str=None):
    if not fecha_str:
        fecha_str = datetime.now().strftime("%Y-%m-%d")
    y, m, _ = fecha_str.split("-")
    return os.path.join("asistencias", f"{y}-{m}", f"{fecha_str}.db")


def ruta_txt_faltas(fecha_str=None):
    if not fecha_str:
        fecha_str = datetime.now().strftime("%Y-%m-%d")
    y, m, _ = fecha_str.split("-")
    carpeta = os.path.join("asistencias", f"{y}-{m}")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, f"{fecha_str}_faltas.txt")


def guardar_faltas_en_txt(fecha_str=None):
    if not fecha_str:
        fecha_str = datetime.now().strftime("%Y-%m-%d")
    ruta_db = ruta_bd_dia(fecha_str)
    if not os.path.isfile(ruta_db):
        return None, "No hay asistencia registrada para esa fecha."

    conn_dia = sqlite3.connect(ruta_db)
    cur = conn_dia.cursor()
    cur.execute(
        """SELECT nombre, ap_paterno, ap_materno, matricula
           FROM control_dia WHERE estado = 'Falta' ORDER BY ap_paterno, nombre"""
    )
    faltas = cur.fetchall()
    conn_dia.close()

    grupos = {}
    conn = sqlite3.connect("sistema.db")
    cur = conn.cursor()
    for _, _, _, mat in faltas:
        cur.execute("SELECT COALESCE(grupo, '') FROM estudiantes WHERE matricula = ?", (mat,))
        row = cur.fetchone()
        grupos[mat] = row[0] if row else ""
    conn.close()

    por_turno = {"Matutino": [], "Vespertino": [], "Sin turno": []}
    for nombre, ap, am, mat in faltas:
        grupo = grupos.get(mat, "")
        turno = turno_nombre_grupo(grupo)
        linea = f"{nombre} {ap} {am} | Mat: {mat} | Grupo: {grupo or '—'}"
        if turno == "Matutino":
            por_turno["Matutino"].append(linea)
        elif turno == "Vespertino":
            por_turno["Vespertino"].append(linea)
        else:
            por_turno["Sin turno"].append(linea)

    fecha_fmt = datetime.strptime(fecha_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = [
        "=" * 60,
        "REPORTE DE FALTAS — SIMEC CONALEP",
        f"Fecha: {fecha_fmt}",
        f"Generado: {ahora}",
        f"Total de faltas: {len(faltas)}",
        "(Turno: tras prefijo de carrera, 1 = mañana, 2 = tarde)",
        "=" * 60,
        "",
    ]
    for titulo, lista in por_turno.items():
        if not lista:
            continue
        lineas.append(f"--- {titulo.upper()} ({len(lista)}) ---")
        lineas.extend(lista)
        lineas.append("")

    ruta_txt = ruta_txt_faltas(fecha_str)
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    return ruta_txt, f"Se guardaron {len(faltas)} faltas en:\n{ruta_txt}"


def programar_exportacion_faltas(root):
    def revisar():
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            if config.get("ultimo_export_faltas") != hoy:
                ahora = datetime.now().strftime("%H:%M")
                if hora_a_minutos(ahora) >= hora_a_minutos(obtener_hora_cierre_dia()):
                    ruta, _ = guardar_faltas_en_txt(hoy)
                    if ruta:
                        config["ultimo_export_faltas"] = hoy
                        guardar_config()
        except Exception as e:
            print(f"Exportación automática de faltas: {e}")
        if root.winfo_exists():
            root.after(60000, revisar)

    root.after(8000, revisar)

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

    frame_import = tk.Frame(panel, bg=COLORS["bg"])
    frame_import.pack(fill="x", padx=30, pady=(0, 20))
    tk.Label(
        frame_import,
        text="Los alumnos se guardan en Excel (carpeta alumnos/). Al importar se borran los registros anteriores.",
        bg=COLORS["bg"],
        fg=COLORS["text"],
        font=("Segoe UI", 9),
        wraplength=700,
        justify="left",
    ).pack(side="left", fill="x", expand=True)
    tk.Button(
        frame_import,
        text="📥 Importar Excel / CSV",
        command=lambda: importar_alumnos_archivo(),
        bg="#059669",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=12,
        pady=6,
    ).pack(side="right")

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
    
    frame_filtros = tk.Frame(panel, bg=COLORS["panel"], relief="groove", bd=2)
    frame_filtros.pack(fill="x", padx=20, pady=(5, 8))

    tk.Label(
        frame_filtros,
        text="🔍 Filtros de búsqueda",
        bg=COLORS["panel"],
        fg=COLORS["text"],
        font=("Segoe UI", 11, "bold"),
    ).grid(row=0, column=0, columnspan=6, sticky="w", padx=12, pady=(10, 4))

    tk.Label(
        frame_filtros,
        text="",
        bg=COLORS["panel"],
        fg="#64748b",
        font=("Segoe UI", 8),
    ).grid(row=1, column=0, columnspan=6, sticky="w", padx=12, pady=(0, 8))

    tk.Label(frame_filtros, text="Nombre / Matrícula", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).grid(
        row=2, column=0, padx=(12, 4), pady=4, sticky="w"
    )
    entrada_busqueda = tk.Entry(frame_filtros, width=22, font=("Segoe UI", 10), relief="solid", bd=1)
    entrada_busqueda.grid(row=2, column=1, padx=4, pady=4, sticky="w")

    tk.Label(frame_filtros, text="Grupo", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).grid(
        row=2, column=2, padx=(16, 4), pady=4, sticky="w"
    )
    entrada_grupo = tk.Entry(frame_filtros, width=10, font=("Segoe UI", 10), relief="solid", bd=1)
    entrada_grupo.grid(row=2, column=3, padx=4, pady=4, sticky="w")

    tk.Label(frame_filtros, text="Turno", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).grid(
        row=2, column=4, padx=(16, 4), pady=4, sticky="w"
    )
    combo_turno = ttk.Combobox(
        frame_filtros,
        values=["Todos", "Matutino (1)", "Vespertino (2)"],
        width=16,
        state="readonly",
        font=("Segoe UI", 9),
    )
    combo_turno.set("Todos")
    combo_turno.grid(row=2, column=5, padx=4, pady=4, sticky="w")

    frame_btns = tk.Frame(frame_filtros, bg=COLORS["panel"])
    frame_btns.grid(row=3, column=0, columnspan=6, pady=(4, 12))

    label_resultados = tk.Label(frame_filtros, text="", bg=COLORS["panel"], fg=COLORS["btn"], font=("Segoe UI", 9, "bold"))
    label_resultados.grid(row=4, column=0, columnspan=6, padx=12, pady=(0, 8))

    columnas = ("Nombre", "Ap Paterno", "Ap Materno", "Matrícula", "Grupo", "Turno", "Estado")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings", selectmode="extended", height=12)
    anchos = {"Nombre": 110, "Ap Paterno": 100, "Ap Materno": 100, "Matrícula": 90, "Grupo": 70, "Turno": 85, "Estado": 70}
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=anchos.get(col, 100), anchor="center")
    tabla.tag_configure("matutino", background="#e8f5e9")
    tabla.tag_configure("vespertino", background="#fff8e1")
    tabla.pack(pady=10, padx=20, fill="both", expand=True)

    def cargar_datos(texto="", prefijo_grupo="", turno_sel="Todos"):
        for item in tabla.get_children():
            tabla.delete(item)
        try:
            conn = sqlite3.connect("sistema.db")
            cursor = conn.cursor()
            condiciones = ["1=1"]
            params = []
            if texto:
                condiciones.append(
                    "(nombre LIKE ? OR ap_paterno LIKE ? OR ap_materno LIKE ? OR matricula LIKE ? OR grupo LIKE ?)"
                )
                p = f"%{texto}%"
                params.extend([p, p, p, p, p])
            if prefijo_grupo:
                condiciones.append("grupo LIKE ?")
                params.append(f"{prefijo_grupo}%")
            filtro_turno = sql_filtro_turno(turno_sel)
            if filtro_turno:
                condiciones.append(filtro_turno)

            query = f"""
                SELECT nombre, ap_paterno, ap_materno, matricula, COALESCE(grupo, ''), COALESCE(estado, '')
                FROM estudiantes
                WHERE {' AND '.join(condiciones)}
                ORDER BY grupo, ap_paterno, nombre
            """
            cursor.execute(query, params)
            filas = cursor.fetchall()
            conn.close()

            for nombre, ap, am, mat, grupo, estado in filas:
                turno = turno_nombre_grupo(grupo)
                tag = "matutino" if turno == "Matutino" else "vespertino" if turno == "Vespertino" else ""
                tabla.insert(
                    "",
                    "end",
                    values=(nombre, ap, am, mat, grupo, turno, estado),
                    tags=(tag,) if tag else (),
                )
            label_resultados.config(text=f"{len(filas)} estudiante(s) encontrado(s)")
        except Exception as e:
            print(f"Error cargando datos: {e}")
            label_resultados.config(text="Error al cargar")

    def aplicar_filtros():
        cargar_datos(
            entrada_busqueda.get().strip(),
            entrada_grupo.get().strip(),
            combo_turno.get(),
        )

    def limpiar_busqueda():
        entrada_busqueda.delete(0, tk.END)
        entrada_grupo.delete(0, tk.END)
        combo_turno.set("Todos")
        cargar_datos()

    tk.Button(frame_btns, text="🔎 Buscar", command=aplicar_filtros, bg=COLORS["btn"], fg="white", font=("Segoe UI", 9, "bold"), padx=12).pack(
        side="left", padx=6
    )
    tk.Button(frame_btns, text="🗑️ Limpiar filtros", command=limpiar_busqueda, bg="#b91c1c", fg="white", font=("Segoe UI", 9, "bold"), padx=12).pack(
        side="left", padx=6
    )
    tk.Button(
        frame_btns,
        text="📥 Importar Excel",
        command=lambda: importar_alumnos_archivo(tabla_widget=tabla, recargar=aplicar_filtros),
        bg="#059669",
        fg="white",
        font=("Segoe UI", 9, "bold"),
        padx=12,
    ).pack(side="left", padx=6)

    entrada_busqueda.bind("<Return>", lambda e: aplicar_filtros())
    entrada_grupo.bind("<Return>", lambda e: aplicar_filtros())
    combo_turno.bind("<<ComboboxSelected>>", lambda e: aplicar_filtros())

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
    frame_cierre = tk.Frame(contenedor, bg=COLORS["panel"], padx=30, pady=20)
    frame_cierre.pack(pady=10, fill="x")
    tk.Label(frame_cierre, text="CIERRE DEL DÍA", bg=COLORS["panel"], fg=COLORS["text"], font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(
        frame_cierre,
        text="Hora para guardar automáticamente el TXT de faltas (HH:MM)",
        bg=COLORS["panel"],
        fg=COLORS["text"],
    ).pack()
    entrada_cierre = tk.Entry(frame_cierre, width=8, justify="center")
    entrada_cierre.insert(0, obtener_hora_cierre_dia())
    entrada_cierre.pack(pady=8)

    def guardar():
        for turno in turnos:
            for clave in entradas[turno]:
                config[turno][clave] = entradas[turno][clave].get()
        for clave in entradas_taller:
            config["taller"][clave] = entradas_taller[clave].get()
        config["hora_cierre_dia"] = entrada_cierre.get().strip()
        guardar_config()
        tk.Label(panel, text="Guardado ✔", bg=COLORS["bg"], fg="green").pack()
    tk.Button(panel, text="Guardar", bg=COLORS["btn"], fg="white", command=guardar).pack(pady=20)

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
        cargar_faltas()
        conn_dia.close()
        label_estado.config(text="✔ Barrido ejecutado", fg="green")

    def exportar_faltas_txt():
        ruta, msg = guardar_faltas_en_txt()
        if ruta:
            hoy = datetime.now().strftime("%Y-%m-%d")
            config["ultimo_export_faltas"] = hoy
            guardar_config()
            messagebox.showinfo("Faltas en TXT", msg)
            label_export.config(text=f"Último archivo: {os.path.basename(ruta)}", fg="green")
        else:
            messagebox.showwarning("Faltas en TXT", msg)

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

    frame_export = tk.Frame(tab_control, bg=COLORS["panel"], relief="groove", bd=2, padx=16, pady=12)
    frame_export.pack(fill="x", padx=30, pady=10)
    tk.Label(
        frame_export,
        text="📄 Reporte de faltas (TXT)",
        bg=COLORS["panel"],
        fg=COLORS["text"],
        font=FONT_SUBTITULO,
    ).pack(anchor="w")
    tk.Label(
        frame_export,
        text=f"Al llegar las {obtener_hora_cierre_dia()} se guarda solo en asistencias/AAAA-MM/AAAA-MM-DD_faltas.txt",
        bg=COLORS["panel"],
        fg="#64748b",
        font=("Segoe UI", 8),
        wraplength=520,
        justify="left",
    ).pack(anchor="w", pady=(4, 8))
    label_export = tk.Label(frame_export, text="", bg=COLORS["panel"], fg=COLORS["btn"], font=("Segoe UI", 9))
    label_export.pack(anchor="w", pady=(0, 6))
    tk.Button(
        frame_export,
        text="💾 Guardar faltas del día en TXT",
        command=exportar_faltas_txt,
        bg="#1d4ed8",
        fg="white",
        font=FONT_BTN,
        padx=14,
        pady=4,
    ).pack(anchor="w")

    cargar_faltas()
    
    # Pestaña Mensajes
    tab_mensajes = tk.Frame(notebook, bg=COLORS["bg"])
    notebook.add(tab_mensajes, text="Mensajes")
    
    # Apartado para Retardos
    frame_retardos = tk.Frame(tab_mensajes, bg=COLORS["bg"])
    frame_retardos.pack(fill="both", expand=True, padx=20, pady=10)
    
    tk.Label(frame_retardos, text="⏰ ENVIAR MENSAJES POR RETARDOS", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SUBTITULO).pack(pady=10)
    
    # Frame para mensaje retardos
    frame_mensaje_ret = tk.Frame(frame_retardos, bg=COLORS["panel"], padx=20, pady=10)
    frame_mensaje_ret.pack(fill="x", pady=5)
    tk.Label(frame_mensaje_ret, text="Mensaje para retardos:", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_NORMAL).pack(anchor="w")
    text_mensaje_ret = tk.Text(frame_mensaje_ret, height=3, font=FONT_NORMAL, wrap="word")
    text_mensaje_ret.pack(fill="x", pady=5)
    text_mensaje_ret.insert("1.0", "Hola, tienes un retardo registrado. Por favor, llega a tiempo mañana.")
    
    # Tabla retardos
    frame_tabla_ret = tk.Frame(frame_retardos, bg=COLORS["bg"])
    frame_tabla_ret.pack(fill="both", expand=True, pady=5)
    
    columnas_ret = ("Seleccionar", "Nombre", "Matrícula", "Teléfono", "Estado")
    tabla_ret = ttk.Treeview(frame_tabla_ret, columns=columnas_ret, show="headings", height=8)
    for col in columnas_ret:
        tabla_ret.heading(col, text=col)
        if col == "Seleccionar":
            tabla_ret.column(col, width=80, anchor="center")
        elif col == "Teléfono":
            tabla_ret.column(col, width=120, anchor="center")
        else:
            tabla_ret.column(col, width=120, anchor="center")
    tabla_ret.pack(fill="both", expand=True)
    
    # Checkboxes para retardos
    checks_ret = {}
    
    def cargar_retardos():
        for item in tabla_ret.get_children():
            tabla_ret.delete(item)
        checks_ret.clear()
        try:
            conn_dia = obtener_bd_dia()
            cur = conn_dia.cursor()
            cur.execute("""
                SELECT e.nombre || ' ' || e.ap_paterno || ' ' || e.ap_materno, e.matricula, e.telefono, c.estado
                FROM estudiantes e
                JOIN control_dia c ON e.matricula = c.matricula
                WHERE c.estado = 'Retardo' AND c.hora_entrada != '' AND e.telefono IS NOT NULL AND e.telefono != ''
            """)
            retardos = cur.fetchall()
            conn_dia.close()
            for ret in retardos:
                nombre_completo, matricula, telefono, estado = ret
                item_id = tabla_ret.insert("", "end", values=("", nombre_completo, matricula, telefono, estado))
                checks_ret[item_id] = tk.BooleanVar()
                tabla_ret.set(item_id, "Seleccionar", "☐")
        except Exception as e:
            print(f"Error cargando retardos: {e}")
    
    def toggle_seleccion_ret(event):
        item = tabla_ret.identify_row(event.y)
        if item:
            if checks_ret[item].get():
                checks_ret[item].set(False)
                tabla_ret.set(item, "Seleccionar", "☐")
            else:
                checks_ret[item].set(True)
                tabla_ret.set(item, "Seleccionar", "☑")
    
    tabla_ret.bind("<Button-1>", toggle_seleccion_ret)
    
    # Botón enviar retardos
    def enviar_mensajes_ret():
        mensaje = text_mensaje_ret.get("1.0", "end-1c").strip()
        if not mensaje:
            messagebox.showwarning("Advertencia", "Por favor ingrese un mensaje para retardos.")
            return
        seleccionados = [item for item, var in checks_ret.items() if var.get()]
        if not seleccionados:
            messagebox.showwarning("Advertencia", "Por favor seleccione al menos un estudiante con retardo.")
            return
        
        import webbrowser
        enviados = 0
        for item in seleccionados:
            telefono = tabla_ret.set(item, "Teléfono")
            if telefono:
                url = f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}"
                webbrowser.open(url)
                enviados += 1
        messagebox.showinfo("Éxito", f"Mensajes de retardo enviados a {enviados} estudiantes.")
    
    tk.Button(frame_retardos, text="📱 Enviar Mensajes Retardos", command=enviar_mensajes_ret, bg="#25D366", fg="white", font=FONT_BTN, padx=20, pady=5).pack(pady=10)
    
    # Apartado para Inasistencias
    frame_inasistencias = tk.Frame(tab_mensajes, bg=COLORS["bg"])
    frame_inasistencias.pack(fill="both", expand=True, padx=20, pady=10)
    
    tk.Label(frame_inasistencias, text="❌ ENVIAR MENSAJES POR INASISTENCIAS", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SUBTITULO).pack(pady=10)
    
    # Frame para mensaje inasistencias
    frame_mensaje_ina = tk.Frame(frame_inasistencias, bg=COLORS["panel"], padx=20, pady=10)
    frame_mensaje_ina.pack(fill="x", pady=5)
    tk.Label(frame_mensaje_ina, text="Mensaje para inasistencias:", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_NORMAL).pack(anchor="w")
    text_mensaje_ina = tk.Text(frame_mensaje_ina, height=3, font=FONT_NORMAL, wrap="word")
    text_mensaje_ina.pack(fill="x", pady=5)
    text_mensaje_ina.insert("1.0", "Hola, tienes una falta registrada. Es importante que asistas a clases.")
    
    # Tabla inasistencias
    frame_tabla_ina = tk.Frame(frame_inasistencias, bg=COLORS["bg"])
    frame_tabla_ina.pack(fill="both", expand=True, pady=5)
    
    columnas_ina = ("Seleccionar", "Nombre", "Matrícula", "Teléfono", "Estado")
    tabla_ina = ttk.Treeview(frame_tabla_ina, columns=columnas_ina, show="headings", height=8)
    for col in columnas_ina:
        tabla_ina.heading(col, text=col)
        if col == "Seleccionar":
            tabla_ina.column(col, width=80, anchor="center")
        elif col == "Teléfono":
            tabla_ina.column(col, width=120, anchor="center")
        else:
            tabla_ina.column(col, width=120, anchor="center")
    tabla_ina.pack(fill="both", expand=True)
    
    # Checkboxes para inasistencias
    checks_ina = {}
    
    def cargar_inasistencias():
        for item in tabla_ina.get_children():
            tabla_ina.delete(item)
        checks_ina.clear()
        try:
            conn_dia = obtener_bd_dia()
            cur = conn_dia.cursor()
            cur.execute("""
                SELECT e.nombre || ' ' || e.ap_paterno || ' ' || e.ap_materno, e.matricula, e.telefono, c.estado
                FROM estudiantes e
                JOIN control_dia c ON e.matricula = c.matricula
                WHERE c.estado = 'Falta' AND e.telefono IS NOT NULL AND e.telefono != ''
            """)
            inasistencias = cur.fetchall()
            conn_dia.close()
            for ina in inasistencias:
                nombre_completo, matricula, telefono, estado = ina
                item_id = tabla_ina.insert("", "end", values=("", nombre_completo, matricula, telefono, estado))
                checks_ina[item_id] = tk.BooleanVar()
                tabla_ina.set(item_id, "Seleccionar", "☐")
        except Exception as e:
            print(f"Error cargando inasistencias: {e}")
    
    def toggle_seleccion_ina(event):
        item = tabla_ina.identify_row(event.y)
        if item:
            if checks_ina[item].get():
                checks_ina[item].set(False)
                tabla_ina.set(item, "Seleccionar", "☐")
            else:
                checks_ina[item].set(True)
                tabla_ina.set(item, "Seleccionar", "☑")
    
    tabla_ina.bind("<Button-1>", toggle_seleccion_ina)
    
    # Botón enviar inasistencias
    def enviar_mensajes_ina():
        mensaje = text_mensaje_ina.get("1.0", "end-1c").strip()
        if not mensaje:
            messagebox.showwarning("Advertencia", "Por favor ingrese un mensaje para inasistencias.")
            return
        seleccionados = [item for item, var in checks_ina.items() if var.get()]
        if not seleccionados:
            messagebox.showwarning("Advertencia", "Por favor seleccione al menos un estudiante con falta.")
            return
        
        import webbrowser
        enviados = 0
        for item in seleccionados:
            telefono = tabla_ina.set(item, "Teléfono")
            if telefono:
                url = f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}"
                webbrowser.open(url)
                enviados += 1
        messagebox.showinfo("Éxito", f"Mensajes de inasistencia enviados a {enviados} estudiantes.")
    
    tk.Button(frame_inasistencias, text="📱 Enviar Mensajes Inasistencias", command=enviar_mensajes_ina, bg="#25D366", fg="white", font=FONT_BTN, padx=20, pady=5).pack(pady=10)
    
    # Cargar datos iniciales
    cargar_retardos()
    cargar_inasistencias()

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
    programar_exportacion_faltas(root)

def pantalla_inicio(root):
    crear_bd()
    sincronizar_alumnos_desde_excel()
    construir_menu(root)
