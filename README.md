# Mistral OCR - PDF to Markdown/DOCX Converter

A Streamlit web application that uses Mistral AI's OCR API to extract text from PDF files and convert them to Markdown and DOCX formats.

## Features

- 📄 **PDF Processing**: Upload and process PDF files through Mistral AI OCR
- 📝 **Markdown Export**: Convert PDFs to clean Markdown format
- 📘 **DOCX Export**: Generate formatted Word documents with:
  - Pandoc for high-quality math rendering
  - python-docx for better table formatting
- 🎨 **Web Interface**: User-friendly Streamlit interface
- ⚙️ **Configurable**: Easy configuration via `secrets.toml`

## Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Mistral-AI-updated
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Secrets

Create a `.streamlit` directory if it doesn't exist:

```bash
mkdir -p .streamlit
```

Copy the example secrets file and fill in your credentials:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your actual credentials:

```toml
[mistral]
ocr_endpoint = "https://your-mistral-ocr-endpoint-url"
api_key = "your-api-key-here"
model = "mistral-document-ai-2505"  # Optional
```

**⚠️ Important**: Never commit `secrets.toml` with real credentials to GitHub!

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. **Upload PDF**: Click "Upload PDF File" and select your PDF document
2. **Configure Settings** (optional):
   - Add a document title (will appear as H1 heading)
   - Toggle page breaks between pages
3. **Process**: Click "🚀 Process PDF" to start OCR processing
4. **Download**: Once processed, download the Markdown or DOCX files
5. **Preview**: View the extracted text, markdown, and raw API response in tabs

## Project Structure

```
.
├── app.py                 # Streamlit application
├── mistral_ocr.py         # Core OCR processing functions
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore rules
└── .streamlit/
    └── secrets.toml       # Configuration (not in git)
```

## Command Line Usage

You can also use the script directly from the command line:

```bash
python mistral_ocr.py document.pdf --title "My Document" --out output.md
```

## Features Details

### Text Extraction
- Extracts text from PDF pages using Mistral AI OCR
- Supports multiple text extraction methods (markdown, lines, paragraphs, blocks)
- Handles various response formats from the OCR API

### Markdown Generation
- Clean markdown output with page separators
- Configurable page breaks
- Removes inline images (text-only mode)

### DOCX Generation
- **Hybrid Approach**: Uses Pandoc for math rendering + python-docx for tables
- **Fallback**: Pure python-docx if Pandoc is unavailable
- Proper table formatting with alignment support
- Clean paragraph and heading styles

## Requirements

- Python 3.8+
- Mistral AI API credentials
- Pandoc (optional, for better math rendering)

## Troubleshooting

### Missing Pandoc
If you see warnings about Pandoc, install it:
- **Windows**: Download from [pandoc.org](https://pandoc.org/installing.html)
- **macOS**: `brew install pandoc`
- **Linux**: `sudo apt-get install pandoc`

The app will work without Pandoc, but math rendering will be plain text.

### API Errors
- Verify your `ocr_endpoint` and `api_key` in `secrets.toml`
- Check that your API key has proper permissions
- Ensure the endpoint URL is correct


