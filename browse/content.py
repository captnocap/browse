from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class Link:
    text: str
    href: str


@dataclass
class FormField:
    name: str
    type: str
    value: str = ""
    placeholder: str = ""


@dataclass
class Form:
    action: str
    method: str
    fields: list[FormField] = field(default_factory=list)


@dataclass
class PageContent:
    url: str
    title: str
    text: str
    links: list[Link] = field(default_factory=list)
    forms: list[Form] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    TEXT_LIMIT = 8000  # max characters of page text to send to the model

    def for_llm(self) -> str:
        """Format page content for LLM consumption with untrusted-data boundaries.

        Wraps everything in clear delimiters so the LLM knows this is
        web content — not instructions — and should not be interpreted
        as commands, tool calls, or system prompts.
        """
        domain = urlparse(self.url).netloc or "unknown"
        parts = []
        parts.append(f"===== UNTRUSTED WEB CONTENT [{domain}] =====")
        parts.append(f"URL: {self.url}")
        parts.append(f"Title: {self.title}")
        parts.append("")
        text = self.text
        if len(text) > self.TEXT_LIMIT:
            text = text[:self.TEXT_LIMIT] + f"\n\n[...truncated — {len(self.text)} chars total, showing first {self.TEXT_LIMIT}]"
        parts.append(text)
        if self.links:
            parts.append("")
            parts.append(f"--- Links ({len(self.links)}) ---")
            for link in self.links[:100]:  # cap to prevent flooding
                parts.append(f"  [{link.text}] -> {link.href}")
        if self.forms:
            parts.append("")
            parts.append(f"--- Forms ({len(self.forms)}) ---")
            for form in self.forms:
                parts.append(f"  <form action={form.action} method={form.method}>")
                for f in form.fields:
                    parts.append(f"    {f.type}: name={f.name}")
        parts.append(f"===== END UNTRUSTED WEB CONTENT [{domain}] =====")
        return "\n".join(parts)


# JavaScript executed in the page to extract structured content.
# Filters out hidden/invisible elements to block prompt injection via
# CSS-hidden text (display:none, visibility:hidden, opacity:0, off-screen
# positioning, zero-size elements, font-size:0, text-indent, clip/clip-path,
# same-color-as-background, transform:scale(0), aria-hidden, etc.).
#
# The key insight: we walk the DOM recursively, checking each element's
# computed style. If an element is hidden, we skip its ENTIRE subtree.
# Since we walk parent-first, a hidden ancestor means we never even look
# at its children — no expensive per-node ancestor traversal needed.
EXTRACT_CONTENT_JS = """
return (function() {
    var result = {};
    result.url = window.location.href;
    result.title = document.title || '';

    // ── Visibility check ──────────────────────────────────────────
    // Returns false if the element is hidden by any CSS trick.
    // Called once per element during the tree walk — since we skip
    // hidden subtrees, we only need to check the element itself,
    // not its ancestors (they already passed).
    function isVisible(el) {
        // Body and documentElement are always "visible" structurally
        if (el === document.body || el === document.documentElement) return true;

        // HTML hidden attribute
        if (el.hidden) return false;

        // aria-hidden (semantic hiding, often paired with visual hiding)
        if (el.getAttribute('aria-hidden') === 'true') return false;

        var s = window.getComputedStyle(el);

        // display: none — not rendered at all
        if (s.display === 'none') return false;

        // visibility: hidden/collapse
        if (s.visibility === 'hidden' || s.visibility === 'collapse') return false;

        // opacity: 0 (fully transparent)
        if (parseFloat(s.opacity) === 0) return false;

        // Zero dimensions — element takes no space
        if (el.offsetWidth === 0 && el.offsetHeight === 0) return false;

        // font-size: 0 — text rendered at zero size
        if (parseFloat(s.fontSize) === 0) return false;

        // clip-path: inset(100%) — clipped to nothing
        var cp = s.clipPath || s.webkitClipPath || '';
        if (cp === 'inset(100%)') return false;

        // clip: rect(0,0,0,0) — old-school clip to nothing
        var clip = s.clip;
        if (clip && clip !== 'auto' && /rect\\(\\s*0[^,]*,\\s*0[^,]*,\\s*0[^,]*,\\s*0/.test(clip)) {
            return false;
        }

        // text-indent far off-screen (e.g. -9999px image replacement trick)
        var ti = parseFloat(s.textIndent);
        if (ti < -900 && s.overflow === 'hidden') return false;

        // overflow:hidden with effectively zero size — content clipped away
        if (s.overflow === 'hidden') {
            if (el.offsetWidth < 2 && el.offsetHeight < 2) return false;
            if (parseFloat(s.maxHeight) === 0) return false;
            if (parseFloat(s.maxWidth) === 0) return false;
        }

        // Off-screen positioning (position:absolute/fixed with huge negative coords)
        try {
            var rect = el.getBoundingClientRect();
            if (rect.right < -500 || rect.bottom < -500) return false;
            if (rect.left < -9000 || rect.top < -9000) return false;
        } catch(e) {}

        // transform: scale(0) — collapsed to a point
        var tf = s.transform;
        if (tf && tf !== 'none') {
            // matrix(0, 0, 0, 0, ...) is what scale(0) computes to
            if (/matrix\\(\\s*0\\s*,\\s*0\\s*,\\s*0\\s*,\\s*0/.test(tf)) return false;
        }

        // filter: opacity(0)
        var filter = s.filter || s.webkitFilter || '';
        if (/opacity\\(\\s*0\\s*\\)/.test(filter)) return false;

        // Same foreground color as background (text blends in)
        var fg = s.color;
        var bg = s.backgroundColor;
        if (bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)' && fg === bg) {
            return false;
        }

        return true;
    }

    // ── Visible text extraction ───────────────────────────────────
    // Walk the DOM depth-first. At each element, check visibility.
    // If hidden, skip the entire subtree. Collect text from visible
    // text nodes, inserting newlines at block boundaries.
    var BLOCK = {DIV:1,P:1,H1:1,H2:1,H3:1,H4:1,H5:1,H6:1,LI:1,TR:1,
                 BLOCKQUOTE:1,PRE:1,SECTION:1,ARTICLE:1,HEADER:1,FOOTER:1,
                 NAV:1,MAIN:1,ASIDE:1,DETAILS:1,SUMMARY:1,FIGCAPTION:1,
                 DD:1,DT:1,TABLE:1,UL:1,OL:1,DL:1,FORM:1,FIELDSET:1,HR:1};
    var SKIP = {SCRIPT:1,STYLE:1,NOSCRIPT:1,TEMPLATE:1,SVG:1};

    var parts = [];
    function walkText(node) {
        if (node.nodeType === 3) {
            var t = node.textContent;
            if (t && t.trim()) parts.push(t);
            return;
        }
        if (node.nodeType !== 1) return;
        var tag = node.tagName;
        if (SKIP[tag]) return;
        if (!isVisible(node)) return;

        if (tag === 'BR') { parts.push('\\n'); return; }
        if (BLOCK[tag]) parts.push('\\n');

        for (var i = 0; i < node.childNodes.length; i++) {
            walkText(node.childNodes[i]);
        }
        if (BLOCK[tag]) parts.push('\\n');
    }

    if (document.body) {
        walkText(document.body);
    }
    result.text = parts.join('').replace(/\\n{3,}/g, '\\n\\n').trim();

    // ── Visible links ─────────────────────────────────────────────
    result.links = [];
    var anchors = document.querySelectorAll('a[href]');
    for (var i = 0; i < anchors.length; i++) {
        var a = anchors[i];
        if (!isVisible(a)) continue;
        var text = (a.innerText || '').trim();
        var href = a.href;
        if (href && !href.startsWith('javascript:')) {
            result.links.push({text: text, href: href});
        }
    }

    // ── Visible forms ─────────────────────────────────────────────
    result.forms = [];
    var formEls = document.querySelectorAll('form');
    for (var i = 0; i < formEls.length; i++) {
        var form = formEls[i];
        if (!isVisible(form)) continue;
        var formData = {
            action: form.action || '',
            method: (form.method || 'get').toLowerCase(),
            fields: []
        };
        var inputs = form.querySelectorAll('input, textarea, select');
        for (var j = 0; j < inputs.length; j++) {
            var inp = inputs[j];
            // Skip hidden inputs that are truly type=hidden (legit form data)
            // but DO skip visually-hidden inputs used for injection
            if (inp.type === 'hidden') {
                formData.fields.push({
                    name: inp.name || '', type: 'hidden',
                    value: '', placeholder: ''
                });
                continue;
            }
            if (!isVisible(inp)) continue;
            formData.fields.push({
                name: inp.name || '',
                type: inp.type || inp.tagName.toLowerCase(),
                value: inp.value || '',
                placeholder: inp.placeholder || ''
            });
        }
        result.forms.push(formData);
    }

    // ── Meta tags (kept minimal — only standard descriptors) ──────
    result.meta = {};
    var SAFE_META = {description:1, author:1, keywords:1, robots:1, viewport:1,
                     'og:title':1, 'og:description':1, 'og:type':1, 'og:url':1,
                     'og:image':1, 'twitter:title':1, 'twitter:description':1};
    var metas = document.querySelectorAll('meta[name], meta[property]');
    for (var i = 0; i < metas.length; i++) {
        var meta = metas[i];
        var key = meta.getAttribute('name') || meta.getAttribute('property');
        if (!key || !SAFE_META[key.toLowerCase()]) continue;
        var val = meta.getAttribute('content') || '';
        // Truncate meta values to limit injection surface
        result.meta[key] = val.substring(0, 500);
    }

    return result;
})();
"""


def extract_page_content(driver) -> PageContent:
    """Extract structured content from the current page."""
    raw = driver.execute_script(EXTRACT_CONTENT_JS)

    links = [Link(text=l.get("text", ""), href=l.get("href", ""))
             for l in raw.get("links", [])]

    forms = []
    for f in raw.get("forms", []):
        fields = [FormField(
            name=ff.get("name", ""),
            type=ff.get("type", ""),
            value=ff.get("value", ""),
            placeholder=ff.get("placeholder", "")
        ) for ff in f.get("fields", [])]
        forms.append(Form(
            action=f.get("action", ""),
            method=f.get("method", "get"),
            fields=fields
        ))

    return PageContent(
        url=raw.get("url", ""),
        title=raw.get("title", ""),
        text=raw.get("text", ""),
        links=links,
        forms=forms,
        meta=raw.get("meta", {})
    )
