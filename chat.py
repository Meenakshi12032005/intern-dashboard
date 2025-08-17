import re
import random
import json
import os
from datetime import datetime
import wikipedia
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"name": None,"facts":[]}

def save_memory(memory):
    with open(MEMORY_FILE,"w") as f:
        json.dump(memory,f)

memory = load_memory()

# Rules
rules = {
    r"\b(hi|hello|hey|greetings)\b": [
        "Hello there! 😊",
        "Hey! How’s your day going?",
        "Hi! How can I assist you today?"
    ],
    r"\b(how are you|how r u|how’s it going)\b": [
        "I’m doing great, thanks for asking! How about you?",
        "Feeling fantastic! How are you doing?",
        "I’m just a chatbot, but I’m feeling awesome 😄"
    ],
    r"\b(joke|funny)\b": [
        "Why don’t skeletons fight each other? They don’t have the guts! 😂",
        "I told my computer I needed a break, and now it won’t stop sending me KitKat ads!",
        "Why did the math book look sad? Because it had too many problems."
    ],
    r"\b(random fact|tell me something)\b": [
        "Did you know? Honey never spoils — archaeologists found 3000-year-old honey still edible!",
        "Sharks existed before trees 🌳",
        "Bananas are berries, but strawberries aren’t! 🍓"
    ],
    r"\b(capital of india)\b": [
        "The capital of India is New Delhi 🇮🇳"
    ],
    r"\b(time|current time|what time is it)\b": [
        lambda: f"The current time is {datetime.now().strftime('%H:%M:%S')}"
    ],
    r"\b(date|day|today’s date)\b": [
        lambda: f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"
    ]
}

def get_response(user_input):
    # Store name
    if re.search(r"\b(my name is|i am)\b", user_input.lower()):
        name_match = re.search(r"\bmy name is ([a-zA-Z]+)|i am ([a-zA-Z]+)", user_input, re.IGNORECASE)
        if name_match:
            name = name_match.group(1) or name_match.group(2)
            memory["name"] = name
            save_memory(memory)
            return f"Nice to meet you, {name}! 💙"

    # Store likes
    if re.search(r"\bi like\b", user_input.lower()):
        fact = user_input[7:]
        memory["facts"].append(fact)
        save_memory(memory)
        return f"Oh, I’ll remember that you like {fact}!"

    # Recall memory
    if re.search(r"\bremember\b", user_input.lower()):
        if memory["name"] or memory["facts"]:
            details = []
            if memory["name"]:
                details.append(f"your name is {memory['name']}")
            if memory["facts"]:
                details.append(f"you like {', '.join(memory['facts'])}")
            return f"I remember that {', and '.join(details)}."
        else:
            return "I don’t know much about you yet!"

    # Recall name
    if re.search(r"\bwhat'?s my name\b", user_input.lower()):
        if memory["name"]:
            return f"Your name is {memory['name']}! 😊"
        else:
            return "I don’t know your name yet. Tell me!"

    # Match predefined rules
    for pattern, responses in rules.items():
        if re.search(pattern, user_input.lower()):
            response = random.choice(responses)
            if callable(response):
                return response()
            else:
                return response

    # If no match → search online
    try:
        summary = wikipedia.summary(user_input, sentences=2)
        return summary
    except Exception:
        return "Sorry, I couldn’t find anything about that."


# HTML with ChatGPT-like UI
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ChatBot</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding: 30px; }
        #container { width: 500px; background: white; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
        #chat { flex: 1; padding: 20px; overflow-y: auto; }
        .msg { margin: 10px 0; padding: 10px 15px; border-radius: 15px; max-width: 75%; }
        .user { background: #0084ff; color: white; margin-left: auto; text-align: right; }
        .bot { background: #e4e6eb; color: black; margin-right: auto; }
        #input-area { display: flex; border-top: 1px solid #ddd; }
        #msg { flex: 1; padding: 15px; border: none; outline: none; font-size: 16px; }
        button { background: #0084ff; color: white; border: none; padding: 0 20px; cursor: pointer; }
        button:hover { background: #006bbf; }
    </style>
</head>
<body>
    <div id="container">
        <div id="chat"></div>
        <div id="input-area">
            <input id="msg" type="text" placeholder="Type a message..." onkeypress="if(event.key==='Enter')send()">
            <button onclick="send()">Send</button>
        </div>
    </div>

    <script>
        function send(){
            let msg = document.getElementById("msg").value;
            if(msg.trim() === "") return;
            let chat = document.getElementById("chat");
            chat.innerHTML += "<div class='msg user'>" + msg + "</div>";
            fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({"message": msg})
            }).then(res => res.json()).then(data => {
                chat.innerHTML += "<div class='msg bot'>" + data.reply + "</div>";
                chat.scrollTop = chat.scrollHeight;
            });
            document.getElementById("msg").value = "";
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]
    reply = get_response(user_input)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
