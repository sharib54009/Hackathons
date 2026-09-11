# SafeRoute

SafeRoute is a proactive ride-safety platform. This repository currently contains only the initial frontend and backend scaffolding.

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

## Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The backend health check is available at `GET http://127.0.0.1:5000/api/health`.
