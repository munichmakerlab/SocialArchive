"""PoC: try to fetch one real public post from the MuMaLab Instagram account,
first via Instaloader, then via gallery-dl, both without login. Instagram is
expected to be the hardest source -- a login-wall/rate-limit error here is
itself the relevant finding and is captured verbatim.
"""

import json
import subprocess
import sys
from pathlib import Path

GALLERY_DL = [sys.executable, "-m", "gallery_dl"]
USERNAME = "munichmakerlab"
RAW_DIR = Path(__file__).parent / "raw" / "instagram"


def try_instaloader() -> bool:
    import instaloader

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        max_connection_attempts=1,  # fail fast for the PoC instead of long rate-limit backoff
    )
    try:
        profile = instaloader.Profile.from_username(loader.context, USERNAME)
        posts_iter = profile.get_posts()
        post = next(posts_iter)
    except Exception as exc:  # noqa: BLE001 -- capture whatever instaloader raises
        (RAW_DIR / "instaloader_error.txt").write_text(f"{type(exc).__name__}: {exc}")
        print(f"Instagram fetch via Instaloader FAILED: {type(exc).__name__}: {exc}")
        return False

    data = {
        "shortcode": post.shortcode,
        "url": f"https://www.instagram.com/p/{post.shortcode}/",
        "caption": post.caption,
        "date_utc": post.date_utc.isoformat(),
        "is_video": post.is_video,
        "typename": post.typename,
        "mediacount": getattr(post, "mediacount", 1),
    }
    out_path = RAW_DIR / f"instaloader_{post.shortcode}.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    print("Instagram fetch via Instaloader OK")
    print(f"  saved: {out_path}")
    print(f"  url: {data['url']}")
    print(f"  typename: {data['typename']} (mediacount={data['mediacount']}, is_video={data['is_video']})")
    return True


def try_gallery_dl() -> bool:
    url = f"https://www.instagram.com/{USERNAME}/"
    result = subprocess.run(
        [*GALLERY_DL, "-j", "--no-download", url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    (RAW_DIR / "gallery-dl_stderr.txt").write_text(result.stderr)

    if result.returncode != 0 or not result.stdout.strip():
        print("Instagram fetch via gallery-dl FAILED")
        print(f"  returncode: {result.returncode}")
        print(f"  stderr (see raw/instagram/gallery-dl_stderr.txt): {result.stderr[:300]}")
        return False

    out_path = RAW_DIR / "gallery-dl_output.json"
    out_path.write_text(result.stdout)
    print("Instagram fetch via gallery-dl OK")
    print(f"  saved: {out_path}")
    return True


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ok_instaloader = try_instaloader()
    ok_gallery_dl = try_gallery_dl()

    if not ok_instaloader and not ok_gallery_dl:
        print("Instagram: both methods failed without login -- see raw/instagram/*_error.txt / *_stderr.txt")
        sys.exit(0)  # documented blocker, not a hard failure of the PoC itself


if __name__ == "__main__":
    main()
