import threading
import tkinter as tk
from functools import wraps
from tkinter import ttk

from PIL import Image, ImageTk, ImageSequence

from logic.filter import ContentFilter
from logic.novel_downloader import NovelDownloader
from logic.websites import get_website_ids
from utils import constants


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

    @threaded_task
    def export_novel(self, novel):
        #novel = self.filter.filter_content(novel)
        self.downloader.write_novel(novel)

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
