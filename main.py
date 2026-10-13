import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import customtkinter as ctk

from calculator import CalculatorError, calculate, format_result


COLORS = {
    "background": ("#F4F5F8", "#14151A"),
    "surface": ("#FFFFFF", "#1E2027"),
    "surface_alt": ("#F0F1F5", "#292B34"),
    "border": ("#E7E8EF", "#343640"),
    "text": ("#20212A", "#F3F3F7"),
    "muted": ("#858795", "#A0A1AE"),
    "accent": ("#6C5CE7", "#8B7BFF"),
    "accent_hover": ("#5B4BD6", "#7969EF"),
    "error": ("#C0394B", "#FF8290"),
}


def history_path() -> Path:
    app_folder = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    return app_folder / "naya_history.json"


class NayaCalculator(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Naya Smart Calculator")
        self.geometry("940x720")
        self.minsize(360, 560)
        self.configure(fg_color=COLORS["background"])

        self.expression = ctk.StringVar()
        self.preview_value = ctk.StringVar(value="0")
        self.status_value = ctk.StringVar(value="")
        self._history_error = ""
        self.history: List[Dict[str, str]] = []
        self.key_buttons: List[ctk.CTkButton] = []
        self._is_wide: Optional[bool] = None
        self._just_calculated = False
        self._font_scale = 1.0
        self._load_history()
        self._build_layout()
        self._refresh_history()
        self._set_responsive_layout()
        self._preview()

        self.bind("<Return>", self._on_enter)
        self.bind("<KP_Enter>", self._on_enter)
        self.bind("<Escape>", self._on_escape)
        self.bind("<Configure>", self._on_resize)

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["background"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.content.grid(row=0, column=0, sticky="nsew", padx=18, pady=14)
        self.content.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(1, weight=1)
        logo = ctk.CTkLabel(
            header, text="N", width=42, height=42, corner_radius=14,
            fg_color=COLORS["surface_alt"], text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI Variable", size=21, weight="bold"),
        )
        logo.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
        self.title_label = ctk.CTkLabel(
            header, text="Naya Smart Calculator", anchor="w",
            text_color=COLORS["text"], font=ctk.CTkFont(family="Segoe UI Variable", size=17, weight="bold"),
        )
        self.title_label.grid(row=0, column=1, sticky="sw")
        subtitle = ctk.CTkLabel(
            header, text="Hitung dengan cara yang lebih sederhana", anchor="w",
            text_color=COLORS["muted"], font=ctk.CTkFont(family="Segoe UI Variable", size=12),
        )
        subtitle.grid(row=1, column=1, sticky="nw")
        self.theme_menu = ctk.CTkOptionMenu(
            header, values=["Otomatis", "Terang", "Gelap"], width=120, height=34,
            fg_color=COLORS["surface_alt"], button_color=COLORS["surface_alt"],
            button_hover_color=COLORS["border"], text_color=COLORS["text"],
            dropdown_fg_color=COLORS["surface"], dropdown_text_color=COLORS["text"],
            command=self._change_theme,
        )
        self.theme_menu.set("Otomatis")
        self.theme_menu.grid(row=0, column=2, rowspan=2, sticky="e")

        self.body = ctk.CTkFrame(self.content, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="ew")
        self.body.grid_columnconfigure(0, weight=1)
        self.calculator_panel = ctk.CTkFrame(
            self.body, fg_color=COLORS["surface"], corner_radius=20,
            border_width=1, border_color=COLORS["border"],
        )
        self.calculator_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        self.calculator_panel.grid_columnconfigure(0, weight=1)

        self.display = ctk.CTkFrame(self.calculator_panel, fg_color="transparent")
        self.display.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        self.display.grid_columnconfigure(0, weight=1)
        self.expression_entry = ctk.CTkEntry(
            self.display, textvariable=self.expression, height=40, border_width=1,
            border_color=COLORS["border"],
            fg_color="transparent", text_color=COLORS["muted"],
            placeholder_text="Ketik ekspresi…", placeholder_text_color=COLORS["muted"],
            justify="right", font=ctk.CTkFont(family="Segoe UI Variable", size=20),
        )
        self.expression_entry.grid(row=0, column=0, sticky="ew")
        self.expression_entry.bind("<KeyRelease>", self._on_expression_change)
        self.expression_entry.bind("<FocusIn>", self._on_expression_focus)
        self.expression_entry.bind("<FocusOut>", self._on_expression_blur)
        self.result_label = ctk.CTkLabel(
            self.display, textvariable=self.preview_value, anchor="e",
            text_color=COLORS["accent"], font=ctk.CTkFont(family="Segoe UI Variable", size=52, weight="bold"),
        )
        self.result_label.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.status_label = ctk.CTkLabel(
            self.display, textvariable=self.status_value, anchor="e",
            text_color=COLORS["error"], font=ctk.CTkFont(family="Segoe UI Variable", size=12),
        )
        self.status_label.grid(row=2, column=0, sticky="ew", pady=(2, 0))

        keypad = ctk.CTkFrame(self.calculator_panel, fg_color="transparent")
        keypad.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        for column in range(4):
            keypad.grid_columnconfigure(column, weight=1, uniform="key")
        for row in range(6):
            keypad.grid_rowconfigure(row, weight=1, minsize=50, uniform="keyrow")
        keys = [
            [("AC", self._clear, "utility"), ("( )", self._parenthesis, "utility"), ("%", lambda: self._insert("%"), "utility"), ("⌫", self._backspace, "utility")],
            [("7", lambda: self._insert("7"), "number"), ("8", lambda: self._insert("8"), "number"), ("9", lambda: self._insert("9"), "number"), ("÷", lambda: self._insert("÷"), "operator")],
            [("4", lambda: self._insert("4"), "number"), ("5", lambda: self._insert("5"), "number"), ("6", lambda: self._insert("6"), "number"), ("×", lambda: self._insert("×"), "operator")],
            [("1", lambda: self._insert("1"), "number"), ("2", lambda: self._insert("2"), "number"), ("3", lambda: self._insert("3"), "number"), ("−", lambda: self._insert("-"), "operator")],
            [("±", self._toggle_sign, "utility"), ("0", lambda: self._insert("0"), "number"), (".", lambda: self._insert("."), "number"), ("+", lambda: self._insert("+"), "operator")],
        ]
        for row, key_row in enumerate(keys):
            for column, (label, command, style) in enumerate(key_row):
                self._make_key(keypad, row, column, label, command, style)
        self.equals_button = ctk.CTkButton(
            keypad, text="=", command=self._calculate, height=50, corner_radius=16,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF", font=ctk.CTkFont(family="Segoe UI Variable", size=21, weight="bold"),
        )
        self.key_buttons.append(self.equals_button)
        self.equals_button.grid(row=5, column=0, columnspan=4, sticky="ew", padx=4, pady=4)

        self.history_panel = ctk.CTkFrame(
            self.body, fg_color=COLORS["surface"], corner_radius=20,
            border_width=1, border_color=COLORS["border"], width=250,
        )
        self.history_panel.grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        self.history_panel.grid_propagate(False)
        self.history_panel.grid_columnconfigure(0, weight=1)
        history_heading = ctk.CTkLabel(
            self.history_panel, text="RIWAYAT", anchor="w",
            text_color=COLORS["muted"], font=ctk.CTkFont(family="Segoe UI Variable", size=12, weight="bold"),
        )
        history_heading.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        self.history_items = ctk.CTkScrollableFrame(
            self.history_panel, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.history_items.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))
        self.history_panel.grid_rowconfigure(1, weight=1)

    def _make_key(self, parent: ctk.CTkFrame, row: int, column: int, label: str, command, style: str) -> None:
        is_operator = style == "operator"
        is_utility = style == "utility"
        button = ctk.CTkButton(
            parent, text=label, command=command, height=50, corner_radius=16,
            fg_color=COLORS["surface_alt"] if is_utility or is_operator else COLORS["surface"],
            hover_color=COLORS["border"],
            border_width=1 if style == "number" else 0,
            border_color=COLORS["border"], text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI Variable", size=19 if is_utility else 21, weight="bold" if is_operator else "normal"),
        )
        self.key_buttons.append(button)
        button.grid(row=row, column=column, sticky="ew", padx=4, pady=4)

    def _on_resize(self, event) -> None:
        if event.widget is not self:
            return
        is_wide = self.winfo_width() >= 760
        if is_wide != self._is_wide:
            self._is_wide = is_wide
            self._set_responsive_layout()
        scale = max(0.84, min(1.08, self.winfo_width() / 900))
        if abs(scale - self._font_scale) > 0.04:
            self._font_scale = scale
            self.result_label.configure(font=ctk.CTkFont(family="Segoe UI Variable", size=int(52 * scale), weight="bold"))
            self.expression_entry.configure(font=ctk.CTkFont(family="Segoe UI Variable", size=max(17, int(20 * scale))))
            for button in self.key_buttons:
                button.configure(
                    height=max(50, min(60, int(52 * scale))),
                    font=ctk.CTkFont(family="Segoe UI Variable", size=max(17, int(21 * scale))),
                )

    def _set_responsive_layout(self) -> None:
        if self._is_wide:
            self.body.grid_columnconfigure(0, weight=1)
            self.body.grid_columnconfigure(1, weight=0, minsize=250)
            self.calculator_panel.grid_configure(row=0, column=0, padx=(0, 12))
            self.history_panel.configure(width=250, height=480)
            self.history_panel.grid_configure(row=0, column=1, padx=(0, 0))
        else:
            self.body.grid_columnconfigure(0, weight=1)
            self.body.grid_columnconfigure(1, weight=0, minsize=0)
            self.calculator_panel.grid_configure(row=0, column=0, padx=(0, 0))
            self.history_panel.configure(width=max(300, self.winfo_width() - 56), height=210)
            self.history_panel.grid_configure(row=1, column=0, padx=(0, 0))

    def _change_theme(self, theme: str) -> None:
        ctk.set_appearance_mode({"Otomatis": "system", "Terang": "light", "Gelap": "dark"}[theme])

    def _on_expression_change(self, _event=None) -> None:
        self._just_calculated = False
        self._preview()

    def _on_enter(self, _event=None):
        self._calculate()
        return "break"

    def _on_escape(self, _event=None):
        self._clear()
        return "break"

    def _preview(self) -> None:
        expression = self.expression.get().strip()
        if not expression:
            self.preview_value.set("0")
            self.status_value.set(self._history_error)
            return
        try:
            self.preview_value.set(format_result(calculate(expression)))
            self.status_value.set(self._history_error)
        except CalculatorError as error:
            self.preview_value.set("—")
            self.status_value.set(str(error))

    def _calculate(self) -> None:
        expression = self.expression.get().strip()
        try:
            result = format_result(calculate(expression))
        except CalculatorError as error:
            self.preview_value.set("—")
            self.status_value.set(str(error))
            return
        self.preview_value.set(result)
        self.status_value.set("")
        self._just_calculated = True
        self.history.insert(0, {"expression": expression, "result": result})
        self.history = self.history[:50]
        self._save_history()
        self._refresh_history()

    def _insert(self, value: str) -> None:
        current = self.expression.get()
        if self._just_calculated and value[0].isdigit():
            current = ""
        self._just_calculated = False
        self.expression.set(current + value)
        self._focus_expression()
        self._preview()

    def _parenthesis(self) -> None:
        current = self.expression.get()
        opening = current.count("(") > current.count(")")
        token = ")" if opening else "("
        if token == "(" and current and (current[-1].isdigit() or current[-1] == ")"):
            token = "*("
        self._insert(token)

    def _toggle_sign(self) -> None:
        expression = self.expression.get().strip()
        if not expression:
            self._insert("-")
        elif expression.startswith("-(") and expression.endswith(")"):
            self.expression.set(expression[2:-1])
            self._preview()
        else:
            self.expression.set("-(" + expression + ")")
            self._preview()
        self._focus_expression()

    def _backspace(self) -> None:
        self.expression.set(self.expression.get()[:-1])
        self._just_calculated = False
        self._focus_expression()
        self._preview()

    def _clear(self) -> None:
        self.expression.set("")
        self._just_calculated = False
        self._focus_expression()
        self._preview()

    def _focus_expression(self) -> None:
        self.expression_entry.focus_set()
        self.expression_entry.icursor("end")

    def _on_expression_focus(self, _event=None) -> None:
        self.expression_entry.configure(border_color=COLORS["muted"])

    def _on_expression_blur(self, _event=None) -> None:
        self.expression_entry.configure(border_color=COLORS["border"])

    def _refresh_history(self) -> None:
        for child in self.history_items.winfo_children():
            child.destroy()
        if not self.history:
            empty = ctk.CTkLabel(
                self.history_items, text="Hasil perhitungan Anda\nakan muncul di sini.",
                justify="left", anchor="nw", text_color=COLORS["muted"],
                font=ctk.CTkFont(family="Segoe UI Variable", size=13),
            )
            empty.grid(row=0, column=0, sticky="ew", padx=8, pady=10)
            return
        for row, item in enumerate(self.history):
            button = ctk.CTkButton(
                self.history_items, text=item["expression"] + "\n= " + item["result"],
                command=lambda expression=item["expression"]: self._reuse_history(expression),
                anchor="w", height=58, corner_radius=12,
                fg_color=COLORS["surface_alt"], hover_color=COLORS["border"],
                text_color=COLORS["text"], font=ctk.CTkFont(family="Segoe UI Variable", size=13),
            )
            button.grid(row=row, column=0, sticky="ew", padx=4, pady=4)

    def _reuse_history(self, expression: str) -> None:
        self.expression.set(expression)
        self._just_calculated = False
        self._focus_expression()
        self._preview()

    def _load_history(self) -> None:
        path = history_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError) as error:
            self._history_error = "Riwayat tidak dapat dibaca: " + str(error)
            self.status_value.set(self._history_error)
            return
        if not isinstance(raw, list):
            self._history_error = "Format file riwayat tidak valid."
            self.status_value.set(self._history_error)
            return
        self.history = [
            {"expression": item["expression"], "result": item["result"]}
            for item in raw
            if isinstance(item, dict)
            and isinstance(item.get("expression"), str)
            and isinstance(item.get("result"), str)
        ][:50]

    def _save_history(self) -> None:
        try:
            history_path().write_text(
                json.dumps(self.history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._history_error = ""
        except OSError as error:
            self._history_error = "Riwayat tidak dapat disimpan: " + str(error)
            self.status_value.set(self._history_error)


if __name__ == "__main__":
    ctk.set_default_color_theme("blue")
    ctk.set_appearance_mode("system")
    NayaCalculator().mainloop()
