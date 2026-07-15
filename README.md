# ezmemory 🧠

A note-taking and spaced-repetition study service. Subscribers take outline-style notes,
turn any bullet into a flashcard with inline syntax, and practice with a
spaced-repetition queue.

Built with **Django** (backend), **htmx** + **Alpine.js** (frontend, vendored locally —
no CDN dependencies), and SQLite for storage.

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

**Deployment.** Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, and `DJANGO_ALLOWED_HOSTS`
(comma-separated) in the environment for production. Run behind a reverse proxy with
TLS; add proxy-level rate limiting for defense in depth. All data lives in `db.sqlite3` —
back that file up.
