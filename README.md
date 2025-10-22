# ChatExtract

Extract chat sessions from OpenAI data exports by date.

## Overview

ChatExtract is a command-line tool that helps you:
1. View all unique dates with conversation counts from your ChatGPT export
2. Extract all conversations from a specific date to organized folders with both JSON and HTML files

## Installation

### Option 1: Using conda (recommended for conda users)

```bash
conda env create -f environment.yml
conda activate chatextract
```

### Option 2: Using pip and venv

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### List all dates

```bash
python chat_extract.py data/Charlie-1
```

This displays:
- All unique dates with conversation counts
- Sample conversation titles from each date

### Extract conversations from a specific date

```bash
python chat_extract.py data/Charlie-1 -d 2025-10-21
```

This extracts all conversations from that date to `extracted/Charlie-1/` with:
- `conversations.json` - Filtered conversations in JSON format
- `chat.html` - Human-readable HTML version of the filtered conversations

### Filter by keyword in title

```bash
python chat_extract.py data/Charlie-1 -d 2025-10-21 -k "python"
```

This extracts only conversations from that date where "python" appears in the title (case-insensitive).

## OpenAI Data Export

To get your `conversations.json` file:
1. Go to ChatGPT Settings → Data Controls
2. Click "Export data"
3. Wait for the email with your data archive
4. Extract the archive and locate the `conversations.json` file

## Examples

```bash
# List all dates with conversation counts
python chat_extract.py data/Charlie-1

# Extract all conversations from October 21, 2025
python chat_extract.py data/Charlie-1 -d 2025-10-21

# Extract only conversations with "python" in the title from that date
python chat_extract.py data/Charlie-1 -d 2025-10-21 -k "python"

# Process a different export
python chat_extract.py data/Another-Export -d 2025-09-15
```

## Folder Structure

```
ChatExtract/
├── data/
│   └── Charlie-1/              # Your OpenAI export (renamed)
│       ├── conversations.json
│       ├── chat.html
│       └── ...
├── extracted/
│   └── Charlie-1/              # Output folder (created by tool)
│       ├── conversations.json  # Filtered conversations (JSON)
│       └── chat.html          # Filtered conversations (HTML)
├── chat_extract.py
└── README.md
```

## Requirements

- Python 3.8+
- See `requirements.txt` for package dependencies

## License

MIT
