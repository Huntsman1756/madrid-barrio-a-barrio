"""
Downloads all five raw sources defined in sources.py.
Handles CSV (direct save) and ZIP (save + extract).
Run: python scripts/fetch_datasets.py
"""

import sys
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(Path(__file__).parent))
from sources import SOURCES

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; madrid-barrio-a-barrio/1.0; "
        "+https://github.com/madrid-barrio-a-barrio)"
    )
}


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers=HEADERS)
    print(f"  GET {url}")
    try:
        with urlopen(req) as response, open(destination, "wb") as out:
            total = response.headers.get("Content-Length")
            downloaded = 0
            chunk = 65_536
            while True:
                block = response.read(chunk)
                if not block:
                    break
                out.write(block)
                downloaded += len(block)
                if total:
                    pct = downloaded / int(total) * 100
                    print(f"    {pct:.0f}%  ({downloaded:,} bytes)", end="\r")
        print(f"    -> {destination} ({destination.stat().st_size:,} bytes)")
    except URLError as exc:
        print(f"  ERROR downloading {url}: {exc}")
        raise


def extract_zip(zip_path: Path) -> None:
    extract_dir = zip_path.parent / zip_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)
    print(f"  extracting {zip_path.name} ...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    print(f"  -> {extract_dir} ({sum(1 for _ in extract_dir.rglob('*'))} files)")


def main() -> None:
    print("=== fetch_datasets.py ===")
    for name, source in SOURCES.items():
        destination = ROOT / source["target"]
        print(f"[download] {name}")
        download(source["url"], destination)
        if source["format"] == "zip":
            extract_zip(destination)
    print("\nAll sources ready. Run python scripts/inspect_columns.py next.")


if __name__ == "__main__":
    main()
