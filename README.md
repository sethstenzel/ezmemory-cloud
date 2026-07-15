# ezmemory 🧠 — hosted at [ezmemory.cloud](https://ezmemory.cloud)

A note-taking and spaced-repetition study service. Subscribers take outline-style notes,
turn any bullet into a flashcard with inline syntax, and practice with a
spaced-repetition queue. **30-day free trial, then $1/month.**

Built with **Django** (backend), **htmx** + **Alpine.js** (frontend, vendored locally —
no CDN dependencies), and SQLite for storage. Push notifications are built in via
Web Push/VAPID — no third-party notification service.

See [app_features.md](app_features.md) for the full feature requirements list.

## Quick start (uv)

```bash
uv sync                      # create the venv and install dependencies
uv run manage.py migrate
uv run manage.py seed        # default admin user + welcome notes + tutorials + blog
uv run manage.py runserver           # http://localhost:8888
# uv run manage.py runserver 0.0.0.0:8888   # reachable from the network
```

Then open http://localhost:8888 and sign in with the seeded account:

- **Username:** `sethcstenzel`
- **Password:** `41Dropsatatime!`

Subscribers create their own accounts at `/signup/`.

<details>
<summary>Without uv (plain pip)</summary>

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      # Windows
# .venv/bin/pip install -r requirements.txt        # Linux/macOS
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed
.venv\Scripts\python manage.py runserver 0.0.0.0:8888
```
</details>

## Using the app

| Where | What |
| ----- | ---- |
| **Today** | Auto-created daily note for quick capture |
| **All Documents** | Documents and folders |
| **Practice** | Spaced-repetition review queue (space to reveal, 1–4 to rate) |
| **Cards** | Every flashcard and its schedule |
| **Search** | Live search across titles and note text |
| **Tutorials** | In-app help articles (seeded) |
| **Blog** | Study-technique articles; staff users author posts via `/admin/` |

### Editor cheatsheet

- `Enter` new bullet · `Tab` / `Shift+Tab` indent/outdent · `↑`/`↓` move · `Backspace` on empty bullet deletes
- `Front :: Back` → flashcard · `A ;; B` → bidirectional pair · `{{hidden}}` → cloze card
- `[[Document]]` → reference (auto-creates the document) · `#tag` → clickable tag
- `**bold**`, `*italic*`, `` `code` ``

## Trial & subscriptions

Every new account starts a **30-day free trial** (no card required). When the trial ends,
the account is redirected to `/subscribe/` — all data is kept, and access resumes the
moment the subscription is activated. Until online checkout is integrated, activate
subscribers in the Django admin (Profiles → select → "Mark selected profiles as
subscribed"). Staff accounts are never gated. Trial state shows in the sidebar
(days-left chip) and on the Settings page.

## Push notifications (phones & desktops)

Built-in Web Push (VAPID) — works on desktop Chrome/Edge/Firefox, Android, and iOS
(16.4+, after the user adds the app to their home screen; the site ships a PWA manifest
and service worker for exactly that).

- Users enable notifications per device on **Settings → Push notifications**, and can
  send themselves a test notification.
- The **daily study reminder** ("You have N cards ready for review") is sent by:
  ```bash
  uv run manage.py send_due_reminders
  ```
  Schedule it once or twice daily via cron / Windows Task Scheduler. Only users who
  enabled the reminder toggle and registered a device are notified.
- VAPID keys are auto-generated on first use into `vapid_private_key.pem` (gitignored) —
  keep it with your backups, since subscriptions are bound to it. Set
  `EZMEMORY_VAPID_CLAIM` (default `mailto:admin@ezmemory.cloud`).
- Web Push requires HTTPS in production (localhost works for development). Devices are
  capped at 10 per account; dead subscriptions are pruned automatically.

## Security & abuse protection (operator notes)

**Password storage.** Passwords are hashed with **Argon2id** (OWASP's recommended
algorithm) via `argon2-cffi`; PBKDF2 and friends remain as verify-only fallbacks, and any
pre-Argon2 hash is transparently upgraded on the user's next successful login. Django's
password validators (length, common-password, similarity, numeric-only) are enforced at
signup. Passwords are never logged or stored in plaintext anywhere.

**Storage abuse.** The service is text-only by design — there are no file-upload
endpoints, no `MEDIA_ROOT`, no form accepts a file, and `FILE_UPLOAD_HANDLERS` is empty,
so PDFs, images, and video are rejected at the framework level. On top of that:

- Request bodies are capped at 256 KB (`DATA_UPLOAD_MAX_MEMORY_SIZE`).
- Per-account quotas (all tunable in `ezmemory/settings.py`): 10,000 bullets,
  1,000 documents, 100 folders, 2,000 characters per bullet, 200 per title.
  Worst case is roughly ~20–40 MB of text per account.
- Review history is pruned to the 10 most recent reviews per card.
- Signups are throttled to 5 accounts per source IP per hour.

Quota violations surface to users as inline error messages, not silent failures.

**Data safety.** `db.sqlite3` is live user data — treat it that way:

- `uv run manage.py backupdb` snapshots it to `backups/db-<timestamp>.sqlite3`
  (keeps the newest 30; schedule it daily alongside `send_due_reminders`).
- `manage.py flush` is guarded: it refuses to run unless `EZMEMORY_ALLOW_FLUSH=1`
  is set, so the database can't be wiped by a reflexive command.
- Set `EZMEMORY_DB_PATH` to point the app (and any test scripts) at a throwaway
  copy of the database instead of the real one.

**Deployment (ezmemory.cloud).** Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`,
`DJANGO_ALLOWED_HOSTS=ezmemory.cloud`, and (if needed)
`DJANGO_CSRF_TRUSTED_ORIGINS=https://ezmemory.cloud` in the environment. Run behind a
reverse proxy with TLS (required for Web Push); add proxy-level rate limiting for
defense in depth. All data lives in `db.sqlite3`, plus `vapid_private_key.pem` — back
both up.
