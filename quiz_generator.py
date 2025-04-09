import streamlit as st
import os
import requests
import re
from dotenv import load_dotenv

# Load the API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("API Key is missing. Please set GEMINI_API_KEY in the .env file.")
    st.stop()

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Parse the response text into quiz questions
def parse_questions(raw_text):
    questions = []
    blocks = raw_text.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        q_data = {"question": "", "options": [], "answer": ""}
        for line in lines:
            if line.startswith("Question:"):
                q_data["question"] = line.replace("Question:", "").strip()
            elif re.match(r"^[A-D][).]", line.strip()):
                q_data["options"].append(line.strip())
            elif line.startswith("Answer:"):
                q_data["answer"] = line.replace("Answer:", "").strip().upper()
        if q_data["question"] and q_data["options"] and q_data["answer"]:
            questions.append(q_data)
    return questions

# Fetch questions using Gemini API
def fetch_questions(text_content, quiz_level):
    prompt = f"""
    You are an expert in creating multiple-choice quizzes.
    Based on the following text, generate 5 multiple-choice questions with 4 answer options each at a {quiz_level} difficulty level.

    Text: {text_content}

    Format:
    Question: [Question Text]
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    Answer: [Correct Option Letter]
    """

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        data = response.json()
        if response.status_code == 200 and "candidates" in data:
            result_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return parse_questions(result_text)
        else:
            st.error(f"Error {response.status_code}: {data.get('message', 'Unknown error')}")
    except Exception as e:
        st.error(f"API Error: {str(e)}")

    return None

# Display quiz questions
def display_quiz():
    st.subheader("Quiz")
    questions = st.session_state["questions"]
    all_answered = True
    selected_answers = []

    with st.form("quiz_form"):
        for index, question in enumerate(questions):
            selected = st.radio(
                label=f"Q{index + 1}. {question['question']}",
                options=question["options"],
                key=f"q_{index}",
                index=None
            )
            if selected:
                selected_answers.append(selected[0])  
            else:
                all_answered = False
                selected_answers.append(None)

        submitted = st.form_submit_button("Submit Quiz")

    if submitted:
        if not all_answered:
            st.warning("Please answer all questions before submitting.")
            return

        score = 0
        st.subheader("Quiz Results")
        for i, (q, user_answer) in enumerate(zip(questions, selected_answers)):
            correct = q["answer"]
            if user_answer.upper() == correct:
                st.success(f"Q{i + 1}: Correct (Your Answer: {user_answer})")
                score += 1
            else:
                correct_option = next((opt for opt in q["options"] if opt.startswith(correct)), "Not found")
                st.error(f"Q{i + 1}: Incorrect (Your Answer: {user_answer})")
                st.info(f"Correct Answer: {correct_option}")

        st.markdown(f"Final Score: {score}/{len(questions)}")

        # Encouragement messages and effects
        if score == len(questions):
            st.balloons()
            st.success("Perfect Score! You're a quiz master!")
        elif score >= len(questions) * 0.7:
            st.snow()
            st.success("Great job! You're almost there! Keep it up!")
        elif score >= len(questions) * 0.4:
            st.info("Not bad! You're improving!")
        else:
            st.warning("Don’t give up! Every mistake is a step forward.")

        st.markdown("---")
        st.markdown("Want to try again with new content? Just paste it above and hit 'Generate Quiz'.")

# Main app function
def main():
    st.set_page_config(page_title="AI Quiz Generator", layout="centered")
    st.title("AI Quiz Generator")
    st.write("Paste your content below and generate a quiz using AI.")

    text_content = st.text_area("Enter your content here:")
    quiz_level = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"]).lower()

    if st.button("Generate Quiz"):
        if not text_content.strip():
            st.warning("Please enter some content before generating a quiz.")
            return
        st.info("Generating quiz, please wait...")
        questions = fetch_questions(text_content, quiz_level)
        if not questions:
            st.error("Could not generate quiz. Please try again.")
            return
        st.session_state["questions"] = questions

    if "questions" in st.session_state:
        display_quiz()

if __name__ == "__main__":
    main()
