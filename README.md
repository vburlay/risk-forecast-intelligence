# 🧠 IQ Early Warning System  
### Predictive Risk Monitoring & Decision Intelligence Platform

---

## 📌 Overview

The IQ Early Warning System converts raw operational data into **structured decision intelligence** by detecting risks early, quantifying uncertainty, and evaluating the impact of potential interventions.

Unlike traditional dashboards that focus on retrospective analysis, the system:

* Detects deviations before they become critical
* Quantifies future risk and uncertainty
* Simulates system behavior under changing conditions
* Evaluates the effectiveness of corrective actions

👉 The goal is to enable **proactive decision-making under uncertainty**, rather than reactive monitoring.


---

## 🧠 Core Concept

The system transforms data into decisions through a structured analytical pipeline:

```
Observe → Predict → Detect → Assess → Simulate → Decide
```

Each stage increases the level of abstraction, turning raw data into actionable decision insights.

---

## ❗ Problem

Operational systems often react too late to emerging risks.

By the time deviations become visible:
- corrective actions are expensive  
- system stability is already compromised  
- decision-makers lack forward-looking insight  

This project addresses:
- delayed risk detection  
- lack of predictive indicators  
- absence of structured decision support  

---

## 🎯 Key Capabilities

### 📊 Monitoring (Operational Control)
- Real-time KPI tracking  
- Forecast vs actual comparison  
- Deviation analysis  
- Team-level risk overview  

---

### 📈 Forecast Analysis
- Time series modeling per team  
- Expected vs actual development  
- Trend-based deviation tracking  

---

### 🔎 Anomaly Detection
- Statistical deviation detection using rolling windows  
- Dynamic sensitivity control  
- Identification of unusual patterns  

**Formula:**
```
|score| = |(Actual - Trend) / Std|
```

---

### 🧬 Risk Assessment
- Gap-based risk scoring  
- Combined signal logic:
  - relative deviation (Gap)
  - anomaly intensity
  - temporal dynamics  

- Risk classification:
  - 🟢 Normal  
  - 🟡 Beobachten (Watch)  
  - 🔴 Kritisch (Critical)  

👉 The system approximates the probability of future risk events, providing a bridge between deterministic signals and probabilistic risk assessment.


---

### ⏳ Time-to-Risk Modeling

The system distinguishes between:

- **Zeit bis kritisch**  
  → deterministic estimate based on trend extrapolation  

- **Expected Time to Gap**  
  → probabilistic risk-based estimate  

👉 This separation enables both **explainability and forward-looking risk assessment**.

---

### 🧪 Simulation & Impact
- Combined workspace with two modes:
  - **Scenario** for what-if analysis
  - **Measure** for corrective actions

- Scenario controls:
  - volume increase  
  - trend acceleration  
  - volatility changes  

- Measure controls:
  - gap reduction  
  - stabilization  
  - forecast adjustment  

- Comparison vs baseline system behavior  
- Evaluation of **risk reduction effectiveness**  

👉 The system connects **prediction → action → outcome**.

---

### 🧭 Decision Support
- Rule-based workspace for action-oriented recommendations
- Compares available corrective actions against the current risk situation
- Explains the recommended action, expected KPI changes, alternatives, and confidence

👉 Decision Support translates simulation outputs into a concrete action recommendation.

---

## 🏗️ Architecture

The system follows a layered decision pipeline:

1. **Monitoring** – observe current system state  
2. **Forecast** – estimate expected behavior  
3. **Anomaly Detection** – detect deviations  
4. **Risk Assessment** – quantify future risk  
5. **Simulation & Impact** – model scenarios and evaluate corrective actions  
6. **Decision Support** – recommend actions and explain expected impact  

---

## 🔄 Data Flow

```
Raw Data 
   → Feature Extraction 
   → Signal Detection 
   → Risk Scoring 
   → Simulation & Impact
```

---

## 🗂️ Project Structure

```
project/
├── app.py                         # Dash application entry point
├── generate_mock_data.py          # synthetic DuckDB dataset generator
├── test_duckdb.py                  # local database smoke check
├── data/                           # ignored local DuckDB files
├── artifacts/                      # future model artifacts
├── archive/
│   └── dashboard_alt.py            # legacy monolithic dashboard reference
├── pack/
│   ├── decision_support/
│   │   ├── __init__.py
│   │   └── core.py                 # decision support recommendation logic
│   ├── anomaly/
│   │   └── detection.py            # anomaly scoring and figures
│   ├── forecast/
│   │   ├── features.py             # forecasting feature engineering
│   │   └── models.py               # baseline and future model interfaces
│   ├── risk/
│   │   ├── core.py                 # deterministic risk logic
│   │   └── survival.py             # heuristic future-risk signals
│   ├── simulation/
│   │   ├── scenario.py             # what-if scenarios
│   │   └── intervention.py         # corrective actions
│   ├── services/
│   │   ├── decision_support_service.py # decision support orchestration
│   │   ├── anomaly_service.py
│   │   ├── forecast_service.py
│   │   ├── monitoring_service.py
│   │   ├── risk_service.py
│   │   └── simulation_service.py
│   ├── ui/
│   │   ├── decision_support.py     # Decision Support workspace
│   │   ├── callbacks.py
│   │   ├── components.py
│   │   ├── monitoring.py
│   │   ├── forecast.py
│   │   ├── anomaly.py
│   │   ├── risk.py
│   │   ├── scenario.py
│   │   ├── intervention.py
│   │   ├── description.py
│   │   └── styles.py
│   ├── config.py
│   └── data_access.py
├── requirements.txt
├── eda.ipynb
└── README.md
```

---

## 🧪 Data

All data is **synthetically generated**.

- No real customer data  
- No real SAP data  
- SAP-like fields used for realism (e.g. `/BIC/...`)  

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate mock data
```bash
python generate_mock_data.py
```

### 3. Run application
```bash
python app.py
```

Open in browser:
```
http://127.0.0.1:8050/
```

---

## 📊 Technology Stack

- Python  
- Dash (Plotly)  
- DuckDB  
- Pandas / NumPy  
- Plotly  

---

## 💡 Use Cases

- Finance → risk monitoring, fraud detection  
- Healthcare → capacity monitoring  
- Manufacturing → process deviations  
- Energy → load anomalies  
- Retail → demand forecasting  
- Security / Defense → early warning systems  

---

## ⚠️ Limitations

- Risk modeling is currently heuristic and not fully probabilistic
- No probabilistic ML model yet  
- Synthetic data only  
- No real-time streaming  
- No causal or intervention learning yet

---

## 🚀 Future Improvements

- Logistic regression for risk prediction  
- Survival analysis (time-to-event modeling)  
- Advanced anomaly detection (probabilistic methods)  
- Advanced decision-support workflows for guided analysis
- Real-time data pipeline  
- API integration  

---

## 🧠 Concept

```
Observe → Predict → Detect → Assess → Simulate → Decide
```

---

## 🧠 Key Insight

The system shifts risk management from:

**reactive monitoring → proactive decision intelligence under uncertainty**

By linking detection, prediction, simulation, and decision-making, it enables organizations to act before risks materialize.


---

## 📄 License

For educational and demonstration purposes only.

---

## 👤 Author

V. Burlay  
Data Analytics / Risk Intelligence Prototype
