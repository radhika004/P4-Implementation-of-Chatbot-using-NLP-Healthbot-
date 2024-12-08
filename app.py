import os
import json
import datetime
import csv
import nltk
import ssl
import streamlit as st
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Initialize necessary NLTK components
ssl._create_default_https_context = ssl._create_unverified_context
nltk.data.path.append(os.path.abspath("nltk_data"))
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Initialize lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Preprocessing function to clean text
def preprocess(text):
    # Convert to lowercase
    text = text.lower()
    # Remove non-alphabetic characters
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Tokenize and remove stopwords
    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return ' '.join(words)

# Load intents from the json file
file_path = os.path.abspath("./intents.json")
with open(file_path, "r") as file:
    intents = json.load(file)

# Extract patterns and responses
patterns = []
responses = {}
tags = []
for intent in intents:
    responses[intent['tag']] = intent['responses']
    tags.extend([intent['tag']] * len(intent["patterns"]))  # Create a list of tags corresponding to each pattern
    for pattern in intent["patterns"]:
        patterns.append(preprocess(pattern))  # Preprocess patterns

# Initialize TF-IDF Vectorizer
vectorizer = TfidfVectorizer(ngram_range=(1, 3))  # 1 to 3 n-grams
X = vectorizer.fit_transform(patterns)

def chatbot(input_text):
    # Preprocess and vectorize input
    input_text = preprocess(input_text)
    input_text_vectorized = vectorizer.transform([input_text])

    # Calculate cosine similarity between the input and all patterns
    similarity_scores = cosine_similarity(input_text_vectorized, X)
    max_sim_score_index = similarity_scores.argmax()  # Find the index with the highest similarity score
    max_sim_score = similarity_scores[0, max_sim_score_index]  # Extract the max similarity score

    # Define a threshold for matching confidence
    similarity_threshold = 0.5  # If the similarity score is below this, provide a fallback

    if max_sim_score >= similarity_threshold:
        # If the input matches well with a pattern, return the corresponding response
        matching_tag = tags[max_sim_score_index]  # Use the tag list to find the matching tag
        matching_pattern_index = patterns.index(patterns[max_sim_score_index])  # Get the index of the matched pattern
        response = responses[matching_tag][matching_pattern_index % len(responses[matching_tag])]  # Pick corresponding response
    else:
        # Fallback to a default message or dictionary meaning
        response = "Sorry, I couldn't understand that. Could you please ask something else?"

    return response

counter = 0

def main():
    global counter
    # Local variable to store conversation history
    conversation = []

    st.sidebar.markdown(f"**Developed by Radhika**", unsafe_allow_html=True)

    menu = ["Home", "Chat History", "About"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.title("Welcome to Healthbot!")
        st.markdown("<center>Your friendly health diagnosis assistant.</center>", unsafe_allow_html=True)

        st.write(
            """
            Ask me questions about health, symptoms, or general medical information,
            and I'll do my best to help.
            """
        )

        if not os.path.exists("chat_log.csv"):
            with open("chat_log.csv", "w", newline="", encoding="utf-8") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["User Input", "Chatbot Response", "Timestamp"])

        # Create a placeholder for conversation history
        conversation_placeholder = st.empty()

        # Display conversation dynamically in a scrollable area
        with conversation_placeholder.container():
            for speaker, msg in conversation:
                if speaker == "user":
                    # Left-aligned for user messages
                    st.markdown(f"<div style='text-align:left; background-color: #f1f0f0; color: #000; border-radius: 15px; padding: 10px; margin: 5px; width: auto; max-width: 60%;'>{msg}</div>", unsafe_allow_html=True)
                else:
                    # Right-aligned for bot messages
                    st.markdown(f"<div style='text-align:right; background-color: #dcf8c6; color: #000; border-radius: 15px; padding: 10px; margin: 5px; width: auto; max-width: 60%;'>{msg}</div>", unsafe_allow_html=True)

        # Input box at the bottom
        user_input = st.text_input("You:", key=f"user_input_{counter}", placeholder="Type your message here...")

        if user_input:
            user_input_str = str(user_input)
            response = chatbot(user_input)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Add to conversation history
            conversation.append(("user", user_input_str))
            conversation.append(("bot", response))

            # Save chat to log
            with open("chat_log.csv", "a", newline="", encoding="utf-8") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([user_input_str, response, timestamp])

            # Re-render conversation after input
            conversation_placeholder.empty()

            # Display updated conversation
            with conversation_placeholder.container():
                for speaker, msg in conversation:
                    if speaker == "user":
                        # Left-aligned for user messages
                        st.markdown(f"<div style='text-align:left; background-color: #f1f0f0; color: #000; border-radius: 15px; padding: 10px; margin: 5px; width: auto; max-width: 60%;'>{msg}</div>", unsafe_allow_html=True)
                    else:
                        # Right-aligned for bot messages
                        st.markdown(f"<div style='text-align:right; background-color: #dcf8c6; color: #000; border-radius: 15px; padding: 10px; margin: 5px; width: auto; max-width: 60%;'>{msg}</div>", unsafe_allow_html=True)

            # If the response is "goodbye", stop the app
            if response.lower() in ["goodbye", "bye"]:
                st.write("Thanks for chatting with me. Have a great day!")
                st.stop()

    elif choice == "Chat History":
        st.header("Chat History")
        with open("chat_log.csv", "r", encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)
            for row in csv_reader:
                st.text(f"User: {row[0]}")
                st.text(f"Chatbot: {row[1]}")
                st.text(f"Timestamp: {row[2]}")
                st.markdown("---")

    elif choice == "About":
        st.title("About Healthbot")
        st.write(
            """
            Healthbot is a chatbot designed to provide basic health information and answer
            your questions about symptoms and general health topics. We aim to make
            healthcare information more accessible and provide a convenient way to get
            started on your health journey.

            **Disclaimer:** Healthbot is not a substitute for professional medical advice.
            If you have any concerns about your health, please consult a doctor or
            other qualified healthcare provider.
            """
        )

if __name__ == "__main__":
    main()
