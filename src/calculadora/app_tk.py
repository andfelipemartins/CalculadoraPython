# -*- coding: utf-8 -*-
"""
app_tk.py

GUI (Tkinter) da Calculadora.
- A GUI NÃO calcula nada. Ela só traduz cliques/teclas para chamadas na Engine.
- Atualiza o display principal e o display secundário a partir do estado da Engine.

Como rodar:
- python -m calculadora
- calculadora
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from calculadora.engine import CalculatorEngine


class CalculatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Calculadora (Tkinter + Engine)")

        self.engine = CalculatorEngine()

        self.var_secondary = tk.StringVar(value="")
        self.var_display = tk.StringVar(value="0")

        self._build_ui()
        self.root.bind("<Key>", self._on_key_event)
        self._render()

    def _build_ui(self):
        self.root.geometry("420x560")
        self.root.minsize(360, 520)

        wrapper = ttk.Frame(self.root, padding=12)
        wrapper.pack(fill="both", expand=True)

        lbl_secondary = ttk.Label(
            wrapper,
            textvariable=self.var_secondary,
            anchor="e",
            font=("Segoe UI", 12),
        )
        lbl_secondary.pack(fill="x", pady=(0, 6))

        lbl_display = ttk.Label(
            wrapper,
            textvariable=self.var_display,
            anchor="e",
            font=("Segoe UI", 28, "bold"),
        )
        lbl_display.pack(fill="x", pady=(0, 12))

        grid = ttk.Frame(wrapper)
        grid.pack(fill="both", expand=True)

        for r in range(5):
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
            for c, (label, value) in enumerate(row):
                btn = ttk.Button(
                    grid,
                    text=label,
                    command=lambda v=value: self._on_press(v),
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

    def _on_press(self, value: str):
        if value.isdigit():
            self.engine.press_digit(value)
        elif value == ".":
            self.engine.press_decimal()
        elif value in {"+", "-", "*", "/"}:
            self.engine.press_operator(value)
        elif value == "=":
            self.engine.press_equals()
        elif value == "C":
            self.engine.press_clear()
        elif value == "CE":
            self.engine.press_clear_entry()
        elif value == "BS":
            self.engine.press_backspace()
        elif value == "±":
            self.engine.press_toggle_sign()

        self._render()

    def _render(self):
        raw = self.engine.get_display()

        # GUI-friendly: limita o tamanho visual do display sem usar float
        # para evitar perda de precisão/representação.
        text = raw

        MAX = 18  # limite visual
        if text not in {"Erro", "Error"} and len(text) > MAX:
            # Se já vier em notação científica, só corta no limite
            if "e" in text.lower():
                text = text[:MAX]
            else:
                # Heurística simples:
                # - mantém sinal
                # - preserva parte inteira e começa a cortar a parte decimal
                sign = ""
                if text.startswith("-"):
                    sign = "-"
                    text_body = text[1:]
                else:
                    text_body = text

                if "." in text_body:
                    int_part, frac_part = text_body.split(".", 1)
                    # reserva: sinal + inteiro + "." + (resto)
                    reserve = len(sign) + len(int_part) + 1
                    if reserve >= MAX:
                        # inteiro já “enche” o display -> mostra começo do inteiro
                        text = (sign + int_part)[:MAX]
                    else:
                        allowed_frac = MAX - reserve
                        text = sign + int_part + "." + frac_part[:allowed_frac]
                else:
                    # número inteiro muito grande -> corta visualmente
                    text = (sign + text_body)[:MAX]

        self.var_display.set(text)
        self.var_secondary.set(self.engine.get_secondary())

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

        if ch in {".", ","} or ks in {"period", "KP_Decimal"}:
            self._on_press(".")
            return

        if ks in {"Return", "KP_Enter"} or ch == "=":
            self._on_press("=")
            return

        if ks == "BackSpace":
            self._on_press("BS")
            return
        if ks == "Delete":
            self._on_press("CE")
            return

        if ks == "Escape":
            self._on_press("C")
            return

        if ch.lower() == "s":
            self._on_press("±")
            return


def main() -> None:
    root = tk.Tk()
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