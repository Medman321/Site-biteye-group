"""Génère dist/biteye-site.html : le site en un seul fichier, bibliothèques et favicon intégrés.

Usage : python3 build.py
"""
import base64
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
html = (ROOT / "index.html").read_text(encoding="utf-8")


def inline_script(match):
    js = (ROOT / match.group(1)).read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f"<script>/* {match.group(1)} */\n{js}\n</script>"


html = re.sub(r'<script src="(vendor/[^"]+)"></script>', inline_script, html)
favicon = base64.b64encode((ROOT / "favicon.svg").read_bytes()).decode()
html = html.replace('href="favicon.svg"', f'href="data:image/svg+xml;base64,{favicon}"')

out = ROOT / "dist" / "biteye-site.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"{out.relative_to(ROOT)} : {out.stat().st_size / 1024:.0f} Ko")
