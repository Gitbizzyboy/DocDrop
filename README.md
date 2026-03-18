# DocDrop 📂

> **Stop asking clients for documents. Send them a link instead.**

DocDrop gives every bookkeeping client a personal upload portal. They drag and drop their files — no login needed — and you see everything organized in your dashboard.

---

## What It Does

- Each client gets a **unique upload URL** (e.g. `https://docdrop.app/upload/abc123`)
- Clients upload directly — no account required
- Bookkeeper sees a clean dashboard: all clients, all docs, new-doc badge counts
- Download individual files or bulk ZIP per client
- Stripe subscription billing ($39/mo)

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+ / Flask 3.0 |
| Database | PostgreSQL (SQLite for local dev) |
| ORM | SQLAlchemy 2.0 |
| Auth | Flask-Login + Werkzeug password hashing |
| Payments | Stripe Checkout + Webhooks |
| Frontend | Jinja2 + Bootstrap 5 CDN |
| Storage | Local filesystem / Railway volume |
| Hosting | Railway |

---

## Local Development Setup

### 1. Clone & create virtualenv

```bash
cd /path/to/DocDrop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — for local dev, the defaults work out of the box (SQLite, no Stripe needed):

```
SECRET_KEY=any-random-string-here
# Leave DATABASE_URL blank to use SQLite (docdrop_dev.db)
# Stripe keys optional for local testing
```

### 3. Run the app

```bash
python app.py
```

Visit `http://localhost:5000` — the database tables are created automatically on first run.

### 4. Test the portal flow

1. Register a bookkeeper account at `/register`
2. Add a client via the dashboard
3. Copy their portal link and open it in an incognito window
4. Upload a test file — it should appear in the dashboard instantly

---

## Deploy to Railway

### Prerequisites

- [Railway account](https://railway.app) (free tier works for launch)
- [Stripe account](https://stripe.com) for payments

### Step 1: Create Railway project

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
```

Or use the Railway dashboard: New Project → Deploy from GitHub repo.

### Step 2: Add PostgreSQL

In the Railway dashboard:
- Click **New** → **Database** → **PostgreSQL**
- Railway auto-sets `DATABASE_URL` in your environment

### Step 3: Add a Volume (file storage)

In the Railway dashboard:
- Go to your service → **Volumes**
- Mount path: `/app/static/uploads`
- This persists uploaded files across deploys

### Step 4: Set environment variables

In Railway dashboard → your service → **Variables**, add:

```
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
UPLOAD_FOLDER=static/uploads
MAX_UPLOAD_MB=25
BASE_URL=https://your-app.railway.app

# Stripe (get from dashboard.stripe.com)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MONTHLY_PRICE_ID=price_...
```

### Step 5: Set up Stripe

1. Create a product in Stripe: **$39/month subscription**
2. Copy the **Price ID** (starts with `price_`) → set as `STRIPE_MONTHLY_PRICE_ID`
3. In Stripe Dashboard → Webhooks → Add endpoint:
   - URL: `https://your-app.railway.app/stripe/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.deleted`
     - `customer.subscription.updated`
     - `invoice.payment_failed`
4. Copy the **Webhook Secret** (starts with `whsec_`) → set as `STRIPE_WEBHOOK_SECRET`

### Step 6: Deploy

```bash
railway up
```

Or push to GitHub — Railway auto-deploys on every push.

### Step 7: Custom domain (optional)

In Railway → your service → **Settings** → **Domains** → Generate domain or add custom.

---

## Project Structure

```
DocDrop/
├── app.py                  # App factory, routes, config
├── requirements.txt
├── Procfile                # gunicorn start command
├── railway.toml            # Railway deploy config
├── .env.example
├── models/
│   ├── __init__.py         # SQLAlchemy db instance
│   ├── user.py             # Bookkeeper account
│   ├── client.py           # Client + portal token
│   └── document.py         # Uploaded file metadata
├── routes/
│   ├── auth.py             # Register / login / logout
│   ├── dashboard.py        # Bookkeeper dashboard + downloads
│   ├── clients.py          # Add / edit / delete clients
│   ├── portal.py           # PUBLIC upload portal (no login)
│   └── stripe_webhook.py   # Stripe event handler
├── services/
│   ├── storage.py          # File save/retrieve/delete
│   └── stripe_service.py   # Checkout + billing portal
├── templates/
│   ├── base.html
│   ├── landing.html
│   ├── auth/{login,register}.html
│   ├── dashboard/{index,client,add_client}.html
│   └── portal/upload.html
└── static/
    ├── style.css
    └── uploads/            # Stored files (gitignored)
```

---

## Database

Tables are auto-created via `db.create_all()` on startup. For production migrations down the road, add Flask-Migrate.

Schema:
- **users** — bookkeeper accounts (email, password_hash, business_name, stripe fields, plan)
- **clients** — linked to a user, has unique `portal_token`
- **documents** — linked to a client, stores file metadata + path

---

## Security Notes

- Passwords hashed with Werkzeug (PBKDF2/SHA-256)
- Portal tokens are 64-char cryptographically random URL-safe strings
- File uploads: type allowlist, 25MB max, UUID-based stored filenames
- Stripe webhooks verified via signature
- Client portal is intentionally unauthenticated (by design — that's the product)

---

## What Jacob Needs to Do

1. **Create Railway account** → railway.app
2. **Create Stripe account** → stripe.com
3. **Create a $39/mo product in Stripe** → copy the Price ID
4. **Push this repo to GitHub** → connect to Railway for auto-deploy
5. **Set environment variables** in Railway (see Step 4 above)
6. **Set up Stripe webhook** pointing to your Railway URL
7. **Add a Railway Volume** mounted at `/app/static/uploads`
8. **Set a custom domain** (optional but looks more legit: `docdrop.app`)
9. **Test the full flow**: register → add client → copy portal link → upload test file → download from dashboard

Total setup time: ~45 minutes.

---

## Future Improvements (Post-MVP)

- Email notifications to bookkeeper when client uploads
- S3/R2 file storage (swap `services/storage.py`)
- Client email notifications ("your files were received")
- Flask-Migrate for DB schema migrations
- Document preview (PDF thumbnail)
- Bulk mark-as-reviewed
- Usage limits on free tier
- Onboarding tour

---

*Built with Flask + Bootstrap 5. Hosted on Railway. Payments via Stripe.*
