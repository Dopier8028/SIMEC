import tkinter as tk
from tkinter import ttk
import sqlite3
import os
from datetime import datetime
import json
import subprocess

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

# Estilo para Treeview
style = ttk.Style()
style.configure("Treeview", background=COLORS["panel"], foreground=COLORS["text"], fieldbackground=COLORS["panel"])
style.map('Treeview', background=[('selected', COLORS["btn_active"])])

FONT_TITULO = ("Segoe UI", 18, "bold")
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
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            ap_paterno TEXT,
            ap_materno TEXT,
            matricula TEXT UNIQUE,
            grupo TEXT,
            estado TEXT DEFAULT ''
        )
    """)

    # Verificar y agregar columna grupo si no existe
    cursor.execute("PRAGMA table_info(estudiantes)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'grupo' not in columns:
        cursor.execute("ALTER TABLE estudiantes ADD COLUMN grupo TEXT")

    # Insertar estudiantes de ejemplo si no existen
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    if cursor.fetchone()[0] == 0:
        estudiantes_ejemplo = [
            ("Juan", "Pérez", "García", "2024001", "A1", ""),
            ("María", "López", "Hernández", "2024002", "A1", ""),
            ("Carlos", "Ramírez", "Torres", "2024003", "A2", ""),
            ("Ana", "Gómez", "Sánchez", "2024004", "A2", ""),
            ("Luis", "Martínez", "Rodríguez", "2024005", "B1", ""),
        ]
        cursor.executemany("INSERT INTO estudiantes (nombre, ap_paterno, ap_materno, matricula, grupo, estado) VALUES (?, ?, ?, ?, ?, ?)", estudiantes_ejemplo)

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
def mostrar_estudiantes(panel):
    limpiar_panel(panel)
    tk.Label(panel, text="ESTUDIANTES", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=10)
    frame_busqueda = tk.Frame(panel, bg=COLORS["bg"])
    frame_busqueda.pack(pady=10)
    tk.Label(frame_busqueda, text="Buscar:", bg=COLORS["bg"], fg=COLORS["text"]).grid(row=0, column=0, padx=5)
    entrada_busqueda = tk.Entry(frame_busqueda, width=30)
    entrada_busqueda.grid(row=0, column=1, padx=10)
    columnas = ("Nombre", "Ap Paterno", "Ap Materno", "Matrícula", "Grupo", "Estado")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings", selectmode="extended", height=12)
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=120, anchor="center")
    tabla.pack(pady=10)
    
    # Frame para botones y label de estado (definir antes de usarlos)
    frame_botones = tk.Frame(panel, bg=COLORS["bg"])
    frame_botones.pack(pady=10)
    label_estado = tk.Label(frame_botones, text="", bg=COLORS["bg"], fg="green", font=("Arial", 10))
    label_estado.pack(side="right", padx=20)
    
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
    def seleccionar_todos():
        for item in tabla.get_children():
            tabla.selection_add(item)
    
    def guardar_cambios():
        seleccionados = tabla.selection()
        if not seleccionados:
            label_estado.config(text="Selecciona estudiantes primero", fg="red")
            panel.after(2000, lambda: label_estado.config(text=""))
            return
        edit_win = tk.Toplevel(panel)
        edit_win.title("Modificar Estado")
        edit_win.geometry("350x180")
        edit_win.configure(bg=COLORS["bg"])
        tk.Label(edit_win, text="Nuevo Estado:", bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=10)
        estado_var = tk.StringVar(value="Suspendido")
        estado_combo = ttk.Combobox(edit_win, textvariable=estado_var, values=["Suspendido", "Incapacitado", "Limpiar"], width=30, state="readonly")
        estado_combo.pack(pady=5, padx=10)
        
        def aplicar_estado():
            nuevo_estado = estado_var.get()
            if not nuevo_estado or nuevo_estado == "Limpiar":
                nuevo_estado = ""
            
            try:
                conn = sqlite3.connect("sistema.db")
                cursor = conn.cursor()
                count = 0
                for item in seleccionados:
                    valores = tabla.item(item, "values")
                    matricula = valores[3]
                    print(f"Actualizando {matricula} con estado {nuevo_estado}")
                    cursor.execute("UPDATE estudiantes SET estado = ? WHERE matricula = ?", (nuevo_estado, matricula))
                    count += 1
                conn.commit()
                print(f"Total actualizados: {count}")
                conn.close()
                cargar_datos()
                label_estado.config(text=f"✔ {count} estudiante(s) actualizado(s)", fg="green")
                panel.after(3000, lambda: label_estado.config(text=""))
                edit_win.destroy()
            except Exception as e:
                print(f"Error al actualizar: {e}")
                label_estado.config(text=f"Error: {e}", fg="red")
                panel.after(3000, lambda: label_estado.config(text=""))
        
        tk.Button(edit_win, text="Aplicar", command=aplicar_estado, bg=COLORS["btn"], fg="white", width=25).pack(pady=15)
    
    def modificar_hora():
        seleccionados = tabla.selection()
        if not seleccionados:
            label_estado.config(text="Selecciona estudiantes primero", fg="red")
            panel.after(2000, lambda: label_estado.config(text=""))
            return
        edit_win = tk.Toplevel(panel)
        edit_win.title("Modificar Hora de Entrada")
        edit_win.geometry("300x150")
        edit_win.configure(bg=COLORS["bg"])
        tk.Label(edit_win, text="Nueva Hora Entrada (HH:MM):", bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=5)
        hora_entry = tk.Entry(edit_win, width=25)
        hora_entry.pack(pady=5, padx=10)
        
        def aplicar_hora():
            nueva_hora = hora_entry.get().strip()
            if not nueva_hora:
                return
            try:
                conn = sqlite3.connect("sistema.db")
                cursor = conn.cursor()
                count = 0
                for item in seleccionados:
                    valores = tabla.item(item, "values")
                    matricula = valores[3]
                    conn_dia = obtener_bd_dia()
                    cur = conn_dia.cursor()
                    cur.execute("UPDATE control_dia SET hora_entrada = ? WHERE matricula = ?", (nueva_hora, matricula))
                    conn_dia.commit()
                    conn_dia.close()
                    count += 1
                conn.close()
                cargar_datos()
                label_estado.config(text=f"✔ Hora actualizada para {count} estudiante(s)", fg="green")
                panel.after(3000, lambda: label_estado.config(text=""))
                edit_win.destroy()
            except Exception as e:
                print(f"Error al actualizar hora: {e}")
                label_estado.config(text=f"Error: {e}", fg="red")
                panel.after(3000, lambda: label_estado.config(text=""))
        
        tk.Button(edit_win, text="Aplicar", command=aplicar_hora, bg=COLORS["btn"], fg="white", width=20).pack(pady=10)
    tabla.bind("<Double-1>", lambda e: None)  # Deshabilitar doble clic para evitar conflicto
    tk.Button(frame_busqueda, text="Buscar", command=buscar, bg=COLORS["btn"], fg="white").grid(row=0, column=2, padx=5)
    tk.Button(frame_busqueda, text="Limpiar", command=limpiar_busqueda, bg="#c0392b", fg="white").grid(row=0, column=3, padx=5)
    tk.Button(frame_busqueda, text="Seleccionar Todos", command=seleccionar_todos, bg=COLORS["btn"], fg="white").grid(row=0, column=4, padx=5)
    
    tk.Button(frame_botones, text="✏️ Modificar Estado", command=guardar_cambios, bg=COLORS["btn"], fg="white").pack(side="left", padx=5)
    tk.Button(frame_botones, text="🕐 Modificar Hora", command=modificar_hora, bg=COLORS["btn"], fg="white").pack(side="left", padx=5)
    
    cargar_datos()

# ====== CONTROL DÍA ======
def vista_control_dia(panel):
    limpiar_panel(panel)
    tk.Label(panel, text="CONTROL POR DÍA", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    columnas = ("Nombre", "Matrícula", "Entrada", "Estado", "Salida")
    tabla = ttk.Treeview(panel, columns=columnas, show="headings")
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=130, anchor="center")
    tabla.pack(pady=20)
    conn = obtener_bd_dia()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nombre, matricula, hora_entrada, estado, hora_salida FROM control_dia
    """)
    for fila in cursor.fetchall():
        tabla.insert("", "end", values=fila)
    conn.close()

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

def vista_control(panel):
    limpiar_panel(panel)
    tk.Label(panel, text="CONTROL AUTOMÁTICO", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITULO).pack(pady=20)
    frame_hora = tk.Frame(panel, bg=COLORS["bg"])
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
    tabla = ttk.Treeview(panel, columns=columnas, show="headings")
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, width=150, anchor="center")
    tabla.pack(pady=20)
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
        for item in tabla.get_children():
            tabla.delete(item)
        cur.execute("SELECT nombre, matricula, estado FROM control_dia WHERE estado = 'Falta'")
        for fila in cur.fetchall():
            tabla.insert("", "end", values=fila)
        conn_dia.close()
        label_estado.config(text="✔ Barrido ejecutado", fg="green")
    def verificar_barrido():
        try:
            hora_actual = datetime.now().strftime("%H:%M")
            if hora_actual >= hora_barrido:
                label_estado.config(text="Hora de barrido alcanzada", fg="orange")
            else:
                label_estado.config(text=f"Próximo barrido a {hora_barrido}", fg="gray")
            panel.after(60000, verificar_barrido)
        except:
            pass
    verificar_barrido()
    tk.Button(panel, text="Marcar Faltas Ahora", command=marcar_faltas, bg=COLORS["btn"], fg="white").pack(pady=10)

# ====== INICIO ======
def vista_inicio(panel):
    limpiar_panel(panel)
    tk.Label(panel, text="BIENVENIDO AL SISTEMA SIMEC", font=FONT_TITULO, bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=20)
    tk.Label(panel, text="Sistema de Gestión de Estudiantes y Control de Asistencias", font=("Segoe UI", 12), bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=10)
    frame_opciones = tk.Frame(panel, bg=COLORS["bg"])
    frame_opciones.pack(expand=True, pady=20)
    opciones = [
        ("👥 Estudiantes", mostrar_estudiantes),
        ("📝 Registro", vista_registro),
        ("📅 Control Día", vista_control_dia),
        ("🔍 Control", vista_control),
        ("⚙️ Configuración", vista_configuracion)
    ]
    for i, (txt, cmd) in enumerate(opciones):
        btn = tk.Button(frame_opciones, text=txt, font=("Segoe UI", 16, "bold"),
                        bg=COLORS["btn"], fg="white", width=20, height=3,
                        relief="ridge", bd=4, padx=10, pady=5,
                        activebackground=COLORS["btn_hover"], activeforeground="white",
                        command=lambda c=cmd: c(panel))
        btn.grid(row=i//3, column=i%3, padx=30, pady=20, sticky="nsew")
    # Configurar el grid para centrar
    frame_opciones.grid_columnconfigure(0, weight=1)
    frame_opciones.grid_columnconfigure(1, weight=1)
    frame_opciones.grid_rowconfigure(0, weight=1)
    frame_opciones.grid_rowconfigure(1, weight=1)

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

    btn("👥 Estudiantes", mostrar_estudiantes)
    btn("📝 Registro", vista_registro)
    btn("📅 Control Día", vista_control_dia)
    btn("⚙️ Configuración", vista_configuracion)
    btn("🔍 Control", vista_control)

    vista_inicio(panel)

def pantalla_inicio(root):
    crear_bd()
    construir_menu(root)