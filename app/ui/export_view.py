import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from app.core.cancel import CancelToken
from app.models.entities import Novel
from app.ui.theme import configure_theme, background_color
from app.core.events import ProgressEvent
from app.ml.review import MLReviewController


class ExportFlowController:
    def __init__(self, app_main, novel: Novel):
        self.app = app_main
        self.root = app_main.root
        self.novel = novel
        self.service = app_main.service
        
        self.window = tk.Toplevel(self.root)
        configure_theme(self.window)
        self.window.title(f"Export Options - {novel.title}")
        self.window.geometry("680x600")
        self.window.configure(background=background_color())
        
        self.model_path_var = tk.StringVar(value="")
        self.filter_novel_var = tk.BooleanVar(value=True)
        self.audio_speed_var = tk.DoubleVar(value=1.0)
        self.audio_speed_display_var = tk.StringVar(value="1.0")
        
        def update_speed_display(*args):
            self.audio_speed_display_var.set(f"{self.audio_speed_var.get():.1f}")
            
        self.audio_speed_var.trace_add("write", update_speed_display)
        self.split_by_chapter_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Export Flow", font=("Segoe UI", 14, "bold")).pack(pady=(0, 15), anchor="w")
        
        # --- Step 1: Cleanup / Preprocessing ---
        prep_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        prep_frame.pack(fill="x", pady=5)
        
        ttk.Label(prep_frame, text="Step 1: Text Cleanup (Optional)", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 5))
        ttk.Label(prep_frame, text="Filter duplicated chapters or use ML prediction flows to remove non-novel text.", style="CardMeta.TLabel").pack(anchor="w", pady=(0, 10))
        
        ttk.Checkbutton(prep_frame, text="Filter duplicate chapters", variable=self.filter_novel_var).pack(anchor="w", pady=(0, 10))

        available, error = self.service.ml_is_available()
        
        prep_btns = ttk.Frame(prep_frame, style="Card.TFrame")
        prep_btns.pack(fill="x")
        
        if available:
            ttk.Button(prep_btns, text="Run ML Cleanup", style="Warning.TButton", command=self.on_run_ml_cleanup).pack(side="left", padx=(0, 10))
            self.ml_status_label = ttk.Label(prep_btns, text="ML Cleanup not run yet.", style="CardMeta.TLabel")
            self.ml_status_label.pack(side="left", pady=8)
        else:
            ttk.Label(prep_btns, text=f"ML Unavailable: {error}", foreground="red", wraplength=450, justify="left", style="CardMeta.TLabel").pack(anchor="w")

        # --- Step 2: Export Outputs ---
        output_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        output_frame.pack(fill="x", pady=20)
        
        ttk.Label(output_frame, text="Step 2: Generate Exports", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 5))
        ttk.Label(output_frame, text="Choose the format to export your novel.", style="CardMeta.TLabel").pack(anchor="w", pady=(0, 10))
        
        # TXT
        txt_frame = ttk.Frame(output_frame, style="Card.TFrame")
        txt_frame.pack(fill="x", pady=5)
        ttk.Label(txt_frame, text="Text Files (.txt)\nStandard offline viewing.", style="CardMeta.TLabel", justify="left").pack(side="left")
        ttk.Button(txt_frame, text="Export TXT", style="Accent.TButton", command=self.on_export_standard).pack(side="right", anchor="e")

        # Audio
        ttk.Separator(output_frame, orient="horizontal").pack(fill="x", pady=15)
        
        audio_frame = ttk.Frame(output_frame, style="Card.TFrame")
        audio_frame.pack(fill="x", pady=5)
        ttk.Label(audio_frame, text="Audiobook (.wav)\nSynthesized voice using Sherpa-ONNX.", style="CardMeta.TLabel", justify="left").pack(side="left")
        
        path_input_frame = ttk.Frame(output_frame, style="Card.TFrame")
        path_input_frame.pack(fill="x", pady=(15, 0))
        
        audio_options_frame = ttk.Frame(output_frame, style="Card.TFrame")
        audio_options_frame.pack(fill="x", pady=(10, 0))
        ttk.Checkbutton(audio_options_frame, text="Generate by chapter", variable=self.split_by_chapter_var).pack(side="left", padx=(0, 20))
        ttk.Label(audio_options_frame, text="Speed:", style="CardMeta.TLabel").pack(side="left")
        ttk.Label(audio_options_frame, textvariable=self.audio_speed_display_var, style="CardTitle.TLabel").pack(side="left", padx=(5, 0))
        ttk.Scale(audio_options_frame, from_=1.0, to=5.0, variable=self.audio_speed_var, orient="horizontal", length=200).pack(side="left", padx=(5, 5))
        
        ttk.Label(path_input_frame, text="Model Directory:", style="CardMeta.TLabel").pack(side="left", padx=(0, 5))
        ttk.Entry(path_input_frame, textvariable=self.model_path_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(path_input_frame, text="Browse", style="Secondary.TButton", command=self.browse_model_path).pack(side="left", padx=(0, 10))
        ttk.Button(path_input_frame, text="Export Audio", style="Accent.TButton", command=self.on_export_audio).pack(side="right")
        
    def browse_model_path(self):
        dir_path = filedialog.askdirectory(title="Locate extracted TTS Model folder")
        if dir_path:
            self.model_path_var.set(dir_path)

    # --- Actions ---
    
    def on_export_standard(self):
        self.window.destroy()
        novel = self._apply_duplicate_filter_if_needed(self.novel)
        def action(_cancel_token: CancelToken):
            outputs = self.service.export_novel(novel)
            self.root.after(0, lambda: messagebox.showinfo("Export complete", "\n".join(outputs)))
        self.app.run_in_thread(action, done_message="Export complete", task_name="export")

    def on_export_audio(self):
        model_path = self.model_path_var.get().strip()
        if not model_path or not os.path.isdir(model_path):
            messagebox.showwarning("Invalid Path", "Please select a valid Sherpa-ONNX model directory.")
            return

        self.window.destroy()
        novel = self._apply_duplicate_filter_if_needed(self.novel)
        def action(cancel_token: CancelToken):
            def progress(event: ProgressEvent):
                self.root.after(0, lambda: self.app.status_bar.set_status(event.message))
                self.root.after(0, lambda: self.app.status_bar.set_progress(event.ratio))

            try:
                outputs = self.service.export_audio(
                    novel, 
                    model_path, 
                    self.audio_speed_var.get(), 
                    self.split_by_chapter_var.get(), 
                    progress, 
                    cancel_token
                )
                self.root.after(0, lambda: messagebox.showinfo("Audio Export Details", "\n".join(outputs)))
            except Exception as e:
                self.root.after(0, lambda e=e: messagebox.showerror("Export Failed", str(e)))

        self.app.run_in_thread(action, done_message="Audio Export Complete", task_name="audio_export")

    def _apply_duplicate_filter_if_needed(self, novel: Novel) -> Novel:
        if self.filter_novel_var.get():
            return self.service.apply_duplicate_filter(novel)
        return novel

    def on_run_ml_cleanup(self):
        novel_dedup = self._apply_duplicate_filter_if_needed(self.novel)

        resp = messagebox.askyesno("Train Model", "Train model before prediction? (If unsure, click Yes).")
        
        if resp:
            def action(cancel_token: CancelToken):
                self.service.build_ml_training_data()
                self.service.train_ml_model(cancel_token=cancel_token)
                self.root.after(0, lambda: self._run_ml_prediction(novel_dedup))
            self.app.run_in_thread(action, done_message="Model training complete", task_name="ml training")
        else:
            self._run_ml_prediction(novel_dedup)

    def _run_ml_prediction(self, novel: Novel):
        self.prediction_window = tk.Toplevel(self.window)
        self.prediction_window.title("Run ML Model")
        self.prediction_window.geometry("400x120")
        self.prediction_window.configure(background=background_color())

        ttk.Label(self.prediction_window, text="Evaluating chapters...", font=("Segoe UI", 11)).pack(pady=10)
        self.prediction_label = ttk.Label(self.prediction_window, text="Ready", font=("Segoe UI", 10))
        self.prediction_label.pack(pady=5)
        
        def action(cancel_token: CancelToken):
            def progress(event: ProgressEvent):
                self.root.after(0, lambda: self.prediction_label.config(text=f"Predicting: {event.message} ({event.current}/{event.total})"))
                self.root.after(0, lambda: self.app.status_bar.set_status(event.message))
                self.root.after(0, lambda: self.app.status_bar.set_progress(event.ratio))

            predicted = self.service.run_ml_predictions(novel, progress_callback=progress, cancel_token=cancel_token)

            def after_prediction():
                self.prediction_window.destroy()
                self._review_flagged_sentences(predicted)

            self.root.after(0, after_prediction)

        self.app.run_in_thread(action, done_message="ML prediction finished", task_name="ml prediction")

    def _review_flagged_sentences(self, novel: Novel):
        controller = MLReviewController(self.root, novel, certainty_threshold=self.app.certainty_threshold, auto_remove_delay=self.app.auto_remove_delay)

        def on_finish():
            flagged_count = 0
            for chapter in novel.chapter_list:
                if chapter.prediction_df is not None and not chapter.prediction_df.empty:
                    flagged_count += int((chapter.prediction_df["Prediction"] == 1).sum())
            if flagged_count > 0:
                self.root.after(0, lambda: self.ml_status_label.config(text=f"ML Cleanup completed: Replaced {flagged_count} flagged sentences.", foreground="#4ADE80"))
            else:
                self.root.after(0, lambda: self.ml_status_label.config(text="ML Cleanup completed: No non-novel content found.", foreground="#CBD5E1"))
            
            def action(cancel_token: CancelToken):
                self.novel = self.service.finalize_ml_cleaning(novel, cancel_token=cancel_token)
            self.app.run_in_thread(action, done_message="ML cleanup applied.", task_name="ml finalize")

        controller.start(on_finish)
        controller.wait()
