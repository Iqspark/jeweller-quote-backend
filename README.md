# JSON → MongoDB → Email Service

A FastAPI microservice that:
1. **Accepts any JSON payload** via `POST /submit`
2. **Saves it to MongoDB** (local) or **Azure CosmosDB** (production)
3. **Renders a branded HTML email** from the JSON data using Jinja2
4. **Sends the email** via Azure Communication Services (ACS) or SMTP (local dev)

---

## Architecture

```
Client
  │
  │  POST /submit  { any JSON }
  ▼
FastAPI
  ├── Save to MongoDB / CosmosDB  ──→  201 OK (fast response)
  └── Background task:
        ├── Render HTML template (Jinja2)
        └── Send email (ACS or SMTP)
```

---

## Project Structure

```
json-to-email/
├── app/
│   ├── main.py              # Routes: /submit, /submissions, /health
│   ├── database.py          # MongoDB / CosmosDB connection (Motor async)
│   ├── email_service.py     # ACS + SMTP email sending
│   ├── template_engine.py   # Jinja2 renderer + JSON flattener
│   └── templates/
│       └── email_generic.html   # HTML email template
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions: test → build → deploy
├── Dockerfile
├── docker-compose.yml       # API + MongoDB + Mongo Express UI
├── deploy-azure.sh          # One-shot Azure infrastructure provisioning
├── MIGRATION.md             # MongoDB → CosmosDB migration guide
├── requirements.txt
├── .env.example
└── README.md
```

---

## Local Development

### 1. Start with Docker Compose

```bash
cp .env.example .env
# Edit .env with your SMTP credentials for local email testing

docker-compose up --build
```

| Service       | URL                        |
|---------------|----------------------------|
| API           | http://localhost:8000      |
| Swagger UI    | http://localhost:8000/docs |
| MongoDB UI    | http://localhost:8081      |

### 2. Test the endpoint

```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Jane Doe",
    "order_id": "ORD-12345",
    "product": "Widget Pro",
    "amount": 49.99
  }'
```

Response:
```json
{
  "message": "Data saved. Email is being sent.",
  "document_id": "665f1a2b3c4d5e6f7a8b9c0d"
}
```

The email will be sent in the background. Check MongoDB Express at
`http://localhost:8081` to see the saved document and its `_meta.status` field
update from `received` → `email_sent`.

---

## Email Behaviour

The template engine automatically:
- **Flattens nested JSON** into a clean key/value table
- **Picks a title** from `title`, `name`, or `type` fields if present
- **Finds the recipient** from `email` or `contact.email` in the payload
- **Skips internal fields** prefixed with `_`

No code changes needed when your JSON schema changes.

---

## Azure Deployment

### One-shot provisioning

```bash
# Edit deploy-azure.sh — set your SUBSCRIPTION_ID and preferred names
bash deploy-azure.sh
```

This creates: Resource Group → ACR → CosmosDB → ACS → Container Apps Environment → Container App

### Switch to CosmosDB

In the Container App, update the `MONGO_URI` env var to your CosmosDB connection string.
See **MIGRATION.md** for how to move existing data across.

### Switch to ACS email

Update the Container App env vars:
```
EMAIL_PROVIDER=acs
ACS_CONNECTION_STRING=<from Azure portal>
ACS_SENDER_ADDRESS=DoNotReply@yourdomain.azurecomm.net
```

---

## CI/CD (GitHub Actions)

Add these secrets to your GitHub repo (**Settings → Secrets → Actions**):

| Secret | Value |
|--------|-------|
| `AZURE_CREDENTIALS` | `az ad sp create-for-rbac --sdk-auth` output |
| `ACR_LOGIN_SERVER`  | `acrjsontoemail.azurecr.io` |
| `ACR_USERNAME`      | ACR admin username |
| `ACR_PASSWORD`      | ACR admin password |

Pipeline on every push to `main`: **Test → Build → Push to ACR → Deploy to ACA**

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/`             | Health check |
| GET  | `/health`       | Health + DB connectivity check |
| POST | `/submit`       | Save JSON + trigger email |
| GET  | `/submissions`  | List recent submissions |
