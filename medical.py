import streamlit as st
import openai
import pandas as pd
import os

# Load your OpenAI API key from Streamlit secrets
openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="AI Medical Assistant", layout="centered")
st.title("🩺 AI Medical Assistant")
st.write("Upload lab results and optionally describe symptoms to get suggestions from AI.")

# Upload CSV file
uploaded_file = st.file_uploader("📄 Upload Lab Test Results (CSV format)", type="csv")

# Optional symptoms input
symptoms = st.text_area("📝 Describe patient symptoms (optional)", height=120)

# Submit button
if st.button("Analyze and Recommend"):
    if uploaded_file:
        # Read and convert lab results to string
        try:
            lab_df = pd.read_csv(uploaded_file)
            lab_data = lab_df.to_string(index=False)
        except Exception as e:
            st.error(f"⚠️ Error reading file: {e}")
            st.stop()

        # Compose prompt
        prompt = f"""
        A patient presents with the following lab test results:

        {lab_data}

        {'They are also experiencing the following symptoms: ' + symptoms if symptoms else ''}

        As a qualified AI medical assistant, provide:
        - Possible diagnoses
        - Recommended medications
        - Any further lab tests or medical actions needed
        Keep it medically clear and concise.
        """

        # OpenAI call
        try:
            with st.spinner("Analyzing..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=800
                )
            st.subheader("🧾 AI Suggestions:")
            st.markdown(response['choices'][0]['message']['content'])

        except Exception as e:
            st.error(f"❌ OpenAI API error: {e}")
    else:
        st.warning("Please upload a lab test file to continue.")
