# Demografy AI Assistant

A Streamlit-based chatbot that assists users in querying Australian demographic data using **LangChain**, **Google Gemini**, and **Google BigQuery**.

## Features

- 🤖 AI-powered natural language chat interface
- 📊 Real-time BigQuery data access
- 🇦🇺 Australian demographic analytics
- 💬 Conversational memory for context-aware responses
- 🔒 Read-only safe query execution

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Streamlit  │ ──────> │  LangChain  │ ──────> │   Gemini    │
│   Chat UI   │ <────── │    Agent    │ <────── │     LLM     │
└─────────────┘         └──────┬──────┘         └─────────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │  BigQuery   │
                        │    Tool     │
                        └──────┬──────┘
                               │
                               ▼
                        ┌─────────────┐
                        │  BigQuery   │
                        │  demografy  │
                        └─────────────┘
```

## Prerequisites

- Python 3.9+
- Google Cloud project with BigQuery access
- Gemini API key

## Setup

### 1. Clone and Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Path to your Google Cloud service account key JSON
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Google Cloud project ID
GOOGLE_CLOUD_PROJECT=demografy

# Gemini API key
GEMINI_API_KEY=your-gemini-api-key-here

# BigQuery configuration
BIGQUERY_PROJECT=demografy
BIGQUERY_DATASET=prod_tables
BIGQUERY_TABLE=a_master_view
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`.

## Project Structure

```
DAX/
├── app.py                      # Main Streamlit application
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration and system prompt
├── chains/
│   ├── __init__.py
│   └── chat_chain.py           # LangChain agent with Gemini
├── tools/
│   ├── __init__.py
│   └── bigquery_tool.py        # Custom BigQuery tool
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Available Demographic Metrics

| Metric | Column | Range |
|--------|--------|-------|
| Prosperity Score | `kpi_1_val` | 0-100% |
| Diversity Index | `kpi_2_val` | 0-1 |
| Migration Footprint | `kpi_3_val` | 0-100% |
| Learning Level | `kpi_4_val` | 0-100% |
| Social Housing | `kpi_5_val` | 0-100% |
| Resident Equity | `kpi_6_val` | 0-100% |
| Rental Access | `kpi_7_val` | 0-100% |
| Resident Anchor | `kpi_8_val` | 0-100% |
| Household Mobility | `kpi_9_val` | 0-1 |
| Young Family | `kpi_10_val` | 0-100% |

## Example Queries

- "What are the top 3 most diverse suburbs in Victoria?"
- "What is the average prosperity score in New South Wales?"
- "Show me suburbs with high young family presence and high learning levels"
- "Compare home ownership vs rental access by state"
- "What are the most stable suburbs in Queensland?"

## Security

- Only `SELECT` queries are permitted
- Maximum 50 rows per query
- Query timeout enforced at 30 seconds
- 1 GB bytes-billed limit per query
- Only the `demografy.prod_tables.a_master_view` table is accessible

## License

Proprietary - Demografy