import pandas as pd
import streamlit as st
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("🧑‍⚕️ AI Medical Assistant with Lab Results")

# File upload
uploaded_file = st.file_uploader("📁 Upload Lab Test Results (CSV)", type="csv")
symptoms = st.text_area("📝 Enter Patient Symptoms (optional)", height=100)

if st.button("Analyze and Recommend"):
    if uploaded_file:
        lab_df = pd.read_csv(uploaded_file)
        lab_text = lab_df.to_string(index=False)

        prompt = f"""
        A patient has the following lab test results:
        {lab_text}
        {'They are also experiencing: ' + symptoms if symptoms else ''}
        
        As a medical assistant, analyze the data and suggest:
        - Likely diagnoses
        - Recommended medications
        - Any additional tests or actions
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            st.subheader("🧾 Medical Suggestions:")
            st.markdown(response['choices'][0]['message']['content'])

        except Exception as e:
            st.error(f"OpenAI API Error: {e}")
    else:
        st.warning("Please upload a lab test file.")
