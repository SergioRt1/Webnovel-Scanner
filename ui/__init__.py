import threading
import tkinter as tk
from functools import wraps
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
from logic.filter import ContentFilter
from logic.novel_downloader import NovelDownloader
from logic.websites import get_website_ids
from utils import constants
from ml_processor.train_model import train
from ml_processor.labeler import build_training_data
from ml_processor import prediction
import os
import webbrowser


def threaded_task(task):
    @wraps(task)
    def wrapper(self, *args, **kwargs):
        self.show_loader()

        def inner_task():
            try:
                task(self, *args, **kwargs)
            finally:
                self.root.after(0, self.hide_loader)

        threading.Thread(target=inner_task).start()

    return wrapper


class NovelUI:
    def __init__(self, downloader: NovelDownloader, content_filter: ContentFilter):
        self.downloader = downloader
        self.filter = content_filter

        # Setup main window
        self.root = tk.Tk()
        self.root.title("Novel Downloader")
        self.root.geometry("1100x1080")

        self.setup_styles()
        self.setup_loader()
        self.setup_widgets()
        self.setup_constants()

        self.downloaded_novels = self.downloader.get_downloaded_novels()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def setup_styles(self):
        self.style = ttk.Style(self.root)
        self.style.configure('TButton', font=('Arial', 12))
        self.style.map('TButton',
                       background=[('disabled', 'gray'), ('active', 'lightblue')],
                       foreground=[('disabled', 'darkgray')])
        self.style.configure('TLabel', font=('Arial', 12))

    def setup_loader(self):
        loader_image = Image.open(constants.loader_image)
        self.loader_frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(loader_image)]
        self.loader_label = tk.Label(self.root, image=self.loader_frames[0])

    def setup_widgets(self):
        self._add_search_bar()
        self._add_books_list_and_details_frame()
        self._add_book_details_frame()

    def setup_constants(self):
        self.auto_remove_delay = 1000
        self.certainty_threshold = 0.998

    def _add_search_bar(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=10, fill='x', padx=30)

        ttk.Label(frame, text="Link Main Page").grid(row=0, column=0, padx=15, pady=5)

        self.search_entry = ttk.Entry(frame, width=50, font=('Arial', 12))
        self.search_entry.grid(row=0, column=1, padx=15, pady=5)
        self.search_entry.bind('<Return>', self.perform_search)

        websites = get_website_ids()
        self.search_option = ttk.Combobox(frame, values=websites, font=('Arial', 12), state="readonly", width=30)
        self.search_option.current(0)
        self.search_option.grid(row=0, column=2)

    def clear_current_book_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def display_books(self, book_list):
        for i, novel in enumerate(book_list):
            button = ttk.Button(self.scrollable_frame, text=novel.title,
                                command=lambda n=novel: self._add_book_image_and_details(n))
            button.grid(row=i, column=0, pady=5, padx=5, sticky='ew')

    def show_loader(self):
        loader_image = Image.open(constants.loader_image)
        self.loader_frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(loader_image)]
        self.loader_label = tk.Label(self.root, image=self.loader_frames[0])

        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        loader_width = self.loader_frames[0].width()
        loader_height = self.loader_frames[0].height()

        x_pos = (window_width - loader_width) // 2
        y_pos = (window_height - loader_height) // 2

        self.loader_label.place(x=x_pos, y=y_pos)
        self.loader_index = 0
        self.update_loader()

    def update_loader(self):
        self.loader_index = (self.loader_index + 1) % len(self.loader_frames)
        frame = self.loader_frames[self.loader_index]
        self.loader_label.configure(image=frame)
        self.loader_task_id = self.root.after(35, self.update_loader)

    def hide_loader(self):
        if hasattr(self, 'loader_label'):
            self.loader_label.place_forget()
            self.loader_label.destroy()
            if hasattr(self, 'loader_task_id'):
                self.root.after_cancel(self.loader_task_id)
            # Clean up loader frames to free memory
            del self.loader_frames
            del self.loader_label

    @threaded_task
    def perform_search(self, event=None):
        novel_url = self.search_entry.get()
        selected_website = self.search_option.get()

        search_results = self.downloader.search_novel(novel_url, selected_website)

        def update_gui():
            self.clear_current_book_list()
            self.display_books(search_results)
        self.root.after(0, update_gui)

    def _add_books_list_and_details_frame(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=10, fill='both', expand=True, padx=20, side='left')

        self.canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.bind('<Configure>',
                         lambda e: self.canvas.itemconfig("window", width=e.width))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw', tags="window")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_frame.columnconfigure(0, weight=1)
        self.display_books(self.downloader.novels)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _add_book_details_frame(self):
        self.details_frame = ttk.Frame(self.root)
        self.details_frame.pack(pady=10, fill='both', expand=True, padx=20, side='right')

    def export_novel(self, novel):
        self.ml_window = tk.Toplevel(self.root)
        self.ml_window.title("ML Processor Options")
        self.ml_window.geometry("400x200")

        ttk.Button(self.ml_window, text="Open Non-Novel Content", command=self.open_non_novel_content).pack(pady=5)
        ttk.Button(self.ml_window, text="Open Novel-Like Content", command=self.open_novel_like_content).pack(pady=5)
        ttk.Button(self.ml_window, text="Train Model", command=lambda: self.train_model(novel)).pack(pady=5)
        ttk.Button(self.ml_window, text="Skip Training", command=lambda: self.skip_training(novel)).pack(pady=5)

    ################ ML Functions ##########################
    @threaded_task
    def train_model(self, novel):
        build_training_data()
        train()
        def after_training():
            tk.messagebox.showinfo("Training Complete", "The model has been trained successfully.")
            self.ml_window.destroy()
            self.show_prediction_view(novel)
        self.root.after(0, after_training)

    def skip_training(self, novel):
        self.ml_window.destroy()
        self.show_prediction_view(novel)

    def show_prediction_view(self, novel):
        self.prediction_window = tk.Toplevel(self.root)
        self.prediction_window.title("Run ML Model")
        self.prediction_window.geometry("800x150")

        ttk.Button(self.prediction_window, text="Run Model", command=lambda: self.run_model(novel)).pack(pady=5)
        self.prediction_label = tk.Label(self.prediction_window, text="Starting predictions...", font=("Arial", 12))
        self.prediction_label.pack(pady=20)

    @threaded_task
    def run_model(self, novel):
        model, tokenizer = prediction.load_model()
        total_chapters = len(novel.chapter_list)
        for i, chapter in enumerate(novel.chapter_list, start=1):
            def update_label(chapter_title=chapter.title, i=i):
                self.prediction_label.config(text=f'Predicting: {chapter_title}\n({i}/{total_chapters})')
            self.root.after(0, update_label)

            print(f'Predicting: {chapter.title}')
            chapter.df = prediction.predict(model, tokenizer, chapter.content)
            
            print("\033[A\r\033[K", end='')  # Delete a line in the CLI, Move up one line, clear the line
            print("\033[A\r\033[K", end='')
            print("\033[A\r\033[K", end='')
            i += 1
        def after_prediction():
            self.prediction_window.destroy()
            self.review_flagged_sentences(novel)
        self.root.after(0, after_prediction)

    def review_flagged_sentences(self, novel):
        self.novel = novel
        self.chapter_index = 0
        self.current_sentence_index = 0
        self.chapters_with_flags = []

        for chapter in novel.chapter_list:
            flagged_df = chapter.df[chapter.df['Prediction'] == 1]
            if not flagged_df.empty:
                self.chapters_with_flags.append((chapter, flagged_df))

        self.init_review_window()
        self.review_next_flagged_sentence()

    def init_review_window(self):
        self.review_window = tk.Toplevel(self.root)
        self.review_window.title("Review Flagged Sentences")

        self.chapter_label = tk.Label(self.review_window, text="", font=("Arial", 12, "bold"))
        self.chapter_label.pack(pady=5)

        self.sentence_text = tk.Text(self.review_window, wrap=tk.WORD, height=10, width=80)
        self.sentence_text.pack(pady=10)

        self.message_label = tk.Label(self.review_window, text="", font=("Arial", 10, "italic"), fg="red")
        self.message_label.pack(pady=5)

        button_frame = ttk.Frame(self.review_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save_sentence).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Remove", command=self.remove_sentence).pack(side='right', padx=10)
        ttk.Button(button_frame, text="Stop Auto-Remove", command=self.stop_auto_remove).pack(side='left', padx=10)

        # Bind key events
        self.review_window.bind('<Control-s>', lambda event: self.save_sentence())
        self.review_window.bind('<Control-d>', lambda event: self.remove_sentence())
        self.review_window.bind('<Control-e>', lambda event: self.stop_auto_remove())
        self.review_window.bind('<Control-Space>', lambda event: self.stop_auto_remove())

    def review_next_flagged_sentence(self):
        if self.chapter_index < len(self.chapters_with_flags):
            chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
            if self.current_sentence_index < len(flagged_df):
                original_index = flagged_df.index[self.current_sentence_index]
                sentence, certainty = flagged_df.loc[original_index, ['Sentence', 'Certainty']]
                self.display_flagged_sentence(sentence, certainty, chapter.title)
                if certainty > self.certainty_threshold and self.auto_remove_enabled:
                    self.auto_remove_timer = self.root.after(self.auto_remove_delay, self.auto_remove_sentence)
            else:
                self.chapter_index += 1
                self.current_sentence_index = 0
                self.review_next_flagged_sentence()
        else:
            self.finalize_cleaned_novel()

    def display_flagged_sentence(self, sentence, certainty, chapter_title):
        self.auto_remove_enabled = True
        self.chapter_label.config(text=f"Chapter: {chapter_title}\n({self.chapter_index+1}/{len(self.chapters_with_flags)})\nCertainty: {certainty:.4%}")
        self.sentence_text.delete('1.0', 'end')
        self.sentence_text.insert('1.0', sentence)
        if certainty > self.certainty_threshold and self.auto_remove_enabled:
            self.message_label.config(text="This sentence will be automatically removed in a second.")
        else:
            self.message_label.config(text="")

    def save_sentence(self):
        if hasattr(self, 'auto_remove_timer'):
            self.root.after_cancel(self.auto_remove_timer)
            del self.auto_remove_timer
        edited_sentence = self.sentence_text.get('1.0', 'end-1c')
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
        original_index = flagged_df.index[self.current_sentence_index]
        chapter.df.loc[original_index, 'Sentence'] = edited_sentence
        self.current_sentence_index += 1
        self.review_next_flagged_sentence()

    def remove_sentence(self):
        if hasattr(self, 'auto_remove_timer'):
            self.root.after_cancel(self.auto_remove_timer)
            del self.auto_remove_timer
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
        original_index = flagged_df.index[self.current_sentence_index]
        chapter.df.loc[original_index, 'Sentence'] = ''
        self.current_sentence_index += 1
        self.review_next_flagged_sentence()

    def auto_remove_sentence(self):
        if self.auto_remove_enabled:
            self.remove_sentence()

    def stop_auto_remove(self):
        self.auto_remove_enabled = False
        if hasattr(self, 'auto_remove_timer'):
            self.root.after_cancel(self.auto_remove_timer)
            del self.auto_remove_timer
        self.message_label.config(text="")

    def finalize_cleaned_novel(self):
        for chapter in self.novel.chapter_list:
            sentences = chapter.df['Sentence'].tolist()
            chapter.content = ' '.join(sentences)
        self.review_window.destroy()
        self.downloader.write_novel(self.novel)
        tk.messagebox.showinfo("Process Complete", "Filtered novel saved successfully.")


    def open_non_novel_content(self):
        self.open_text_file("./ml_data/non-novel.txt")

    def open_novel_like_content(self):
        self.open_text_file("./ml_data/novel-like.txt")

    def open_text_file(self, file_path):
        if os.path.exists(file_path):
            webbrowser.open('file://' + os.path.realpath(file_path))
        else:
            tk.messagebox.showerror("Error", "Content file not found.")

    ################ ML Functions - END ####################

    @threaded_task
    def download_novel(self, novel):
        success = self.downloader.download_novel(novel)
        if success:
            self.downloaded_novels.add(novel.title)
            def update_gui():
                self._add_book_image_and_details(novel)
            self.root.after(0, update_gui)

    @threaded_task
    def delete_novel(self, novel):
        success = self.downloader.delete_novel(novel)
        if success:
            def update_gui():
                self.downloader.sync_novels()
                self.clear_current_book_list()
                self.display_books(self.downloader.novels)
                self.destroy_details_section()
            self.root.after(0, update_gui)

    def _add_book_image_and_details(self, novel):
        self.destroy_details_section()

        image = Image.open(novel.get_image_path())
        image = image.resize((300, 400), Image.LANCZOS)
        self.book_image = ImageTk.PhotoImage(image)

        ttk.Label(self.details_frame, image=self.book_image).grid(row=0, column=0, columnspan=2, pady=20)
        ttk.Label(self.details_frame, text=novel.title, font=('Arial', 16, 'bold')).grid(row=1, column=0, columnspan=2)

        self.book_desc_text = tk.Text(self.details_frame, wrap=tk.WORD, height=20, width=65)
        self.book_desc_text.insert(tk.END, novel.desc)
        self.book_desc_text.grid(row=2, column=0, columnspan=2, pady=10)

        scrollbar = ttk.Scrollbar(self.details_frame, command=self.book_desc_text.yview)
        scrollbar.grid(row=2, column=2, sticky='ns')
        self.book_desc_text['yscrollcommand'] = scrollbar.set

        ttk.Label(self.details_frame,
                  text=f"Chapters Downloaded: {len(novel.downloaded_set)}/{len(novel.chapter_list)}",
                  background='#EAFAF1').grid(row=3, column=0, columnspan=2, pady=10)

        button_frame = ttk.Frame(self.details_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=5)

        export_button = ttk.Button(button_frame, text="Export", command=lambda: self.export_novel(novel))
        if novel.is_new():
            export_button.config(state=tk.DISABLED)
        export_button.grid(row=0, column=0, padx=5, pady=5)

        download_button = ttk.Button(button_frame, text="Download", command=lambda: self.download_novel(novel))
        if novel.title in self.downloaded_novels:
            download_button.config(state=tk.DISABLED)
        download_button.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(button_frame, text="Delete", command=lambda: self.delete_novel(novel)).grid(row=0, column=2, padx=5, pady=5)

    def destroy_details_section(self):
        for widget in self.details_frame.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()

    def close(self):
        print("============== CLOSING APPLICATION ==============")
        self.downloader.scrapper.close()
        self.root.destroy()
