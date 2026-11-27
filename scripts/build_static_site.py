"""Build the static site assets served by the Cloudflare Worker."""

import hashlib
import shutil
from pathlib import Path

from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
STATIC_DIR = ROOT / "static"
TEMPLATES_DIR = ROOT / "templates"


def _asset_version() -> str:
    h = hashlib.md5()
    for name in sorted(["style.css", "alerts.js"]):
        path = STATIC_DIR / name
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()[:8]


def build() -> None:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)

    shutil.copytree(STATIC_DIR, SITE_DIR / "static")
    shutil.copy2(STATIC_DIR / "sw.js", SITE_DIR / "sw.js")

    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    version = _asset_version()

    (SITE_DIR / "index.html").write_text(
        templates.get_template("index.html").render(asset_version=version)
    )
    (SITE_DIR / "map-tab.html").write_text(
        templates.get_template("map_fragment.html").render()
    )
    (SITE_DIR / "sailings-tab.html").write_text(
        templates.get_template("sailings_tab_fragment.html").render()
    )

    print(f"Built static site in {SITE_DIR} (asset version {version})")


if __name__ == "__main__":
    build()
