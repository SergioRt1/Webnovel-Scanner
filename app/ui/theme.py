from __future__ import annotations

from tkinter import ttk

bg = "#111827"
card = "#1F2937"
text = "#E5E7EB"
white = "#F9FAFB"
muted = "#9CA3AF"
status_bg = "#0F172A"

primary = "#2563EB"
primary_active = "#1D4ED8"
success = "#16A34A"
success_active = "#15803D"
warning = "#D97706"
warning_active = "#B45309"
danger = "#DC2626"
danger_active = "#B91C1C"
secondary = "#334155"
secondary_active = "#1E293B"


def configure_theme(root) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 11))
    style.configure("Header.TLabel", background=bg, font=("Segoe UI Semibold", 20), foreground=white)
    style.configure("SubHeader.TLabel", background=bg, font=("Segoe UI", 10), foreground=muted)

    style.configure(
        "TButton",
        font=("Segoe UI", 10),
        padding=8,
        background=secondary,
        foreground=white,
        borderwidth=0,
        focusthickness=0,
    )
    style.map(
        "TButton",
        background=[("active", secondary_active), ("pressed", secondary_active), ("disabled", "#374151")],
        foreground=[("disabled", "#9CA3AF")],
    )

    style.configure(
        "Accent.TButton",
        font=("Segoe UI Semibold", 10),
        padding=9,
        background=primary,
        foreground=white,
        borderwidth=0,
        focusthickness=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", primary_active), ("pressed", primary_active), ("disabled", "#60A5FA")],
        foreground=[("disabled", white)],
    )

    style.configure("Success.TButton", font=("Segoe UI Semibold", 10), padding=9, background=success, foreground=white, borderwidth=0)
    style.map("Success.TButton", background=[("active", success_active), ("pressed", success_active), ("disabled", "#4ADE80")])

    style.configure("Warning.TButton", font=("Segoe UI Semibold", 10), padding=9, background=warning, foreground=white, borderwidth=0)
    style.map("Warning.TButton", background=[("active", warning_active), ("pressed", warning_active), ("disabled", "#FBBF24")])

    style.configure("Danger.TButton", font=("Segoe UI Semibold", 10), padding=9, background=danger, foreground=white, borderwidth=0)
    style.map("Danger.TButton", background=[("active", danger_active), ("pressed", danger_active), ("disabled", "#823E3E")])

    style.configure("Secondary.TButton", font=("Segoe UI Semibold", 10), padding=9, background=secondary, foreground=white, borderwidth=0)
    style.map("Secondary.TButton", background=[("active", secondary_active), ("pressed", secondary_active), ("disabled", "#64748B")])

    style.configure("Card.TFrame", background=card)
    style.configure("CardTitle.TLabel", background=card, foreground=white, font=("Segoe UI Semibold", 11))
    style.configure("CardMeta.TLabel", background=card, foreground=muted, font=("Segoe UI", 9))
    style.configure("Status.TLabel", background=status_bg, foreground="#CBD5E1")
    style.configure("Horizontal.TProgressbar", background=primary, troughcolor="#C2D6ED", thickness=16)
    style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
    style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))

    style.configure("TCheckbutton", background=bg, font=("Segoe UI Semibold", 10), foreground=white)
    style.map("TCheckbutton", background=[("active", secondary_active), ("pressed", secondary_active)])

    return style

def background_color():
    return bg
