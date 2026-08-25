# Regenerates sample_discharge.pdf -- the 2-page test document whose
# first page is the worked example (Fig. 2) from the IEEE paper.
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PAGE1 = [
    "CITY CARE HOSPITAL -- DISCHARGE SUMMARY (Page 1 of 2)",
    "",
    "The patient, a 58-year-old male with a ten-year history of hypertension, was",
    "prescribed amlodipine 5 mg once daily after his blood pressure averaged 158/96",
    "mmHg across three visits. Lifestyle counselling on sodium restriction and aerobic",
    "exercise was provided, and a follow-up lipid profile was ordered given his family",
    "history of coronary artery disease. He was educated on home blood-pressure",
    "monitoring and advised to record readings twice daily. No adverse drug reactions",
    "were observed during the admission, and fasting blood glucose remained within",
    "the normal reference range throughout his stay.",
]

PAGE2 = [
    "CITY CARE HOSPITAL -- INSTRUCTIONS (Page 2 of 2)",
    "",
    "Take one amlodipine tablet every morning with water, at roughly the same time",
    "each day. Do not stop the medicine suddenly, even if you feel well. Reduce salt",
    "intake to less than one teaspoon per day and walk briskly for thirty minutes at",
    "least five days a week. Report immediately if you notice swelling of the ankles,",
    "unusual dizziness, or chest discomfort. Your lipid profile is scheduled at the",
    "central laboratory next Monday between 7 and 10 in the morning; twelve hours of",
    "fasting is required before the blood draw. The next cardiology review is booked",
    "for the 14th of next month. Bring your home readings diary to every visit.",
]


def build(path="sample_discharge.pdf"):
    c = canvas.Canvas(path, pagesize=letter)
    for page in (PAGE1, PAGE2):
        y = 10.2 * inch
        c.setFont("Helvetica", 11)
        for line in page:
            c.drawString(0.9 * inch, y, line)
            y -= 16
        c.showPage()
    c.save()
    print("wrote", path)


if __name__ == "__main__":
    build()
