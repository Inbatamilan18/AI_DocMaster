# ------------------------------------------------------------------
# DocMaster AI -- prompt templates (Table II of the IEEE paper)
# Each template is filled with the text of ONE page and sent to the
# Gemini Flash model.  Keeping templates in one file makes them easy
# to tune and easy to show in the viva.
# ------------------------------------------------------------------

PARAGRAPH_PROMPT = """You are a careful document assistant.
Using ONLY the page text below, write a single flowing summary of 80-120 words.
Keep every number, name and date exactly as written. Add no outside facts.

PAGE TEXT:
\"\"\"{page}\"\"\"

PARAGRAPH SUMMARY:"""

BULLET_PROMPT = """You are a careful document assistant.
Using ONLY the page text below, extract 3 to 7 bullet points, one idea per bullet.
Preserve numbers, dates and named entities verbatim. Add no outside facts.
Return ONLY the bullets, one per line, each starting with "- ".

PAGE TEXT:
\"\"\"{page}\"\"\"

BULLET SUMMARY:"""

AUDIO_PROMPT = """You are a careful document assistant.
Rewrite the page text below so it can be read aloud by a text-to-speech engine.
Rules: short sentences; everyday words; spell out numbers and abbreviations in
words; no symbols, parentheses or bullet marks; second person where natural.
5-8 sentences maximum. Use ONLY information from the page text.

PAGE TEXT:
\"\"\"{page}\"\"\"

AUDIO-FRIENDLY SUMMARY:"""

GLOSSARY_PROMPT = """You are a careful document assistant.
From the page text below, pick up to {max_terms} specialist or difficult terms.
For every term return exactly three lines:
TERM: <the term as it appears>
SENSE: <the meaning that fits how the term is used on THIS page, one line>
SIMPLE: <a plain-language definition in one short line, as if explaining to a 12-year-old>
Use ONLY the page text. Do not include common everyday words.

PAGE TEXT:
\"\"\"{page}\"\"\"

GLOSSARY:"""
