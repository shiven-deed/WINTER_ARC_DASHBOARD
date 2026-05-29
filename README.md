# Full-Stack Fitness Analytics Dashboard with Cloud Relational Database and Predictive Modeling

An end-to-end web application deployed via Streamlit Cloud that enables users to log, manage, and model personal metrics over time. The system integrates a Supabase PostgreSQL cloud backend for relational data persistence, an inline machine learning pipeline for trajectory forecasting, and a context-aware Large Language Model (LLM) coaching module driven by data deltas.

## Deployed Application
* **Production URL:** [https://winterarcdashboard.streamlit.app/]

## Core Architecture & Technologies
* **User Interface & Deployment:** Streamlit / Streamlit Cloud (Python-native interface)
* **Cloud Database Layer:** Supabase PostgreSQL (`psycopg2` driver)
* **Data Pipelines & Manipulation:** Pandas, NumPy
* **Statistical Modeling:** Scikit-Learn (`LinearRegression`)
* **Data Visualization:** Matplotlib (`mdates` chronological plotting)
* **Generative AI Integration:** Groq SDK (`llama-3.1-8b-instant`)

---

## Technical Implementations & System Logic

### 1. Relational Cloud Database Integration (`db.py`)
* Implemented a centralized **Supabase PostgreSQL** cluster to manage user data across distinct client sessions safely.
* Optimized database writes by utilizing an `ON CONFLICT(date) DO UPDATE` relational query execution block, successfully preventing duplicate primary-key conflicts for calendar dates.
* Enforced parametric query styling within database calls to safeguard data transactions against common security risks like SQL injection.

### 2. Time-Series Predictive Modeling & Data Constraints
* Mapped chronological date fields into numeric data format (`date_ordinal`) to execute an inline Scikit-Learn `LinearRegression` model.
* Engineered a 14-day tracking algorithm to chart real-world weight projections against ideal path parameters.
* **Data Ingestion Threshold:** Programmed a structural model constraint requiring a minimum dataset of **5 entries logged across 5 distinct days**. This rule establishes a statistically valid trendline before executing the two-week linear regression forecast.
* Formulated trendline trajectory comparison mathematical vectors ($m$) to instantly evaluate performance statuses (On-Track vs. Off-Track) against user-defined target values:
    $$\text{Required Slope} = \frac{\text{Target Weight} - \text{Current Weight}}{\text{Days Remaining}}$$
* Implemented a 7-day data smoothing framework via Pandas `.rolling(window=7, min_periods=2).mean()` to filter out daily fluid fluctuations and isolate genuine compositional trends.

### 3. State-Managed LLM Prompt Engineering
* Constructed a rule-based logic switch inside the data-processing pipeline to evaluate structural database deltas (such as days elapsed since last entry and immediate weight variance).
* Configured the application to dynamically bifurcate system prompt structures routed to the Groq API endpoint depending on real-time database evaluations.
* Established strict operational parameters (such as temperature controls and maximum token limits) to guarantee concise, deterministic text outputs from the inference model.

### 4. Advanced Analytical Visualization & Data Storytelling (Matplotlib)
* Managed data ink ratio by completely redesigning matplotlib defaults to maximize cognitive scannability for stakeholders (custom grid opacity adjustments, rotated tick parameters, and clean boundary layouts).
* Implemented dual-layer chronological trend plotting utilizing `matplotlib.dates` (`mdates`) to dynamically format multi-month time axes cleanly across changing calendar intervals.
* Engineered multi-line visual markers to contrast non-linear historical moving averages against linear predictive regression forecasts, allowing end-users to evaluate performance metrics at a glance.
---

## Local Deployment Instructions

### 1. Environment Configuration
To maintain operational security, the database credentials and API components must be configured as environment variables. Do not hardcode these keys into the codebase.
```bash
export DATABASE_URL="your_supabase_postgresql_connection_string"
export GROQ_API_KEY="your_groq_api_key"
2. Repository Installation
Clone the repository to your local runtime environment and establish dependencies:

Bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/shiven-deed/WINTER_ARC_DASHBOARD.git)
cd WINTER_ARC_DASHBOARD
pip install -r requirements.txt
