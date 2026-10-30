# CarbonIQ — Backend API (FastAPI & MongoDB)

The official high-performance Python backend for **CarbonIQ**, an AI-powered sustainability management platform. This service powers carbon accounting, energy tracking, transportation and smart bus route optimization, waste stream management, AI Sustainability Advisors, scenario simulation, and progress tracking.

---

## 1. Architecture Overview

The backend is built with a modular, layered architecture adhering to separation of concerns:

```
backend/
├── app/
│   ├── main.py                  # FastAPI application boot, CORS, lifespan, and health check
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment variables
│   │   ├── security.py          # Bcrypt password hashing & JWT encoding/decoding
│   │   └── exceptions.py        # Centralized HTTP error hierarchy
│   ├── db/
│   │   ├── mongodb.py           # AsyncIOMotorClient connection pool & test fixtures
│   │   └── indexes.py           # Index creation for uniqueness and isolation
│   ├── api/
│   │   ├── dependencies.py      # JWT authentication & server-side workspace isolation
│   │   ├── router.py            # API aggregate router
│   │   └── routes/              # Domain endpoints (auth, electricity, transportation, bus_routes, waste, dashboard, ai, simulator, progress, reports, demo)
│   ├── schemas/                 # Pydantic request & response validation schemas
│   ├── services/                # Business logic, query builders, and AI context engines
│   ├── calculations/            # Deterministic, verified mathematical emission engines
│   ├── data/
│   │   ├── emission_factors.py  # Centralized emission factors catalog & benchmark tariffs
│   │   └── demo_data.py         # Isolated, read-only demo dataset
│   └── utils/                   # Semantic ID generation and UTC ISO date parsing
├── tests/                       # Pytest asynchronous unit & integration test suite (36 tests)
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore rules for secrets and virtualenvs
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Verified Python dependencies
└── README.md                    # Documentation & integration guide
```

---

## 2. Prerequisites

* **Python**: 3.10 or newer (tested with Python 3.10.6)
* **MongoDB Atlas** or local MongoDB instance (v6.0+)
* **pip** (Python package manager)

---

## 3. Installation & Local Setup

### Step 1: Clone and navigate to backend directory
```bash
cd backend
```

### Step 2: Create a virtual environment (optional but recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure environment variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or: cp .env.example .env (Linux/macOS)
```

Edit `.env` with your settings:
```ini
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
DEBUG=true

# MongoDB Atlas URI (or mongodb://localhost:27017 for local development)
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=carboniq_db

# JWT Secret (Generate with: openssl rand -hex 32)
JWT_SECRET_KEY=carboniq-hackathon-development-secret-key-32bytes-min
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Allowed CORS origins
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Optional LLM integration (leaves deterministic rule-based fallback active if unset)
LLM_API_KEY=
LLM_MODEL=gemini-1.5-flash
```

---

## 4. Running the Server

Start the development server with live reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
* **Interactive OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. Running the Test Suite

The test suite uses an in-memory asynchronous mock database (`mongomock`), allowing **100% of automated tests to run offline without requiring external database credentials**.

Run the full test suite with verbose reporting:
```bash
pytest -v
```

All 36 tests verify:
1. User registration, duplicate email rejection, login, and JWT authorization
2. Workspace isolation (User B cannot read, update, or delete User A's records)
3. Electricity CRUD, monthly filtering, and emissions calculation ($E = \text{kWh} \times 0.82$)
4. Transportation CRUD, actual fuel method vs distance/efficiency method, and prevention of double-counting
5. Bus route management, seating capacity checks, corridor consolidation, and infeasible route rejection
6. Waste management CRUD, recycling negative credit ($-0.45\text{ kg CO}_2\text{e/kg}$), and recycling rates
7. AI Sustainability Advisors (Electricity, Transport, Waste) with structured calculation breakdowns
8. Savings simulator scenarios without mutating database state
9. Audit-ready report generation and public read-only demo access isolation

---

## 6. Key Endpoints & API Reference

### A. Authentication
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user & provision workspace | No |
| `POST` | `/api/auth/login` | Authenticate email & password, return JWT | No |
| `GET` | `/api/auth/me` | Get profile & workspace details | Yes (Bearer) |

### B. Electricity Management
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/electricity` | List workspace electricity records (`?month=YYYY-MM`) | Yes |
| `POST` | `/api/electricity` | Create record & compute emissions ($0.82\text{ kg CO}_2\text{e/kWh}$) | Yes |
| `GET` | `/api/electricity/summary` | Aggregate consumption, bills, emissions, and trends | Yes |
| `GET` | `/api/electricity/{id}` | Get single record | Yes |
| `PUT` | `/api/electricity/{id}` | Update record & recalculate | Yes |
| `DELETE` | `/api/electricity/{id}` | Delete record | Yes |

### C. Transportation & Fuel
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/transportation` | List workspace travel records | Yes |
| `POST` | `/api/transportation` | Create travel record (actual fuel or distance/efficiency) | Yes |
| `GET` | `/api/transportation/summary`| Aggregate distance, fuel liters, cost, emissions | Yes |
| `GET` | `/api/transportation/{id}` | Get single record | Yes |
| `PUT` | `/api/transportation/{id}` | Update record | Yes |
| `DELETE` | `/api/transportation/{id}` | Delete record | Yes |

### D. Smart Bus Route Optimization
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/transportation/routes` | List registered bus routes | Yes |
| `POST` | `/api/transportation/routes` | Add bus route (stops, distance, students, capacity) | Yes |
| `POST` | `/api/transportation/optimize`| Analyze routes & generate consolidation proposals | Yes |
| `POST` | `/api/transportation/optimize/accept` | Save proposal as a planned intervention | Yes |
| `GET` | `/api/transportation/routes/{id}` | Get single route | Yes |
| `PUT` | `/api/transportation/routes/{id}` | Update route | Yes |
| `DELETE` | `/api/transportation/routes/{id}` | Delete route | Yes |

### E. Waste Management
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/waste` | List waste records | Yes |
| `POST` | `/api/waste` | Create waste record & calculate net emissions | Yes |
| `GET` | `/api/waste/summary` | Aggregate waste, recycling rate, net emissions | Yes |
| `GET` | `/api/waste/{id}` | Get single waste record | Yes |
| `PUT` | `/api/waste/{id}` | Update record | Yes |
| `DELETE` | `/api/waste/{id}` | Delete record | Yes |

### F. Dashboard & Analytics
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/dashboard/summary` | Workspace aggregated metrics & category breakdown | Yes |
| `GET` | `/api/dashboard/trends` | Combined monthly emissions and cost progression | Yes |

### G. AI Sustainability Advisors
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/ai/electricity` | Energy advisor queries & savings breakdowns | Yes |
| `POST` | `/api/ai/transportation` | Route and fleet advisor queries | Yes |
| `POST` | `/api/ai/waste` | Waste stream & segregation recommendations | Yes |

### H. Simulator & Progress
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/simulator/electricity` | Model % reduction scenarios | Yes |
| `POST` | `/api/simulator/transportation` | Model distance reduction scenarios | Yes |
| `POST` | `/api/simulator/waste` | Model recycling diversion scenarios | Yes |
| `GET` | `/api/progress/goals` | List sustainability targets | Yes |
| `POST` | `/api/progress/goals` | Create quantifiable goal | Yes |
| `GET` | `/api/progress/interventions` | List planned interventions | Yes |
| `POST` | `/api/progress/interventions` | Log intervention | Yes |
| `GET` | `/api/reports/emissions` | Generate audit-ready emissions report | Yes |

### I. Public Demo Access (Read-Only)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/demo/dashboard` | Read-only demo overview metrics | No |
| `GET` | `/api/demo/electricity` | Read-only demo electricity records | No |
| `GET` | `/api/demo/transportation` | Read-only demo travel records | No |
| `GET` | `/api/demo/waste` | Read-only demo waste records | No |
| `GET` | `/api/demo/routes` | Read-only demo bus routes | No |

---

## 7. Example Request & Response Payloads

### Example 1: Register User & Provision Workspace
**Request:**
```http
POST /api/auth/register HTTP/1.1
Content-Type: application/json

{
  "full_name": "Aarav Sharma",
  "email": "aarav@reva.edu.in",
  "password": "SecurePassword123!",
  "workspace_name": "REVA Green Campus"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "user": {
    "id": "usr_9b3c4f7e1b9a2c3d",
    "full_name": "Aarav Sharma",
    "email": "aarav@reva.edu.in",
    "workspace_id": "ws_8a2d1e0c4b5a6f7e",
    "workspace_name": "REVA Green Campus",
    "created_at": "2026-10-28T09:30:00+00:00",
    "initials": "AS"
  }
}
```

### Example 2: Log Electricity Record
**Request:**
```http
POST /api/electricity HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "reporting_month": "2026-03",
  "consumption_kwh": 1240.0,
  "bill_amount_inr": 10540.0,
  "building_or_department": "Engineering Academic Wing",
  "notes": "Post semester break energy audit"
}
```

**Response (201 Created):**
```json
{
  "id": "elec_4f7e1b9a2c3d4e5f",
  "workspace_id": "ws_8a2d1e0c4b5a6f7e",
  "reporting_month": "2026-03",
  "consumption_kwh": 1240.0,
  "bill_amount_inr": 10540.0,
  "building_or_department": "Engineering Academic Wing",
  "notes": "Post semester break energy audit",
  "calculated_emissions_kg": 1016.8,
  "emission_factor_used": 0.82,
  "factor_type": "illustrative_grid_factor",
  "created_at": "2026-10-28T09:35:00+00:00",
  "updated_at": "2026-10-28T09:35:00+00:00"
}
```

### Example 3: AI Electricity Advisor Query
**Request:**
```http
POST /api/ai/electricity HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "How much can I save by reducing electricity usage by 15%?"
}
```

**Response (200 OK):**
```json
{
  "id": "ai_elec_7a1b2c3d4e5f6a7b",
  "role": "assistant",
  "content": "Under a modeled **15% electricity reduction** for your latest recorded period (2026-03), your workspace would reduce approximately **186.0 kWh**, cutting estimated monthly emissions by **152.5 kg CO2e** and saving around **₹1,581/month**.",
  "timestamp": "2026-10-28T09:36:00+00:00",
  "calculation_breakdown": {
    "formula": "Potential Reduction = Current kWh × (Reduction % ÷ 100)",
    "inputs": {
      "Current consumption": "1,240.0 kWh",
      "Target reduction": "15%",
      "Estimated variable tariff": "₹8.5/kWh",
      "Grid emission factor": "0.82 kg CO2e/kWh"
    },
    "assumptions": [
      "Illustrative grid emission factor: 0.82 kg CO2e/kWh (CEA CO2 Baseline Database v19).",
      "Estimated variable electricity tariff: INR 8.5/kWh (excluding fixed meter and demand charges)."
    ],
    "result": "₹1,581/month estimated savings (186.0 kWh / 152.5 kg CO2e)"
  },
  "suggested_follow_ups": [
    "What actions can reduce my electricity emissions?",
    "Compare this month with the previous month.",
    "Which month had the highest electricity consumption?"
  ]
}
```

---

## 8. Frontend Integration Guide

When connecting the Next.js frontend (`frontend/`):

1. **Configure Environment Variable**:
   In `frontend/.env.local`:
   ```ini
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
2. **Session Storage**:
   Store the received `access_token` in memory or secure storage. Send `Authorization: Bearer <token>` in subsequent requests.
3. **Demo vs Authenticated Routing**:
   * When `session.mode === 'demo'`, call `/api/demo/*`.
   * When `session.mode === 'authenticated'`, call `/api/*` with Bearer token.
4. **CORS Validation**:
   The backend allows requests from `http://localhost:3000` by default. Update `FRONTEND_ORIGINS` in `backend/.env` for production URLs.
