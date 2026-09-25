# 🏠 Immobiliare System

> Professional desktop real-estate management application — Python + PySide6 + SQLAlchemy.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green)](https://doc.qt.io/qtforpython/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-yellow)](tests/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

A production-oriented, modular, secure desktop app for real-estate agencies:
properties, owners, clients, agents, visits, contracts (rent/sale), payments,
expenses, documents, calendar, reports, users/roles, audit log, backup/restore
and settings — all in one modern Qt interface (Italian default, light/dark theme).

---

## ✨ Features

| Area | What you get |
|---|---|
| 📊 Dashboard | KPI cards (properties, sale/rent, sold/rented, clients, visits, payments, revenue/expenses), recent activity, appointments, latest properties |
| 🏢 Properties | Full registry (code, type, sale/rent, status, address, surfaces, rooms, energy class, price/rent, owner, agent…), advanced filters, tabbed detail (general, description, photos, documents, history), photo gallery with thumbnails + primary image, duplicate detection, soft-delete/archive |
| 👤 Owners / 🤝 Clients / 💼 Agents | CRUD, contact + tax data, portfolios, client requirements + **matching engine** (price / surface / city / type / rooms with reasons), favorites |
| 👁 Visits / 📅 Calendar | Scheduling, confirm/complete/cancel, follow-up notes, auto calendar entries, deadlines, reminders |
| 📝 Contracts / 🔑 Rentals / 💰 Sales | Rental & sale contracts, status workflow (draft → active → terminated), coherent property-status updates, all inside DB transactions |
| 💳 Payments / 🧾 Expenses | Due/paid/late/cancelled tracking, auto late detection, unique references, per-property/owner expenses |
| 📄 Documents | Property/owner/client/contract/payment attachments, type + size validation, safe filenames, no path traversal |
| 📊 Reports | Inventory, sales, rentals, due payments, revenue, expenses, owner statements, agent commissions, monthly stats — export to **PDF / Excel / CSV** |
| 👥 Users & Roles | ADMIN / MANAGER / AGENT / ACCOUNTANT / VIEWER with **permission-based** auth (`properties.view`, `contracts.create`, …) — never role-name checks in UI |
| 🛡 Audit log | Login, CRUD, exports, contracts, payments, users, backups — with user, timestamp, old/new values, result |
| 💾 Backup | Manual backup, verified restore (header + schema check), rotation, optional Fernet encryption |
| ⚙ Settings | Company data, language, theme, currency, date format, backup/doc dirs, session timeout |
| 🌙 UX | Sidebar + toolbar + statusbar, shortcuts (Ctrl+1…9), tooltips, confirm dialogs, empty states, validation + toast messages, responsive layout |

## 🔐 Security (first-class)

- Argon2id password hashing, strength validation, no plaintext passwords
- Account lockout after N failed logins, enable/disable accounts, secure reset tokens
- Session with inactivity auto-logout
- Parameterized SQL via SQLAlchemy only — no string-built queries
- Encrypted sensitive fields (Fernet), OS keyring for the app key (file fallback with `0600`)
- Upload validation (type + size + real-image check), UUID filenames under `documents/`
- Structured logs with secret redaction — passwords/keys/tokens never logged
- Transaction rollback on multi-step failures, FK + unique constraints, permission gates in services

## 🧱 Architecture

```text
GUI (PySide6 pages/dialogs/widgets)
 → Services (business logic, permissions, audit, transactions)
 → Repositories (SQL only here)
 → SQLAlchemy ORM
 → SQLite (Alembic-ready)
```

```text
app/
├── main.py            # entrypoint (python -m app.main)
├── config/            # settings (env-overridable), logging, i18n hook
├── i18n/              # it (default) + en string tables
├── database/          # connection, models (17 tables, enums, indexes, soft-delete)
├── security/          # password, encryption, auth, permissions, session
├── repositories/      # generic base + audit recorder
├── services/          # property, people, schedule, deal, platform (docs/users/reports/backup/…)
├── validators/        # Pydantic input schemas
├── utils/             # secure files, duplicates, formatting, CSV/Excel export
├── reports/           # ReportLab PDF builder
├── gui/               # theme, helpers, context (DI), widgets, windows, pages
└── seed.py            # fake demo data (never real personal data)
tests/                 # pytest: auth, permissions, CRUD, matching, backup, validation
```

Key rules enforced: no DB queries in widgets, small focused classes, type hints,
no giant files, no global mutable business state (`AppContext` is injected).

## 🚀 Quickstart

**Requirements:** Python 3.10+, Windows/Linux/macOS.

```bash
# 1. Install
pip install -r requirements.txt

# 2. (optional) Load demo data — all fake
python -m app.seed

# 3. Run
python -m app.main
```

First run auto-creates the SQLite DB (`data/immobiliare.db`) and a default admin
if the DB is empty.

### 🔑 Demo accounts (seed)

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin123!` | ADMIN |
| `manager` | `Manager123!` | MANAGER |
| `agente` | `Agente123!` | AGENT |
| `contabile` | `Contabile123!` | ACCOUNTANT |
| `viewer` | `Viewer123!` | VIEWER |

> Change these passwords before any real use. Reset the demo DB anytime:
> `python -m app.seed --reset`.

## ⚙️ Configuration

All settings are env-overridable (see [`.env.example`](.env.example) — no real secrets):

| Variable | Default | Description |
|---|---|---|
| `IMMOBILIARE_DB_URL` | `sqlite:///data/immobiliare.db` | Database URL |
| `IMMOBILIARE_LANGUAGE` | `it` | `it` / `en` |
| `IMMOBILIARE_THEME` | `light` | `light` / `dark` |
| `IMMOBILIARE_BACKUP_DIR` | `backups/` | Backup destination |
| `IMMOBILIARE_DOC_DIR` | `documents/` | Photos + documents root |
| `IMMOBILIARE_SESSION_TIMEOUT_MIN` | `15` | Inactivity logout |
| `IMMOBILIARE_MAX_LOGIN_ATTEMPTS` | `5` | Lockout threshold |
| `IMMOBILIARE_LOCKOUT_SECONDS` | `300` | Lockout duration |

In-app **Settings** page persists company name, language and theme to the DB.

## 🧪 Tests

```bash
pytest -q
```

Covers: password hashing/strength, login lockout, permission enforcement,
property CRUD + duplicate rejection, client CRUD + matching engine,
contract → payment flow + status transitions, backup create/verify, Pydantic validation.

> Note: `requirements.txt` pins `SQLAlchemy==2.0.44` — v2.1's C extension is
> blocked by some Windows App-Control policies and v2.0.36 lacks Python 3.14
> typing support.

## 📦 Packaging (PyInstaller)

```bash
pyinstaller --noconfirm --windowed --name ImmobiliareSystem app/main.py
```

See [`build.spec.example`](build.spec.example) for a fuller spec
(hidden imports for `sqlalchemy`, `argon2`, `cryptography`, `keyring`).
Photos/documents/backups live outside the executable (`documents/`, `backups/`,
`data/`) so a frozen build keeps working.

## 🗄 Migrations

The app uses `Base.metadata.create_all()` for zero-config startup. Alembic
scaffolding is included (`alembic.ini`, `alembic/env.py` — autogenerate from
`app.database.models.Base`):

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
## ⌨️ Shortcuts

| Keys | Action |
|---|---|
| `Ctrl+1 … Ctrl+9` | Jump to first 9 modules |
| `Enter` (in search) | Run search |
| `Esc` | Close dialog |

## 🤝 Contributing

1. Fork → feature branch → PR with description + tests.
2. Keep style PEP 8, type hints, small modules; never put SQL in GUI code.
3. Never commit secrets, real personal data, or production DBs (`data/*.db` is git-ignored).
4. Run `pytest -q` before pushing.

## 📄 License

MIT — see [LICENSE](LICENSE) (add one if missing). Demo data is fictional;
any resemblance to real persons or properties is coincidental.

---

Made with Python, PySide6, SQLAlchemy and a healthy obsession for clean architecture. 🏡

## 👤 Author

**zakariaelqannaa-dv** — https://github.com/zakariaelqannaa-dv
