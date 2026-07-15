# ezmemory — Feature Requirements

A subscription note-taking and spaced-repetition study service. All features run on a
single server against a SQLite database — no external services, no AI.

## 1. Accounts & Authentication
- [x] Create new user accounts (username + password sign-up)
- [x] Sign in / sign out; landing page doubles as the product pitch
- [x] Passwords hashed with Argon2id; Django password validators enforced at signup
- [x] All personal content (notes, flashcards, review history) is scoped per user
- [x] Seeded default admin account
- [x] Signup throttling per source IP

## 2. Note Editor (Outliner)
- [x] Hierarchical, outline-based editor: every line is a bullet ("node")
- [x] `Enter` creates a new sibling bullet; `Tab` indents; `Shift+Tab` outdents
- [x] Nodes can be nested to arbitrary depth; children can be collapsed/expanded
- [x] Edits save automatically to the server
- [x] Delete a bullet (with its children) via `Backspace` on an empty bullet or the node menu
- [x] Inline references to other documents with `[[Document Title]]` syntax, rendered as links
- [x] Inline `#tags` for lightweight labeling, rendered as clickable chips
- [x] Basic inline formatting: `**bold**`, `*italic*`, `` `code` ``

## 3. Documents, Folders & Daily Notes
- [x] Create, rename, and delete documents
- [x] Organize documents into folders (sidebar tree)
- [x] Daily Documents: an auto-created note per calendar day for quick capture
- [x] Sidebar navigation: pinned sections for Daily Notes, All Documents, Flashcards, Search

## 4. Flashcards (created inside your notes)
- [x] Turn any bullet into a flashcard with inline syntax:
  - `Front :: Back` — forward card (question → answer)
  - `Front ;; Back` — bidirectional card (practiced both directions)
  - `Text with {{hidden}} parts` — cloze / fill-in-the-blank card
- [x] Cards stay linked to their source bullet; editing the note updates the card
- [x] Cards list view showing every card, its type, and its scheduling state

## 5. Spaced Repetition & Practice Queue
- [x] Practice queue that surfaces cards when they are due (SM-2 style scheduling algorithm)
- [x] Review flow: show front → reveal answer → rate recall (Again / Hard / Good / Easy)
- [x] Rating adjusts each card's ease and interval; failed cards repeat in the same session
- [x] Daily study stats: due count, new count, reviews completed today
- [x] Review history log per card

## 6. Search & Navigation
- [x] Instant full-text search across document titles and note content (live results as you type)
- [x] Tag pages: click a `#tag` to see every node using it
- [x] Quick document switching from the sidebar

## 7. Knowledge Organization
- [x] References between documents build a simple linked knowledge base
- [x] Backlinks: a document shows which other documents reference it

## 8. Tutorials (in-app help center)
- [x] Built-in Tutorials section organized as collections of articles
      (e.g. "Getting Started", "Flashcards & Practice", "Organizing Your Knowledge")
- [x] Each collection lists its articles with descriptions; articles are ordered, readable pages
- [x] Seeded with articles that teach the app itself (editor keys, card syntax, the queue)

## 9. Blog
- [x] Blog index with one featured post at the top, then a card grid of latest posts
- [x] Each post card shows image/placeholder, title, short description, publish date,
      and estimated reading time
- [x] Posts ordered newest first; full post pages rendered from Markdown-style text
- [x] Staff users can author posts via the Django admin

## 10. Cost & Abuse Controls
The service is text-only by design so that no subscriber can run up storage costs:

- [x] No file uploads of any kind — no PDFs, images, audio, or video; no upload
      endpoints or media storage exist, and Django's upload handlers are disabled
- [x] Request bodies capped at 256 KB
- [x] Per-account quotas: bullets, documents, folders, bullet length, title length
- [x] Review history pruned per card
- [x] Signup rate-limited per IP

## Explicitly Out of Scope
Removed because they depend on AI services, third-party infrastructure, special
hardware, or would expose the service to unbounded storage costs:

- AI tutor chat, AI-generated flashcards/quizzes/summaries/explanations
- Lecture recording and transcription
- PDF / slide upload and annotation, web clipper
- Handwritten notes / stylus input, image occlusion cards
- Any user file storage (images, audio, video, attachments)
- Native mobile & desktop apps, offline mode
- Real-time multi-user collaboration and public document publishing
- Plugin/extension marketplace
