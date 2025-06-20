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
STYLE_BLOCK = (
    "<style>\n"
    "figure img, p > img {\n"
    "  max-width: 33vw;\n"
    "  display: block;\n"
    "  margin-left: auto;\n"
    "  margin-right: auto;\n"
    "}\n"
    "figcaption {\n"
    "  text-align: center;\n"
    "  font-style: italic;\n"
    "}\n"
    "</style>"
)
DEFAULT_META = {
    "title": "Untitled Post",
    "description": "Markdown to HTML output",
    "keywords": "blog, markdown, python",
    "canonical": "",
    "image": "imgs/social.webp",
    "url": "",
    "date": "",  # ISO-8601 e.g. 2024-03-15
}

IMG_P_TAG = re.compile(r"<p>\s*(<img[^>]+>)\s*</p>", re.IGNORECASE)


def convert_img_captions(html: str) -> str:
    """Wrap standalone <img> paragraphs in <figure> and add <figcaption>.

    Caption priority: title attribute > alt attribute.
    """

    def _repl(match):
        img_tag = match.group(1)

        # Extract attributes
        title_m = re.search(r'title="([^"]+)"', img_tag, re.IGNORECASE)
        alt_m = re.search(r'alt="([^"]+)"', img_tag, re.IGNORECASE)
        caption = None
        if title_m:
            caption = title_m.group(1).strip()
        elif alt_m:
            caption = alt_m.group(1).strip()

        if caption:
            # convert URLs in caption to clickable links
            def linkify(match):
                url = match.group(0)
                return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'

            caption_html = re.sub(r"https?://[^\s]+", linkify, caption)
            return f"<figure>{img_tag}<figcaption>{caption_html}</figcaption></figure>"
        # If no caption, leave unchanged
        return match.group(0)

    return IMG_P_TAG.sub(_repl, html)


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
    date = m.get("date", DEFAULT_META["date"])

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
    {STYLE_BLOCK}
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
    body_html = inject_date_subtitle(body_html, meta.get("date", ""))
    full_html = build_html(meta, body_html)
    output_path.write_text(full_html, encoding="utf-8")
    print(f"[ OK ] Wrote HTML to {output_path}")


def inject_date_subtitle(html: str, date: str) -> str:
    """Insert a subtitle line with the date immediately after the first <h1>."""
    if not date:
        return html

    match = re.search(r"<h1[^>]*>.*?</h1>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return html

    end = match.end()
    subtitle = f'\n<p class="subtitle"><time datetime="{date}">{date}</time></p>'
    return html[:end] + subtitle + html[end:]


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
