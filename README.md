# Novel Scanner

**Novel Scanner** is a desktop Python application for scraping webnovels from supported sites, storing them locally, exporting them to `.txt`, and optionally cleaning the content with a machine learning pipeline. It includes a `tkinter` GUI, Selenium-based scraping, local file persistence, duplicate filtering, and an interactive ML review flow.

## Features

- **Webnovel Scraper**: Extracts metadata, chapter lists, and chapter content from supported webnovel sites.
- **Desktop GUI**: Built with `tkinter`, with a cleaner interface for browsing, downloading, exporting, and running ML cleanup.
- **Local File Database**: Stores novels locally using JSON metadata and chapter `.txt` files.
- **Incremental Downloads**: Keeps track of downloaded chapters and only fetches missing ones.
- **ML-Powered Content Filtering**: Optional machine learning pipeline to identify and remove non-novel content.
- **Manual Review Workflow**: Review flagged sentences before saving cleaned output.
- **Duplicate Chapter Filtering**: Optional duplicate detection before ML processing.
- **Multi-Site Support**: Works with multiple supported webnovel platforms.
- **Task Cancellation**: Cancel long-running scraping or ML operations without closing the app.

## Requirements

- Python **3.8** to **3.11**
- Google Chrome or Chromium installed
- `tkinter` available in your Python installation

> `undetected_chromedriver` does not currently support Python 3.12+, so Python 3.11 is recommended.

## Project Structure

```text
Webnovel-Scanner/
├─ app/
│  ├─ core/
│  ├─ filters/
│  ├─ ml/
│  ├─ models/
│  ├─ scraping/
│  ├─ storage/
│  ├─ ui/
│  └─ utils/
├─ assets/
├─ data/
├─ ml_data/
├─ Novels/
├─ requirements.txt
└─ README.md
````

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/SergioRt1/Webnovel-Scanner
cd Webnovel-Scanner
```

### 2. Install `tkinter`

For Linux-based systems:

```bash
sudo apt install python3.11-tk
python3 -c "import tkinter; tkinter.Tk()"
```

For Python 3.8, use:

```bash
sudo apt install python3-tk
```

### 3. Create and activate a virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Install the optional ML dependency

Novel Scanner supports an optional external ML package that exposes:

* `ml_processor.train_model.train`
* `ml_processor.labeler.build_training_data`
* `ml_processor.prediction`

Install your local `novel_cleaner` package:

```bash
pip install /home/user/projects/novel_cleaner
```

Update the path to match your machine.

Optional, if your ML environment requires a custom PyTorch build such as ROCm:

```bash
pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/rocm6.2
```

Use a version compatible with your OS, drivers, and hardware.

### 6. Add required assets

Place these files in the `assets/` directory:

* `icon.png`
* `placeholder.png`
* `loader.gif`

### 7. Run the application

```bash
python -m app.main
```

## Usage

1. Enter the URL of a novel’s main page in the search field.
2. Select the corresponding website from the supported site list.
3. Load the novel metadata and chapter list.
4. Download missing chapters.
5. Export the novel as `.txt`.
6. Optionally run the ML cleanup flow to detect and remove non-novel content.
7. Review flagged sentences before saving the cleaned output.

## Machine Learning Integration

## Overview

Novel Scanner includes an optional ML-powered cleanup workflow for detecting content that does not belong to the novel, such as:

* ads
* promotional blocks
* navigation text
* repeated garbage content
* other non-story fragments

## ML Workflow

The integrated ML flow supports:

* **Build Training Data**: Uses your labeled datasets to prepare training data.
* **Train Model**: Trains a classifier using the external ML package.
* **Run Prediction**: Evaluates each downloaded chapter and flags suspicious sentences.
* **Review Flagged Sentences**: Lets you manually keep, edit, or remove flagged text.
* **Save Cleaned Novel**: Rebuilds the chapter text and exports the cleaned novel.

## Training Data Files

The review/training flow expects these files:

```text
ml_data/non-novel.txt
ml_data/novel-like.txt
```

These are used to distinguish novel-like vs non-novel text.

## Notes About ML Support

* The app works normally without the ML dependency installed.
* If `ml_processor` is not available, scraping and export still work.
* Only the ML-specific actions will be unavailable.

## Local Storage

Novel Scanner uses a file-based local database.

### Stored data includes:

* novel metadata in JSON
* chapter text in `.txt`
* downloaded cover images
* exported output files

This replaces the older pickle-based storage model and makes the data easier to inspect and recover manually.

## Export Output

By default, the app can generate:

* split `.txt` files for large novels
* a single full `.txt`
* metadata JSON export

Exports are stored in the `Novels/` directory.

## Supported Sites

The app is structured to support multiple sites through isolated scraper modules under:

```text
app/scraping/sites/
```

If a website changes its HTML structure, only the site-specific scraper usually needs to be updated.

## Disclaimer

This tool is intended for personal and educational use only.

Do not use **Novel Scanner** in ways that violate the terms of service, copyright rules, or access policies of the websites you scrape. You are responsible for how you use this software.

## License

This project is licensed under the MIT License.

