# dando | A donation intelligence tool

## About
dando is a donor intelligence platform that transforms donation data into actionable fundraising strategies. It provides trend insights, donor segmenation of donation data It leverages Elasticsearch ES|QL for data retrieval and inference API for data insights reasoning.

## Agents
### Donor Segmentation
- **Major Gift Agent:** High-capacity prospect identification
- **Retention Agent:** Churn detection and "Win-back" plans
- **Campaign Simulator Agent:** Analyze campaign feasability
### Forecasting
- **Donation Forecaster Agent:** Donation forecasting analysis

## Technical Stack
- Frontend: Streamlit (Python)
- Database: Elasticsearch (Serverless)
- Query Language: ES|QL (Elasticsearch Query Language)
- AI Engine: Google Gemini 2.5 via Elastic Inference API
- Data Processing: Pandas

## Getting Started
1. Environment Configuration
Create a .env file in the root directory with your Elastic credentials:

Bash
```
ELASTIC_URL=https://your-project.es.us-central1.gcp.elastic.cloud
ELASTIC_API_KEY=your_secure_api_key
```

2. Installation

Bash
```
pip install streamlit elasticsearch python-dotenv pandas
```

3. Running the App

Bash
```
streamlit run streamlit_app.py
```
