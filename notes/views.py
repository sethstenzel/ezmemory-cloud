from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from flashcards.sync import sync_node_cards

from . import limits
from .models import Document, Folder, Node


def quota_denied(message):
    """Plain-text 400 for htmx endpoints; the frontend shows it as a toast."""
    return HttpResponse(message, status=400, content_type="text/plain")


# ---------------------------------------------------------------- helpers

def build_tree(document):
    """Return the outline as a nested list of {node, children} dicts."""
    nodes = list(document.nodes.all())
    by_parent = {}
    for node in nodes:
        by_parent.setdefault(node.parent_id, []).append(node)

    def build(parent_id):
        return [
            {"node": n, "children": build(n.id), "has_children": bool(by_parent.get(n.id))}
            for n in sorted(by_parent.get(parent_id, []), key=lambda n: (n.position, n.id))
        ]

    return build(None)


def visible_order(tree):
    """Flatten the tree into the order nodes appear on screen (skipping collapsed subtrees)."""
    flat = []
    for item in tree:
        flat.append(item["node"])
        if not item["node"].collapsed:
            flat.extend(visible_order(item["children"]))
    return flat


def resequence(document, parent):
    siblings = Node.objects.filter(document=document, parent=parent).order_by("position", "id")
    for i, sib in enumerate(siblings):
        if sib.position != i:
            Node.objects.filter(pk=sib.pk).update(position=i)


def outline_response(request, document, focus_id=None):
    tree = build_tree(document)
    return render(request, "notes/_outline.html", {"document": document, "tree": tree, "focus_id": focus_id})


def get_node(request, pk):
    return get_object_or_404(Node, pk=pk, document__user=request.user)


def save_text(node, request):
    text = request.POST.get("text")
    if text is not None:
        text = limits.clamp_node_text(text)
    if text is not None and text != node.text:
        node.text = text
        node.save(update_fields=["text", "updated_at"])
        sync_node_cards(node)
        node.document.save(update_fields=["updated_at"])


def sidebar_context(request):
    folders = Folder.objects.filter(user=request.user).prefetch_related("documents")
    loose_docs = Document.objects.filter(user=request.user, folder=None, is_daily=False)
    return {
        "sidebar_folders": folders,  # flat, for selects and the documents page
        "sidebar_folder_tree": [f for f in folders if f.parent_id is None],
        "sidebar_documents": loose_docs,
    }


# ---------------------------------------------------------------- pages

@login_required
def home(request):
    return redirect("daily_today")


@login_required
def daily_today(request):
    today = timezone.localdate()
    title = today.strftime("%B %d, %Y").replace(" 0", " ")
    if (
        not Document.objects.filter(user=request.user, is_daily=True, daily_date=today).exists()
        and limits.document_quota_left(request.user) <= 0
    ):
        messages.error(request, limits.DOCUMENT_QUOTA_MESSAGE)
        return redirect("document_list")
    doc, created = Document.objects.get_or_create(
        user=request.user,
        is_daily=True,
        daily_date=today,
        defaults={"title": title},
    )
    if created:
        Node.objects.create(document=doc, text="")
    return redirect("document_detail", pk=doc.pk)


@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    if not document.nodes.exists():
        Node.objects.create(document=document, text="")
    tree = build_tree(document)

    # Backlinks: other documents whose nodes reference this one with [[Title]]
    ref = f"[[{document.title}]]"
    backlinks = (
        Document.objects.filter(user=request.user, nodes__text__contains=ref)
        .exclude(pk=document.pk)
        .distinct()
    )

    dailies = Document.objects.filter(user=request.user, is_daily=True).order_by("-daily_date")[:10]
    context = {
        "document": document,
        "tree": tree,
        "focus_id": None,
        "backlinks": backlinks,
        "recent_dailies": dailies,
        **sidebar_context(request),
    }
    return render(request, "notes/document.html", context)


@login_required
def document_list(request):
    documents = Document.objects.filter(user=request.user, is_daily=False)
    dailies = Document.objects.filter(user=request.user, is_daily=True).order_by("-daily_date")
    return render(
        request,
        "notes/documents.html",
        {"documents": documents, "dailies": dailies, **sidebar_context(request)},
    )


@login_required
def document_open(request):
    """Resolve a [[reference]] by title: open the document, creating it if needed."""
    title = limits.clamp_title(request.GET.get("title", "").strip())
    if not title:
        return redirect("home")
    doc = Document.objects.filter(user=request.user, title__iexact=title).first()
    if doc is None:
        if limits.document_quota_left(request.user) <= 0:
            messages.error(request, limits.DOCUMENT_QUOTA_MESSAGE)
            return redirect("document_list")
        doc = Document.objects.create(user=request.user, title=title)
        Node.objects.create(document=doc, text="")
    return redirect("document_detail", pk=doc.pk)


@login_required
@require_POST
def document_create(request):
    if limits.document_quota_left(request.user) <= 0:
        messages.error(request, limits.DOCUMENT_QUOTA_MESSAGE)
        return redirect("document_list")
    title = limits.clamp_title(request.POST.get("title", "").strip()) or "Untitled"
    folder_id = request.POST.get("folder") or None
    folder = None
    if folder_id:
        folder = get_object_or_404(Folder, pk=folder_id, user=request.user)
    doc = Document.objects.create(user=request.user, title=title, folder=folder)
    Node.objects.create(document=doc, text="")
    return redirect("document_detail", pk=doc.pk)


@login_required
@require_POST
def document_rename(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    title = limits.clamp_title(request.POST.get("title", "").strip())
    if title:
        document.title = title
        document.save(update_fields=["title", "updated_at"])
    return redirect("document_detail", pk=document.pk)


@login_required
@require_POST
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    document.delete()
    return redirect("document_list")


@login_required
@require_POST
def document_move(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    folder_id = request.POST.get("folder") or None
    document.folder = get_object_or_404(Folder, pk=folder_id, user=request.user) if folder_id else None
    document.save(update_fields=["folder", "updated_at"])
    return redirect("document_detail", pk=document.pk)


@login_required
@require_POST
def folder_create(request):
    name = limits.clamp_title(request.POST.get("name", "").strip())
    if name:
        if limits.folder_quota_left(request.user) <= 0:
            messages.error(request, limits.FOLDER_QUOTA_MESSAGE)
        else:
            parent_id = request.POST.get("parent") or None
            parent = None
            if parent_id:
                parent = get_object_or_404(Folder, pk=parent_id, user=request.user)
            Folder.objects.get_or_create(user=request.user, name=name, defaults={"parent": parent})
    return redirect(request.POST.get("next") or "document_list")


@login_required
@require_POST
def folder_move(request, pk):
    folder = get_object_or_404(Folder, pk=pk, user=request.user)
    parent_id = request.POST.get("parent") or None
    if parent_id:
        parent = get_object_or_404(Folder, pk=parent_id, user=request.user)
        if parent.pk == folder.pk or any(a.pk == folder.pk for a in parent.ancestors()):
            return quota_denied("A topic can't be moved into itself or one of its subtopics.")
        if sum(1 for _ in parent.ancestors()) >= 9:
            return quota_denied("Topics can't be nested this deep.")
        folder.parent = parent
    else:
        folder.parent = None
    folder.save(update_fields=["parent"])
    return redirect(request.POST.get("next") or "document_list")


@login_required
@require_POST
def folder_delete(request, pk):
    folder = get_object_or_404(Folder, pk=pk, user=request.user)
    # Contents survive: documents and subfolders move up to the deleted folder's level.
    folder.documents.update(folder=folder.parent)
    folder.subfolders.update(parent=folder.parent)
    folder.delete()
    next_url = request.POST.get("next", "")
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("document_list")


# ---------------------------------------------------------------- node ops (htmx)

@login_required
@require_POST
def node_save(request, pk):
    node = get_node(request, pk)
    save_text(node, request)
    return render(request, "notes/_node_display.html", {"node": node})


@login_required
@require_POST
def node_create(request, pk):
    node = get_node(request, pk)
    save_text(node, request)
    if limits.node_quota_left(request.user) <= 0:
        return quota_denied(limits.NODE_QUOTA_MESSAGE)

    has_children = node.children.exists()
    if has_children and not node.collapsed:
        # Insert as first child, matching outliner convention
        Node.objects.filter(document=node.document, parent=node).update(position=models.F("position") + 1)
        new = Node.objects.create(document=node.document, parent=node, position=0, text="")
    else:
        Node.objects.filter(
            document=node.document, parent=node.parent, position__gt=node.position
        ).update(position=models.F("position") + 1)
        new = Node.objects.create(
            document=node.document, parent=node.parent, position=node.position + 1, text=""
        )
    return outline_response(request, node.document, focus_id=new.id)


@login_required
@require_POST
def node_bulk_create(request, pk):
    """Paste support: add one bullet per non-empty line, after the given node.

    If the current bullet is empty, the first line fills it instead.
    """
    node = get_node(request, pk)
    save_text(node, request)
    node.refresh_from_db()

    lines = [
        limits.clamp_node_text(line.strip())
        for line in request.POST.get("lines", "").splitlines()
        if line.strip()
    ]
    if not lines:
        return outline_response(request, node.document, focus_id=node.id)

    fill_current = not node.text.strip()
    new_count = len(lines) - (1 if fill_current else 0)
    if new_count > limits.node_quota_left(request.user):
        return quota_denied(limits.NODE_QUOTA_MESSAGE)

    if fill_current:
        node.text = lines.pop(0)
        node.save(update_fields=["text", "updated_at"])
        sync_node_cards(node)

    Node.objects.filter(
        document=node.document, parent=node.parent, position__gt=node.position
    ).update(position=models.F("position") + len(lines))
    focus = node
    for offset, line in enumerate(lines, start=1):
        focus = Node.objects.create(
            document=node.document, parent=node.parent, position=node.position + offset, text=line
        )
        sync_node_cards(focus)
    node.document.save(update_fields=["updated_at"])
    return outline_response(request, node.document, focus_id=focus.id)


@login_required
@require_POST
def node_indent(request, pk):
    node = get_node(request, pk)
    save_text(node, request)
    prev = node.previous_sibling()
    if prev is None:
        return outline_response(request, node.document, focus_id=node.id)
    old_parent = node.parent
    node.parent = prev
    node.position = prev.children.count()
    node.save(update_fields=["parent", "position", "updated_at"])
    if prev.collapsed:
        prev.collapsed = False
        prev.save(update_fields=["collapsed"])
    resequence(node.document, old_parent)
    return outline_response(request, node.document, focus_id=node.id)


@login_required
@require_POST
def node_outdent(request, pk):
    node = get_node(request, pk)
    save_text(node, request)
    parent = node.parent
    if parent is None:
        return outline_response(request, node.document, focus_id=node.id)
    Node.objects.filter(
        document=node.document, parent=parent.parent, position__gt=parent.position
    ).update(position=models.F("position") + 1)
    node.parent = parent.parent
    node.position = parent.position + 1
    node.save(update_fields=["parent", "position", "updated_at"])
    resequence(node.document, parent)
    return outline_response(request, node.document, focus_id=node.id)


@login_required
@require_POST
def node_delete(request, pk):
    node = get_node(request, pk)
    document = node.document
    tree = build_tree(document)
    order = visible_order(tree)
    ids = [n.id for n in order]
    focus_id = None
    if node.id in ids:
        idx = ids.index(node.id)
        if idx > 0:
            focus_id = ids[idx - 1]
        elif len(ids) > 1:
            # Focus the next node that isn't inside the deleted subtree
            descendants = {node.id}
            changed = True
            while changed:
                changed = False
                for n in order:
                    if n.parent_id in descendants and n.id not in descendants:
                        descendants.add(n.id)
                        changed = True
            for n in order[idx + 1:]:
                if n.id not in descendants:
                    focus_id = n.id
                    break
    parent = node.parent
    node.delete()
    resequence(document, parent)
    if not document.nodes.exists():
        new = Node.objects.create(document=document, text="")
        focus_id = new.id
    return outline_response(request, document, focus_id=focus_id)


@login_required
@require_POST
def node_toggle(request, pk):
    node = get_node(request, pk)
    node.collapsed = not node.collapsed
    node.save(update_fields=["collapsed"])
    return outline_response(request, node.document)


# ---------------------------------------------------------------- search & tags

@login_required
def search(request):
    return render(request, "notes/search.html", {"query": request.GET.get("q", ""), **sidebar_context(request)})


@login_required
def search_results(request):
    query = request.GET.get("q", "").strip()[:200]
    documents, nodes = [], []
    if query:
        documents = Document.objects.filter(user=request.user, title__icontains=query)[:20]
        nodes = (
            Node.objects.filter(document__user=request.user, text__icontains=query)
            .select_related("document")[:50]
        )
    return render(
        request, "notes/_search_results.html", {"query": query, "documents": documents, "nodes": nodes}
    )


@login_required
def tag_detail(request, name):
    nodes = (
        Node.objects.filter(document__user=request.user, text__icontains=f"#{name}")
        .select_related("document")
    )
    return render(request, "notes/tag.html", {"tag": name, "nodes": nodes, **sidebar_context(request)})
