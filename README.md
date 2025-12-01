# STEM Tutor AI

**An AI-powered, multi-agent learning companion for personalised STEM education.**

STEM Tutor AI brings together intelligent tutoring, adaptive quiz generation, and smart reasoning to help students learn Maths & Science more effectively.

## 🚀 **Overview**

STEM Tutor AI is a multi-agent, stateful AI tutoring system designed to:

* Provide personalised explanations for STEM topics
* Generate quizzes dynamically based on the learner’s level
* Adapt to student performance over time
* Integrate external tools such as Google Search & Quiz Generation database
* Serve as a future-ready foundation for AI-augmented education platforms

This project is organised for extension, experimentation, and deployment in real-world STEM learning environments.

## 🎯 Motivation
### The Challenge
STEM subjects often require **personalised, immediate feedback**, but many students lack access to private tutors.
Online resources are generic, and teachers cannot individually adapt content for every learner.
### The Opportunity
Recent advancements in AI and agent-based architectures allow us to build **adaptive, conversational learning systems** capable of:
* Assessing a student’s misunderstanding
* Generating targeted practice material
* Giving step-by-step explanations
* Tracking learning progress
* Self-evaluating teaching quality

### The Vision
STEM Tutor AI aims to become a **“Study Copilot”** — an intelligent assistant that helps students learn independently, efficiently, and enjoyably.

## 🧠 Core Features
### 📘 1. Intent Agent - It is the system’s “dispatcher.”
* Concept explanation
* Request for a quiz
* Current or latest trends and information
* Information lookup
* General conversation
* Memory or progress requests

### 📘 2. Tutor Agent - It is the “brain” of STEM Tutor. 
* Handles student questions
* Explains concepts at the right difficulty level
* Provides worked examples
* Detects prior context using persistent memory

### ❓ 3. QuizMaster Agent - A Dedicated Remote A2A Service
The Quizmaster uses a **real curated dataset of 50,000 STEM MCQs**
* Generates quizzes (MCQs, short questions, topic-based sets)
* Grades answers and provides feedback
* Integrates with external quiz APIs or local generators

### 🔍 4. Google Search Agent - Controlled Web Search
* Fetches factual information
* Assists with real-time data for advanced topics

### 🧩 5. Multi-Agent A2A Architecture
* Agents interact with each other (A2A calls)
* Tutor Agent delegates tasks (e.g., quiz creation, searching)
* Modular and easily extendable

### 📚 6. Subject Classifier - It is the gatekeeper of the entire tutoring pipeline
* Automatically detects whether the user is asking about:
  * 📐 Mathematics
  * 🔬 Physics
  * 🧪 Chemistry
  * 🧬 Biology
    
Helps route tasks internally to the right specialist logic

### ⚙️ 6. Deployment-Ready
* Cloud Run compatible
* Dockerised environment
* Can be adapted for Streamlit, FastAPI, or custom frontends

## 📁 Project Structure

```

stemtutorai/
├── agents/
│   ├── intent_agent.py
│   ├── tutor_agent.py
│   ├── quizmaster_agent.py
│   ├── google_search_agent.py
│   └── subject_classifier_agent.py
├── runtime/
│   ├── agent_runtime.py
│   └── session_manager.py
├── tools/
│   ├── google_search_tool.py
│   └── quiz_generation_tool.py
├── cloudrun/
│   └── Dockerfile
├── requirements.txt
├── README.md
└── LICENSE
```
## 🔧 Installation

Clone the repository:
```
bash

git clone https://github.com/ASquareDigitalUK/stemtutorai.git
cd stemtutorai
```

Create a virtual environment:
```
bash

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

Install dependencies:
```
bash

pip install -r requirements.txt
```

## ▶️ Running Locally
### Option 1 — Python App (e.g., FastAPI backend)
```
bash

uvicorn app.main:app --reload
```

Visit:

👉 Open: [http://localhost:8000](http://localhost:8000/)

### Option 2 — Docker
```
bash

docker build -t stemtutorai .
docker run -p 8080:8080 stemtutorai
```

## 🧪 Example Usage
### Ask a Question
```
ardunio

"Explain Pythagoras theorem with a simple example."
```

### Generate a Quiz
```
bash

"Give me a 5-question algebra quiz for a Year 9 student."
```
### Ask for Step-by-Step Solutions
```
bash

"Solve 3x + 7 = 25 step-by-step.."
```
### Use Subject Auto-Classification
```
bash

"What is Newton’s second law?"
→ Automatically routed to Physics
```

## ☁️ Deploying to Cloud Run

1. Build the container:
```
bash

gcloud builds submit --tag gcr.io/<PROJECT-ID>/stemtutorai
```

2. Deploy it:
```
bash

gcloud run deploy stemtutorai --image gcr.io/<PROJECT-ID>/stemtutorai --platform managed
```

3. Enjoy your auto-scaled, serverless STEM Tutor instance 🚀

## 🛠️ Configuration

Create an `.env` file or use environment variables:
```
ini

GEMINI_API_KEY=your_key_here
GOOGLE_SEARCH_KEY=optional
QUESTGEN_API_KEY=optional
```
## 🤝 Contributing

Contributions are welcome and encouraged!

* 1. Fork the repo
* 2. Create a feature branch (`git checkout -b feature/new-feature`)
* 3. Commit changes
* 4. Push to your branch
* 5. Open a Pull Request

Please follow repository structure and agent design patterns.

## ⭐ Acknowledgements

* **Google Gemini AI** for LLM agent capabilities
* **Firestore storage**
* **Google ADK multi-agent framework**
* Inspiration from cutting-edge AI tutoring research
