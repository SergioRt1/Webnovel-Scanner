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

import platform
import os
import subprocess

def threaded_task(task):
    @wraps(task)
    def wrapper(self, *args, **kwargs):
        self.show_loader()

        def inner_task():
            try:
                task(self, *args, **kwargs)
            finally:
                self.hide_loader()

        threading.Thread(target=inner_task).start()

    return wrapper


class NovelUI:
    def __init__(self, downloader: NovelDownloader, filter: ContentFilter):
        self.downloader = downloader
        self.filter = filter

        # Setup main window
        self.root = tk.Tk()
        self.root.title("Novel downloader")
        self.root.geometry("1100x1080")

        self.style = ttk.Style(self.root)
        self.style.configure('TButton', font=('Arial', 12))
        self.style.map('TButton',
                       background=[('disabled', 'gray'), ('active', 'lightblue')],
                       foreground=[('disabled', 'darkgray')],
                       )
        self.style.configure('TLabel', font=('Arial', 12))

        self._add_search_bar()
        self._add_books_list_and_details_frame()
        self._add_book_details_frame()

        self.downloaded_novels = self.downloader.get_downloaded_novels()

    def _add_search_bar(self):
        # Search Bar Frame
        frame = ttk.Frame(self.root)
        frame.pack(pady=10, fill='x', padx=30)

        search_label = ttk.Label(frame, text="Link main page")
        search_label.grid(row=0, column=0, padx=15, pady=5)

        self.search_entry = ttk.Entry(frame, width=50, font=('Arial', 12))
        self.search_entry.grid(row=0, column=1, padx=15, pady=5)
        self.search_entry.bind('<Return>', self.perform_search)  # Bind the Enter key event

        websites = get_website_ids()

        self.search_option = ttk.Combobox(frame, values=websites, font=('Arial', 12), state="readonly", width=30)
        self.search_option.current(0)
        self.search_option.grid(row=0, column=2)

    def clear_current_book_list(self):
        """Clear the current displayed list of books."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def display_books(self, book_list):
        """Display provided list of books."""
        for i, novel in enumerate(book_list):
            button = ttk.Button(self.scrollable_frame, text=novel.title,
                                command=lambda n=novel: self._add_book_image_and_details(n))
            button.grid(row=i, column=0, pady=5, padx=5, sticky='ew')

    def show_loader(self):
        loader_image = Image.open(constants.loader_image)
        self.loader_frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(loader_image)]
        self.loader_label = tk.Label(self.root, image=self.loader_frames[0])

        # Centering the loader on the root window
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        loader_width = self.loader_frames[0].width()
        loader_height = self.loader_frames[0].height()

        x_pos = (window_width - loader_width) // 2
        y_pos = (window_height - loader_height) // 2

        self.loader_label.place(x=x_pos, y=y_pos)  # Using place() for absolute positioning

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
            # Stop the loader animation loop
            if hasattr(self, 'loader_frames'):
                self.root.after_cancel(self.loader_task_id)

    @threaded_task
    def perform_search(self, event=None):
        novel_url = self.search_entry.get()
        selected_website = self.search_option.get()

        search_results = self.downloader.search_novel(novel_url, selected_website)

        # Update the displayed list
        self.clear_current_book_list()
        self.display_books(search_results)

    def _add_books_list_and_details_frame(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=10, fill='both', expand=True, padx=20, side='left')

        self.canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Make the scrollable_frame expand as canvas resizes
        self.canvas.bind('<Configure>',
                         lambda e: self.canvas.itemconfig("window", width=e.width))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw', tags="window")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Configure the scrollable frame's column to expand
        self.scrollable_frame.columnconfigure(0, weight=1)

        self.display_books(self.downloader.novels)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _add_book_details_frame(self):
        # Separate frame for book details
        self.details_frame = ttk.Frame(self.root)
        self.details_frame.pack(pady=10, fill='both', expand=True, padx=20, side='right')

    def export_novel(self, novel):
        # Create a new Toplevel window for ML options
        self.ml_window = tk.Toplevel(self.root)
        self.ml_window.title("ML Processor Options")
        self.ml_window.geometry("400x200")

        open_non_novel_button = ttk.Button(self.ml_window, text="Open Non-Novel Content", command=self.open_non_novel_content)
        open_non_novel_button.pack(pady=5)

        open_novel_like_button = ttk.Button(self.ml_window, text="Open Novel-Like Content", command=self.open_novel_like_content)
        open_novel_like_button.pack(pady=5)

        train_model_button = ttk.Button(self.ml_window, text="Train Model", command=lambda: self.train_model(novel))
        train_model_button.pack(pady=5)

        skip_button = ttk.Button(self.ml_window, text="Skip Training", command=lambda: self.skip_training(novel))
        skip_button.pack(pady=5)

################ ML Functions ##########################
    @threaded_task
    def train_model(self, novel):
        build_training_data()
        train()
        tk.messagebox.showinfo("Training Complete", "The model has been trained successfully.")
        self.ml_window.destroy()
        self.show_prediction_view(novel)

    def skip_training(self, novel):
        self.ml_window.destroy()
        self.show_prediction_view(novel)

    def show_prediction_view(self, novel):
        self.prediction_window = tk.Toplevel(self.root)
        self.prediction_window.title("Run ML Model")
        self.prediction_window.geometry("800x150")

        run_model_button = ttk.Button(self.prediction_window, text="Run Model", command=lambda: self.run_model(novel))
        run_model_button.pack(pady=5)

        self.prediction_label = tk.Label(self.prediction_window, text="Starting predictions...", font=("Arial", 12))
        self.prediction_label.pack(pady=20)

    @threaded_task
    def run_model(self, novel):
        model, tokenizer = prediction.load_model()
        i = 0
        total = len(novel.chapter_list)
        for chapter in novel.chapter_list:
            self.prediction_label.config(text=f'Predicting: {chapter.title}\n({i}/{total})')
            self.prediction_window.update_idletasks() 
            print(f'Predicting: {chapter.title}')
            chapter.df = prediction.predict(model, tokenizer, chapter.content)
            print("\033[A\r\033[K", end='')  # Delete a line in the CLI, Move up one line, clear the line
            print("\033[A\r\033[K", end='')
            print("\033[A\r\033[K", end='')
            i += 1

        self.prediction_window.destroy()
        self.review_flagged_sentences(novel)
    
    def review_flagged_sentences(self, novel):
        self.novel = novel
        self.chapter_index = 0  # Keep track of the current chapter
        self.current_sentence_index = 0  # Keep track of the current sentence in the chapter
        self.chapters_with_flags = []  # List to store chapters that have flagged sentences

        # Collect all chapters that have flagged sentences
        for chapter in novel.chapter_list:
            flagged_df = chapter.df[chapter.df['Prediction'] == 1]
            if not flagged_df.empty:
                self.chapters_with_flags.append((chapter, flagged_df))

        # Initialize the main window for sentence review
        self.init_review_window()
        self.review_next_flagged_sentence()

    def init_review_window(self):
        # Create the window for reviewing sentences
        self.review_window = tk.Toplevel(self.root)
        self.review_window.title("Review Flagged Sentences")

        self.chapter_label = tk.Label(self.review_window, text="", font=("Arial", 12, "bold"))
        self.chapter_label.pack(pady=5)

        self.sentence_text = tk.Text(self.review_window, height=10, width=80)
        self.sentence_text.pack(pady=10)

        button_frame = ttk.Frame(self.review_window)
        button_frame.pack(pady=10)

        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_sentence)
        self.save_button.pack(side='left', padx=10)

        self.remove_button = ttk.Button(button_frame, text="Remove", command=self.remove_sentence)
        self.remove_button.pack(side='right', padx=10)

    def review_next_flagged_sentence(self):
        if self.chapter_index < len(self.chapters_with_flags):
            chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
            if self.current_sentence_index < len(flagged_df):
                # Get the sentence and its index in chapter.df
                original_index = flagged_df.index[self.current_sentence_index]
                sentence = flagged_df.loc[original_index, 'Sentence']
                self.display_flagged_sentence(sentence, chapter.title)
            else:
                # Move to the next chapter
                self.chapter_index += 1
                self.current_sentence_index = 0
                self.review_next_flagged_sentence()
        else:
            self.finalize_cleaned_novel()

    def display_flagged_sentence(self, sentence, chapter_title):
        # Update chapter label and sentence text
        self.chapter_label.config(text=f"Chapter: {chapter_title} ({self.chapter_index+1}/{len(self.chapters_with_flags)})")
        self.sentence_text.delete('1.0', 'end')
        self.sentence_text.insert('1.0', sentence)

    def save_sentence(self):
        edited_sentence = self.sentence_text.get('1.0', 'end-1c')
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
        original_index = flagged_df.index[self.current_sentence_index]
        chapter.df.loc[original_index, 'Sentence'] = edited_sentence
        self.current_sentence_index += 1
        self.review_next_flagged_sentence()

    def remove_sentence(self):
        chapter, flagged_df = self.chapters_with_flags[self.chapter_index]
        original_index = flagged_df.index[self.current_sentence_index]
        chapter.df.loc[original_index, 'Sentence'] = ''
        self.current_sentence_index += 1
        self.review_next_flagged_sentence()

    def finalize_cleaned_novel(self):
        for chapter in self.novel.chapter_list:
            # Rebuild chapter content from the df['Sentence']
            sentences = chapter.df['Sentence'].tolist()
            chapter.content = ' '.join(sentences)
        self.review_window.destroy()
        # Write the modified novel
        self.downloader.write_novel(self.novel)
        tk.messagebox.showinfo("Process Complete", "Filtered novel saved successfully.")


    def open_non_novel_content(self):
        file_path = "./ml_data/non-novel.txt"
        self.open_text_file(file_path)
    
    def open_novel_like_content(self):
        file_path = "./ml_data/novel-like.txt"
        self.open_text_file(file_path)
    
    def open_text_file(self, file_path):
        if os.path.exists(file_path):
            current_os = platform.system()

            if current_os == "Windows":
                os.startfile(file_path)  # For Windows, not tested
            elif current_os == "Darwin":
                subprocess.call(('open', file_path))  # For macOS, not tested
            elif current_os == "Linux":
                subprocess.call(('xdg-open', file_path))  # For Linux
            else:
                tk.messagebox.showerror("Error", f"Unsupported OS: {current_os}")
        else:
            tk.messagebox.showerror("Error", "Content file not found.")
    


################ ML Functions - END ####################

    @threaded_task
    def download_novel(self, novel):
        success = self.downloader.download_novel(novel)
        if success:
            self.downloaded_novels.add(novel.title)
            self._add_book_image_and_details(novel)

    @threaded_task
    def delete_novel(self, novel):
        success = self.downloader.delete_novel(novel)
        if success:
            self.downloader.sync_novels()
            self.clear_current_book_list()
            self.display_books(self.downloader.novels)
            self.destroy_details_section()

    def _add_book_image_and_details(self, novel):
        self.destroy_details_section()

        # Load and resize the image
        image = Image.open(novel.get_image_path())
        image = image.resize((300, 400), Image.LANCZOS)
        self.book_image = ImageTk.PhotoImage(image)

        book_img_label = ttk.Label(self.details_frame, image=self.book_image)
        book_img_label.grid(row=0, column=0, columnspan=2, pady=20)

        book_title_label = ttk.Label(self.details_frame, text=novel.title, font=('Arial', 16, 'bold'))
        book_title_label.grid(row=1, column=0, columnspan=2)

        self.book_desc_text = tk.Text(self.details_frame, wrap=tk.WORD, height=20, width=65)
        self.book_desc_text.insert(tk.END, novel.desc)
        self.book_desc_text.grid(row=2, column=0, columnspan=2, pady=10)

        scrollbar = ttk.Scrollbar(self.details_frame, command=self.book_desc_text.yview)
        scrollbar.grid(row=2, column=2, sticky='ns')
        self.book_desc_text['yscrollcommand'] = scrollbar.set

        book_details_label = ttk.Label(self.details_frame,
                                       text=f"Chapters Downloaded: {len(novel.downloaded_set)}/{len(novel.chapter_list)}",
                                       background='#EAFAF1')
        book_details_label.grid(row=3, column=0, columnspan=2, pady=10)

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

        delete_button = ttk.Button(button_frame, text="Delete", command=lambda: self.delete_novel(novel))
        delete_button.grid(row=0, column=2, padx=5, pady=5)

    def destroy_details_section(self):
        # Clear previous details if any
        for widget in self.details_frame.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()

    def close(self):
        print("============== CLOSING APPLICATION ==============")
        self.downloader.scrapper.close()
        self.root.destroy()
