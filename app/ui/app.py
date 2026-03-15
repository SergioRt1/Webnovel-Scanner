from __future__ import annotations

import os
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from app.config import APP_GEOMETRY, APP_MIN_SIZE, APP_NAME, ICON_PATH, PLACEHOLDER_IMAGE
from app.core.cancel import EventToken, NoopToken, CancelToken, TaskCancelledError
from app.core.events import ProgressEvent
from app.core.service import NovelService
from app.ml.review import MLReviewController
from app.models.entities import Novel
from app.ui.theme import configure_theme, background_color
from app.ui.widgets import ScrollableFrame, StatusBar


class NovelApp:
    def __init__(self, service: NovelService):
        self.service = service
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(APP_GEOMETRY)
        self.root.minsize(*APP_MIN_SIZE)
        if Path(ICON_PATH).exists():
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=ICON_PATH))
            except Exception:
                pass

        self.style = configure_theme(self.root)
        self.busy = False
        self.current_novel: Novel | None = None
        self.novels: list[Novel] = []
        self.filtered_novels: list[Novel] = []
        self.cover_image = None
        self.current_cancel_token: EventToken = NoopToken()
        self.current_task_name = ""

        self.auto_remove_delay = 1000
        self.certainty_threshold = 0.98

        self._build_layout()
        self._load_initial_data()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self._build_top_bar()
        self._build_content()
        self._build_status_bar()

    def _build_top_bar(self) -> None:
        top = ttk.Frame(self.root, padding=(16, 16, 16, 10))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Novel Downloader 2.0", style="Header.TLabel").grid(row=0, column=0, columnspan=8, sticky="w")
        ttk.Label(top, text="Find, download, organize and export webnovels.", style="SubHeader.TLabel").grid(row=1, column=0, columnspan=8, sticky="w", pady=(2, 12))

        ttk.Label(top, text="Novel URL").grid(row=2, column=0, sticky="w", padx=(0, 7))
        self.search_entry = ttk.Entry(top)
        self.search_entry.grid(row=2, column=1, sticky="ew", padx=(0, 7))
        self.search_entry.bind("<Return>", lambda _event: self.on_search())

        self.site_combo = ttk.Combobox(top, values=self.service.browser.get_registered_websites(), state="readonly", width=18)
        self.site_combo.grid(row=2, column=2, sticky="ew", padx=(0, 7))
        self.site_combo.current(0)

        ttk.Button(top, text="Search", style="Accent.TButton", command=self.on_search).grid(row=2, column=3, padx=(0, 7))
        ttk.Button(top, text="Refresh Library", style="Secondary.TButton", command=self.reload_library).grid(row=2, column=4, padx=(0, 7))
        ttk.Button(top, text="Open Export Folder", style="Secondary.TButton", command=self.open_export_hint).grid(row=2, column=5, padx=(0, 7))
        self.cancel_button = ttk.Button(top, text="Cancel Current Task", style="Danger.TButton", command=self.cancel_current_task)
        self.cancel_button.grid(row=2, column=6, padx=(0, 7))
        self.cancel_button.state(["disabled"])

    def _build_content(self) -> None:
        content = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(1, weight=1)

        left_card = ttk.Frame(content, style="Card.TFrame", padding=12)
        left_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        left_card.columnconfigure(0, weight=1)
        left_card.rowconfigure(2, weight=1)

        ttk.Label(left_card, text="Library", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.filter_entry = ttk.Entry(left_card)
        self.filter_entry.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        self.filter_entry.bind("<KeyRelease>", lambda _event: self.apply_library_filter())

        self.library = ScrollableFrame(left_card, style="Card.TFrame")
        self.library.grid(row=2, column=0, sticky="nsew")

        right_card = ttk.Frame(content, style="Card.TFrame", padding=14)
        right_card.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right_card.columnconfigure(1, weight=1)
        right_card.rowconfigure(1, weight=1)

        self.cover_label = ttk.Label(right_card, text="No cover", style="CardMeta.TLabel")
        self.cover_label.grid(row=0, column=0, rowspan=4, sticky="nw", padx=(0, 16))

        self.title_label = ttk.Label(right_card, text="Select a novel", style="CardTitle.TLabel")
        self.title_label.grid(row=0, column=1, sticky="w")

        self.meta_label = ttk.Label(right_card, text="", style="CardMeta.TLabel", justify="left")
        self.meta_label.grid(row=1, column=1, sticky="nw")

        self.desc_text = tk.Text(right_card, wrap="word", height=18, bg="#1F2937", fg="#E5E7EB", relief="flat", font=("Segoe UI", 10))
        self.desc_text.grid(row=2, column=1, sticky="nsew", pady=(12, 12))
        self.desc_text.config(state="disabled")

        actions = ttk.Frame(right_card, style="Card.TFrame")
        actions.grid(row=3, column=1, sticky="ew")
        ttk.Button(actions, text="Download Missing Chapters", style="Accent.TButton", command=self.on_download).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export", style="Secondary.TButton", command=self.on_export).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export with ML", style="Secondary.TButton", command=self.on_export_with_ml).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Delete", style="Danger.TButton", command=self.on_delete).pack(side="left")

    def _build_status_bar(self) -> None:
        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _load_initial_data(self) -> None:
        self.novels = self.service.get_downloaded_novels()
        self.apply_library_filter()

    def reload_library(self) -> None:
        self.novels = self.service.get_downloaded_novels()
        self.apply_library_filter()
        self.status_bar.set_status("Library refreshed")

    def apply_library_filter(self) -> None:
        query = self.filter_entry.get().strip().lower()
        if not query:
            self.filtered_novels = sorted(self.novels, key=lambda n: n.title.lower())
        else:
            self.filtered_novels = [
                novel for novel in self.novels
                if query in novel.title.lower() or query in novel.author.lower() or query in novel.website.lower()
            ]
        self.render_library()

    def render_library(self) -> None:
        for widget in self.library.inner.winfo_children():
            widget.destroy()

        for row, novel in enumerate(self.filtered_novels):
            text = f"{novel.title}\n{novel.author} • {novel.website} • {novel.progress_text}"
            btn = tk.Button(
                self.library.inner,
                text=text,
                justify="left",
                anchor="w",
                bg="#111827" if self.current_novel != novel else "#1D4ED8",
                fg="#F9FAFB",
                relief="flat",
                padx=12,
                pady=10,
                wraplength=360,
                command=lambda n=novel: self.select_novel(n),
            )
            btn.grid(row=row, column=0, sticky="ew", pady=4)
            self.library.inner.columnconfigure(0, weight=1)

    def select_novel(self, novel: Novel) -> None:
        self.current_novel = novel
        self.render_library()
        self.title_label.config(text=novel.title)
        self.meta_label.config(
            text=(
                f"Author: {novel.author}\n"
                f"Website: {novel.website}\n"
                f"Progress: {novel.progress_text}\n"
                f"Source URL: {novel.url}"
            )
        )
        self.desc_text.config(state="normal")
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", novel.desc or "No description available.")
        self.desc_text.config(state="disabled")
        self._render_cover(novel)

    def _render_cover(self, novel: Novel) -> None:
        image_path = Path(novel.image_path) if novel.image_path else Path(PLACEHOLDER_IMAGE)
        if not image_path.exists():
            image_path = Path(PLACEHOLDER_IMAGE)
        try:
            image = Image.open(image_path)
            image = ImageOps.contain(image, (240, 320))
            self.cover_image = ImageTk.PhotoImage(image)
            self.cover_label.config(image=self.cover_image, text="")
        except Exception:
            self.cover_label.config(image="", text="No cover")

    def set_busy(self, busy: bool, status: str = "Working...", task_name: str = "") -> None:
        self.busy = busy
        self.current_task_name = task_name if busy else ""
        self.status_bar.set_status(status)
        if busy:
            self.cancel_button.state(["!disabled"])
        else:
            self.cancel_button.state(["disabled"])
            self.status_bar.set_progress(0)
            self.current_cancel_token = None

    def cancel_current_task(self) -> None:
        if self.current_cancel_token and not self.current_cancel_token.is_cancelled:
            self.current_cancel_token.cancel()
            self.status_bar.set_status(f"Cancelling {self.current_task_name or 'task'}...")

    def run_in_thread(self, action, done_message: str | None = None, task_name: str = "task"):
        if self.busy:
            return

        cancel_token = CancelToken()
        self.current_cancel_token = cancel_token
        self.set_busy(True, status=f"Starting {task_name}...", task_name=task_name)

        def worker():
            try:
                action(cancel_token)
                if done_message:
                    self.root.after(0, lambda: self.status_bar.set_status(done_message))
            except TaskCancelledError:
                self.root.after(0, lambda: self.status_bar.set_status(f"{task_name.capitalize()} cancelled"))
            except Exception as exc:
                error_msg = str(exc)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
                self.root.after(0, lambda msg=error_msg: self.status_bar.set_status(msg))
            finally:
                self.root.after(0, lambda: self.set_busy(False, self.status_bar.label.cget("text")))

        threading.Thread(target=worker, daemon=True).start()

    def on_search(self) -> None:
        url = self.search_entry.get().strip()
        website = self.site_combo.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a novel URL.")
            return

        def action(cancel_token: CancelToken):
            novel = self.service.search_novel(url, website, cancel_token=cancel_token)
            self.novels = self.service.get_downloaded_novels()
            self.root.after(0, self.apply_library_filter)
            self.root.after(0, lambda: self.select_novel(novel))

        self.run_in_thread(action, done_message="Novel loaded", task_name="search")

    def _handle_progress(self, event: ProgressEvent) -> None:
        self.root.after(0, lambda: self.status_bar.set_status(event.message))
        self.root.after(0, lambda: self.status_bar.set_progress(event.ratio))

    def on_download(self) -> None:
        if not self.current_novel:
            messagebox.showinfo("Select a novel", "Choose a novel first.")
            return

        def action(cancel_token: CancelToken):
            updated = self.service.download_novel(self.current_novel, progress_callback=self._handle_progress, cancel_token=cancel_token)
            self.current_novel = updated
            self.novels = self.service.get_downloaded_novels()
            self.root.after(0, self.apply_library_filter)
            self.root.after(0, lambda: self.select_novel(updated))

        self.run_in_thread(action, done_message="Download finished", task_name="download")

    def on_export(self) -> None:
        if not self.current_novel:
            messagebox.showinfo("Select a novel", "Choose a novel first.")
            return

        def action(_cancel_token: CancelToken):
            outputs = self.service.export_novel(self.current_novel)
            self.root.after(0, lambda: messagebox.showinfo("Export complete", "\n".join(outputs)))

        self.run_in_thread(action, done_message="Export complete", task_name="export")

    def on_open_ml_tools(self) -> None:
        if not self.current_novel:
            messagebox.showinfo("Select a novel", "Choose a novel first.")
            return
        self._open_ml_window(self.current_novel)

    def on_export_with_ml(self) -> None:
        if not self.current_novel:
            messagebox.showinfo("Select a novel", "Choose a novel first.")
            return
        self._open_ml_window(self.current_novel)

    def _open_ml_window(self, novel: Novel) -> None:
        available, error = self.service.ml_is_available()

        self.ml_window = tk.Toplevel(self.root)
        configure_theme(self.ml_window)
        self.ml_window.title("ML Processor Options")
        self.ml_window.geometry("460x320")
        self.ml_window.configure(background=background_color())

        self.filter_novel_var = tk.BooleanVar(value=True)

        ttk.Label(self.ml_window, text="Optional ML cleanup flow for non-novel content.", font=("Segoe UI", 11, "bold")).pack(pady=(16, 8))
        ttk.Checkbutton(self.ml_window, text="Filter duplicate chapters before ML", variable=self.filter_novel_var).pack(pady=6)
        ttk.Button(self.ml_window, text="Open Non-Novel Content", style="Secondary.TButton", command=self.open_non_novel_content).pack(pady=6)
        ttk.Button(self.ml_window, text="Open Novel-Like Content", style="Secondary.TButton", command=self.open_novel_like_content).pack(pady=6)

        if available:
            ttk.Button(self.ml_window, text="Train Model", style="Warning.TButton", command=lambda: self.train_model_and_continue(novel)).pack(pady=6)
            ttk.Button(self.ml_window, text="Skip Training", style="Accent.TButton", command=lambda: self.show_prediction_view(novel)).pack(pady=6)
        else:
            ttk.Label(self.ml_window, text=error, foreground="red", wraplength=420, justify="left").pack(padx=12, pady=12)

    def _apply_duplicate_filter_if_needed(self, novel: Novel) -> Novel:
        if self.filter_novel_var.get():
            return self.service.apply_duplicate_filter(novel)
        return novel

    def train_model_and_continue(self, novel: Novel) -> None:
        novel = self._apply_duplicate_filter_if_needed(novel)

        def action(cancel_token: CancelToken):
            self.service.build_ml_training_data()
            self.service.train_ml_model(cancel_token=cancel_token)
            self.root.after(0, lambda: messagebox.showinfo("Training Complete", "The model has been trained successfully."))
            self.root.after(0, lambda: self.show_prediction_view(novel))

        self.run_in_thread(action, done_message="Model training complete", task_name="ml training")

    def show_prediction_view(self, novel: Novel) -> None:
        novel_dedup = self._apply_duplicate_filter_if_needed(novel)
        self.root.after(0, self.ml_window.destroy)

        self.prediction_window = tk.Toplevel(self.root)
        self.prediction_window.title("Run ML Model")
        self.prediction_window.geometry("800x220")
        self.prediction_window.configure(background=background_color())

        ttk.Label(self.prediction_window, text="Evaluate all chapters using the ML model", font=("Segoe UI", 12)).pack(pady=20)
        self.prediction_label = ttk.Label(self.prediction_window, text="Ready", font=("Segoe UI", 11))
        self.prediction_label.pack(pady=10)
        ttk.Button(self.prediction_window, text="Run Model", style="Warning.TButton", command=lambda: self.run_model(novel_dedup)).pack(pady=6)
        ttk.Button(self.prediction_window, text="Skip Model Evaluation", style="Secondary.TButton", command=lambda: self.skip_prediction(novel_dedup)).pack(pady=6)

    def run_model(self, novel: Novel) -> None:
        def action(cancel_token: CancelToken):
            def progress(event: ProgressEvent):
                self.root.after(0, lambda: self.prediction_label.config(text=f"Predicting: {event.message} ({event.current}/{event.total})"))
                self._handle_progress(event)

            predicted = self.service.run_ml_predictions(novel, progress_callback=progress, cancel_token=cancel_token)

            def after_prediction():
                self.prediction_window.destroy()
                self.review_flagged_sentences(predicted)

            self.root.after(0, after_prediction)

        self.run_in_thread(action, done_message="ML prediction finished", task_name="ml prediction")

    def review_flagged_sentences(self, novel: Novel) -> None:
        controller = MLReviewController(self.root, novel, certainty_threshold=self.certainty_threshold, auto_remove_delay=self.auto_remove_delay)

        def on_finish():
            def action(cancel_token: CancelToken):
                cleaned = self.service.finalize_ml_cleaning(novel, cancel_token=cancel_token)
                outputs = self.service.export_novel(cleaned)
                flagged_count = 0
                for chapter in novel.chapter_list:
                    if chapter.prediction_df is not None and not chapter.prediction_df.empty:
                        flagged_count += int((chapter.prediction_df["Prediction"] == 1).sum())
                if flagged_count > 0:
                    message = "Filtered novel saved successfully.\n\n" + "\n".join(outputs)
                else:
                    message = "No non-novel content found. Novel saved successfully.\n\n" + "\n".join(outputs)
                self.root.after(0, lambda: messagebox.showinfo("Process Complete", message))

            self.run_in_thread(action, done_message="ML cleanup finished", task_name="ML cleanup")

        controller.start(on_finish)
        controller.wait()

    def skip_prediction(self, novel: Novel) -> None:
        self.prediction_window.destroy()

        def action(_cancel_token: CancelToken):
            outputs = self.service.export_novel(novel)
            self.root.after(0, lambda: messagebox.showinfo("Process Complete", "Novel saved successfully.\n\n" + "\n".join(outputs)))

        self.run_in_thread(action, done_message="Novel exported without ML cleanup", task_name="export")

    def open_non_novel_content(self) -> None:
        self.open_text_file("./ml_data/non-novel.txt")

    def open_novel_like_content(self) -> None:
        self.open_text_file("./ml_data/novel-like.txt")

    def open_text_file(self, file_path: str) -> None:
        if os.path.exists(file_path):
            webbrowser.open("file://" + os.path.realpath(file_path))
        else:
            messagebox.showerror("Error", "Content file not found.")

    def on_delete(self) -> None:
        if not self.current_novel:
            messagebox.showinfo("Select a novel", "Choose a novel first.")
            return
        if not messagebox.askyesno("Delete novel", f"Delete '{self.current_novel.title}' from the local library?"):
            return

        title = self.current_novel.title
        success = self.service.delete_novel(title)
        if success:
            self.current_novel = None
            self.reload_library()
            self.title_label.config(text="Select a novel")
            self.meta_label.config(text="")
            self.desc_text.config(state="normal")
            self.desc_text.delete("1.0", "end")
            self.desc_text.config(state="disabled")
            self.cover_label.config(image="", text="No cover")
            self.status_bar.set_status(f"Deleted {title}")

    def open_export_hint(self) -> None:
        messagebox.showinfo("Export folder", "Your exports are stored in the 'Novels' folder next to the project.")

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        try:
            if self.current_cancel_token and not self.current_cancel_token.is_cancelled:
                self.current_cancel_token.cancel()
            self.service.close()
        finally:
            self.root.destroy()
