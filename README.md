# Cruzhacks26

## Frontend Setup

```bash
cd frontend
npm i
npm run dev
```

The frontend will run on http://localhost:3000

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend will run on http://localhost:8000
