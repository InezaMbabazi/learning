import streamlit as st
import openai
import fitz  # PyMuPDF
import io

# Initialize OpenAI API with the secret key
openai.api_key = st.secrets["openai"]["api_key"]

# Function to generate questions based on lesson content
def generate_questions_from_content(lesson_content):
    prompt = f"Generate 3 questions based on the following lesson content:\n{lesson_content}\n\nMake sure the questions test the student's understanding."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    generated_questions = response['choices'][0]['message']['content'].strip().split("\n")
    return generated_questions

# Function to load PDF content and extract images
def load_pdf_content(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")  # Use stream to read the file
        content = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")  # Get the text from the page
            images = []
            
            # Extract images
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_stream = io.BytesIO(image_bytes)
                images.append((image_stream, page_num))  # Store image stream and page number

            content.append((text.strip(), images))  # Store text and images for each page

        return content
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")
        return []

# Function to display content for a specific page
def display_page_content(page_content):
    text, images = page_content
    st.subheader("Extracted Content")
    st.write(text)  # Display the extracted text content

    for image_stream, page_num in images:
        st.image(image_stream, use_column_width=True)
        st.write(f"Image from Page {page_num + 1}")

# Streamlit UI
st.image("header.png", use_column_width=True)
st.title("Kepler College AI-Powered Lesson Assistant")

st.markdown("""
    <div style="background-color: #f0f0f5; padding: 20px; border-radius: 10px;">
        <h3 style="color: #2E86C1;">Welcome to Kepler College's AI-Powered Lesson Assistant</h3>
        <p>Upload your lesson content in <strong>PDF format</strong>, or type the lesson content manually.</p>
    </div>
    """, unsafe_allow_html=True)

# Option 1: Upload PDF file
st.subheader("Option 1: Upload PDF File")
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

# Option 2: Manual text input
st.subheader("Option 2: Paste Specific Lesson Content Here")
manual_content = st.text_area("Paste lesson content here:")

# Load content from PDF or manual input
pdf_content = []
if uploaded_file is not None:
    pdf_content = load_pdf_content(uploaded_file)  # Load the PDF content
    st.session_state.pdf_content = pdf_content  # Store in session state
    st.session_state.current_page = 0  # Reset to first page on new upload
elif manual_content:
    st.session_state.pdf_content = [(manual_content, [])]  # Store manual content as a single page
    st.session_state.current_page = 0  # Reset to first page

# Initialize current_page if not already done
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

# Check if pdf_content is available
if 'pdf_content' in st.session_state and st.session_state.pdf_content:
    # Ensure current_page is within bounds
    st.session_state.current_page = min(st.session_state.current_page, len(st.session_state.pdf_content) - 1)
    current_page_content = st.session_state.pdf_content[st.session_state.current_page]
    display_page_content(current_page_content)  # Display the content for the current page

    # Pagination controls
    if st.session_state.current_page > 0:
        if st.button("Previous Page"):
            st.session_state.current_page -= 1

    if st.session_state.current_page < len(st.session_state.pdf_content) - 1:
        if st.button("Next Page"):
            st.session_state.current_page += 1

    # Show current page number
    st.write(f"Page {st.session_state.current_page + 1} of {len(st.session_state.pdf_content)}")

# Generate questions if content is available
if 'pdf_content' in st.session_state and st.session_state.pdf_content:
    lesson_content = st.session_state.pdf_content[st.session_state.current_page][0]
    if st.button("Generate Questions"):
        st.session_state.generated_questions = generate_questions_from_content(lesson_content)
    
    if 'generated_questions' in st.session_state and st.session_state.generated_questions:
        st.subheader("Test Questions")

        # Student answers section
        student_answers = []
        with st.form(key='question_form'):
            for i, question in enumerate(st.session_state.generated_questions):
                st.write(f"Question {i+1}: {question}")
                answer = st.text_input(f"Your answer to question {i+1}", key=f"answer_{i}")
                student_answers.append(answer)
            
            # Submit button for form
            submit = st.form_submit_button("Submit Answers")
            
            if submit and all(student_answers):
                feedback = get_grading(student_answers, st.session_state.generated_questions, lesson_content)
                st.subheader("Feedback on Your Answers:")
                st.markdown(f"<div class='chatbox'>{feedback}</div>", unsafe_allow_html=True)
            elif submit:
                st.warning("Please answer all questions before submitting.")
else:
    st.write("Please upload a PDF file or enter the lesson content manually.")
