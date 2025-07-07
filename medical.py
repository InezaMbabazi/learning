import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI Doctor Assistant", layout="centered")
st.title("🧑‍⚕️ AI Medical Assistant")

st.write("Describe the patient's symptoms below:")

# Input box for symptoms
symptoms = st.text_area("📝 Patient Symptoms", height=150)

if st.button("Get Diagnosis & Medication"):
    if symptoms:
        with st.spinner("Analyzing symptoms..."):
            prompt = f"""
            A patient reports the following symptoms: {symptoms}.
            As a medical assistant, suggest possible illnesses and appropriate medications that can be used.
            Make sure to mention if further lab tests or a physical checkup are recommended.
            """
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=700
                )
                st.success("Here is the medical suggestion:")
                st.markdown(response['choices'][0]['message']['content'])

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter the symptoms.")

