# Retreat Planner Backend

Multi-agent retreat planning backend powered by CrewAI and Tavily.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
```

### Required API Keys

| Variable | Description | Get it from |
|----------|-------------|-------------|
| `OPENAI_API_KEY` | OpenAI API key | [OpenAI Platform](https://platform.openai.com) |
| `TAVILY_API_KEY` | Tavily search API | [Tavily](https://tavily.com) |
| `STRIPE_SECRET_KEY` | Stripe test key | [Stripe Dashboard](https://dashboard.stripe.com) |

### Run Locally

```bash
# Start the server
uv run uvicorn src.main:app --reload --port 8000

# Or using the main module
uv run python -m src.main
```

## 📚 API Documentation

**Live API (Hosted on GCP Cloud Run)**:
- **Base URL**: https://hack-nation-backend-490752502534.europe-west3.run.app
- **Swagger UI**: https://hack-nation-backend-490752502534.europe-west3.run.app/docs
- **ReDoc**: https://hack-nation-backend-490752502534.europe-west3.run.app/redoc

## 🔌 Endpoints

### Flow Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze-requirements` | Agent 1: Parse requirements |
| POST | `/api/v1/discover-options` | Agent 2: Search vendors |
| POST | `/api/v1/rank-packages` | Agent 3: Rank packages |
| POST | `/api/v1/cart/build` | Agent 4: Build cart |
| POST | `/api/v1/cart/modify` | Agent 4: Modify cart |
| POST | `/api/v1/checkout` | Agent 5: Process checkout |
| POST | `/api/v1/full-flow` | Run all agents (testing) |

### Utility Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/api/v1/session/{id}` | Get session state |
| DELETE | `/api/v1/session/{id}` | Delete session |

## 📝 Example Usage

### 1. Full Flow (Quick Test)

```bash
curl -X POST https://hack-nation-backend-490752502534.europe-west3.run.app/api/v1/full-flow \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Plan a 2-day retreat in Las Vegas for 50 managers. Budget $60,000. Need 4-star hotel, flights from SF, meeting room, catering."
  }'
```

### 2. Step-by-Step Flow

```bash
# Step 1: Analyze requirements
curl -X POST https://hack-nation-backend-490752502534.europe-west3.run.app/api/v1/analyze-requirements \
  -H "Content-Type: application/json" \
  -d '{"user_input": "50 people, Las Vegas, 2 days, $60k budget"}'

# Save the session_id from response

# Step 2: Discover options
curl -X POST "https://hack-nation-backend-490752502534.europe-west3.run.app/api/v1/discover-options?session_id=YOUR_SESSION_ID"

# Step 3: Rank packages
curl -X POST "https://hack-nation-backend-490752502534.europe-west3.run.app/api/v1/rank-packages?session_id=YOUR_SESSION_ID"

# Step 4: Build cart (use package_id from ranked results)
curl -X POST "https://hack-nation-backend-490752502534.europe-west3.run.app/api/v1/cart/build?session_id=YOUR_SESSION_ID&package_id=pkg_abc123"
```

## 🎯 Dynamic Scoring

Weights are fully adjustable. Example:

```json
{
  "category_importance": {
    "flights": 25,
    "hotels": 45,
    "meeting_rooms": 15,
    "catering": 15
  },
  "hotels": {
    "price_weight": 20,
    "trust_weight": 50,
    "location_weight": 20,
    "amenities_weight": 10
  }
}
```

## 🏗️ Project Structure

```
backend/
├── pyproject.toml          # Dependencies
├── .python-version         # Python 3.11
├── .env.example            # Environment template
├── Procfile                # Deployment
├── README.md
└── src/
    ├── main.py             # FastAPI app
    ├── config.py           # Settings
    ├── agents/             # 5 CrewAI agents
    ├── crew/               # Crew orchestration
    ├── models/             # Pydantic models
    ├── services/           # Tavily, scoring
    └── utils/              # Validators
```

## 🚢 Deployment (Google Cloud Run)

### Prerequisites

1. Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
2. Authenticate with GCP:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

### Deploy with gcloud

```bash
# Navigate to backend directory
cd backend

# Build and deploy in one command
gcloud run deploy retreat-planner-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "OPENAI_API_KEY=sk-...,TAVILY_API_KEY=tvly-...,STRIPE_SECRET_KEY=sk_test_...,CORS_ORIGINS=https://your-frontend.app"
```

### Alternative: Build and Deploy Separately

```bash
# Step 1: Build the container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/retreat-planner-backend

# Step 2: Deploy to Cloud Run
gcloud run deploy retreat-planner-backend \
  --image gcr.io/YOUR_PROJECT_ID/retreat-planner-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300
```

### Set Environment Variables (After Deployment)

```bash
gcloud run services update retreat-planner-backend \
  --region us-central1 \
  --set-env-vars "OPENAI_API_KEY=sk-..." \
  --set-env-vars "TAVILY_API_KEY=tvly-..." \
  --set-env-vars "STRIPE_SECRET_KEY=sk_test_..." \
  --set-env-vars "CORS_ORIGINS=https://your-frontend.app"
```

### View Deployment URL

```bash
gcloud run services describe retreat-planner-backend \
  --region us-central1 \
  --format "value(status.url)"
```

### Local Development

```bash
uv run uvicorn src.main:app --reload --port 8000
```

## 🏛️ System Architecture Diagrams

These diagrams visualize how your agents collaborate and how the frontend interacts with the backend. Use these for your presentation slides!

---

### 1. Agent Coordination (End-to-End Flow)

This sequence diagram shows how the 5 agents work together to turn a single chat message into a confirmed booking.

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#4F46E5',
    'primaryTextColor': '#111827',
    'primaryBorderColor': '#4338CA',
    'lineColor': '#374151',

    'secondaryColor': '#10B981',
    'tertiaryColor': '#F59E0B',

    'noteBkgColor': '#FEF3C7',
    'noteTextColor': '#1F2937',

    'actorBkg': '#E0E7FF',
    'actorTextColor': '#1E3A8A',
    'actorBorder': '#6366F1',

    'labelTextColor': '#111827'
  }
}}%%
sequenceDiagram
    autonumber
    participant User as 💻 User (Frontend)
    participant A1 as 📋 Agent 1: Requirements
    participant A2 as 🔍 Agent 2: Discovery
    participant A3 as 🏆 Agent 3: Ranking
    participant A4 as 🛒 Agent 4: Cart
    participant A5 as 💳 Agent 5: Checkout

    rect rgb(239, 246, 255)
        User->>A1: Plan a Paris retreat
        Note over A1: Step 1: Input Analysis
        A1->>A1: Extract attendees, budget, location
        A1-->>User: Returns Structured Brief
    end

    rect rgb(236, 253, 245)
        User->>A2: Request Discovery
        Note over A2: Step 2: Multi-Source Discovery
        A2->>A2: Web Search (Tavily)
        A2-->>User: Returns Vendor Options
    end

    rect rgb(255, 251, 235)
        User->>A3: Rank with Weights
        Note over A3: Step 3: Interactive Scoring
        A3->>A3: Apply Weighted Math
        A3-->>User: Returns Scored Packages
    end

    rect rgb(254, 242, 242)
        User->>A4: Build Cart
        Note over A4: Step 4: Cart Optimization
        A4->>A4: Calc Subtotal, Tax, Fees
        A4-->>User: Returns Final Cart
    end

    rect rgb(245, 243, 255)
        User->>A5: Final Checkout
        Note over A5: Step 5: Master Booking
        A5->>A5: Simulated Payment (Stripe)
        A5-->>User: Returns Master Confirmation ID
    end
```

---

### 2. Overall System Architecture

Professional block diagram with color-coded layers.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'fontSize': '14px'}}}%%
flowchart TB
    subgraph Presentation["🖥️ Presentation Layer - Lovable"]
        UI["⚛️ React + Tailwind UI"]
        Session["🗃️ Session Management"]
    end

    subgraph Logic["☁️ Logic Layer - Google Cloud Run"]
        API["⚡ FastAPI Endpoints"]
    end

    subgraph Agentic["🤖 Agentic Core - CrewAI"]
        RA["📋 Requirements Analyst"]
        DA["🔍 Discovery Agent"]
        RankA["🏆 Ranking Agent"]
        CA["🛒 Cart Agent"]
        ChA["💳 Checkout Agent"]
    end

    subgraph External["🌐 External Services"]
        Tavily["🔎 Tavily Search API"]
        OpenAI["🧠 OpenAI LLM"]
        Stripe["💵 Stripe Payments"]
    end

    UI --> Session
    Session --> API
    API --> RA
    API --> DA
    API --> RankA
    API --> CA
    API --> ChA

    RA --> OpenAI
    DA --> Tavily
    DA --> OpenAI
    RankA --> OpenAI
    CA --> OpenAI
    ChA --> Stripe
    ChA --> OpenAI

    style Presentation fill:#22C55E,stroke:#16A34A,stroke-width:2px,color:#fff
    style Logic fill:#3B82F6,stroke:#2563EB,stroke-width:2px,color:#fff
    style Agentic fill:#F97316,stroke:#EA580C,stroke-width:2px,color:#fff
    style External fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
    
    style UI fill:#4ADE80,stroke:#22C55E,color:#000
    style Session fill:#4ADE80,stroke:#22C55E,color:#000
    style API fill:#60A5FA,stroke:#3B82F6,color:#000
    style RA fill:#FB923C,stroke:#F97316,color:#000
    style DA fill:#FB923C,stroke:#F97316,color:#000
    style RankA fill:#FB923C,stroke:#F97316,color:#000
    style CA fill:#FB923C,stroke:#F97316,color:#000
    style ChA fill:#FB923C,stroke:#F97316,color:#000
    style Tavily fill:#C084FC,stroke:#A855F7,color:#000
    style OpenAI fill:#C084FC,stroke:#A855F7,color:#000
    style Stripe fill:#C084FC,stroke:#A855F7,color:#000
```

---

### 3. Explaining the Architecture for Judges

| Concept | Description |
|---------|-------------|
| **Agentic Orchestration** | Unlike a traditional app, ours uses CrewAI to manage state. Each agent is a specialist. |
| **Asynchronous Flow** | The high-latency work (web search) is isolated in Step 2, ensuring the rest of the UI feels snappy. |
| **Micro-Services Ready** | Each agent is logically separate, making it easy to add more specialized agents in the future. |

---

## 📄 License

MIT
