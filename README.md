# STEM Tutor AI

**An AI-powered, multi-agent tutoring system for personalised STEM
education.**\
STEM Tutor AI delivers adaptive explanations, intelligent quiz
generation, real-time search-augmented reasoning, and persistent memory
to support student learning across Science, Technology, Engineering, and
Mathematics.

------------------------------------------------------------------------

## 📚 Overview

The system now uses a **modular micro-services architecture** following
a full code refactor.\
Each service is isolated, independently deployable, and communicates via
lightweight HTTP APIs.

### Core Services

-   **Tutor Service** -- Primary reasoning engine for teaching,
    explanations, examples, intent detection, and student modelling.
-   **QuizMaster Service** -- Generates adaptive quizzes, evaluates
    difficulty, and analyses student performance.
-   **Frontend UI Service** -- Lightweight user interface layer (can be
    replaced or extended by mobile or web clients).

All services include their own `Dockerfile`, configuration, and
dependency management.

------------------------------------------------------------------------

## 🧱 Project Structure

    aitutor/
    │
    ├── frontend/                     # UI micro-service
    │   ├── ui_service.py
    │   ├── config.py
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── static/
    │
    ├── tutor/                        # Core Tutor micro-service
    │   ├── agent_entrypoint.py
    │   ├── tutor_agent_service.py
    │   ├── intent_classifier_agent.py
    │   ├── subject_classifier_agent.py
    │   ├── google_search_agent.py
    │   ├── quizmaster_tools.py
    │   ├── persistent_memory.py
    │   ├── logging_plugin.py
    │   ├── config.py
    │   ├── requirements.txt
    │   └── Dockerfile
    │
    ├── quizmaster/                   # Quiz generation micro-service
    │   ├── quizmaster_agent_service.py
    │   ├── config.py
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── .well-known/
    │
    ├── cloudbuild-aitutor.yaml       # Cloud Build pipeline for Tutor + QuizMaster
    ├── cloudbuild-gradio.yaml        # Cloud Build pipeline for Frontend
    ├── firebase.json                 # Optional hosting configuration
    └── README.md                     # This file

Files excluded by `.gitignore` (e.g., virtualenv folders, cache
directories, local configs, system files) are intentionally omitted from
this structure.

------------------------------------------------------------------------

## 🧠 Architecture Summary

### **Tutor Agent Service**

Handles: - STEM concept explanations\
- Adaptive complexity adjustment\
- Worked examples + stepwise reasoning\
- Student context memory\
- Intent + subject classification\
- Web search tool access

Key modules: - `tutor_agent_service.py` - `intent_classifier_agent.py` -
`subject_classifier_agent.py` - `persistent_memory.py` -
`google_search_agent.py` - `quizmaster_tools.py`

------------------------------------------------------------------------

### **QuizMaster Service**

A dedicated engine for: - Adaptive quiz generation\
- Difficulty assessment\
- Structured learning path generation\
- Answer validation\
- Performance feedback

Entry point:\
`quizmaster_agent_service.py`

------------------------------------------------------------------------

### **Frontend UI Service**

A minimal, extendable interface layer enabling conversation and quiz
interaction.

Entry point:\
`ui_service.py`

------------------------------------------------------------------------

## 🐳 Running with Docker

Each micro-service builds and runs independently.

### Build images

``` sh
docker build -t tutor-service ./tutor
docker build -t quizmaster-service ./quizmaster
docker build -t frontend-service ./frontend
```

### Run services

``` sh
docker run -p 8001:8001 tutor-service
docker run -p 8002:8002 quizmaster-service
docker run -p 8000:8000 frontend-service
```

------------------------------------------------------------------------

## ☁️ Deployment (Google Cloud Build)

Two deployment pipelines are included:

  File                        Description
  --------------------------- ------------------------------------------
  `cloudbuild-aitutor.yaml`   Deploys Tutor + QuizMaster microservices
  `cloudbuild-gradio.yaml`    Deploys Frontend UI

Trigger a build manually:

``` sh
gcloud builds submit --config cloudbuild-aitutor.yaml
```

------------------------------------------------------------------------

## 🔧 Configuration

Each service uses its own `config.py` and environment variables for:

-   API keys and authentication\
-   Model selection\
-   Routing endpoints\
-   Persistent memory configuration\
-   Logging and tracing\
-   CORS + service metadata

Create your environment variables using a template such as:

    OPENAI_API_KEY=...
    GOOGLE_SEARCH_API_KEY=...
    QUIZMASTER_URL=...
    TUTOR_URL=...

------------------------------------------------------------------------

## 🧪 Running Locally Without Docker

``` sh
python -m tutor.tutor_agent_service
python -m quizmaster.quizmaster_agent_service
python -m frontend.ui_service
```

Ensure dependencies are installed for each service:

``` sh
pip install -r tutor/requirements.txt
pip install -r quizmaster/requirements.txt
pip install -r frontend/requirements.txt
```

------------------------------------------------------------------------

## 🗺️ Roadmap

-   Analytics dashboard for student progress\
-   Spaced repetition scheduling\
-   Multimodal input (diagrams, handwriting, audio)\
-   Lesson planning + curriculum generation\
-   Full classroom admin tools

------------------------------------------------------------------------

## 🤝 Contributing

1.  Fork the repo\
2.  Create a feature branch (`feature/...`)\
3.  Make your changes\
4.  Ensure `.gitignore` exclusions remain intact\
5.  Open a Pull Request with a clear and descriptive summary

------------------------------------------------------------------------

## 📄 License

MIT License unless otherwise stated.

------------------------------------------------------------------------

## 👨‍🏫 About

STEM Tutor AI is designed to make high-quality STEM education accessible
to all learners through intelligent, adaptive tutoring.
