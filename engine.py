# ------------------------------------------------------------------
# DocMaster AI -- the "Gemini Flash prompt engine" (architecture box 4)
# With a Gemini API key: summaries + glossary come from Gemini Flash
# using the paper's prompt templates (prompts.py / Table II).
# Without a key the engine switches to a transparent OFFLINE mode
# (extractive summaries + heuristic glossary) so the whole pipeline
# can still be demonstrated end-to-end.
# ------------------------------------------------------------------
import os
import re
from collections import Counter

import prompts
import textproc

MODEL_CANDIDATES = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
_client = None
_model_name = None


def configure(api_key: str | None):
    """Call once per session. Empty/None key => offline mode."""
    global _client, _model_name
    _client, _model_name = None, None
    key = (api_key or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        return False
    try:
        from google import genai
        _client = genai.Client(api_key=key)
        return True
    except Exception:
        return False


def online() -> bool:
    return _client is not None


# ----------------------------- Gemini path -----------------------------

def _ask(prompt: str, max_tokens: int = 640) -> str:
    """Ask Gemini; walk MODEL_CANDIDATES until one answers, remember it."""
    global _model_name
    from google.genai import types
    cfg = types.GenerateContentConfig(temperature=0.3,
                                      max_output_tokens=max_tokens)
    candidates = ([_model_name] if _model_name else []) + \
        [m for m in MODEL_CANDIDATES if m != _model_name]
    last_err = None
    for name in candidates:
        try:
            resp = _client.models.generate_content(model=name, contents=prompt,
                                                   config=cfg)
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                _model_name = name
                return text
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Gemini call failed: {last_err}")


def summarize(page_text: str, style: str) -> str:
    """style in {'paragraph', 'bullets', 'audio'}"""
    if online():
        tmpl = {"paragraph": prompts.PARAGRAPH_PROMPT,
                "bullets": prompts.BULLET_PROMPT,
                "audio": prompts.AUDIO_PROMPT}[style]
        try:
            out = _ask(tmpl.format(page=page_text[:6000]))
            if out:
                return out
        except Exception as e:
            return f"[Gemini error: {e}] Falling back to offline summary.\n\n" \
                   + _offline_summary(page_text, style)
    return _offline_summary(page_text, style)


def glossary(page_text: str, max_terms: int = 6) -> list[dict]:
    """Return [{'term','sense','simple'}]. Online: parsed from Gemini.
    Offline: heuristic candidates + the sentence they appear in."""
    if online():
        try:
            raw = _ask(prompts.GLOSSARY_PROMPT.format(page=page_text[:6000],
                                                      max_terms=max_terms),
                       max_tokens=800)
            items = _parse_glossary(raw)
            if items:
                return items[:max_terms]
        except Exception:
            pass
    return _offline_glossary(page_text, max_terms)


def _parse_glossary(raw: str) -> list[dict]:
    items, cur = [], {}
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("TERM:"):
            if cur.get("term"):
                items.append(cur)
            cur = {"term": line[5:].strip()}
        elif line.upper().startswith("SENSE:"):
            cur["sense"] = line[6:].strip()
        elif line.upper().startswith("SIMPLE:"):
            cur["simple"] = line[7:].strip()
    if cur.get("term"):
        items.append(cur)
    return [i for i in items if i.get("sense") or i.get("simple")]


# ----------------------------- offline path -----------------------------

def _score_sentences(sents: list[str]) -> list[tuple[float, int, str]]:
    """Tiny word-frequency (TextRank-flavoured) sentence scorer."""
    freq = Counter()
    for s in sents:
        for w in re.findall(r"[a-z]{3,}", s.lower()):
            freq[w] += 1
    if not freq:
        return []
    m = freq.most_common(1)[0][1]
    scored = []
    for i, s in enumerate(sents):
        words = re.findall(r"[a-z]{3,}", s.lower())
        if not words:
            continue
        score = sum(freq[w] / m for w in words) / (len(words) ** 0.4)
        scored.append((score, i, s))
    return scored


def _looks_like_header(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return True
    upp = sum(c.isupper() for c in letters) / len(letters)
    return upp > 0.6 and len(s) < 80


def _offline_summary(page_text: str, style: str) -> str:
    sents = [s for s in textproc.sentences(page_text) if not _looks_like_header(s)]
    ranked = _score_sentences(sents)
    if not ranked:
        return "(no readable text on this page)"
    top = [s for _, _, s in sorted(ranked[:4], key=lambda x: x[1])]
    if style == "paragraph":
        return " ".join(top)
    if style == "bullets":
        return "\n".join("- " + s for s in top)
    # audio-friendly: short sentences, symbols -> words
    out = []
    for s in top:
        s = re.sub(r"\((.*?)\)", r", \1, ", s)
        s = s.replace("%", " percent").replace("&", " and ")
        for chunk in re.split(r"(?<=[,;])\s+", s):
            chunk = chunk.strip()
            if chunk:
                out.append(chunk[0].upper() + chunk[1:])
    try:
        from num2words import num2words
        out = [re.sub(r"\b\d+\b", lambda m: num2words(int(m.group())), c)
               for c in out]
    except Exception:
        pass
    return " ".join(c if c.endswith((".", "!", "?")) else c + "." for c in out)


def _offline_glossary(page_text: str, max_terms: int) -> list[dict]:
    sents = textproc.sentences(page_text)
    cands = textproc.noun_candidates(page_text)
    seen, items = set(), []
    for c in cands:
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        ctx = next((s for s in sents if key in s.lower()), "")
        items.append({
            "term": c,
            "sense": f"As used on this page: \"{ctx[:180]}\"" if ctx
                     else "Specialist term on this page.",
            "simple": "(offline mode: connect a Gemini key for a plain-language definition)",
        })
        if len(items) >= max_terms:
            break
    return items
