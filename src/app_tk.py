# -*- coding: utf-8 -*-
"""
app_tk.py

GUI (Tkinter) da Calculadora.
- A GUI NÃO calcula nada. Ela só traduz cliques/teclas para chamadas na Engine.
- Atualiza o display principal e o display secundário a partir do estado da Engine.

Como rodar (na raiz do projeto):
    python ./src/app_tk.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# Garante que o import funcione ao rodar "python ./src/app_tk.py"
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent  # C:\Calculadora
ASSETS_DIR = PROJECT_ROOT / "assets"
sys.path.insert(0, str(SRC_DIR))

from engine import CalculatorEngine  # noqa: E402


class CalculatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CalculadoraPython")

        # Engine
        self.engine = CalculatorEngine()

        # Estado de UI
        self.secondary_var = tk.StringVar(value=self.engine.get_secondary())
        self.display_var = tk.StringVar(value=self.engine.get_display())

        # Layout base
        self._build_ui()
        self._apply_app_icon()
        self._bind_keys()
        self._refresh()

        # Ajuda a janela a aparecer na frente (Windows às vezes abre atrás)
        self.root.after(50, self._bring_to_front)

    # -------------------------
    # Aparência / Ícone
    # -------------------------
    def _apply_app_icon(self):
        """
        Usa assets/icon.ico se existir.
        Se não existir ou falhar, não quebra o app (fallback silencioso).
        """
        ico_path = ASSETS_DIR / "icon.ico"
        if not ico_path.exists():
            return

        try:
            # No Windows, iconbitmap funciona bem com .ico
            self.root.iconbitmap(str(ico_path))
        except Exception:
            # Se der problema (tema, permissões, etc.), só ignora.
            pass

    # -------------------------
    # UI
    # -------------------------
    def _build_ui(self):
        self.root.minsize(360, 520)
        self.root.geometry("380x560")
        self.root.resizable(True, True)

        outer = ttk.Frame(self.root, padding=12)
        outer.grid(row=0, column=0, sticky="nsew")

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Display secundário (ex: "10 +")
        secondary = ttk.Label(
            outer,
            textvariable=self.secondary_var,
            anchor="e",
            font=("Segoe UI", 11),
        )
        secondary.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        # Display principal
        display = ttk.Label(
            outer,
            textvariable=self.display_var,
            anchor="e",
            font=("Segoe UI", 28, "bold"),
        )
        display.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        outer.columnconfigure(0, weight=1)

        # Grade de botões
        grid = ttk.Frame(outer)
        grid.grid(row=2, column=0, sticky="nsew")
        outer.rowconfigure(2, weight=1)

        for r in range(6):
            grid.rowconfigure(r, weight=1)
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        buttons = [
            [("CE", "CE"), ("C", "C"), ("⌫", "BS"), ("÷", "/")],
            [("7", "7"), ("8", "8"), ("9", "9"), ("×", "*")],
            [("4", "4"), ("5", "5"), ("6", "6"), ("−", "-")],
            [("1", "1"), ("2", "2"), ("3", "3"), ("+", "+")],
            [("±", "±"), ("0", "0"), (".", "."), ("=", "=")],
        ]

        for r, row in enumerate(buttons):
            for c, (label, key) in enumerate(row):
                btn = ttk.Button(
                    grid,
                    text=label,
                    command=lambda k=key: self._on_press(k),
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

        hint = ttk.Label(
            outer,
            text="Teclado: Enter (=), Esc (C), Delete (CE), Backspace (⌫), Numpad OK",
            anchor="w",
            font=("Segoe UI", 9),
        )
        hint.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def _bring_to_front(self):
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.attributes("-topmost", True)
            self.root.after(150, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        try:
            self.root.focus_force()
        except tk.TclError:
            pass

    # -------------------------
    # Engine bridge
    # -------------------------
    def _on_press(self, key: str):
        if key.isdigit():
            self.engine.press_digit(key)
        elif key == ".":
            self.engine.press_decimal()
        elif key in {"+", "-", "*", "/"}:
            self.engine.press_operator(key)
        elif key == "=":
            self.engine.press_equals()
        elif key == "C":
            self.engine.press_clear()
        elif key == "CE":
            self.engine.press_clear_entry()
        elif key == "BS":
            self.engine.press_backspace()
        elif key == "±":
            self.engine.press_toggle_sign()

        self._refresh()

    def _refresh(self):
        self.display_var.set(self.engine.get_display())
        self.secondary_var.set(self.engine.get_secondary())

    # -------------------------
    # Key bindings
    # -------------------------
    def _bind_keys(self):
        self.root.bind_all("<Key>", self._on_key_event)

    def _on_key_event(self, event: tk.Event):
        ks = event.keysym
        ch = event.char

        if ch.isdigit():
            self._on_press(ch)
            return

        if ks.startswith("KP_") and len(ks) == 4 and ks[-1].isdigit():
            self._on_press(ks[-1])
            return

        if ch in {"+", "-", "*", "/"}:
            self._on_press(ch)
            return

        if ks == "KP_Add":
            self._on_press("+")
            return
        if ks == "KP_Subtract":
            self._on_press("-")
            return
        if ks == "KP_Multiply":
            self._on_press("*")
            return
        if ks == "KP_Divide":
            self._on_press("/")
            return

        if ch in {".", ","} or ks == "period":
            self._on_press(".")
            return

        if ks in {"Return", "KP_Enter"} or ch == "=":
            self._on_press("=")
            return

        if ks == "BackSpace":
            self._on_press("BS")
            return
        if ks == "Escape":
            self._on_press("C")
            return
        if ks == "Delete":
            self._on_press("CE")
            return

        # atalhos opcionais
        if ch.lower() == "c":
            self._on_press("C")
            return
        if ch.lower() == "e":
            self._on_press("CE")
            return
        if ch.lower() == "s":
            self._on_press("±")
            return


def main():
    root = tk.Tk()

    # Tema ttk (se existir no Windows)
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass

    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()