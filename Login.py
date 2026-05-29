import tkinter as tk
from tkinter import messagebox
import menu  # IMPORTANTE: usa el menu corregido

# ====== VENTANA ======
ventana = tk.Tk()
ventana.title("Login del Sistema")
ventana.geometry("600x420")
ventana.configure(bg="#f5f6fa")
ventana.resizable(False, False)

# Centrar ventana
x = (ventana.winfo_screenwidth() // 2) - (600 // 2)
y = (ventana.winfo_screenheight() // 2) - (420 // 2)
ventana.geometry(f"600x420+{x}+{y}")

# ====== CONTENEDOR ======
contenedor = tk.Frame(
    ventana,
    bg="white",
    highlightbackground="#dcdde1",
    highlightthickness=1
)
contenedor.place(relx=0.5, rely=0.5, anchor="center", width=420, height=340)

# ====== BARRA VERDE SUPERIOR ======
barra = tk.Frame(contenedor, bg="#0a7f5a", height=8)
barra.pack(fill="x", side="top")

# ====== TITULO ======
titulo = tk.Label(
    contenedor,
    text="INICIAR SESIÓN",
    bg="white",
    fg="#2c3e50",
    font=("Segoe UI", 18, "bold")
)
titulo.pack(pady=15)

# ====== FORMULARIO ======
form = tk.Frame(contenedor, bg="white")
form.pack(pady=5)

# Usuario
tk.Label(form, text="Usuario", bg="white", fg="#34495e",
         font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", pady=5)

usuario = tk.Entry(form, font=("Segoe UI", 12),
                   bd=1, relief="solid", width=28)
usuario.grid(row=1, column=0, pady=5, ipady=6)

# Contraseña
tk.Label(form, text="Contraseña", bg="white", fg="#34495e",
         font=("Segoe UI", 11)).grid(row=2, column=0, sticky="w", pady=5)

password = tk.Entry(form, show="*", font=("Segoe UI", 12),
                    bd=1, relief="solid", width=28)
password.grid(row=3, column=0, pady=5, ipady=6)

# ====== FUNCIONES ======
def aceptar():
    import sqlite3
    conn = sqlite3.connect(menu.ruta_datos("sistema.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM usuarios WHERE usuario = ?", (usuario.get(),))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] == password.get():
        ventana.destroy()
        root = tk.Tk()
        menu.pantalla_inicio(root)
        root.mainloop()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

def cancelar():
    ventana.destroy()

# ====== BOTONES ======
btn_frame = tk.Frame(contenedor, bg="white")
btn_frame.pack(pady=20, padx=30, fill="x")

btn_aceptar = tk.Button(
    btn_frame,
    text="Ingresar",
    bg="#0a7f5a",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    height=2,
    bd=0,
    activebackground="#086a4a",
    cursor="hand2",
    command=aceptar
)
btn_aceptar.grid(row=0, column=0, padx=5, sticky="ew")

btn_cancelar = tk.Button(
    btn_frame,
    text="Salir",
    bg="#95a5a6",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    height=2,
    bd=0,
    activebackground="#7f8c8d",
    cursor="hand2",
    command=cancelar
)
btn_cancelar.grid(row=0, column=1, padx=5, sticky="ew")

btn_frame.columnconfigure(0, weight=1)
btn_frame.columnconfigure(1, weight=1)

# ====== FOOTER ======
footer = tk.Label(
    ventana,
    text="Sistema de Control",
    bg="#f5f6fa",
    fg="#7f8c8d",
    font=("Segoe UI", 9)
)
footer.pack(side="bottom", pady=10)

ventana.mainloop()