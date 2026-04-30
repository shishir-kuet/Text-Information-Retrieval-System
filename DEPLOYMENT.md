# Deployment (Render) — Non-Docker

This project can be deployed on Render (https://render.com) with minimal configuration. The repository includes a `render.yaml` that defines two services: the backend (Python web service) and the frontend (static site). The backend expects a MongoDB connection via `MONGO_URI`.

Recommended production setup
- Backend: Render Web Service (Python) using Gunicorn (start command provided in `render.yaml`).
- Frontend: Render Static Site — build with `npm run build` and publish `frontend/dist`.
- Database: Use MongoDB Atlas (free tier) and set `MONGO_URI` in service env vars.
- TLS: Render provides automatic TLS for both services.

Quick steps
1. Push your repository to GitHub/GitLab.
2. In Render, create a new service from your repo or import using `render.yaml`.
   - Replace `REPO_URL_PLACEHOLDER` in `render.yaml` with your repo when needed.
3. For the backend service, set these environment variables in Render dashboard (or use secrets):
   - `MONGO_URI` — connection string from MongoDB Atlas
   - `DB_NAME` — (optional) defaults to `book_search_system`
   - `JWT_SECRET` — set a secure random value
4. For the frontend service, Render will run `npm install` and `npm run build` as configured.

MongoDB Atlas (free tier)
1. Create an Atlas account: https://www.mongodb.com/cloud/atlas
2. Create a free cluster and a database user with a strong password.
3. In Network Access, allow access from anywhere (0.0.0.0/0) for quick testing — for production, restrict by IP.
4. Copy the connection string and replace `<username>`, `<password>`, and optionally `/?retryWrites=true&w=majority`.
5. Set the resulting URL as `MONGO_URI` in Render env vars. Example:

   mongodb+srv://myuser:MyP@ssw0rd@cluster0.abcd123.mongodb.net/?retryWrites=true&w=majority

Backend start command
The `render.yaml` uses:

```
gunicorn -w 4 -b 0.0.0.0:$PORT backend.run:app
```

which loads the Flask `app` exposed by `backend/run.py`.

Local testing notes
- Create `backend/.env` from `backend/.env.example` and set a local `MONGO_URI` (e.g., `mongodb://localhost:27017/`).
- Create and activate a virtualenv, then:

```bash
pip install -r backend/requirements.txt
python backend/run.py
```

Optional improvements
- Add health-check endpoints, readiness probes, and background job handling if you add async processes.
- Consider using Render's private services or VPC peering with Atlas for production security.
- Add CI/CD (GitHub Actions) to run tests and automate deploys.

Step-by-step: Deploy with Render (recommended)

1. Push your repository to GitHub or GitLab (ensure `render.yaml` is in the repo root).
2. Open the Render dashboard and choose "New -> Import from repo" (or "New -> Web Service" / "Static Site").
3. If Render supports importing `render.yaml`, use that option. Otherwise create two services manually:
   - Backend (Web Service):
     - Environment: Python
     - Build Command: `pip install -r backend/requirements.txt`
     - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT backend.run:app` (or use `backend/start.sh`)
     - Branch: `main` (or your chosen branch)
   - Frontend (Static Site):
     - Build Command: `cd frontend && npm ci && npm run build`
     - Publish Path: `frontend/dist`

4. In the Render service settings for the backend, add environment variables / secrets:
   - `MONGO_URI` — MongoDB Atlas connection string.
   - `DB_NAME` — optional, default `book_search_system`.
   - `JWT_SECRET` — set to a secure random string.

5. For MongoDB Atlas:
   - Create a free cluster and a database user.
   - In Network Access, either allow access from anywhere (`0.0.0.0/0`) for quick testing or configure VPC peering (paid) for production.
   - Copy the connection string and paste it into `MONGO_URI` on Render.

6. Trigger a deploy (push to the repo branch). Monitor the build logs in Render — the backend will start with Gunicorn and the frontend will be published as a static site.

7. (Optional) Configure a custom domain and enable automatic TLS in Render.

Troubleshooting tips
- If `gunicorn` fails to start, confirm it's listed in `backend/requirements.txt` and that Render installed dependencies.
- If the app can't reach MongoDB, check `MONGO_URI` and Atlas network allowlist.
- Check logs in Render dashboard (Build and Live logs) for stack traces and errors.

