"""Render a node's raw text to display HTML: escapes input, then applies
[[references]], #tags, **bold**, *italic*, `code`, and flashcard-separator styling."""

import re

from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

REF_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
TAG_RE = re.compile(r"(?<![\w#])#([\w-]+)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
CODE_RE = re.compile(r"`([^`]+)`")


def _apply_inline(text):
    text = CODE_RE.sub(r"<code>\1</code>", text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)

    def ref(match):
        title = match.group(1)
        url = reverse("document_open") + "?title=" + escape(title)
        return f'<a class="ref" href="{url}">{title}</a>'

    text = REF_RE.sub(ref, text)

    def tag(match):
        name = match.group(1)
        url = reverse("tag_detail", args=[name])
        return f'<a class="tag" href="{url}">#{name}</a>'

    text = TAG_RE.sub(tag, text)
    return text


def render_node_text(raw):
    """Full display rendering for an outline bullet, including card separators."""
    text = escape(raw)

    if "{{" in text:
        text = re.sub(r"\{\{(.+?)\}\}", r'<span class="cloze">\1</span>', text)
    for sep, css in (("::", "sep-fwd"), (";;", "sep-bi")):
        if sep in text:
            front, back = text.split(sep, 1)
            arrow = "⇄" if sep == ";;" else "→"
            text = f'{front}<span class="card-sep {css}" title="flashcard">{arrow}</span>{back}'
            break

    return mark_safe(_apply_inline(text))


def render_card_text(raw):
    """Rendering for a card face (no card-separator handling)."""
    return mark_safe(_apply_inline(escape(raw)))
