# ------------------------------------------------------------------
# DocMaster AI -- Streamlit web app (architecture box 6)
# Dual summary panels * glossary expanders * language picker *
# audio player * per-page downloads.  Run:  streamlit run app.py
# ------------------------------------------------------------------
import hashlib

import streamlit as st

import docparser
import engine
import services
import textproc

st.set_page_config(page_title="DocMaster AI", page_icon="📄",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.block-container {padding-top: 1.6rem;}
.dm-page {font-size: 1.35rem; font-weight: 700;}
.dm-badge {background:#e8f0fe; color:#1a3e72; border-radius:6px;
           padding:2px 10px; font-size:0.85rem; margin-left:8px;}
</style>""", unsafe_allow_html=True)


# -------------------- cached pipeline stages (paper: "cache" box) --------------------

@st.cache_data(show_spinner=False)
def cached_pages(file_bytes: bytes):
    return [textproc.clean_text(p) for p in docparser.extract_pages(file_bytes)]


@st.cache_data(show_spinner=False)
def cached_summary(key_present: bool, page_text: str, style: str):
    return engine.summarize(page_text, style)


@st.cache_data(show_spinner=False)
def cached_glossary(key_present: bool, page_text: str):
    return engine.glossary(page_text, max_terms=6)


@st.cache_data(show_spinner=False)
def cached_translation(text: str, lang_display: str):
    return services.translate_text(text, lang_display)


@st.cache_data(show_spinner=False)
def cached_audio(text: str, lang_display: str):
    return services.tts_bytes(text, lang_display)


# -------------------- sidebar --------------------

with st.sidebar:
    st.title("📄 DocMaster AI")
    st.caption("Multilingual document summarization with audio support")

    api_key = st.text_input("Gemini API key (free: aistudio.google.com)",
                            type="password",
                            help="Leave empty to run in offline demo mode")
    engine.configure(api_key)
    if engine.online():
        st.success("Engine: Gemini Flash (online)", icon="🤖")
    else:
        st.warning("Engine: OFFLINE demo mode\n\nOutputs are extractive "
                   "approximations. Paste a Gemini key for real LLM output.",
                   icon="⚠️")

    lang_display = st.selectbox("🌐 Output language",
                                list(services.LANGUAGES.keys()), index=0)
    st.divider()
    st.caption("Stack: pypdf · pdfplumber · spaCy · langdetect · "
               "Gemini Flash · deep-translator · gTTS · Streamlit")

# -------------------- upload --------------------

uploaded = st.file_uploader("Upload a PDF document", type=["pdf"])
col_hint, col_sample = st.columns([3, 1])
with col_sample:
    try:
        with open("sample_discharge.pdf", "rb") as f:
            st.download_button("⬇️ Try the sample PDF", f.read(),
                               file_name="sample_discharge.pdf")
    except FileNotFoundError:
        pass

if uploaded is None:
    st.info("Upload a PDF to begin — or download the sample document above "
            "and drop it back in. 🙂", icon="👆")
    st.stop()

file_bytes = uploaded.read()
digest = hashlib.md5(file_bytes).hexdigest()[:8]
st.caption(f"**{uploaded.name}** · {len(file_bytes)/1024:.0f} KB · id `{digest}`")

with st.spinner("Parsing pages…"):
    pages = cached_pages(file_bytes)
if not pages:
    st.error("No pages could be extracted from this file.")
    st.stop()

# -------------------- page selector --------------------

left, right = st.columns([2, 3])
with left:
    scope = st.radio("Process", ["One page at a time", "Entire document"],
                     horizontal=True)
with right:
    page_no = st.selectbox("Page", range(1, len(pages) + 1),
                           format_func=lambda n: f"Page {n} of {len(pages)}") \
        if scope == "One page at a time" else None

page_indices = [page_no - 1] if scope == "One page at a time" else list(range(len(pages)))
if st.button("▶️ Analyze", type="primary"):
    st.session_state["run"] = True
if not st.session_state.get("run"):
    st.stop()

# -------------------- main loop over selected pages --------------------
key_present = engine.online()

for idx in page_indices:
    raw_page = pages[idx]
    lang = textproc.detect_language(raw_page)
    st.markdown(f"<span class='dm-page'>Page {idx + 1}</span>"
                f"<span class='dm-badge'>detected language: {lang}</span>",
                unsafe_allow_html=True)

    if not raw_page.strip():
        st.warning("This page has no readable text (a scanned image?). "
                   "Install Tesseract OCR to process such pages.")
        continue

    with st.spinner(f"Analyzing page {idx + 1}…"):
        para = cached_summary(key_present, raw_page, "paragraph")
        bullets = cached_summary(key_present, raw_page, "bullets")
        audio_text = cached_summary(key_present, raw_page, "audio")
        terms = cached_glossary(key_present, raw_page)

        # ---- translation of every artefact ----
        t_para = cached_translation(para, lang_display)
        t_bullets = cached_translation(bullets, lang_display)
        t_audio = cached_translation(audio_text, lang_display)

    # ---- dual panels (paper: side-by-side paragraph + bullets) ----
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📖 Paragraph summary")
        st.write(t_para)
    with c2:
        st.subheader("⚡ Bullet summary")
        for line in t_bullets.splitlines():
            line = line.strip()
            if line:
                st.markdown(line if line.startswith(("-", "•")) else "- " + line)

    # ---- audio-friendly + player ----
    st.subheader("🔊 Audio-friendly summary")
    st.write(t_audio)
    with st.spinner("Synthesizing speech…"):
        mp3 = cached_audio(t_audio, lang_display)
    if mp3:
        st.audio(mp3, format="audio/mp3")
        st.download_button("⬇️ Download audio (MP3)", mp3,
                           file_name=f"page{idx+1}_audio.mp3",
                           mime="audio/mpeg", key=f"aud{idx}")
    else:
        st.caption("Audio unavailable (offline TTS endpoint unreachable).")

    # ---- glossary ----
    st.subheader("📚 Vocabulary glossary")
    if terms:
        for t in terms:
            with st.expander(f"**{t['term']}**"):
                st.markdown(f"**As used here:** {t.get('sense','')}")
                st.markdown(f"**Simply:** {t.get('simple','')}")
                if lang_display != "English (original)":
                    st.markdown(f"**Translated:** " +
                                cached_translation(t.get("simple", ""), lang_display))
    else:
        st.caption("No difficult terms found on this page.")

    # ---- per-page downloads ----
    bundle = (f"DocMaster AI -- {uploaded.name} -- page {idx+1}\n"
              f"Language: {lang_display}\n\nPARAGRAPH:\n{t_para}\n\n"
              f"BULLETS:\n{t_bullets}\n\nAUDIO SCRIPT:\n{t_audio}\n")
    st.download_button("⬇️ Download page results (TXT)", bundle,
                       file_name=f"page{idx+1}_results.txt", key=f"txt{idx}")
    st.divider()

if not key_present:
    st.info("You are in offline demo mode. Get a free Gemini key at "
            "https://aistudio.google.com and paste it in the sidebar for "
            "full abstractive summaries and plain-language glossary.",
            icon="🔑")
