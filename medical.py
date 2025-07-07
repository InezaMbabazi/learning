import streamlit as st
import openai
import pandas as pd
from PIL import Image
import pytesseract
import os

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("🩺 AI Medical Assistant")
st.write("Upload lab results (CSV or image) and enter symptoms for diagnosis support.")

# Upload options
uploaded_file = st.file_uploader("📄 Upload Lab Test Results (CSV format)", type=["csv"])
uploaded_image = st.file_uploader("🖼️ Upload Lab Result Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
symptoms = st.text_area("📝 Describe patient symptoms (optional)", height=120)

# Analyze button
if st.button("Analyze and Recommend"):
    lab_data = ""

    # Handle CSV
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            lab_data = df.to_string(index=False)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            st.stop()

    # Handle image
    elif uploaded_image:
        try:
            image = Image.open(uploaded_image)
            ocr_text = pytesseract.image_to_string(image)
            lab_data = ocr_text
            st.info("🧠 Extracted Text from Image:")
            st.text(ocr_text)
        except Exception as e:
            st.error(f"Error processing image: {e}")
            st.stop()

    # If no file was uploaded
    if not lab_data:
        st.warning("No lab data provided.")
        lab_data = "Lab data not available."

    # GPT Prompt
    prompt = f"""
    A patient presents with the following lab results or extracted text:

    {lab_data}

    {'They are also experiencing: ' + symptoms if symptoms else ''}

    Please provide:
    - Possible diagnoses
    - Recommended medications
    - Further tests or referrals if needed
    """

    with st.spinner("Analyzing..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            st.subheader("🧾 AI Suggestions:")
            st.markdown(response['choices'][0]['message']['content'])
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
