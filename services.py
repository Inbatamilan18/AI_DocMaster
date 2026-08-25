# ------------------------------------------------------------------
# DocMaster AI -- translation (Google Translate / deep-translator)
# and speech synthesis (gTTS).  Architecture box 5: "Post-processing".
# Both degrade gracefully when the network or a service is unavailable.
# ------------------------------------------------------------------
import io

# languages offered in the UI:
# display name -> (google code, gTTS code, MyMemory code)
LANGUAGES = {
    "English (original)": ("en", "en", "en-US"),
    "Tamil (தமிழ்)": ("ta", "ta", "ta-IN"),
    "Hindi (हिन्दी)": ("hi", "hi", "hi-IN"),
    "Spanish": ("es", "es", "es-ES"),
    "French": ("fr", "fr", "fr-FR"),
    "German": ("de", "de", "de-DE"),
    "Chinese (Simplified)": ("zh-CN", "zh-cn", "zh-CN"),
}

MAX_CHARS = 4500  # Google Translate web endpoint limit per call


def translate_text(text: str, target_display: str) -> str:
    """Translate `text` to the language picked in the UI.
    Chain: Google Translate (twice) -> MyMemory fallback -> original+note.
    Chunks long text; never raises."""
    gcode, _, mcode = LANGUAGES.get(target_display, LANGUAGES["English (original)"])
    if gcode == "en" or not text.strip():
        return text
    chunks = [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
    try:  # primary: Google Translate
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="auto", target=gcode)
        out = "\n".join(tr.translate(c) for c in chunks)
        if out and "Error 500" not in out and "That’s an error" not in out \
                and "That's an error" not in out:
            return out
    except Exception:
        pass
    try:  # fallback: MyMemory (assumes English source, our common case)
        from deep_translator import MyMemoryTranslator
        tr = MyMemoryTranslator(source="en-US", target=mcode)
        return "\n".join(tr.translate(c) for c in chunks)
    except Exception as e:
        return f"{text}\n\n[translation unavailable right now: {e}]"


def tts_bytes(text: str, target_display: str) -> bytes | None:
    """Synthesize `text` to MP3 bytes in the UI language (fallback: en)."""
    lang = LANGUAGES.get(target_display, ("en", "en"))[1]
    if not text.strip():
        return None
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text[:2500], lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        try:  # accent fallback, e.g. zh-cn not available -> English
            from gtts import gTTS
            buf = io.BytesIO()
            gTTS(text=text[:2500], lang="en").write_to_fp(buf)
            return buf.getvalue()
        except Exception:
            return None
