"""Seed the database with the default user, a welcome document, tutorials, and blog posts.

Idempotent: safe to run more than once.
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from content.models import BlogPost, TutorialArticle, TutorialCollection
from flashcards.sync import sync_node_cards
from notes.models import Document, Folder, Node

DEFAULT_USERNAME = "sethcstenzel"
DEFAULT_PASSWORD = "41Dropsatatime!"


class Command(BaseCommand):
    help = "Seed the default user, welcome notes, tutorials, and blog posts."

    def handle(self, *args, **options):
        user = self.seed_user()
        self.seed_notes(user)
        self.seed_tutorials()
        self.seed_blog(user)
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def seed_user(self):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=DEFAULT_USERNAME,
            defaults={"is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            self.stdout.write(f"Created user {DEFAULT_USERNAME}")
        else:
            self.stdout.write(f"User {DEFAULT_USERNAME} already exists")
        return user

    def seed_notes(self, user):
        if Document.objects.filter(user=user, title="Welcome to ezmemory").exists():
            return
        folder, _ = Folder.objects.get_or_create(user=user, name="Getting Started")
        doc = Document.objects.create(user=user, folder=folder, title="Welcome to ezmemory")

        def add(parent, position, text):
            node = Node.objects.create(document=doc, parent=parent, position=position, text=text)
            sync_node_cards(node)
            return node

        intro = add(None, 0, "**Welcome!** This is your knowledge base. Every line is a bullet — click any line to edit it.")
        add(intro, 0, "Press *Enter* for a new bullet, *Tab* to indent, *Shift+Tab* to outdent.")
        add(intro, 1, "Use `[[Study Plan]]` style references to link documents — try clicking one after editing.")
        add(intro, 2, "Add #tags anywhere, like this: #tips")

        cards = add(None, 1, "**Flashcards** live inside your notes:")
        add(cards, 0, "What is spaced repetition? :: Reviewing material at increasing intervals, right before you would forget it.")
        add(cards, 1, "Capital of France ;; Paris")
        add(cards, 2, "The powerhouse of the cell is the {{mitochondria}}.")
        add(cards, 3, "Head to **Practice** in the sidebar to review these. #tips")

        daily = add(None, 2, "**Daily notes**: click *Today* in the sidebar for a fresh page every day.")
        add(daily, 0, "Great for meeting notes, journaling, and quick capture — reorganize later.")

        self.stdout.write("Created welcome document")

    def seed_tutorials(self):
        if TutorialCollection.objects.exists():
            return

        data = [
            {
                "title": "Getting Started",
                "emoji": "🚀",
                "description": "New here? Start with these — you'll be productive in five minutes.",
                "articles": [
                    (
                        "ezmemory in 5 Minutes",
                        "The three ideas the whole app is built on.",
                        """
ezmemory is built around three things: **notes**, **flashcards**, and **spaced-repetition practice**.

## 1. Take notes as an outline

Every document is an outline. Each line is a bullet:

- Press **Enter** to create a new bullet.
- Press **Tab** to indent it under the bullet above; **Shift+Tab** to outdent.
- Click any bullet to edit it. Changes save automatically.

Use the **Today** page (sidebar) for quick capture — a fresh daily note is created for each calendar day.

## 2. Turn notes into flashcards

While writing a note, add `::` to make it a flashcard:

```
What is a covalent bond? :: A bond where a pair of electrons is shared.
```

Whatever comes before the `::` is the front of the card, whatever comes after is the back.

## 3. Practice with spaced repetition

Open **Practice** in the sidebar. You'll see the front of a card — think of the answer, reveal it, then rate how well you remembered. The scheduler decides when you'll see the card again, resurfacing it just before you'd forget.

That's it. Everything else in ezmemory builds on these three ideas.
""",
                    ),
                    (
                        "The Editor in 5 Minutes",
                        "Keyboard shortcuts and inline formatting.",
                        """
## Keys

| Key | Action |
| --- | ------ |
| Enter | New bullet |
| Tab / Shift+Tab | Indent / outdent |
| ↑ / ↓ | Move between bullets |
| Backspace (on an empty bullet) | Delete the bullet |

Bullets with children show a ▾ arrow — click it to collapse or expand the subtree.

## Inline formatting

- `**bold**` → **bold**
- `*italic*` → *italic*
- `` `code` `` → `code`

## Links and tags

- `[[Document Title]]` creates a reference to another document. If it doesn't exist yet, opening the reference creates it.
- `#tag` adds a tag. Click a tag to see everything that uses it.

Documents you reference show a **Linked from** section at the bottom, so knowledge connects in both directions.
""",
                    ),
                ],
            },
            {
                "title": "Flashcards & Practice",
                "emoji": "🧠",
                "description": "Make cards while you write, then let the scheduler handle when to review.",
                "articles": [
                    (
                        "All the Card Types",
                        "Forward, bidirectional, and cloze cards.",
                        """
All cards are written inline, inside a normal bullet.

## Forward cards

```
Front of the card :: Back of the card
```

You'll be shown the front and asked to recall the back.

## Bidirectional cards

```
hola ;; hello
```

Creates **two** cards — one in each direction. Great for vocabulary.

## Cloze (fill-in-the-blank) cards

Wrap the part to hide in double curly braces:

```
The powerhouse of the cell is the {{mitochondria}}.
```

Each hidden section becomes its own card, shown with a `[...]` blank.

## Editing and deleting cards

Cards stay linked to their source bullet. Edit the bullet and the card updates; remove the syntax and the card is deleted. See every card and its schedule under **Cards** in the sidebar.
""",
                    ),
                    (
                        "How the Practice Queue Works",
                        "What the Again / Hard / Good / Easy buttons actually do.",
                        """
Open **Practice** to review whatever is due. For each card:

1. Read the front and try to recall the answer.
2. Press **Show Answer** (or the space bar).
3. Rate yourself: **Again**, **Hard**, **Good**, or **Easy** (keys 1–4).

## What the ratings do

The scheduler uses an SM-2 style algorithm. Every card has an *interval* (how long until you see it again) and an *ease* (how fast that interval grows).

- **Again** — you forgot. The card resets and comes back in about 10 minutes, within the same session.
- **Hard** — the interval grows slowly and the ease drops a little.
- **Good** — the normal path: 1 day, then 6 days, then multiplying by the ease each time.
- **Easy** — the interval jumps ahead and the ease increases.

Honest ratings matter more than good ones — the algorithm adapts to *you*.

## Daily stats

The queue header shows how many cards are due, how many of those are brand new, and how many reviews you've completed today.
""",
                    ),
                ],
            },
            {
                "title": "Organizing Your Knowledge",
                "emoji": "🗂️",
                "description": "Documents, folders, daily notes, references, tags, and search.",
                "articles": [
                    (
                        "Documents, Folders & Daily Notes",
                        "Where notes live and how to keep them tidy.",
                        """
## Documents

Create a document with the **+** button in the sidebar. Click a document's title to rename it, and use the **⋯** menu to move it into a folder or delete it.

## Folders

Folders group documents in the sidebar. Deleting a folder keeps its documents — they just move out of the folder.

## Daily notes

**Today** (sidebar) opens a note named for the current date, created on first visit. Use it as an inbox: capture quickly during the day, then move ideas into real documents with `[[references]]` when you have time. Recent daily notes are listed at the bottom of each daily page.
""",
                    ),
                    (
                        "References, Tags & Search",
                        "Connect ideas and find them again.",
                        """
## References

Type `[[Some Document]]` in any bullet to link to that document. Clicking the link opens it — and creates it first if it doesn't exist, which makes references a fast way to grow your knowledge base. Each document lists the documents that link **to** it under *Linked from*.

## Tags

Add `#exam` or `#idea` anywhere in a bullet. Clicking a tag shows every bullet that uses it, across all your documents.

## Search

**Search** (sidebar) matches document titles and note text as you type. Use it as your main way to move around once your knowledge base grows past a handful of documents.
""",
                    ),
                ],
            },
        ]

        for c_order, c in enumerate(data):
            collection = TutorialCollection.objects.create(
                title=c["title"],
                slug=c["title"].lower().replace(" ", "-").replace("&", "and"),
                description=c["description"],
                emoji=c["emoji"],
                order=c_order,
            )
            for a_order, (title, description, body) in enumerate(c["articles"]):
                TutorialArticle.objects.create(
                    collection=collection,
                    title=title,
                    slug=title.lower().replace(" ", "-").replace("?", "").replace(",", "").replace("&", "and"),
                    description=description,
                    body=body.strip(),
                    order=a_order,
                )
        self.stdout.write("Created tutorial collections")

    def seed_blog(self, user):
        if BlogPost.objects.exists():
            return

        posts = [
            {
                "title": "Notes vs. Flashcards: Why You Need Both",
                "emoji": "⚖️",
                "featured": True,
                "published_at": datetime.date(2026, 7, 9),
                "description": "Notes help you understand; flashcards help you remember. The magic is in connecting the two so neither goes stale.",
                "body": """
Most study tools force a choice: a notes app that's great for capturing lectures but terrible for retention, or a flashcard app that drills you on facts with no surrounding context.

## Notes build understanding

Writing an outline forces you to structure material — what's the main idea, what supports it, what's an aside. That act of organizing is where comprehension happens.

## Flashcards build retention

Understanding decays. Without reinforcement, most of what you learn this week is gone in a month. Flashcards with spaced repetition are the most evidence-backed fix we have.

## The problem with separating them

When your cards live in a different app from your notes, two bad things happen:

1. **Cards lose context.** A card you wrote in October is a mystery in December because the surrounding explanation lives somewhere else.
2. **You stop making cards.** Copying material between apps is friction, and friction wins.

## Write cards where you take notes

In ezmemory, a flashcard is just a bullet in your notes with `::` in it. The card keeps its context forever — during practice, one click takes you back to the exact spot in the document where you wrote it. And because making a card costs three keystrokes, you actually make them.
""",
            },
            {
                "title": "What Is Spaced Repetition, and Why Does It Work?",
                "emoji": "📈",
                "featured": False,
                "published_at": datetime.date(2026, 6, 24),
                "description": "A short tour of the forgetting curve, and how reviewing at the right moment turns short-term cramming into long-term memory.",
                "body": """
In the 1880s, Hermann Ebbinghaus measured how quickly he forgot lists of nonsense syllables. The result — the *forgetting curve* — shows memory decaying rapidly at first, then more slowly.

## The key insight

Every time you successfully recall something *just before you would have forgotten it*, the memory gets more durable and the next review can wait longer. Review after 1 day, then 6, then two weeks, then a couple of months — five minutes of well-timed reviews beats hours of re-reading.

## Why cramming fails

Cramming works for tomorrow's exam because everything is still on the steep part of the curve. But without follow-up reviews the curve does its thing, and three weeks later the all-nighter has evaporated.

## What the ratings are for

When you rate a card **Again / Hard / Good / Easy**, you're feeding the scheduler information about *your* forgetting curve for *that* card. Easy material gets out of your way; hard material shows up more often. That per-card adaptation is what makes the technique efficient rather than just repetitive.

## Getting started

Don't build a thousand cards on day one. Write cards for things you actually need to remember, practice daily (it's usually minutes, not hours), and rate honestly.
""",
            },
            {
                "title": "How to Create Effective Flashcards",
                "emoji": "✍️",
                "featured": False,
                "published_at": datetime.date(2026, 6, 2),
                "description": "The five rules that separate cards you'll still be answering correctly next year from cards you'll dread.",
                "body": """
Spaced repetition only works as well as the cards you feed it. Five rules cover most of what matters.

## 1. One fact per card

If the answer has four parts, you'll fail the card whenever you remember three. Split it: four small cards are faster to review and give the scheduler better signal.

## 2. Make it a question you can fail

"Photosynthesis — important!" is not a card. `What are the inputs of photosynthesis? :: Light, water, and CO2` is.

## 3. Prefer cloze deletion for facts in context

Wrap the key term instead of inventing an artificial question:

```
The Treaty of Westphalia was signed in {{1648}}.
```

## 4. Use both directions for vocabulary

`palabra ;; word` quizzes you both ways — recognition and production are different skills.

## 5. Keep cards connected to their source

Review works best when a confusing card is one click away from the note that explains it. That's why ezmemory cards live inside your notes rather than in a separate deck.
""",
            },
            {
                "title": "The Daily Note: A Simple Habit for Messy Thinkers",
                "emoji": "📅",
                "featured": False,
                "published_at": datetime.date(2026, 5, 12),
                "description": "You don't need a perfect filing system on day one. Capture everything in today's note and let structure emerge.",
                "body": """
The biggest reason note systems die is that filing feels like work. Where does this idea go? What should the document be called? Skip the decision entirely: put it in today's note.

## The habit

Open **Today**, write the thing down, move on. Meeting notes, half-formed ideas, a quote, a task — everything lands in the same place, timestamped by the page itself.

## Structure comes later

Once a week, skim your recent daily notes. Anything worth keeping gets a `[[reference]]` to a real document — and if that document doesn't exist yet, clicking the reference creates it. The good ideas graduate; the rest stays behind as a searchable journal.

## Why this works

You never lose a thought to "I'll file it later," and you never build elaborate empty folder structures for notes that don't exist yet. The structure you end up with reflects what you actually think about — because it grew out of what you actually wrote down.
""",
            },
        ]

        for p in posts:
            BlogPost.objects.create(
                author=user,
                title=p["title"],
                slug=p["title"].lower().replace(" ", "-").replace(",", "").replace(":", "").replace("?", "").replace(".", ""),
                description=p["description"],
                body=p["body"].strip(),
                emoji=p["emoji"],
                featured=p["featured"],
                published_at=p["published_at"],
            )
        self.stdout.write("Created blog posts")
