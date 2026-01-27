# dando
A multi-step agent donation intelligence tool

## Features

- **Campaign Simulator (Agentic Forecasting):** Uses Elastic aggregations to simulate ROI for potential outreach based on historical gift patterns.
- **Personalized Action Drafter:** A multi-step workflow that retrieves constituent profiles, CRM history to generate hyper-personalized outreach.
- **Customer Segmentation:** Leverages **ES|QL** and Runtime Fields for real-time engagement scoring across disconnected datasets.

## Architecture

The application is built using a modern Python stack optimized for serverless deployment:

* **Backend:** FastAPI
* **Search Engine:** Elasticsearch (Elastic Cloud)
* **Orchestration:** Elastic Agent Builder
* **Frontend:** Jinja2 Templates
* **Deployment:** Vercel



[Image of AI agent architecture diagram]


## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- An Elastic Cloud account (or local Elasticsearch instance)
