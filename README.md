# Voice AI Platform (Vobiz)

A production-ready, scalable Voice AI orchestration platform built with LiveKit, OpenAI/Azure, Deepgram, and Next.js.

## 🚀 Features

*   **Real-time Voice Agents**: Low-latency conversational AI using LiveKit Agents.
*   **Outbound Campaigns**: Schedule and blast calls via CSV upload using Celery & Redis.
*   **Inbound Handling**: SIP trunking support for receiving calls.
*   **Call Analytics**: Detailed logs, recording playback (S3 compatible), and cost estimation.
*   **Modern UI**: React/Next.js frontend with shading/dark mode support.
*   **Scalable Architecture**: Dockerized services for API, worker, frontend, and redis.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, TailwindCSS, Shadcn/UI
*   **Backend**: Python (FastAPI), LiveKit SDK
*   **Database**: MongoDB (Atlas or Local)
*   **Queue**: Redis + Celery
*   **Voice/AI**: LiveKit, Deepgram (STT), OpenAI/Azure (LLM/TTS)
*   **Infrastructure**: Docker Compose

## 📋 Prerequisites

*   Docker & Docker Compose
*   Node.js 18+ (for local frontend dev)
*   Python 3.10+ (for local backend dev)
*   LiveKit Cloud Account (or self-hosted)
*   OpenAI API Key
*   MongoDB URI

## ⚡ Quick Start (Docker)

To run the entire platform instantly:

```bash
# 1. Clone the repository
git clone https://github.com/Piyush-sahoo/Voice-AI-Platform.git
cd Voice-AI-Platform

# 2. Configure Environment
# Create livekit-outbound-calls/.env.local with your keys (see .env.example)

# 3. Launch
docker-compose up -d --build
```
Access the **Frontend** at http://localhost:3000 and **API Docs** at http://localhost:8000/docs.

---

## 💻 Local Development Setup

If you want to contribute or develop features, it's best to run services locally.

### Backend Setup (Python/FastAPI)

1.  **Navigate directly** to the backend directory:
    ```bash
    cd livekit-outbound-calls
    ```
2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: .\venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Environment Variables**:
    Create `.env.local` and add your keys (LiveKit, OpenAI, Mongo, AWS S3).
5.  **Run Redis**:
    Ensure, you have a local Redis instance running (or use Docker for just Redis).
    ```bash
    docker run -d -p 6379:6379 redis:alpine
    ```
6.  **Start API Server**:
    ```bash
    python run_server.py
    ```
7.  **Start Worker Agent** (in a new terminal):
    ```bash
    python run_agent.py start
    ```

### Frontend Setup (React/Vite)

1.  **Navigate** to the frontend directory:
    ```bash
    cd frontend
    ```
2.  **Install Packages**:
    ```bash
    npm install
    ```
3.  **Configure API URL**:
    Create `.env` file:
    ```env
    VITE_API_URL=http://localhost:8000
    ```
4.  **Run Dev Server**:
    ```bash
    npm run dev
    ```
    The app will proceed to run at http://localhost:5173 (usually).

---

## 🤝 How to Contribute

We welcome contributions! specifically fixes, improvements, and new features.

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork locally.
3.  **Create a Branch** for your feature:
    ```bash
    git checkout -b feature/my-new-feature
    ```
4.  **Commit** your changes:
    ```bash
    git commit -m "Add some amazing feature"
    ```
5.  **Push** to your branch:
    ```bash
    git push origin feature/my-new-feature
    ```
6.  **Open a Pull Request** against the `main` branch.

### Coding Standards
*   **Backend**: Follow PEP8. Use type hints.
*   **Frontend**: Use functional components and strict TypeScript typing.
*   **Commits**: Use clear, descriptive commit messages.

## 📂 Project Structure

```
├── frontend/                 # React UI application
│   ├── src/                 # Source code
│   │   ├── components/      # Reusable UI components (Shadcn)
│   │   ├── pages/           # Route pages (Dashboard, Calls, etc.)
│   │   └── lib/             # API clients and utils
├── livekit-outbound-calls/   # Python Backend & Agent
│   ├── agent/               # LiveKit Worker Agent logic
│   ├── api/                 # FastAPI Router & Endpoints
│   ├── services/            # Core business logic (S3, SIP, Calls)
│   ├── tasks_queue/         # Celery Worker for Campaigns
│   └── database/            # MongoDB Models & Connection
└── docker-compose.yml        # Orchestration
```

## 🔒 Security Note
*   **Authentication**: The system uses JWT. Ensure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are kept secret (use `.env.local`).
*   **S3**: Recordings are private; the backend generates signed URLs for authorized users only.

## 📄 License
MIT License. See `LICENSE` for more information.
