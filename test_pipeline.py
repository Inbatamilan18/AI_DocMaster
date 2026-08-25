# Headless end-to-end test of the DocMaster pipeline (no Streamlit).
import engine, docparser, textproc, services

print("== 1. parse sample pdf ==")
data = open("sample_discharge.pdf", "rb").read()
pages = [textproc.clean_text(p) for p in docparser.extract_pages(data)]
print(f"pages: {len(pages)} | page1 chars: {len(pages[0])}")
assert len(pages) == 2 and "hypertension" in pages[0]

print("== 2. language detect ==", textproc.detect_language(pages[0]))

print("== 3. engine mode ==", engine.configure(None), "(False = offline demo)")
page = pages[0]
print("\n-- paragraph --\n", engine.summarize(page, "paragraph")[:300])
print("\n-- bullets --\n", engine.summarize(page, "bullets")[:300])
print("\n-- audio --\n", engine.summarize(page, "audio")[:400])
gl = engine.glossary(page)
print("\n-- glossary (first 3) --")
for g in gl[:3]:
    print(" *", g["term"], "|", g["sense"][:90])

print("\n== 4. translation (ta) ==")
out = services.translate_text("The patient was advised to reduce salt intake.", "Tamil (தமிழ்)")
print(out)

print("\n== 5. tts ==")
mp3 = services.tts_bytes("This is a fifty eight year old man.", "English (original)")
print("mp3 bytes:", len(mp3) if mp3 else "FAILED")
open("test_audio.mp3", "wb").write(mp3 or b"")

print("\nALL PIPELINE TESTS DONE")
