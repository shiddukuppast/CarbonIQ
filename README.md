# team-immortal-t3-09

#  CarbonIQ — AI-Powered Carbon Footprint Intelligence Platform

**Measure. Understand. Predict. Reduce.**

CarbonIQ is an AI-powered sustainability management platform designed to help individuals, educational institutions, and organizations understand, monitor, and reduce their carbon footprint.

The platform brings together carbon emission calculations, historical activity analysis, machine learning, and Large Language Models (LLMs) to transform environmental data into meaningful sustainability insights.

Instead of simply displaying carbon emission numbers, CarbonIQ aims to help users understand where their emissions come from, identify opportunities for improvement, explore potential emission reductions, and make more informed sustainability decisions.

---

## 📌 Table of Contents

1. [Overview](#-overview)
2. [Problem Statement](#-problem-statement)
3. [Our Solution](#-our-solution)
4. [Target Users](#-target-users)
5. [Core Features](#-core-features)
6. [System Architecture](#-system-architecture)
7. [Technology Stack](#-technology-stack)
8. [How CarbonIQ Works](#-how-carboniQ-works)
9. [AI, ML and LLM Integration](#-ai-ml-and-llm-integration)
10. [Carbon Emission Calculation](#-carbon-emission-calculation)
11. [Data Management](#-data-management)
12. [Project Structure](#-project-structure)
13. [Installation and Setup](#-installation-and-setup)
14. [Environment Variables](#-environment-variables)
15. [Running the Application](#-running-the-application)
16. [API Overview](#-api-overview)
17. [Security and Data Isolation](#-security-and-data-isolation)
18. [Future Enhancements](#-future-enhancements)
19. [Limitations](#-limitations)
20. [Contributors](#-contributors)

---

## 🌍 Overview

Climate change and increasing greenhouse gas emissions have made environmental sustainability an important responsibility for individuals and organizations.

However, understanding one's carbon footprint is not always straightforward.

Electricity consumption, transportation activities, waste generation, and institutional operations all contribute to carbon emissions. These activities are often tracked separately, making it difficult to understand their combined environmental impact.

**CarbonIQ brings these activities together into a unified sustainability intelligence platform.**

It combines:

* Deterministic carbon emission calculations.
* Historical activity and emission analysis.
* Machine learning-based emission modelling.
* LLM-powered sustainability insights.
* What-if savings simulations.
* Sustainability reports and visualizations.

Our goal is to make carbon footprint management more understandable, accessible, and actionable.

---

## ❗ Problem Statement

Individuals, colleges, and organizations face several challenges when trying to manage their carbon footprint.

* **Fragmented Information:** Electricity, transportation, and waste-related information is maintained separately.
* **Lack of Visibility:** Users often do not understand which activities contribute most to their carbon emissions.
* **Limited Predictive Insights:** Traditional carbon calculators mainly show current or historical emissions without providing meaningful predictive analysis.
* **Difficult Decision-Making:** Users may know that they need to reduce emissions but lack practical recommendations.
* **No Centralized Sustainability Management:** Educational institutions and organizations need a unified way to monitor their environmental impact.

CarbonIQ addresses these challenges through an integrated, data-driven approach.

---

## 💡 Our Solution

CarbonIQ provides a centralized platform where users can record their activities, calculate associated emissions, understand historical patterns, and explore possible emission-reduction strategies.

The platform follows a continuous sustainability workflow:

**Measure → Analyze → Predict → Recommend → Simulate → Track**

| Stage     | Description                                                          |
| --------- | -------------------------------------------------------------------- |
| Measure   | Collect electricity, transportation, and waste activity data.        |
| Analyze   | Calculate emissions and identify important contributing activities.  |
| Predict   | Apply available machine learning models where supported by the data. |
| Recommend | Generate contextual sustainability insights using an LLM.            |
| Simulate  | Explore how proposed changes could affect emissions.                 |
| Track     | Monitor historical trends and sustainability progress.               |

---

## 👥 Target Users

CarbonIQ is designed around three primary user categories.

### 1. Individuals

Individuals can:

* Monitor personal electricity consumption.
* Record waste generation.
* Understand their personal carbon footprint.
* Receive AI-powered sustainability recommendations.
* Explore potential emission reductions.

### 2. Colleges and Educational Institutions

Colleges can:

* Monitor institutional sustainability activities.
* Track electricity consumption.
* Analyze transportation-related emissions.
* Monitor waste generation.
* Explore campus transportation improvements.
* Understand sustainability trends.

### 3. Organizations

Organizations can:

* Monitor operational carbon emissions.
* Analyze energy consumption.
* Track transportation activities.
* Monitor waste-related emissions.
* Identify opportunities for operational improvements.
* Access sustainability insights and reports.

Each user category is intended to operate within its own authorized workspace.

---

## 🚀 Core Features

### 1. Sustainability Dashboard

The dashboard provides a centralized overview of sustainability performance.

It is designed to display:

* Total estimated carbon emissions.
* Electricity-related emissions.
* Transportation-related emissions.
* Waste-related emissions.
* Historical emission trends.
* Category-wise contribution.
* Sustainability insights.

The dashboard helps users understand their overall environmental impact without navigating through multiple modules.

### 2. Electricity Management ⚡

The electricity module focuses on monitoring energy consumption and its associated carbon emissions.

Key capabilities:

* Record electricity consumption.
* Monitor consumption over time.
* Calculate electricity-related emissions.
* Analyze historical consumption patterns.
* Generate contextual AI-powered recommendations.

### 3. Transportation Management 🚗

The transportation module focuses on emissions generated through transportation activities.

Key capabilities:

* Record transportation-related activities.
* Calculate associated carbon emissions.
* Analyze transportation contributions.
* Explore opportunities to reduce transportation emissions.
* Support institutional transportation analysis.

### 4. Waste Management ♻️

The waste module helps users understand the environmental impact of waste generation.

Key capabilities:

* Record waste-related activities.
* Categorize waste information.
* Calculate estimated waste-related emissions.
* Analyze waste trends.
* Generate recommendations for improved waste management.

### 5. AI Sustainability Insights 🤖

CarbonIQ integrates Large Language Models to provide contextual sustainability explanations and recommendations.

The AI layer is designed to:

* Explain emission patterns.
* Identify important contributing activities.
* Interpret historical trends.
* Suggest practical emission-reduction strategies.
* Answer sustainability-related questions.
* Provide contextual explanations based on available user data.

The LLM is used as an interpretation and recommendation layer rather than the source of numerical emission calculations.

### 6. Savings Simulator 📊

The Savings Simulator allows users to explore hypothetical sustainability improvements.

For example:

* What happens if electricity consumption decreases?
* What happens if transportation activity is reduced?
* What happens if waste generation is reduced?
* How might proposed changes affect estimated emissions?

The objective is to compare existing activity levels against proposed scenarios.

Simulation results depend on the availability and correctness of baseline activity data and emission factors.

### 7. Reports and Exports 📄

The reporting module is intended to provide structured sustainability information.

Potential reporting information includes:

* Overall carbon footprint.
* Category-wise emissions.
* Historical trends.
* Activity summaries.
* Sustainability insights.
* Emission-reduction progress.

### 8. Bus Route Optimization 🚌

Institutional transportation optimization is an extension of the CarbonIQ concept.

The proposed approach combines route optimization algorithms, road-distance information, and emission calculations to explore more efficient transportation arrangements.

The objective is to:

* Reduce unnecessary travel distances.
* Improve vehicle utilization.
* Explore efficient pickup arrangements.
* Estimate potential transportation emission reductions.

This feature should be considered under development unless the route optimization implementation is integrated and verified.

---

## 🏗️ System Architecture

CarbonIQ follows a frontend-backend architecture with dedicated AI/ML services.

### High-Level Architecture

```text
                 ┌───────────────────────────┐
                 │        USER               │
                 │ Individual / College /    │
                 │ Organization              │
                 └─────────────┬─────────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │       FRONTEND            │
                 │                           │
                 │ Next.js                   │
                 │ React + TypeScript        │
                 │ Tailwind CSS              │
                 └─────────────┬─────────────┘
                               │
                         REST API Requests
                               │
                               ▼
                 ┌───────────────────────────┐
                 │       BACKEND             │
                 │                           │
                 │ Python + FastAPI          │
                 │                           │
                 │ Authentication            │
                 │ Business Logic            │
                 │ Data Processing           │
                 │ Emission Calculations     │
                 └──────┬───────────┬────────┘
                        │           │
              ┌─────────▼───┐   ┌───▼─────────────┐
              │  MongoDB    │   │  AI / ML LAYER  │
              │  Atlas      │   │                │
              │             │   │ ML Model       │
              │ User Data   │   │ Groq LLM       │
              │ Activity    │   │ Qwen Model     │
              │ Records     │   │                │
              └─────────────┘   └─────────────────┘
```

### Architecture Responsibilities

| Component          | Responsibility                                                     |
| ------------------ | ------------------------------------------------------------------ |
| Frontend           | User interaction, dashboards, forms, charts, and visualizations.   |
| Backend            | API handling, authentication, business logic, and data processing. |
| MongoDB Atlas      | Persistent storage of application and activity data.               |
| Calculation Engine | Deterministic carbon emission calculations.                        |
| ML Layer           | Model-based emission analysis or prediction where supported.       |
| LLM Layer          | Natural-language explanations and sustainability recommendations.  |

---

## 🛠️ Technology Stack

### Frontend

* **Next.js** — React-based web application framework.
* **React** — Component-based user interface.
* **TypeScript** — Type-safe frontend development.
* **Tailwind CSS** — Responsive UI styling.

### Backend

* **Python** — Core backend programming language.
* **FastAPI** — Backend REST API framework.
* **Uvicorn** — ASGI server.

### Database

* **MongoDB Atlas** — Cloud-hosted NoSQL database.
* **Mongoose** — Used where applicable in the associated JavaScript application components; the Python backend should use its actual configured MongoDB client.

### Artificial Intelligence and Machine Learning

* **Scikit-learn / compatible model tooling** — Model development and inference, depending on the saved model.
* **Joblib** — Serialization and loading of the trained model.
* **Groq API** — LLM inference.
* **Qwen** — Language model used through the Groq integration.

### Development Tools

* Visual Studio Code
* Git and GitHub
* Postman
* Python Virtual Environment

---

## 🔄 How CarbonIQ Works

The application follows a structured data-processing workflow.

### Step 1: User Registration and Authentication

Users register and select their account category:

* Individual
* College
* Organization

After authentication, users access their authorized workspace.

### Step 2: Activity Data Collection

Users enter activity information through the relevant modules:

* Electricity consumption.
* Transportation activity.
* Waste generation.

### Step 3: Data Storage

The backend validates the submitted information and stores activity records in MongoDB Atlas.

### Step 4: Carbon Emission Calculation

The backend processes activity data using the emission calculation logic.

The calculation engine produces estimated emissions based on the applicable activity values and emission factors.

### Step 5: Historical Analysis

Available historical records can be used to understand:

* Changes in emissions.
* Category-wise contributions.
* Consumption patterns.
* Sustainability trends.

### Step 6: Machine Learning Analysis

The available trained model can be loaded for inference when its input features and prediction target match the requested task.

The model artifact reported in the project is:

`backend/carboniq_emissions_model.joblib`


The model's exact prediction capabilities and evaluation methodology should be documented alongside the model's training configuration.

### Step 7: AI-Powered Interpretation

Relevant activity information, calculated metrics, and historical context can be supplied to the LLM.

The LLM generates explanations and sustainability recommendations.

### Step 8: Simulation and Reporting

Users can explore proposed changes and review their potential environmental impact.

The platform brings these results together through dashboards and reporting functionality.

---

## 🧠 AI, ML and LLM Integration

One of the important architectural decisions in CarbonIQ is separating numerical calculations from language-model interpretation.

Instead of asking an LLM to calculate the entire carbon footprint, CarbonIQ uses different components for different responsibilities.

### 1. Deterministic Calculation Engine

The calculation engine is responsible for numerical emission calculations.

It uses:

* Activity data.
* Applicable emission factors.
* Calculation rules.

Conceptually:

```text
Estimated Emissions = Activity Amount × Emission Factor
```

The exact formula depends on the activity category and the units of the emission factor.

The calculation engine provides the numerical results used by the rest of the application.

### 2. Machine Learning Model

CarbonIQ includes a serialized model artifact:

```text
carboniq_emissions_model.joblib
```

The model is intended to support data-driven emission analysis.

Model inference must use the same feature definitions, preprocessing, and units used during training.

Predictions should only be presented as forecasts when the model has actually been trained and evaluated for a forecasting task.

### 3. Large Language Model Integration

CarbonIQ integrates Groq for LLM inference, using Qwen through the configured Groq model endpoint.

The LLM is intended to:

* Explain calculated results.
* Interpret available historical information.
* Identify relevant patterns.
* Suggest possible sustainability improvements.
* Answer user questions using available context.

### Why Separate Calculation, ML and LLM?

| Component          | Primary Responsibility                                           |
| ------------------ | ---------------------------------------------------------------- |
| Calculation Engine | Numerical emission calculations.                                 |
| Machine Learning   | Model-based analysis and predictions.                            |
| LLM                | Explanations, recommendations, and natural-language interaction. |

This separation helps prevent language-model-generated numbers from being treated as authoritative emission calculations.

---

## 📐 Carbon Emission Calculation

CarbonIQ uses activity-based calculations to estimate environmental impact.

The general calculation is:

```text
Carbon Emissions (kg CO₂e)
          =
Activity Data × Emission Factor
```

For example, electricity-related emissions can be calculated using:

```text
Electricity Emissions =
Electricity Consumption (kWh)
×
Electricity Emission Factor (kg CO₂e/kWh)
```

Transportation and waste calculations require their respective activity units and emission factors.

### Important Considerations

* Emission factors must have documented sources.
* Activity units must be consistent with the emission factors.
* Different transportation modes require appropriate factors.
* Waste treatment and disposal methods can affect emission calculations.
* Results should be described as estimates unless supported by a verified measurement and methodology.

CarbonIQ aims to keep calculation logic separate from AI-generated explanations.

---

## 🗄️ Data Management

MongoDB Atlas is used for persistent application data storage.

The application is designed to organize information around users and their respective workspaces.

### Data Categories

| Data Category          | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| User Information       | Account and authentication information.                    |
| Workspace Information  | Individual, college, or organization context.              |
| Electricity Records    | Electricity activity data.                                 |
| Transportation Records | Transportation activity data.                              |
| Waste Records          | Waste activity data.                                       |
| Bus Route Information  | Institutional transportation information.                  |
| Emission Information   | Calculated emission results and related records.           |
| AI Context             | Relevant information used to generate contextual insights. |

### Historical Data

Historical activity records are important for understanding changes over time.

CarbonIQ can use available historical data to support:

* Trend analysis.
* Category comparisons.
* Sustainability summaries.
* Contextual AI explanations.

The amount and quality of historical information directly affect the reliability of any analysis.

### Synthetic Dataset

A synthetic dataset was also generated during development for experimentation.

Dataset characteristics:

* 10,000 synthetic activity records.
* 50 workspaces.
* 36 months of records.
* January 2023 to December 2025.
* Electricity, transportation, and waste-related fields.

File:

```text
data/carboniq_synthetic_dataset.csv
```

**Important:** Synthetic records are intended for development, experimentation, and demonstrations. They must not be represented as actual user measurements or verified environmental data.

---

## 📁 Project Structure

The following is a logical overview of the project components. Update directory names to match the final repository before publishing.

```text
CarbonIQ/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── public/
│   ├── styles/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── carboniq_emissions_model.joblib
│   ├── metrics.json
│   ├── requirements.txt
│   └── .env
│
├── data/
│   └── carboniq_synthetic_dataset.csv
│
├── README.md
└── .gitignore
```

The structure above is illustrative. The actual repository structure and module names should be used in the final version.

---

## ⚙️ Installation and Setup

### Prerequisites

Install the following before running CarbonIQ:

* Node.js
* npm
* Python 3.10 or compatible project-supported version
* Git
* MongoDB Atlas account
* Groq API key

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

```bash
cd CarbonIQ
```

### 2. Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the frontend environment file:

```text
.env.local
```

Add the backend API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Backend Setup

Open another terminal and navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the backend directory.

Refer to the environment-variable section below.

### 5. Start the Backend

From the backend directory, run:

```bash
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### 6. Start the Frontend

From the frontend directory:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

The frontend communicates with the FastAPI backend through the configured API URL.

---

## 🔐 Environment Variables

### Backend `.env`

```env
MONGODB_URI=your_mongodb_connection_string

GROQ_API_KEY=your_groq_api_key

GROQ_MODEL=your_configured_groq_model

JWT_SECRET=your_secure_jwt_secret

```

### Frontend `.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Security Notes:**

* Never commit `.env` or `.env.local` files.
* Never expose API keys in frontend code.
* Never commit database credentials.
* Use secure secrets for production deployments.
* Configure environment variables through the hosting platform when deploying.

---

## 🔌 API Overview

CarbonIQ uses REST APIs to connect the frontend with backend services.

The following are the API areas implemented or reported during development.

| API Endpoint                | Purpose                             |
| --------------------------- | ----------------------------------- |
| `/api/auth/register`        | User registration.                  |
| `/api/auth/login`           | User authentication.                |
| `/api/emissions/trend`      | Emission trend information.         |
| `/api/emissions/factors`    | Emission factor information.        |
| `/api/emissions/model-info` | Model information.                  |
| `/api/ai/electricity`       | Electricity-related AI insights.    |
| `/api/ai/transportation`    | Transportation-related AI insights. |
| `/api/ai/waste`             | Waste-related AI insights.          |
| `/api/ai/insights`          | General sustainability insights.    |
| `/api/ai/chat`              | AI interaction endpoint alias.      |

Additional endpoints support activity records, bus routes, savings simulations, and reports.

For the complete request and response specifications, refer to the FastAPI Swagger documentation:

```text
http://localhost:8000/docs
```

---

## 🔒 Security and Data Isolation

CarbonIQ is designed to support different user categories and their respective workspaces.

Important security considerations include:

* JWT-based authentication.
* Authenticated API requests.
* Workspace-aware data access.
* Backend-side authorization.
* Separation of user activity records.
* Secure handling of API credentials.

Workspace isolation should be enforced by the backend rather than relying only on frontend visibility or role selection.

---

## 🔮 Future Enhancements

CarbonIQ has several opportunities for further development.

### Advanced Emission Forecasting

* Improve historical emission forecasting.
* Evaluate time-series models.
* Support longer-term sustainability projections.
* Compare predicted and actual emissions.

### Intelligent Transportation Optimization

* Integrate road-distance and travel-time information.
* Apply vehicle-routing optimization algorithms.
* Consider vehicle capacity and pickup constraints.
* Estimate potential transportation emission reductions.

### Advanced AI Sustainability Analyst

* Improve historical context retrieval.
* Generate more personalized recommendations.
* Support evidence-grounded explanations.
* Improve response speed and structured output handling.

### Sustainability Reporting

* Advanced PDF and spreadsheet exports.
* Monthly and annual sustainability summaries.
* Institutional sustainability comparisons.
* Progress tracking against reduction targets.

### Additional Integrations

* Real-time energy monitoring.
* IoT-based activity collection.
* More detailed institutional sustainability analytics.
* External emission-factor databases.

---

## ⚠️ Limitations

CarbonIQ's results depend on the quality, completeness, and accuracy of the activity data and emission factors supplied to the platform.

Important limitations include:

* Emission calculations are estimates and depend on the selected factors and assumptions.
* Synthetic data must not be treated as actual environmental measurements.
* ML predictions are only as reliable as their training data and evaluation methodology.
* LLM recommendations may require human review.
* Missing historical records can limit trend analysis and predictions.
* Transportation optimization requires valid route, distance, capacity, and operational data.
* Results should not be treated as independently verified carbon accounting or regulatory certification.

---

## 🤝 Contributors

CarbonIQ was developed as a collaborative AI/ML project.

The team worked across:

* Frontend development.
* Backend development.
* Database integration.
* Machine learning.
* LLM integration.
* Sustainability analysis.
* System integration and presentation.


---

##  Our Vision

We believe sustainability should not be limited to awareness.

It should be measurable, understandable, and actionable.

CarbonIQ aims to make environmental impact visible and help individuals and organizations make better decisions through data, artificial intelligence, and technology.

**Measure your impact. Understand your footprint. Make a difference.**

CarbonIQ — Turning Carbon Data into Sustainable Decisions.
