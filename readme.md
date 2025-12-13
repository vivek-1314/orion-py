# How to Use Orion

## 1. Setup

### Clone the repository:
```bash
git clone https://github.com/<your_username>/orion.git
cd orion
``` 

### setup the virtual enviornment
### Create a Python virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

## Install dependencies:
```bash 
pip install -r requirements.txt
```

### Configure environment variables (example): in .env 
```
GROQ_API_KEY= 
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
JINA_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
PINECONE_ENV=
##### pooled connection string for supabase
SUPABASE_URL=
SUPABASE_PASSWORD=
##### langsmith for tracing
LANGSMITH_API_KEY=
LANGSMITH_TRACING=
LANGSMITH_ENDPOINT= 
```

## 2. Start Orion Service

``` sh 
uvicorn orion_main:app --reload
```

## 3. Open postman 
#### and call `post http://localhost:8000/run-graph`

> payload
```json 
{
  "user_id": "user_123",
  "input": "Remind me what events I have tonight and update my favorite music genre to jazz."
}
```

## Workflow
### Execution Flow:
##### Segmentation Node:
    - Splits user input into memory_to_write, memory_to_fetch, ignore.

##### Classification Node:
    - Assigns memory types (identity, habits, preferences, events, tasks) deterministically.

##### Router Node:
    - Triggers memory writes and reads in parallel:

> Memory Writer: generates embeddings, upserts to Pinecone, stores structured memory in Postgres.

>Memory Reader: fetches identity from Postgres, performs semantic recall for preferences/habits/events via Pinecone + Postgres.

##### Final Answer Node:

    - Aggregates retrieved context
    - Invokes LLM once to generate response
    - Returns final answer