import os
import socket
import platform
import sqlite3
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

PASSWORD = "1234"
KEY_FILE = "key.key"

# ===== KEY =====
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
else:
    with open(KEY_FILE, "rb") as f:
        key = f.read()

cipher = Fernet(key)

# ===== DB =====
conn = sqlite3.connect("security.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    created_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT,
    username TEXT,
    password TEXT
)
""")

conn.commit()

# ===== SYSTEM INFO =====
def save_data():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    system = platform.system()
    time_now = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %I:%M:%S %p")

    info = f"Host:{hostname} | IP:{ip} | OS:{system}"
    encrypted = cipher.encrypt(info.encode())

    cur.execute("INSERT INTO logs (data, created_at) VALUES (?, ?)", (encrypted, time_now))
    conn.commit()
    messagebox.showinfo("Done", "System info saved")

def load_logs():
    text_area.delete(1.0, tk.END)

    cur.execute("SELECT * FROM logs")
    rows = cur.fetchall()

    for row in rows:
        try:
            decrypted = cipher.decrypt(row[1]).decode()
            text_area.insert(tk.END, f"{decrypted}\nTime: {row[2]}\n\n")
        except:
            text_area.insert(tk.END, "Error decrypting log\n")

# ===== PASSWORDS =====
def add_password():
    site = site_entry.get()
    user = user_entry.get()
    pwd = pass_entry.get()

    encrypted = cipher.encrypt(pwd.encode())

    cur.execute(
        "INSERT INTO passwords (site, username, password) VALUES (?, ?, ?)",
        (site, user, encrypted)
    )
    conn.commit()
    messagebox.showinfo("Done", "Password saved")

def show_passwords():
    if master_entry.get() != PASSWORD:
        messagebox.showerror("Error", "Wrong Master Password")
        return

    text_area.delete(1.0, tk.END)

    cur.execute("SELECT * FROM passwords")
    rows = cur.fetchall()

    if not rows:
        text_area.insert(tk.END, "No passwords saved\n")
        return

    for row in rows:
        try:
            decrypted = cipher.decrypt(row[3]).decode()
            text_area.insert(
                tk.END,
                f"Site: {row[1]}\nUser: {row[2]}\nPassword: {decrypted}\n\n"
            )
        except:
            text_area.insert(tk.END, "Error decrypting\n")

# ===== CHECK PASSWORD STRENGTH =====
def check_strength():
    pw = checker_entry.get()
    score = 0

    if len(pw) >= 8:
        score += 1
    if any(c.islower() for c in pw):
        score += 1
    if any(c.isupper() for c in pw):
        score += 1
    if any(c.isdigit() for c in pw):
        score += 1
    if any(not c.isalnum() for c in pw):
        score += 1

    if score <= 2:
        result = "Weak Password"
    elif score in (3, 4):
        result = "Medium Password"
    else:
        result = "Strong Password"

    messagebox.showinfo("Result", result)

# ===== LOGIN =====
def check_password():
    if entry.get() == PASSWORD:
        login.destroy()
        open_app()
    else:
        messagebox.showerror("Error", "Wrong Password")

# ===== MAIN APP =====
def open_app():
    global text_area, site_entry, user_entry, pass_entry, master_entry, checker_entry

    app = tk.Tk()
    app.title("Security Tool")
    app.geometry("750x600")

    notebook = ttk.Notebook(app)
    notebook.pack(fill="both", expand=True)

    # ===== TAB 1: ADD PASSWORD =====
    tab1 = tk.Frame(notebook)
    notebook.add(tab1, text="Add Password")

    tk.Label(tab1, text="Site").pack()
    site_entry = tk.Entry(tab1)
    site_entry.pack()

    tk.Label(tab1, text="Username").pack()
    user_entry = tk.Entry(tab1)
    user_entry.pack()
    tk.Label(tab1, text="Password").pack()
    pass_entry = tk.Entry(tab1, show="*")
    pass_entry.pack()

    tk.Button(tab1, text="Save Password", command=add_password).pack(pady=5)

    # ===== TAB 2: VIEW PASSWORDS =====
    tab2 = tk.Frame(notebook)
    notebook.add(tab2, text="View Passwords")

    tk.Label(tab2, text="Master Password").pack()
    master_entry = tk.Entry(tab2, show="*")
    master_entry.pack()

    tk.Button(tab2, text="Show Passwords", command=show_passwords).pack(pady=10)

    # ===== TAB 3: SYSTEM INFO =====
    tab3 = tk.Frame(notebook)
    notebook.add(tab3, text="System Info")

    tk.Button(tab3, text="Save System Info", command=save_data).pack(pady=5)
    tk.Button(tab3, text="Load Logs", command=load_logs).pack(pady=5)

    # ===== TAB 4: CHECKER =====
    tab4 = tk.Frame(notebook)
    notebook.add(tab4, text="Password Checker")

    checker_entry = tk.Entry(tab4, show="*")
    checker_entry.pack(pady=10)

    tk.Button(tab4, text="Check Strength", command=check_strength).pack()

    # ===== OUTPUT =====
    text_area = scrolledtext.ScrolledText(app, width=80, height=15)
    text_area.pack()

    tk.Label(app, text="Created by Yzeed Al Harthi", fg="gray").pack(side="bottom")

    app.mainloop()

# ===== LOGIN =====
login = tk.Tk()
login.title("Login")
login.geometry("250x150")

tk.Label(login, text="Enter Password").pack(pady=5)
entry = tk.Entry(login, show="*")
entry.pack()

tk.Button(login, text="Login", command=check_password).pack(pady=10)

login.mainloop()