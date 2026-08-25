# ------------------------------------------------------------------
# DocMaster AI -- pre-processing (architecture box 3)
# Cleaning, sentence splitting and per-page language detection.
# spaCy is used when its model is installed; a regex fallback keeps
# the app fully functional without it (nice for low-spec laptops).
# ------------------------------------------------------------------
import re
from langdetect import detect, LangDetectException

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")   # parser needed for noun_chunks
except Exception:
    _nlp = None


def clean_text(text: str) -> str:
    """Repair the usual PDF extraction damage: broken newlines, stray
    whitespace, hyphen-split words, odd control characters."""
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"-\n(\w)", r"\1", text)          # rejoin hyphen-broken words
    text = re.sub(r"[ \t]+", " ", text)              # collapse horizontal space
    text = re.sub(r"\n{3,}", "\n\n", text)           # cap blank lines
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)     # join single line-breaks
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def sentences(text: str) -> list[str]:
    """Split text into sentences with spaCy, fallback to a regex."""
    if not text:
        return []
    if _nlp is not None:
        return [s.text.strip() for s in _nlp(text[:100000]).sents if s.text.strip()]
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text.replace("\n", " "))
    return [p.strip() for p in parts if len(p.strip()) > 2]


def detect_language(text: str) -> str:
    """Return an ISO code like 'en', 'ta', 'hi'; 'en' when unsure."""
    try:
        return detect(text[:3000]) if text.strip() else "en"
    except LangDetectException:
        return "en"


def noun_candidates(text: str) -> list[str]:
    """Candidate glossary terms: spaCy noun-chunks + named entities when
    available, else a capitalised-word / long-word heuristic. Filters
    out measurements, doses, ALL-CAPS headers and substring duplicates."""
    raw = []
    if _nlp is not None and text.strip():
        doc = _nlp(text[:100000])
        raw += [c.text for c in doc.noun_chunks]
        raw += [e.text for e in doc.ents]
    else:
        raw += re.findall(r"[A-Za-z][A-Za-z\-]{5,}", text)

    kept: list[str] = []
    ok = re.compile(r"^[A-Za-z][A-Za-z'\-]*( [A-Za-z][A-Za-z'\-]*)*$")
    stop = {"the", "a", "an", "his", "her", "their", "your", "our", "its",
            "he", "she", "they", "we", "i", "this", "that", "these", "those",
            "no", "not", "and", "or", "of", "to", "in", "on", "for", "with",
            "without", "was", "were", "is", "are", "by", "at", "as", "it",
            "per", "across", "during", "throughout"}
    for t in raw:
        t = t.strip(" .,;:()\"'")
        if not (3 <= len(t) <= 45) or not ok.match(t):
            continue                      # digits, units, doses out
        if t.upper() == t and len(t) > 2:
            continue                      # ALL-CAPS headers out
        if " " not in t and len(t) < 6:
            continue                      # short plain words out
        if {w.lower().strip("'-") for w in t.split()} & stop:
            continue                      # determiner/function-word chunks out
        low = t.lower()
        if any(low in k or k in low for k in (x.lower() for x in kept)):
            continue                      # substring duplicates out
        kept.append(t)
    return kept
