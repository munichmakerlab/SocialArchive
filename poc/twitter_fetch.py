"""PoC: try to fetch one real post from the (defunct) MuMaLab Twitter/X
account via gallery-dl, without login/cookies. X requires a login for
virtually all public timeline access today, so a blocked result here is
itself the relevant finding.
"""

import subprocess
import sys
from pathlib import Path

GALLERY_DL = [sys.executable, "-m", "gallery_dl"]
USERNAME = "munichmakerlab"
RAW_DIR = Path(__file__).parent / "raw" / "twitter"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://twitter.com/{USERNAME}"

    result = subprocess.run(
        [*GALLERY_DL, "-j", "--no-download", url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    (RAW_DIR / "gallery-dl_stderr.txt").write_text(result.stderr)
    if result.stdout.strip():
        (RAW_DIR / "gallery-dl_stdout.txt").write_text(result.stdout)

    if result.returncode != 0 or not result.stdout.strip():
        print("Twitter/X fetch via gallery-dl FAILED (expected without login)")
        print(f"  returncode: {result.returncode}")
        print(f"  stderr (see raw/twitter/gallery-dl_stderr.txt): {result.stderr[:300]}")
        return

    print("Twitter/X fetch via gallery-dl OK")
    print("  saved: raw/twitter/gallery-dl_stdout.txt")


if __name__ == "__main__":
    main()
