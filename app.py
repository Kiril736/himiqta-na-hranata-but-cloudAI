import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Food Label Analyzer",
    page_icon="🧪",
    layout="centered"
)

# ─────────────────────────────────────────────
# OCR MODEL (CACHED)
# ─────────────────────────────────────────────
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en', 'bg'], verbose=False)

reader = load_reader()

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
harmful_e_numbers = {
    "E250": "Sodium nitrite – may increase health risks",
    "E407": "Carrageenan – possible digestive irritation",
    "E450": "Diphosphates – may affect kidneys",
    "E621": "MSG – may cause headaches",
    "E952": "Cyclamate – artificial sweetener",
    "E150d": "Caramel colour - a lot from it can make you pass out",
    "E330": "sodium - can make your bones softer"
}

ingredient_warnings = {
    "palm oil": "Highly processed fat",
    "preservative": "May contain nitrates/sulfites",
    "phosphate": "May affect kidneys",
    "sweetener": "Artificial sweeteners should be limited",
    "colouring": "May trigger allergies",
    "палмово масло": "Силно преработено",
    "лактоза": "Може да причини дискомфорт",
}

alternatives = {
    "sausage": ["Grilled chicken", "Eggs", "Home-cooked meat"],
    "chips": ["Baked potatoes", "Nuts", "Popcorn"],
    "soda": ["Sparkling water", "Tea", "Homemade lemonade"]
}

trigger_map = {
    "sausage": ["sausage", "колбас", "луканка", "шунка"],
    "chips": ["chips", "чипс"],
    "soda": ["soda", "cola", "газирано"]
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def normalize_text(text):
    text = text.lower()
    text = text.replace("-", "").replace(",", "")
    return text

def find_e_numbers(text):
    pattern = r"\bE[\s-]?\d{3}\b"
    matches = re.findall(pattern, text.upper())
    return list(set(m.replace(" ", "").replace("-", "") for m in matches))

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
st.title("🧪 Food Label Analyzer")

uploaded_file = st.file_uploader("Upload label", type=["png", "jpg", "jpeg"])
camera_image = st.camera_input("Or take a photo")

image_source = uploaded_file if uploaded_file else camera_image

# ─────────────────────────────────────────────
# PROCESS
# ─────────────────────────────────────────────
if image_source:

    try:
        image = Image.open(image_source)
        st.image(image, caption="Label", use_container_width=True)

        with st.spinner("Scanning..."):
            image_np = np.array(image)

            # get confidence too
            results = reader.readtext(image_np, detail=1)

            extracted_text = " ".join([r[1] for r in results])

        text_clean = normalize_text(extracted_text)

        # ───────── TEXT
        st.subheader("📄 Recognized Text")
        st.text_area("", extracted_text, height=150)

        # ───────── E NUMBERS
        st.subheader("🚨 Harmful E-Numbers")

        detected_e = find_e_numbers(extracted_text)
        found_e = []

        for code in detected_e:
            if code in harmful_e_numbers:
                found_e.append((code, harmful_e_numbers[code]))

        if found_e:
            for code, desc in found_e:
                st.error(f"{code} → {desc}")
        else:
            st.success("No harmful E-numbers detected")

        # ───────── INGREDIENTS
        st.subheader("⚠️ Ingredient Warnings")

        found_keywords = []

        for keyword, warning in ingredient_warnings.items():
            if keyword in text_clean:
                found_keywords.append((keyword, warning))

        if found_keywords:
            for keyword, warning in set(found_keywords):
                st.warning(f"{keyword} → {warning}")
        else:
            st.success("No risky ingredients found")

        # ───────── ALTERNATIVES
        st.subheader("🥗 Alternatives")

        shown = False

        for category, triggers in trigger_map.items():
            if any(t in text_clean for t in triggers):
                st.info(f"Better than {category}:")
                for item in alternatives[category]:
                    st.write(f"✓ {item}")
                shown = True

        if not shown:
            st.write("No specific alternatives")

        # ───────── CONFIDENCE (NEW)
        with st.expander("🔍 OCR Confidence Details"):
            for _, text, conf in results:
                st.write(f"{text} ({round(conf, 2)})")

        # ───────── REPORT
        report = f"""
FOOD LABEL REPORT
====================

TEXT:
{extracted_text}

E-NUMBERS:
{found_e if found_e else "None"}

WARNINGS:
{found_keywords if found_keywords else "None"}
"""

        st.download_button(
            "Download Report",
            report,
            file_name="report.txt"
        )

    except Exception as e:
        st.error("Error processing image")
        st.exception(e)
