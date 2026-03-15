from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        canvas = tk.Canvas(self, bg="#111827", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = ttk.Frame(canvas)

        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas = canvas


class StatusBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.label = ttk.Label(self, text="Ready", style="Status.TLabel")
        self.label.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100, length=500, style="Horizontal.TProgressbar")
        self.progress.grid(row=0, column=1, sticky="ew", padx=10, pady=6)

    def set_status(self, text: str):
        self.label.config(text=text)

    def set_progress(self, ratio: float):
        self.progress["value"] = max(0.0, min(100.0, ratio * 100.0))

    def reset(self):
        self.set_status("Ready")
        self.set_progress(0)
