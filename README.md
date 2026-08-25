# DocMaster AI — Working Prototype

Multilingual document summarization with audio support. This is the
implementation behind the IEEE paper *"DocMaster AI: Multilingual Document
Summarization with Audio Support"* (Dept. of AI & DS, St. Joseph's Institute
of Technology).

## What it does (per page of an uploaded PDF)

1. **Paragraph summary** — 80–120 words, for careful reading
2. **Bullet summary** — 3–7 points, for quick scanning
3. **Audio-friendly summary** — short sentences, spelled-out numbers → MP3
4. **Contextual glossary** — hard terms explained *as used on that page*
5. Everything **translatable** (Tamil, Hindi, Spanish, French, German, Chinese)
6. **Audio playback + downloads** in the browser

## Tech stack (= Table III of the paper)

| Component | Library |
|---|---|
| Runtime | Python 3.11+ |
| PDF parsing | pypdf, pdfplumber |
| OCR fallback (optional) | Tesseract via pytesseract + pypdfium2 |
| NLP pre-processing | spaCy (en_core_web_sm), langdetect |
| LLM | Google Gemini Flash (google-genai SDK) |
| Translation | Google Translate (deep-translator); MyMemory auto-fallback |
| Speech | gTTS |
| Web app + cache | Streamlit (st.cache_data) |

## Setup (Windows / Linux, ~5 minutes)

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Get a **free Gemini API key**:
1. Go to https://aistudio.google.com
2. Sign in → *Get API key* → *Create API key* → copy it

Run:

```bash
# option A: paste the key into the app's sidebar (recommended for demo)
streamlit run app.py

# option B: environment variable
set GEMINI_API_KEY=your_key_here      # Windows
export GEMINI_API_KEY=your_key_here   # Linux/Mac
streamlit run app.py
```

Open http://localhost:8501 — download the bundled `sample_discharge.pdf`
from the app and drop it back in to try everything instantly.

### Optional: scanned (image) PDFs
Install Tesseract OCR (Windows: UB Mannheim installer; Linux:
`sudo apt install tesseract-ocr`). Without it, scanned pages are skipped
gracefully — every other feature keeps working.

## Offline demo mode

No API key pasted? The app still works end-to-end in **offline demo mode**:
summaries become extractive (word-frequency TextRank-style) and glossary
definitions show the term's context sentence. The sidebar tells you which
mode you are in. Real abstractive output needs the Gemini key.

## File map → paper sections (viva guide!)

| File | Paper section |
|---|---|
| `docparser.py` | §III-B Parsing |
| `textproc.py` | §III-C Pre-processing & language detection |
| `prompts.py` | §III-D/E/F + Table IV (prompt templates) |
| `engine.py` | §III "Gemini Flash prompt engine" box |
| `services.py` | §III-G/H Translation & speech |
| `app.py` | §III-I User interface |
| `make_sample_pdf.py`, `sample_discharge.pdf` | Fig. 2 worked example |
| `test_pipeline.py` | headless end-to-end check |

## Notes
- Free tiers only; no GPU. Rate limits (~15 req/min on Gemini Flash) are
  plenty for demo and the 30-document evaluation.
- Translation chain: Google Translate → MyMemory → original text with a
  note, so the app never hard-fails on network issues.
