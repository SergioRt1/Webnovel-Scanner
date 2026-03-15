from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.models.entities import Novel
from app.ui.theme import background_color


class MLReviewController:
    def __init__(self, root, novel: Novel, certainty_threshold: float = 0.98, auto_remove_delay: int = 1000):
        self.root = root
        self.novel = novel
        self.certainty_threshold = certainty_threshold
        self.auto_remove_delay = auto_remove_delay

        self.chapter_index = 0
        self.current_sentence_index = 0
        self.current_total_index = 0
        self.total_flags = 0
        self.auto_remove_enabled = True
        self.auto_remove_timer = None
        self.chapters_with_flags: list[tuple] = []

        self.window = tk.Toplevel(root)
        self.window.title("Review Flagged Sentences")
        self.window.geometry("950x520")
        self.window.configure(background=background_color())

        self._collect_flags()
        self._build_ui()

    def _collect_flags(self) -> None:
        for chapter in self.novel.chapter_list:
            df = chapter.prediction_df
            if df is None or df.empty:
                continue
            flagged_df = df[df["Prediction"] == 1]
            if not flagged_df.empty:
                self.total_flags += len(flagged_df)
                self.chapters_with_flags.append((chapter, flagged_df))

    def _build_ui(self) -> None:
        self.chapter_label = ttk.Label(self.window, text="", font=("Segoe UI", 12, "bold"))
        self.chapter_label.pack(pady=(14, 8))

        self.sentence_text = tk.Text(self.window, wrap="word", height=12, width=100, font=("Segoe UI", 11))
        self.sentence_text.pack(fill="both", expand=True, padx=16, pady=8)

        self.message_label = ttk.Label(self.window, text="", foreground="red")
        self.message_label.pack(pady=4)

        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save_sentence).pack(side="left", padx=8)
        ttk.Button(button_frame, text="Remove", command=self.remove_sentence).pack(side="left", padx=8)
        ttk.Button(button_frame, text="Stop Auto-Remove", command=self.stop_auto_remove).pack(side="left", padx=8)

        shortcuts = (
            "CTRL+S → Save   |   "
            "CTRL+D → Remove   |   "
            "CTRL+E / CTRL+SPACE → Stop Auto-Remove"
        )
        ttk.Label(self.window, text=shortcuts).pack(pady=(0, 10))

        self.window.bind("<Control-s>", lambda _event: self.save_sentence())
        self.window.bind("<Control-d>", lambda _event: self.remove_sentence())
        self.window.bind("<Control-e>", lambda _event: self.stop_auto_remove())
        self.window.bind("<Control-space>", lambda _event: self.stop_auto_remove())

    def has_flags(self) -> bool:
        return len(self.chapters_with_flags) > 0

    def start(self, on_finish) -> None:
        self.on_finish = on_finish
        if not self.has_flags():
            self._finish()
            return
        self.review_next_flagged_sentence()

    def review_next_flagged_sentence(self) -> None:
        if self.chapter_index >= len(self.chapters_with_flags):
            self._finish()
            return
        self.current_total_index += 1
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]

        if self.current_sentence_index >= len(flagged_df):
            self.chapter_index += 1
            self.current_sentence_index = 0
            self.review_next_flagged_sentence()
            return

        original_index = flagged_df.index[self.current_sentence_index]
        sentence = flagged_df.loc[original_index, "Sentence"]
        certainty = float(flagged_df.loc[original_index, "Certainty"])

        self.chapter_label.config(
            text=f"{chapter.title}   |   certainty={certainty:.4f}   |   chapter {self.current_sentence_index + 1}/{len(flagged_df)}   |   total {self.current_total_index}/{self.total_flags}"
        )
        self.sentence_text.delete("1.0", "end")
        self.sentence_text.insert("1.0", sentence)

        if certainty > self.certainty_threshold and self.auto_remove_enabled:
            self.message_label.config(text="High certainty flag detected. Auto-remove scheduled.")
            self.auto_remove_timer = self.root.after(self.auto_remove_delay, self.auto_remove_sentence)
        else:
            self.message_label.config(text="")

    def save_sentence(self) -> None:
        self._cancel_timer()
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
        original_index = flagged_df.index[self.current_sentence_index]
        edited_sentence = self.sentence_text.get("1.0", "end-1c")
        chapter.prediction_df.loc[original_index, "Sentence"] = edited_sentence
        self.current_sentence_index += 1
        self.review_next_flagged_sentence()

    def remove_sentence(self) -> None:
        self._cancel_timer()
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
        original_index = flagged_df.index[self.current_sentence_index]
        chapter.prediction_df.loc[original_index, "Sentence"] = ""
        self.current_sentence_index += 1
        self.review_next_flagged_sentence()

    def auto_remove_sentence(self) -> None:
        if self.auto_remove_enabled:
            self.remove_sentence()

    def stop_auto_remove(self) -> None:
        self.auto_remove_enabled = False
        self._cancel_timer()
        self.message_label.config(text="Auto-remove stopped for the rest of this review.")

    def _cancel_timer(self) -> None:
        if self.auto_remove_timer is not None:
            self.root.after_cancel(self.auto_remove_timer)
            self.auto_remove_timer = None

    def _finish(self) -> None:
        self._cancel_timer()
        self.window.destroy()
        self.on_finish()

    def wait(self) -> None:
        try:
            if self.window.winfo_exists():
                self.window.grab_set()
                self.window.wait_window()
        except tk.TclError:
            pass
