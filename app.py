from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyAAetRqDERV4aRxZMKjNR2HFQ3CdBLXDqo"))

# --- MongoDB Setup ---
MONGO_URI = os.getenv("MONGO_URI")  # .env me save karna
client = MongoClient(MONGO_URI)
db = client["rama_chatbot"]
collection = db["knowledge"]

# --- Scraping helper ---
def scrape_page(url, limit=800):
    try:
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.content, "html.parser")
        text = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])
        return text[:limit] if text else "⚠️ No content found."
    except Exception as e:
        return f"⚠️ Error fetching data: {e}"

# --- MongoDB helper ---
def get_from_db(keyword):
    doc = collection.find_one({"keyword": keyword})
    return doc["content"] if doc else None

def save_to_db(keyword, content):
    collection.update_one(
        {"keyword": keyword},
        {"$set": {"content": content}},
        upsert=True
    )

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()

    if not user_message:
        return jsonify({"reply": "⚠️ Please provide a message"}), 400

    # ✅ Custom answers
    if "kisne banaya" in user_message or "who made you" in user_message:
        return jsonify({"reply": "Mujhe Vikas Pathak ne banaya hai. 😊"})

    if "tumhara naam" in user_message or "your name" in user_message:
        return jsonify({"reply": "Mera naam Rama University Chatbot hai. 🤖"})

    if "address" in user_message or "location" in user_message:
        return jsonify({"reply": "📍 Rama University, Rama City, Mandhana, Kanpur, Uttar Pradesh, India - 209217"})

    if "contact" in user_message or "phone" in user_message:
        return jsonify({"reply": "📞 Contact us at: +91-512-2780886, +91-7781008700"})

    if "email" in user_message:
        return jsonify({"reply": "📧 You can reach us at: info@ramauniversity.ac.in"})

    # ✅ Website + MongoDB hybrid
    if "admission" in user_message:
        data = get_from_db("admission")
        if not data:
            data = scrape_page("https://ramauniversity.ac.in/admissions")
            save_to_db("admission", data)
        return jsonify({"reply": f"📝 Admission info:\n{data}"})

    if "course" in user_message or "program" in user_message:
        data = get_from_db("courses")
        if not data:
            data = scrape_page("https://ramauniversity.ac.in/academics")
            save_to_db("courses", data)
        return jsonify({"reply": f"🎓 Courses offered:\n{data}"})

    if "fee" in user_message:
        data = get_from_db("fees")
        if not data:
            data = scrape_page("https://ramauniversity.ac.in/fees")
            save_to_db("fees", data)
        return jsonify({"reply": f"💰 Fee Structure:\n{data}"})

    if "news" in user_message or "notice" in user_message:
        data = get_from_db("news")
        if not data:
            data = scrape_page("https://ramauniversity.ac.in/news")
            save_to_db("news", data)
        return jsonify({"reply": f"📰 Latest News:\n{data}"})

    # ✅ Otherwise use AI (Gemini streaming)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        def generate():
            for chunk in model.generate_content(user_message, stream=True):
                if chunk.text:
                    yield chunk.text

        return Response(generate(), mimetype="text/plain")

    except Exception as e:
        return jsonify({"reply": f"⚠️ Error: {str(e)}"})


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Server running ✅"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
