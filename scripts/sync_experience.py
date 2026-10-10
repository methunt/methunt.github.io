"""Regenerate the Experience section of index.html from Data-Engineer.md.

Usage:
    python scripts/sync_experience.py

Reads D:\\AI\\resume-prep\\resume\\Data-Engineer.md (the ## Professional Experience
section), converts each role to the site's HTML job-card markup, and replaces
the content between the EXPERIENCE:START / EXPERIENCE:END markers in index.html.
Everything outside those markers (styling, other sections) is untouched.

Edit the resume .md, then re-run this script — no manual HTML editing needed.
"""
import re
import sys
from pathlib import Path

RESUME_MD = Path(r"D:\AI\resume-prep\resume\Data-Engineer.md")
INDEX_HTML = Path(__file__).resolve().parent.parent / "index.html"
START_MARK = "<!-- EXPERIENCE:START"
END_MARK = "<!-- EXPERIENCE:END -->"


def esc(text: str) -> str:
    """Escape raw text, then turn **bold** markdown into <strong>."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def parse_experience(md_text: str):
    """Pull '## Professional Experience' section, split into roles."""
    m = re.search(r"^##\s*Professional Experience\s*$(.*?)(?=^##\s|\Z)", md_text, re.M | re.S)
    if not m:
        sys.exit("Could not find '## Professional Experience' section in the resume.")
    block = m.group(1)

    roles = []
    # Each role starts with "### Title, Company, City | Date range"
    for role_match in re.finditer(r"^###\s*(.+?)\s*\|\s*(.+?)$(.*?)(?=^###\s|\Z)", block, re.M | re.S):
        header, dates, body = role_match.groups()
        title, _, rest = header.strip().partition(",")
        org_city = rest.strip()
        bullets, subhead = [], None
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("<!--") or line.startswith("#####"):
                continue
            if line.startswith("####"):
                subhead = esc(line.lstrip("#").strip())
                continue
            if line.startswith("- "):
                text = esc(line[2:].strip())
                if subhead:
                    text = f"<strong>{subhead}:</strong> {text}"
                    subhead = None
                bullets.append(text)
        roles.append({
            "title": title.strip(),
            "org_city": org_city,
            "dates": dates.strip().replace(" to ", " — "),
            "bullets": bullets,
        })
    return roles


def render_job(role) -> str:
    bullets = "\n".join(f"        <li>{b}</li>" for b in role["bullets"])
    return (
        '    <div class="job reveal">\n'
        f'      <h3>{esc(role["title"])} — {esc(role["org_city"])}</h3>\n'
        f'      <div class="meta">{esc(role["dates"])}</div>\n'
        "      <ul>\n"
        f"{bullets}\n"
        "      </ul>\n"
        "    </div>"
    )


def main():
    md_text = RESUME_MD.read_text(encoding="utf-8")
    roles = parse_experience(md_text)
    if not roles:
        sys.exit("No roles parsed — check the resume format.")

    html = INDEX_HTML.read_text(encoding="utf-8")
    start_idx = html.find(START_MARK)
    end_idx = html.find(END_MARK)
    if start_idx == -1 or end_idx == -1:
        sys.exit("EXPERIENCE markers not found in index.html.")
    start_line_end = html.find("\n", start_idx) + 1

    new_block = "\n".join(render_job(r) for r in roles) + "\n"
    new_html = html[:start_line_end] + new_block + html[end_idx:]

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"Synced {len(roles)} roles into {INDEX_HTML.name}.")


if __name__ == "__main__":
    main()
