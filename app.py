import streamlit as st
import easyocr
import numpy as np
from PIL import Image

st.set_page_config(
    page_title="Food Label Analyzer",
    page_icon="🧪",
    layout="centered"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Page background */
    .stApp { background-color: #f8f9fa; }

    /* Hide default Streamlit header padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 720px; }

    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
        color: white;
    }
    .hero h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; letter-spacing: -0.5px; }
    .hero p  { font-size: 1rem; opacity: 0.75; margin: 0; }

    /* Upload card */
    .upload-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }

    /* Section heading */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin: 1.5rem 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* Result cards */
    .result-box {
        background: white;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }

    /* Pill badges */
    .badge-danger  { display:inline-block; background:#fdecea; color:#c0392b; border-radius:999px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin-right:6px; }
    .badge-warning { display:inline-block; background:#fff8e1; color:#b7791f; border-radius:999px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin-right:6px; }
    .badge-success { display:inline-block; background:#e9f7ef; color:#1a7a4a; border-radius:999px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin-right:6px; }
    .badge-info    { display:inline-block; background:#e8f4fd; color:#1565c0; border-radius:999px; padding:2px 10px; font-size:0.8rem; font-weight:600; margin-right:6px; }

    /* Ingredient row */
    .ingredient-row {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .ingredient-row:last-child { border-bottom: none; }
    .ingredient-name { font-weight: 600; font-size: 0.9rem; color: #1a1a2e; min-width: 140px; }
    .ingredient-desc { font-size: 0.875rem; color: #555; }

    /* Alternative item */
    .alt-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: #f0faf5;
        border-radius: 8px;
        margin-bottom: 0.4rem;
        font-size: 0.9rem;
        color: #1a7a4a;
        font-weight: 500;
    }

    /* OCR text area */
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
        font-size: 0.875rem !important;
        background: #fafafa !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: #1a1a2e !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
    }

    /* Divider */
    hr { border: none; border-top: 1px solid #eee; margin: 1.5rem 0; }

    /* Footer */
    .footer { text-align: center; font-size: 0.8rem; color: #aaa; margin-top: 2rem; }

    /* Hide Streamlit file uploader default label clutter */
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 10px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🧪 Food Label Analyzer</h1>
    <p>Upload a photo of any food label — we'll scan it, flag risky additives, and suggest healthier alternatives.</p>
</div>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
harmful_e_numbers = {
    "E250": "Sodium nitrite – potential risk with excessive consumption",
    "E407": "Carrageenan – possible digestive issues",
    "E450": "Diphosphates – may affect kidneys",
    "E621": "Monosodium glutamate – possible headaches",
    "E952": "Cyclamate – artificial sweetener",
    "E471": "Emulsifier",
    "E472": "Emulsifier",
    "E330": "Citric acid – may irritate tooth enamel",
    "E300": "Ascorbic acid – irritates stomach in large amounts",
    "E262": "Sodium acetate",
}

ingredient_warnings = {
    "palm oil":      "Palm oil is often heavily processed",
    "preservative":  "Preservatives may contain nitrates or sulfites",
    "phosphate":     "Phosphates may negatively affect kidneys",
    "lactose":       "Lactose may cause discomfort in intolerant individuals",
    "sweetener":     "Artificial sweeteners should be limited",
    "colouring":     "Some colorings can trigger allergies",
    "палмово масло": "Палмовото масло е силно преработено",
    "консерван":     "Консервантите могат да съдържат нитрати",
    "фосфат":        "Фосфатите могат да влияят на бъбреците",
    "лактоза":       "Лактозата може да причини дискомфорт",
    "подсладител":   "Изкуствените подсладители трябва да се ограничават",
    "оцветител":     "Някои оцветители могат да причинят алергии",
}

alternatives = {
    "sausage":  ["Grilled chicken breast", "Home-cooked meat", "Eggs with vegetables"],
    "chips":    ["Baked potatoes", "Mixed nuts", "Homemade popcorn"],
    "soda":     ["Sparkling water", "Homemade lemonade", "Unsweetened tea"],
    "колбас":   ["Печено пиле", "Домашно месо", "Яйца със зеленчуци"],
    "чипс":     ["Печени картофи", "Ядки", "Домашен пуканки"],
    "газирано": ["Минерална вода", "Домашна лимонада", "Чай без захар"],
}

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📂 Upload a label image</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose a PNG, JPG or JPEG file",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed",
)

st.markdown('<p class="section-title">📸 Or take a photo</p>', unsafe_allow_html=True)

camera_image = st.camera_input("Take a photo of the label", label_visibility="collapsed")

image_source = uploaded_file or camera_image

# ── Processing ────────────────────────────────────────────────────────────────
if image_source:
    image = Image.open(image_source)

    col_img, _ = st.columns([2, 1])
    with col_img:
        st.image(image, caption="Uploaded label", use_container_width=True)

    with st.spinner("🔍 Scanning label with AI (this may take a moment)…"):
        reader = easyocr.Reader(['bg', 'en'], verbose=False)
        image_np = np.array(image)
        results = reader.readtext(image_np, detail=0)
        extracted_text = " ".join(results)

    text_upper = extracted_text.upper()
    text_lower = extracted_text.lower()

    # ── Recognised text ───────────────────────────────────────────────────────
    st.markdown('<p class="section-title">📄 Recognised text</p>', unsafe_allow_html=True)
    with st.container():
        st.text_area("", extracted_text, height=180, label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── E-numbers ─────────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">🚨 Detected harmful E-numbers</p>', unsafe_allow_html=True)

    found_e = [(code, desc) for code, desc in harmful_e_numbers.items() if code in text_upper]

    if found_e:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        for code, desc in found_e:
            st.markdown(
                f'<div class="ingredient-row">'
                f'<span class="badge-danger">{code}</span>'
                f'<div><span class="ingredient-desc">{desc}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="result-box"><span class="badge-success">✓ No harmful E-numbers detected</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Ingredient keywords ───────────────────────────────────────────────────
    st.markdown('<p class="section-title">⚠️ Flagged ingredient keywords</p>', unsafe_allow_html=True)

    found_kw = [(kw, warn) for kw, warn in ingredient_warnings.items() if kw in text_lower]

    if found_kw:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        for kw, warn in found_kw:
            st.markdown(
                f'<div class="ingredient-row">'
                f'<span class="badge-warning">{kw}</span>'
                f'<span class="ingredient-desc">{warn}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="result-box"><span class="badge-success">✓ No risky keywords found</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Alternatives ──────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">🥗 Healthier alternatives</p>', unsafe_allow_html=True)

    shown_alts = False
    trigger_map = {
        "sausage":  ["sausage", "lukanка", "луканка", "шунка", "колбас"],
        "chips":    ["chips", "чипс"],
        "soda":     ["soda", "cola", "газирано"],
    }

    for category, triggers in trigger_map.items():
        if any(t in text_lower for t in triggers):
            label_en = {"sausage": "Instead of processed meat", "chips": "Instead of chips", "soda": "Instead of fizzy drinks"}[category]
            st.markdown(f'<p style="font-size:0.85rem;color:#888;margin:0.5rem 0 0.25rem">{label_en}:</p>', unsafe_allow_html=True)
            # pick from whichever key exists
            items = alternatives.get(category) or alternatives.get(list(alternatives.keys())[0])
            for item in items:
                st.markdown(f'<div class="alt-item">✓ {item}</div>', unsafe_allow_html=True)
            shown_alts = True

    if not shown_alts:
        st.markdown(
            '<div class="result-box"><span class="badge-info">No specific alternatives suggested for this product.</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Report download ───────────────────────────────────────────────────────
    st.markdown('<p class="section-title">📥 Download report</p>', unsafe_allow_html=True)

    report_lines = ["FOOD LABEL ANALYSIS REPORT", "=" * 40, "",
                    "RECOGNISED TEXT:", extracted_text, "", "-" * 40, "DETECTED E-NUMBERS:"]
    if found_e:
        report_lines += [f"  {c} — {d}" for c, d in found_e]
    else:
        report_lines.append("  None detected.")

    report_lines += ["", "-" * 40, "FLAGGED KEYWORDS:"]
    if found_kw:
        report_lines += [f"  {k} — {w}" for k, w in found_kw]
    else:
        report_lines.append("  None detected.")

    report = "\n".join(report_lines)

    st.download_button(
        label="⬇️  Download TXT report",
        data=report,
        file_name="food_label_report.txt",
        mime="text/plain",
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">Food Chemistry + AI · Python · Streamlit · EasyOCR</div>',
    unsafe_allow_html=True,
)
