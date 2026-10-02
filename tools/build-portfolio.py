"""Build /portfolio/ (en), /portfolio/es/ and /portfolio/de/ from one trilingual source.

The source, tools/portfolio.src.html, is the standalone portfolio page kept in the CV folder: every
translatable element carries lang="en|es|de". This script keeps one language per output page and drops
the others, wraps the content in this site's head conventions (canonical, hreflang alternates, Open Graph,
JSON-LD), and styles it with portfolio.css, which maps the content's class names onto aelena.com's own
tokens: Cormorant Garamond for headings, IBM Plex Mono for labels, monochrome, no accent.

One language per URL is what search engines and assistants need to index three languages properly; a
JavaScript toggle on one URL would show them English only.

    python tools/build-portfolio.py
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "portfolio.src.html"
SITE = "https://aelena.com"
LANGS = ("en", "es", "de")
VOID = {"meta", "link", "br", "img", "hr", "input", "source", "wbr"}

TEXT = {
    "en": {
        "title": "Antonio Elena · Portfolio",
        "description": "Selected work of Antonio Elena, CTO and software architect in Madrid: applied AI tools with tests and evaluations, .NET and Python libraries on NuGet and PyPI, two books, essays, and the advisory practice at sig-intent.com.",
        "back": "aelena.com",
        "langs": "language",
        "theme_dark": "> dark",
        "theme_light": "> light",
        "og_locale": "en_US",
        "path": "/portfolio/",
    },
    "es": {
        "title": "Antonio Elena · Portfolio",
        "description": "Trabajo seleccionado de Antonio Elena, CTO y arquitecto de software en Madrid: herramientas de IA aplicada con tests y evaluaciones, librerías .NET y Python en NuGet y PyPI, dos libros, ensayos y la práctica de asesoría en sig-intent.com.",
        "back": "aelena.com",
        "langs": "idioma",
        "theme_dark": "> oscuro",
        "theme_light": "> claro",
        "og_locale": "es_ES",
        "path": "/portfolio/es/",
    },
    "de": {
        "title": "Antonio Elena · Portfolio",
        "description": "Ausgewählte Arbeiten von Antonio Elena, CTO und Softwarearchitekt in Madrid: angewandte KI-Werkzeuge mit Tests und Evaluierungen, .NET- und Python-Bibliotheken auf NuGet und PyPI, zwei Bücher, Essays und die Beratungspraxis auf sig-intent.com.",
        "back": "aelena.com",
        "langs": "Sprache",
        "theme_dark": "> dunkel",
        "theme_light": "> hell",
        "og_locale": "de_DE",
        "path": "/portfolio/de/",
    },
}

# What the page describes, as typed entities an assistant can lift. English names; inLanguage is per page.
WORKS = [
    ("SoftwareSourceCode", "RAG Advisor", "https://github.com/aelena/rag-advisor", "Python", "Rule-based CLI, library and Claude Code skill that analyses a document corpus and recommends a complete RAG configuration with provenance, and validates it against ground-truth queries."),
    ("SoftwareSourceCode", "Agentic Board (Idea Refiner)", "https://github.com/aelena/agentic-board", "Python", "A boardroom of AI agents declared in YAML: hostile round, chaired deliberation, coaching, synthesis and a refine loop, with grounding, an uncertainty policy and a blind evaluation against a single model."),
    ("SoftwareSourceCode", "Trustworthy AI Body of Knowledge", "https://github.com/aelena/trustworthy-ai", "Python", "A programme for an in-house AI assurance capability: 24 pages, five code modules and a companion lab."),
    ("SoftwareSourceCode", "Documentation Curator", "https://github.com/aelena/doc-curator", "Python", "Reports what a folder of documents is worth as text before knowledge-base ingestion: metrics, PII, convertibility, duplicates, versions, and a curation plan."),
    ("SoftwareSourceCode", "c-tiktoken", "https://github.com/aelena/c-tiktoken", "C", "OpenAI's BPE tokenizer implemented in C23 as teaching material, with differential tests and fuzzing."),
    ("SoftwareSourceCode", "FlowTrack", "https://github.com/aelena/flowtrack", "Python", "An opinionated portfolio tracker with abandonment criteria and pre-mortems, driven by an agent through an MCP server."),
    ("SoftwareSourceCode", "Aelena.FileApi", "https://github.com/aelena/file-api", "C#", ".NET document-processing platform exposed as HTTP API, CLI, gRPC and NuGet packages, with the AGPL PDF engine isolated so the core stays MIT."),
    ("SoftwareSourceCode", "PerceptualHash.NET", "https://github.com/aelena/imagehash-net", "C#", "Perceptual image hashing for .NET, bit-compatible with the Python imagehash library."),
    ("SoftwareSourceCode", "Common-Extensions", "https://github.com/aelena/useful-extensions", "C#", "C# extension members for strings, sequences and string metrics; a 2014 library rewritten in 2026."),
    ("SoftwareSourceCode", "Dorksmith", "https://github.com/aelena/dorksmith", "TypeScript", "Deterministic generator of search-operator queries for OSINT and exposure discovery, on npm, PyPI and GitHub Pages."),
    ("SoftwareSourceCode", "XSP Editor", "https://github.com/aelena/xsp-editor", "TypeScript", "Editor for XML-Structured Prompts, companion to the book."),
    ("Book", "Build a Tokenizer in C", "https://aelena74.gumroad.com/l/c-tokenizer", None, "Builds OpenAI's tiktoken tokenizer from scratch in C over eight chapters."),
    ("Book", "Guide to XML-Structured Prompting", "https://aelena74.gumroad.com/l/xsp", None, "Prompting treated as a software engineering discipline."),
]


class LangFilter(HTMLParser):
    """Re-emit the markup, dropping every element (and subtree) whose lang attribute is another language."""

    def __init__(self, keep: str):
        super().__init__(convert_charrefs=False)
        self.keep = keep
        self.out: list[str] = []
        self.skip_depth = 0  # >0 while inside a dropped subtree

    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            if tag not in VOID:
                self.skip_depth += 1
            return
        lang = dict(attrs).get("lang")
        if lang and lang != self.keep:
            if tag not in VOID:
                self.skip_depth = 1
            return
        self.out.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if self.skip_depth:
            return
        lang = dict(attrs).get("lang")
        if lang and lang != self.keep:
            return
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.skip_depth:
            if tag not in VOID:
                self.skip_depth -= 1
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(data)

    def handle_entityref(self, name):
        if not self.skip_depth:
            self.out.append(f"&{name};")

    def handle_charref(self, name):
        if not self.skip_depth:
            self.out.append(f"&#{name};")

    def handle_comment(self, data):
        pass


def filter_lang(html: str, keep: str) -> str:
    f = LangFilter(keep)
    f.feed(html)
    f.close()
    return "".join(f.out)


def inner(html: str, tag: str) -> str:
    m = re.search(rf"<{tag}\b[^>]*>(.*)</{tag}>", html, re.S)
    if not m:
        raise SystemExit(f"no <{tag}> in {SRC}")
    return m.group(1)


def jsonld(lang: str) -> str:
    t = TEXT[lang]
    graph = [
        {
            "@type": "WebPage",
            "@id": f"{SITE}{t['path']}#page",
            "url": f"{SITE}{t['path']}",
            "name": t["title"],
            "description": t["description"],
            "inLanguage": lang,
            "isPartOf": {"@id": f"{SITE}/#website"},
            "about": {"@id": f"{SITE}/#person"},
            "mainEntity": {"@id": f"{SITE}{t['path']}#works"},
        },
        {
            "@type": "ItemList",
            "@id": f"{SITE}{t['path']}#works",
            "name": "Selected work",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i,
                    "item": {
                        "@type": kind,
                        "name": name,
                        "url": url,
                        "author": {"@id": f"{SITE}/#person"},
                        "description": desc,
                        **({"programmingLanguage": pl} if pl else {"bookFormat": "https://schema.org/EBook"}),
                        **({"codeRepository": url} if kind == "SoftwareSourceCode" else {}),
                    },
                }
                for i, (kind, name, url, pl, desc) in enumerate(WORKS, start=1)
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)


def page(lang: str, main_html: str, rail_html: str) -> str:
    t = TEXT[lang]
    alternates = "\n".join(
        f'  <link rel="alternate" hreflang="{l}" href="{SITE}{TEXT[l]["path"]}">' for l in LANGS
    ) + f'\n  <link rel="alternate" hreflang="x-default" href="{SITE}{TEXT["en"]["path"]}">'
    switch = " <span class=\"sep\">/</span> ".join(
        (f'<span class="on" aria-current="page">{l}</span>' if l == lang else f'<a href="{TEXT[l]["path"]}" hreflang="{l}" lang="{l}">{l}</a>')
        for l in LANGS
    )
    og_alt = "\n".join(f'  <meta property="og:locale:alternate" content="{TEXT[l]["og_locale"]}">' for l in LANGS if l != lang)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t['title']}</title>
  <meta name="description" content="{t['description']}">
  <meta name="author" content="Antonio Elena">
  <link rel="canonical" href="{SITE}{t['path']}">
{alternates}
  <meta property="og:title" content="{t['title']}">
  <meta property="og:description" content="{t['description']}">
  <meta property="og:type" content="profile">
  <meta property="og:url" content="{SITE}{t['path']}">
  <meta property="og:site_name" content="Antonio Elena">
  <meta property="og:locale" content="{t['og_locale']}">
{og_alt}
  <meta property="og:image" content="{SITE}/og.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Antonio Elena — ai · architecture · cloud · software · writing">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t['title']}">
  <meta name="twitter:description" content="{t['description']}">
  <meta name="twitter:image" content="{SITE}/og.png">
  <link rel="alternate" type="text/plain" href="{SITE}/llms.txt" title="llms.txt">
  <script type="application/ld+json">
{jsonld(lang)}
  </script>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect x='3' y='3' width='10' height='10' fill='%231a1a1a'/%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
  <link rel="stylesheet" href="/portfolio.css">
  <script>
    (function () {{
      try {{
        var saved = localStorage.getItem('theme');
        if (saved === 'dark' || saved === 'light') {{ document.documentElement.setAttribute('data-theme', saved); }}
      }} catch (e) {{}}
    }})();
  </script>
</head>
<body class="portfolio">
  <header class="pf-top">
    <a class="pf-back" href="/"><span class="prompt">&gt;</span> {t['back']}</a>
    <nav class="pf-langs" aria-label="{t['langs']}">{switch}</nav>
    <button class="theme-toggle pf-theme" type="button" aria-label="Toggle dark mode" aria-pressed="false" data-dark="{t['theme_dark']}" data-light="{t['theme_light']}"><span data-theme-label>{t['theme_dark']}</span></button>
  </header>
  <div class="pf-page">
    <nav class="rail" aria-label="Sections">{rail_html}</nav>
    <main class="pf-main">{main_html}</main>
  </div>
  <script>
    (function () {{
      var btn = document.querySelector('.theme-toggle'); var label = btn.querySelector('[data-theme-label]'); var root = document.documentElement;
      function current() {{ var a = root.getAttribute('data-theme'); if (a) return a; return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }}
      function render() {{ var d = current() === 'dark'; label.textContent = d ? btn.getAttribute('data-light') : btn.getAttribute('data-dark'); btn.setAttribute('aria-pressed', d ? 'true' : 'false'); }}
      btn.addEventListener('click', function () {{ var next = current() === 'dark' ? 'light' : 'dark'; root.setAttribute('data-theme', next); try {{ localStorage.setItem('theme', next); }} catch (e) {{}} render(); }});
      render();
      var links = [].slice.call(document.querySelectorAll('nav.rail a')); var byId = {{}}; links.forEach(function (a) {{ byId[a.getAttribute('href').slice(1)] = a; }});
      if ('IntersectionObserver' in window) {{
        var io = new IntersectionObserver(function (es) {{ es.forEach(function (e) {{ if (e.isIntersecting && byId[e.target.id]) {{ links.forEach(function (a) {{ a.classList.remove('active'); }}); byId[e.target.id].classList.add('active'); }} }}); }}, {{ rootMargin: '-30% 0px -60% 0px' }});
        document.querySelectorAll('main section[id]').forEach(function (s) {{ io.observe(s); }});
      }}
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    main_html = inner(src, "main")
    rail_html = inner(re.search(r'<nav class="rail"[^>]*>.*?</nav>', src, re.S).group(0), "nav")
    # the copy buttons depend on the source page's script; show the plain values instead
    main_html = re.sub(r'\s*<button class="copy"[^>]*>.*?</button>', "", main_html, flags=re.S)
    for lang in LANGS:
        out = ROOT / TEXT[lang]["path"].strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(lang, filter_lang(main_html, lang), filter_lang(rail_html, lang)), encoding="utf-8")
        print(f"{lang}: {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
