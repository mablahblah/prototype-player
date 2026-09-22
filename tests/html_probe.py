"""Reads a page the way a browser or a screen reader would, not as text.

Tests that match raw markup break when markup is rewritten to do the same
thing — a renamed id or class fails them although nothing a person sees has
changed. This builds a small element tree instead, so a test can ask for "the
button whose name is Copy embed code" rather than for a literal string.

Standard library only: html.parser does the parsing.
"""
from html.parser import HTMLParser

# Tags that never have an end tag, so they must not open a nesting level.
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Content inside these is code, not readable text.
OPAQUE = {"script", "style"}


class Element:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children = []
        self.pieces = []

    def text(self):
        """This element's readable text, whitespace collapsed."""
        out = list(self.pieces)
        for child in self.children:
            out.append(child.text())
        return " ".join(" ".join(out).split())

    def find_all(self, tag):
        found = []
        for child in self.children:
            if child.tag == tag:
                found.append(child)
            found.extend(child.find_all(tag))
        return found

    def find(self, tag):
        found = self.find_all(tag)
        return found[0] if found else None

    def accessible_name(self):
        """What a screen reader would announce for this element."""
        for key in ("aria-label", "title", "alt"):
            value = (self.attrs.get(key) or "").strip()
            if value:
                return value
        return self.text()

    def ancestors(self):
        node, out = self.parent, []
        while node is not None:
            out.append(node)
            node = node.parent
        return out

    def __repr__(self):
        return f"<{self.tag} {self.attrs}>"


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, None)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if self.stack[-1].tag in OPAQUE:
            return
        if data.strip():
            self.stack[-1].pieces.append(data)


def parse(html):
    """Return the document root of `html`."""
    builder = _Builder()
    builder.feed(html)
    builder.close()
    return builder.root


def lowest_common_ancestor(a, b):
    """The innermost element containing both, or None."""
    b_line = {id(node) for node in [b] + b.ancestors()}
    for node in [a] + a.ancestors():
        if id(node) in b_line:
            return node
    return None
