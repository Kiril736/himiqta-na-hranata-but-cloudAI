import streamlit as st
import easyocr
import numpy as np
from PIL import Image

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Food Label Analyzer",
    page_icon="🧪",
    layout="centered"
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>

.stApp {
    background-color: #f8f9fa;
}

.block-container {
    padding-top: 2rem;
    max-width: 760px;
}

.hero {
    background: linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
    border-radius: 18px;
    padding: 2.5rem;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

.hero h1 {
    margin: 0;
    font-size: 2.2rem;
}

.hero p {
    opacity: 0.85;
    margin-top: 0.5rem;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    color: #1a1a2e;
}

.result-box {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}

.badge-danger {
    background: #fdecea;
    color: #c0392b;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.badge-warning {
    background: #fff3cd;
    color: #946200;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.badge-success {
    background: #e9f7ef;
    color: #1a7a4a;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.alt-item {
    background: #eefaf2;
    color: #1a7a4a;
    padding: 0.7rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.footer {
    text-align: center;
    color: #aaa;
    margin-top: 3rem;
    font-size: 0.85rem;
}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🧪 Food Label Analyzer</h1>
    <p>
        Upload a food label and detect harmful additives,
        risky ingredients, and healthier alternatives.
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# OCR MODEL (CACHED)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en', 'bg'], verbose=False)

reader = load_reader()

# ─────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────
harmful_e_numbers = {
    "E250": "Sodium nitrite – excessive intake may increase health risks",
    "E407": "Carrageenan – possible digestive irritation",
    "E450": "Diphosphates – excessive use may affect kidneys",
    "E621": "MSG – may cause headaches in sensitive individuals",
    "E952": "Cyclamate – artificial sweetener",
    "E471": "Emulsifier",
    "E472": "Emulsifier",
    "E330": "Citric acid – may affect tooth enamel",
    "E300": "Ascorbic acid – large amounts may irritate stomach",
    "E262": "Sodium acetate"
}

ingredient_warnings = {
    "palm oil": "Palm oil is often highly processed",
    "preservative": "Preservatives may contain nitrates or sulfites",
    "phosphate": "Phosphates may negatively affect kidneys",
    "sweetener": "Artificial sweeteners should be limited",
    "colouring": "Some colorings may trigger allergies",
    "лактоза": "Лактозата може да причини дискомфорт",
    "палмово масло": "Палмовото масло е силно преработено",
}

alternatives = {
    "sausage": [
        "Grilled chicken breast",
        "Home-cooked meat",
        "Eggs with vegetables"
    ],
    "chips": [
        "Baked potatoes",
        "Mixed nuts",
        "Homemade popcorn"
    ],
    "soda": [
        "Sparkling water",
        "Homemade lemonade",
        "Unsweetened tea"
    ]
}

trigger_map = {
    "sausage": ["sausage", "колбас", "луканка", "шунка"],
    "chips": ["chips", "чипс"],
    "soda": ["soda", "cola", "газирано"]
}

# ─────────────────────────────────────────────────────────────
# FILE INPUT
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<p class="section-title">📂 Upload a label image</p>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload image",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed"
)

st.markdown(
    '<p class="section-title">📸 Or take a photo</p>',
    unsafe_allow_html=True
)

camera_image = st.camera_input(
    "Take photo",
    label_visibility="collapsed"
)

# SELECT IMAGE SOURCE
image_source = uploaded_file if uploaded_file else camera_image

# ─────────────────────────────────────────────────────────────
# PROCESS IMAGE
# ─────────────────────────────────────────────────────────────
if image_source:

    try:
        image = Image.open(image_source)

        st.image(
            image,
            caption="Uploaded label",
            use_container_width=True
        )

        with st.spinner("🔍 Scanning label..."):

            image_np = np.array(image)

            results = reader.readtext(
                image_np,
                detail=0
            )

            extracted_text = " ".join(results)

        text_upper = extracted_text.upper()
        text_lower = extracted_text.lower()

        # ─────────────────────────────────────────
        # RECOGNIZED TEXT
        # ─────────────────────────────────────────
        st.markdown(
            '<p class="section-title">📄 Recognized Text</p>',
            unsafe_allow_html=True
        )

        st.text_area(
            "",
            extracted_text,
            height=180,
            label_visibility="collapsed"
        )

        # ─────────────────────────────────────────
        # E-NUMBERS
        # ─────────────────────────────────────────
        st.markdown(
            '<p class="section-title">🚨 Harmful E-Numbers</p>',
            unsafe_allow_html=True
        )

        found_e = []

        for code, desc in harmful_e_numbers.items():
            if code in text_upper:
                found_e.append((code, desc))

        st.markdown('<div class="result-box">', unsafe_allow_html=True)

        if found_e:
            for code, desc in found_e:
                st.markdown(
                    f"""
                    <p>
                        <span class="badge-danger">{code}</span>
                        {desc}
                    </p>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<span class="badge-success">✓ No harmful E-numbers detected</span>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ─────────────────────────────────────────
        # INGREDIENT WARNINGS
        # ─────────────────────────────────────────
        st.markdown(
            '<p class="section-title">⚠️ Ingredient Warnings</p>',
            unsafe_allow_html=True
        )

        found_keywords = []

        for keyword, warning in ingredient_warnings.items():
            if keyword in text_lower:
                found_keywords.append((keyword, warning))

        st.markdown('<div class="result-box">', unsafe_allow_html=True)

        if found_keywords:
            for keyword, warning in found_keywords:
                st.markdown(
                    f"""
                    <p>
                        <span class="badge-warning">{keyword}</span>
                        {warning}
                    </p>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<span class="badge-success">✓ No risky ingredients found</span>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ─────────────────────────────────────────
        # ALTERNATIVES
        # ─────────────────────────────────────────
        st.markdown(
            '<p class="section-title">🥗 Healthier Alternatives</p>',
            unsafe_allow_html=True
        )

        shown_alternatives = False

        for category, triggers in trigger_map.items():

            if any(trigger in text_lower for trigger in triggers):

                st.markdown(
                    '<div class="result-box">',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<b>Better alternatives to {category}:</b>",
                    unsafe_allow_html=True
                )

                for item in alternatives[category]:
                    st.markdown(
                        f'<div class="alt-item">✓ {item}</div>',
                        unsafe_allow_html=True
                    )

                st.markdown('</div>', unsafe_allow_html=True)

                shown_alternatives = True

        if not shown_alternatives:
            st.markdown(
                """
                <div class="result-box">
                    No specific alternatives suggested.
                </div>
                """,
                unsafe_allow_html=True
            )

        # ─────────────────────────────────────────
        # REPORT DOWNLOAD
        # ─────────────────────────────────────────
        st.markdown(
            '<p class="section-title">📥 Download Report</p>',
            unsafe_allow_html=True
        )

        report = f"""
FOOD LABEL ANALYSIS REPORT
========================================

RECOGNIZED TEXT:
{extracted_text}

----------------------------------------
HARMFUL E-NUMBERS:
"""

        if found_e:
            for code, desc in found_e:
                report += f"\n{code} — {desc}"
        else:
            report += "\nNone detected."

        report += "\n\n----------------------------------------\n"
        report += "INGREDIENT WARNINGS:\n"

        if found_keywords:
            for keyword, warning in found_keywords:
                report += f"\n{keyword} — {warning}"
        else:
            report += "\nNone detected."

        st.download_button(
            label="⬇️ Download TXT Report",
            data=report,
            file_name="food_label_report.txt",
            mime="text/plain"
        )

    except Exception as e:

        st.error("❌ Error processing image")
        st.exception(e)

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="footer">
        Food Chemistry + AI · Streamlit · EasyOCR
    </div>
    """,
    unsafe_allow_html=True
)
