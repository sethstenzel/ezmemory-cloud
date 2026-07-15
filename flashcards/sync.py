"""Parse flashcard syntax out of node text and keep Card rows in sync.

Supported syntax inside a bullet:
    Front :: Back              -> one forward card
    Front ;; Back              -> forward + reverse cards
    Text with {{hidden}} bits  -> one cloze card per {{...}} occurrence
"""

import re

from .models import Card

CLOZE_RE = re.compile(r"\{\{(.+?)\}\}")


def parse_cards(text):
    """Return a list of (kind, cloze_index, front, back) tuples for a bullet's text."""
    text = text.strip()
    if not text:
        return []

    clozes = CLOZE_RE.findall(text)
    if clozes:
        cards = []
        for i in range(len(clozes)):
            occurrence = [0]

            def repl(match, target=i, occurrence=occurrence):
                idx = occurrence[0]
                occurrence[0] += 1
                return "[...]" if idx == target else match.group(1)

            front = CLOZE_RE.sub(repl, text)
            back = CLOZE_RE.sub(lambda m: m.group(1), text)
            cards.append((Card.Kind.CLOZE, i, front, back))
        return cards

    if ";;" in text:
        front, back = (part.strip() for part in text.split(";;", 1))
        if front and back:
            return [
                (Card.Kind.FORWARD, 0, front, back),
                (Card.Kind.REVERSE, 0, back, front),
            ]
        return []

    if "::" in text:
        front, back = (part.strip() for part in text.split("::", 1))
        if front and back:
            return [(Card.Kind.FORWARD, 0, front, back)]
        return []

    return []


def sync_node_cards(node):
    """Upsert cards for a node, preserving scheduling state of existing cards."""
    parsed = parse_cards(node.text)
    existing = {(c.kind, c.cloze_index): c for c in node.cards.all()}
    keep = set()

    for kind, cloze_index, front, back in parsed:
        keep.add((kind, cloze_index))
        card = existing.get((kind, cloze_index))
        if card:
            if card.front != front or card.back != back:
                card.front = front
                card.back = back
                card.save(update_fields=["front", "back", "updated_at"])
        else:
            Card.objects.create(
                user=node.document.user,
                node=node,
                kind=kind,
                cloze_index=cloze_index,
                front=front,
                back=back,
            )

    for key, card in existing.items():
        if key not in keep:
            card.delete()
