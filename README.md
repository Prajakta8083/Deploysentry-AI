# 🚀 DeploySentry AI

**An AI-augmented gatekeeper that decides whether a code deployment is safe to go live — and explains why in plain English.**

---

## Why I built this

Every company that ships code regularly runs into the same problem: before new code goes live, *someone* has to decide if it's safe. Usually that's a person manually reviewing a pull request, which is slow, inconsistent, and depends on who happens to be free that day.

I wanted to build something that automates the *first pass* of that decision — a system that looks at what changed, checks it against a clear set of rules, and either lets it through, waves a flag for a human to double-check, or blocks it outright. And when it flags or blocks something, instead of just throwing an error code at a developer, it explains *why* in a sentence a person can actually understand.

That's DeploySentry AI.

---

## What it actually does

You give it details about a proposed change — which files were touched, how many lines changed, which branch, whether it came through a pull request — and it responds with one of three decisions:

- 🟢 **APPROVE** — looks safe, proceed
- 🟡 **REVIEW** — needs a human to double-check before continuing
- 🔴 **BLOCK** — stops the deployment entirely

If the decision isn't a clean APPROVE, Gemini generates a short, human-readable explanation of what triggered the flag — so nobody has to dig through logs to understand what happened.

Every decision, whether small or serious, gets permanently logged, so there's a full history of what was approved, flagged, or blocked, and why.

---

## How it works (the actual flow)

```
Developer pushes code
        │
        ▼
Jenkins pipeline starts
        │
        ▼
Jenkins calls DeploySentry's /evaluate endpoint
        │
        ▼
Policy Engine checks the change against rules.yaml
   e.g. "touches auth/ or payments/ → REVIEW"
        "pushed directly to main → BLOCK"
        "over 500 lines changed → REVIEW"
        │
        ▼
Decision made: APPROVE / REVIEW / BLOCK
        │
        ▼
If REVIEW or BLOCK → Gemini writes a plain-English explanation
        │
        ▼
Decision + explanation saved to the audit log (SQLite)
        │
        ▼
An exit code is sent back to Jenkins (0 / 1 / 2)
        │
        ▼
Jenkins continues, pauses for approval, or halts — automatically
```

The important design decision here: **the actual APPROVE/REVIEW/BLOCK decision is rule-based, not AI-based.** Rules are deterministic — the same input always gives the same output, which matters a lot when the decision affects whether code reaches production. AI only comes in *afterward*, to explain a decision in words — never to make the decision itself.

---

## What's under the hood

| Piece | What it's doing here |
|---|---|
| **Python** | The actual policy logic — reading rules and checking them against a proposed change |
| **FastAPI** | Turns the policy engine into a real API other tools (like Jenkins) can call |
| **rules.yaml** | Where all the risk rules live, in plain readable format — change the rules without touching code |
| **Google Gemini API** | Writes the human-readable explanation when something's flagged or blocked |
| **SQLite** | Stores a permanent audit trail of every decision ever made |
| **Docker** | Packages the whole app so it runs identically anywhere, not just on my laptop |
| **Kubernetes** | Runs the containerized app reliably, restarting it automatically if something crashes |
| **Jenkins** | The CI/CD pipeline that actually triggers the check before every deployment |

---

## Project structure

```
deploysentry-ai/
├── main.py               → FastAPI app, defines all API endpoints
├── policy_engine.py      → Core rule-checking logic
├── rules.yaml            → All risk rules, editable without touching code
├── gemini.py              → Handles calls to Gemini for explanations
├── database.py           → Sets up and writes to the SQLite audit log
├── jenkins_check.py       → Script Jenkins runs; turns a decision into an exit code
├── Jenkinsfile            → Defines the actual CI/CD pipeline stages
├── Dockerfile              → Packages the app into a container
├── requirements.txt        → Python dependencies
├── audit_logs.db           → SQLite database (not committed to GitHub)
└── k8s/
    ├── deployment.yaml     → Tells Kubernetes how to run the container
    └── service.yaml        → Gives the deployment a stable network address
```

---

## How to run it yourself

**1. Install dependencies**
```
pip install -r requirements.txt
```

**2. Add your Gemini API key**

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```
Get a free key at https://aistudio.google.com/apikey

**3. Start the server**
```
uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

**4. Try it**

Open `http://localhost:8090/docs` — this gives you an interactive page to test `/evaluate` and `/audit-logs` directly, no coding required.

Example request to `/evaluate`:
```json
{
  "files_changed": ["auth/login.py"],
  "lines_changed": 40,
  "branch": "feature/fix-login",
  "is_pull_request": true
}
```

---

## Running it with Docker

```
docker build -t deploysentry-ai .
docker run -p 8090:8090 -e GEMINI_API_KEY=your_key_here deploysentry-ai
```

## Running it with Kubernetes (local, via Docker Desktop)

```
kubectl create secret generic deploysentry-secrets --from-literal=gemini-api-key=your_key_here
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl port-forward service/deploysentry-service 8090:80
```

---

## Being honest about scope

This is a student/portfolio project, and I want to be upfront about what's fully working versus what's set up to demonstrate understanding:

- ✅ **Fully working:** the policy engine, the API, Gemini explanations, and the SQLite audit log — all genuinely functional, tested locally
- ✅ **Fully working:** Docker containerization and local Kubernetes deployment (via Docker Desktop)
- 🔧 **Simulated / not connected to a real pipeline:** the Jenkinsfile shows the intended pipeline structure and correctly triggers the exit-code logic, but isn't wired into a live, running Jenkins server processing real deployments

I'd rather be clear about that than overstate it — the goal here was to understand and correctly implement each piece of a real CI/CD safety gate, not to fake a production system.

---

## What I'd add next
- Connect this to a real, running Jenkins instance instead of a standalone script
- Add automated tests for the policy engine
- Deploy the API somewhere publicly accessible (not just localhost)
- Add a simple frontend dashboard instead of relying on `/docs`