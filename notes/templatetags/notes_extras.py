import markdown as md
from django import template
from django.utils.safestring import mark_safe

from notes.render import render_card_text, render_node_text

register = template.Library()


@register.filter
def node_html(text):
    return render_node_text(text)


@register.filter
def card_html(text):
    return render_card_text(text)


@register.filter
def markdown(text):
    return mark_safe(md.markdown(text, extensions=["fenced_code", "tables"]))
