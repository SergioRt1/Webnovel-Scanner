# Novel Scanner

Novel Scanner is a Python application that allows users to scrape novels from webnovel pages and save them in `.txt` format. The app features a graphical user interface (GUI) built with `tkinter` and uses `Selenium` with Chrome to perform the web scraping.

## Requirements
This project requires Python 3.8 or 3.11. Please note that undetected_chromedriver does not support Python 3.12 or higher.


## Installation and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SergioRt1/Webnovel-Scanner
   cd Webnovel-Scanner
   ```

2. **Install Tkinter package**:
   ```bash
   sudo apt install python3.11-tk # Or sudo apt install python3-tk
   python3 -c "import tkinter; tkinter.Tk()" # Validate instalation
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```
   Install ML depencency
   ```bash
   pip install /home/user/projects/novel_cleaner # put the actual root path of novel cleaner lib
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## Usage
The application provides a simple graphical interface to start scraping webnovels from specific pages. Enter the URL of the webnovel you wish to scrape, and the program will automatically collect the content and save it as a `.txt` file in the designated output folder.

## File-Based Database
This application uses a file-based database powered by `pickle` to store and retrieve data. The data is serialized and saved locally.

## Disclaimer
This tool is intended for educational and personal use only. Please do not use Novel Scanner for malicious purposes or in any way that violates the terms of service of the websites you scrape. Abusing this tool for financial gain or unethical reasons is strictly discouraged.

## License
MIT License
