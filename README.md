# Novel Scanner

**Novel Scanner** is a Python application that scrapes webnovels from specific web pages and saves them in `.txt` format. It offers a graphical user interface (GUI) built using `tkinter` and uses `Selenium` with Chrome for web scraping. Additionally, it integrates machine learning (ML) to automatically filter and clean novel content.

## Features
- **Webnovel Scraper**: Extracts content from specified webnovel pages.
- **GUI Interface**: Easy-to-use graphical interface for web scraping, implemented with `tkinter`.
- **File-Based Database**: Saves scraped novels and other data using `pickle`.
- **ML-Powered Content Filtering**: Optional machine learning model to identify and remove non-novel content from scraped texts.
- **Multi-Site Support**: Supports scraping from multiple webnovel platforms.

## Requirements
- Python 3.8 or 3.11 is required. Please note that `undetected_chromedriver` does not support Python 3.12 or higher.
  
## Installation and Setup

### 1. Clone the repository:
```bash
git clone https://github.com/SergioRt1/Webnovel-Scanner
cd Webnovel-Scanner
```

### 2. Install `tkinter`:
For Linux-based systems, install the `tkinter` package:
```bash
sudo apt install python3.11-tk  # or sudo apt install python3-tk for Python 3.8
python3 -c "import tkinter; tkinter.Tk()"  # Validate installation
```

### 3. Create and activate a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 5. Install the ML dependency:
Install the [novel_cleaner](https://github.com/SergioRt1/novel-cleaner) library by specifying its root path:
```bash
pip install /home/user/projects/novel_cleaner  # Update the path as needed
```
(Optional) If using PyTorch with ROCm:
   ```bash
   pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/rocm6.2 # Use a compatible version with your OS and hardware
   ```

### 6. Run the application:
```bash
python main.py
```

## Usage

1. Enter the URL of the webnovel's main page into the search bar.
2. Select the website from the drop-down list of supported sites.
3. The application will scrape and download the novel content.
4. Export the downloaded content in `.txt` format.
5. Optionally, use the built-in ML tools to filter out non-novel content and automatically clean up the text.

## Machine Learning (ML) Integration

### Overview:
The **Novel Scanner** app includes an optional ML-powered content filtering feature. This functionality allows the system to:
- Automatically detect non-novel content (e.g., ads, promotional text) and flag it for review.
- Train custom models to refine the filtering accuracy based on the content you're scraping.

### Key Features:
- **Train Model**: This option allows users to build training data and train a machine learning model to classify [novel-like](ml_data/novel-like.txt) vs. [non-novel](ml_data/non-novel.txt) content. 
- **Prediction**: Once trained, the ML model can automatically filter out non-novel content from the scraped novels.
- **Review Flagged Sentences**: Users can manually review flagged sentences to ensure only novel content remains.

## File-Based Database
The application uses `pickle` to serialize and store data locally, ensuring that previously downloaded novels are accessible.

## Disclaimer
This tool is intended for educational and personal use only. Do not use **Novel Scanner** for any purpose that violates the terms of service of the websites you scrape. Misuse of this tool for unethical purposes, such as scraping content for financial gain, is strongly discouraged.

## License
This project is licensed under the MIT License.

