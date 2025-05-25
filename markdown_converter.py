import re
import sys
from pathlib import Path

import markdown
import yaml

# -------------------------------------------------------------
# Configuration constants
# -------------------------------------------------------------
CSS_LINK = '<link rel="stylesheet" href="css/pico.classless.cyan.min.css" />'
MATHJAX_SCRIPT = (
    '<script type="text/x-mathjax-config">\n'
    "MathJax.Hub.Config({\n"
    "  tex2jax: {\n"
    '    inlineMath: [["$","$"]],\n'
    '    displayMath: [["$$","$$"]],\n'
    "    processEscapes: true\n"
    "  },\n"
    '  "HTML-CSS": {\n'
    "    linebreaks: { automatic: true },\n"
    '    availableFonts: ["STIX"],\n'
    '    preferredFont: "STIX",\n'
    '    webFont: "STIX-Web",\n'
    "    imageFont: null,\n"
    "    undefinedFamily: \"STIXGeneral,'Arial Unicode MS',serif\"\n"
    "  }\n"
    "});\n"
    "</script>\n"
    '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.9/MathJax.js?config=TeX-AMS_CHTML"></script>'
)
DEFAULT_META = {
    "title": "Untitled Post",
    "description": "Markdown to HTML output",
    "keywords": "blog, markdown, python",
    "canonical": "",
    "image": "imgs/social.webp",
    "url": "",
}

IMG_CAPTION_PATTERN = re.compile(
    r'<p>\s*<img([^>]*?)title="([^"]+)"([^>]*?)>\s*</p>', re.IGNORECASE
)


def convert_img_captions(html: str) -> str:
    """Wrap images (with title attribute) in <figure> adding <figcaption>."""

    def _repl(match):
        before_attrs = match.group(1).strip()
        caption = match.group(2).strip()
        after_attrs = match.group(3).strip()
        attrs = " ".join([part for part in (before_attrs, after_attrs) if part]).strip()
        return f'<figure><img{(" " + attrs) if attrs else ""} /><figcaption>{caption}</figcaption></figure>'

    return IMG_CAPTION_PATTERN.sub(_repl, html)


# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------


def parse_markdown(file_path: Path):
    """Parse the markdown file, extracting YAML front-matter if present."""
    text = file_path.read_text(encoding="utf-8")

    if text.startswith("---"):
        # Split front-matter and body
        parts = text.split("---", 2)
        if len(parts) >= 3:
            _, yaml_block, md_body = parts[0], parts[1], parts[2]
            meta = yaml.safe_load(yaml_block) or {}
            return meta, md_body.lstrip()
    return {}, text


def build_html(meta: dict, body_html: str) -> str:
    """Construct the final HTML document string."""
    m = {**DEFAULT_META, **meta}
    title = m["title"]
    description = m["description"]
    keywords = m["keywords"]
    canonical = m["canonical"] or m.get("url", "")
    url = m.get("url", canonical)
    image = m.get("image", DEFAULT_META["image"])

    head = f"""
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
    <link rel=\"icon\" href=\"/favicon.ico\" />
    <meta name=\"color-scheme\" content=\"dark\">

    <title>{title}</title>
    <meta name=\"title\" content=\"{title}\" />
    <meta name=\"description\" content=\"{description}\" />
    <meta name=\"keywords\" content=\"{keywords}\" />
    <link rel=\"canonical\" href=\"{canonical}\" />

    <!-- Open Graph / Facebook -->
    <meta property=\"og:type\" content=\"website\" />
    <meta property=\"og:url\" content=\"{url}\" />
    <meta property=\"og:title\" content=\"{title}\" />
    <meta property=\"og:description\" content=\"{description}\" />
    <meta property=\"og:image\" content=\"{image}\" />

    <!-- Twitter -->
    <meta property=\"twitter:card\" content=\"summary_large_image\" />
    <meta property=\"twitter:url\" content=\"{url}\" />
    <meta property=\"twitter:title\" content=\"{title}\" />
    <meta property=\"twitter:description\" content=\"{description}\" />
    <meta property=\"twitter:image\" content=\"{image}\" />
    {CSS_LINK}
    {MATHJAX_SCRIPT}
    """.strip()

    html_doc = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
{head}
</head>
<body>
<main class=\"container\">
{body_html}
</main>
</body>
</html>"""
    return html_doc


def convert(markdown_path: Path, output_path: Path):
    """Convert a markdown file to HTML and write to output path."""
    meta, md_body = parse_markdown(markdown_path)

    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "footnotes",
            "tables",
            "toc",
        ]
    )
    body_html = md.convert(md_body)
    body_html = convert_img_captions(body_html)
    full_html = build_html(meta, body_html)
    output_path.write_text(full_html, encoding="utf-8")
    print(f"[ OK ] Wrote HTML to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python converter.py <input.md> [output.html]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Input file {input_file} does not exist.")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = input_file.with_suffix(".html")

    convert(input_file, output_file)
