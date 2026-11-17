"""Shared configuration for the video pipeline.

Every constant here was settled by editing real footage. Changing one changes the
look or the safety of every reel, so each carries the reason it has that value.
"""
import os
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[2]
WORK_ROOT = REPO / "data" / "video"          # gitignored working area
VOICE = REPO / "voice"
MASTER_CSV = REPO / "Niyi_Scripts_Master_FULL.csv"

# --- Drive ------------------------------------------------------------------
REMOTE = "gdrive"                            # rclone remote name; must match on every machine
DRIVE_ROOT = "My Reels & Photos"
UNEDITED = f"{REMOTE}:{DRIVE_ROOT}/Videos Unedited"
EDITED = f"{REMOTE}:{DRIVE_ROOT}/Videos Edited"
CAROUSELS = f"{REMOTE}:{DRIVE_ROOT}/Carousels"

# --- video ------------------------------------------------------------------
W, H, FPS = 1080, 1920, 30

# --- cutting ----------------------------------------------------------------
PAUSE_GAP = 0.80          # silence that ends an utterance
SIMILAR = 0.70            # opening-similarity threshold for a repeated line
MAX_HANDLE = 0.25         # never take more than 250ms of handle
HANDLE_SHARE = 0.45       # of available silence, leaving room for the neighbour

# transition -> default frames. fadeblack is the house default; the others appear
# occasionally where a pause would interrupt a sentence. No hard cuts.
TRANSITIONS = {"fadeblack": 3, "fade": 4, "hblur": 5}
DEFAULT_TRANSITION = "fadeblack"

# --- captions ---------------------------------------------------------------
CAPTION_BOTTOM = 1530     # FIXED bottom edge; centring makes the block shake
CAPTION_SAFE_W = 880      # clears Instagram's right-hand action rail
CAPTION_SIZE = 68
CAPTION_STROKE = 7
LINE_GAP = 14
STRIP_TOP, STRIP_H = 1240, 320
CAPTION_FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
ACCENT = (255, 210, 74, 255)
WHITE = (255, 255, 255, 255)
STROKE_COLOR = (0, 0, 0, 235)
PHRASE_MIN, PHRASE_MAX = 2, 5
PHRASE_GAP = 0.70

# --- B-roll -----------------------------------------------------------------
INSET_W, INSET_H, INSET_X, INSET_Y = 820, 615, 130, 430
INSET_BORDER = 6
BROLL_MIN, BROLL_MAX = 3.0, 4.0     # seconds a still holds

# --- encode -----------------------------------------------------------------
VIDEO_ARGS = [
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "60", "-keyint_min", "60",
    "-sc_threshold", "0", "-x264-params", "force-cfr=1",
]
AUDIO_ARGS = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]

# --- services ---------------------------------------------------------------
ELEVEN_BASE = "https://api.elevenlabs.io"
STT_MODEL = "scribe_v1"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia requires a descriptive User-Agent or throttles to ~10 req/min.
# Never put Niyi's email here - use the project identifier.
USER_AGENT = "aipie-content-pipeline/1.0 (https://github.com/niyiomotoso/aipie-base)"
PIXABAY_API = "https://pixabay.com/api/"


def load_env() -> dict:
    """Read .env without exporting or printing anything."""
    out = {}
    f = REPO / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    for k in ("ELEVENLABS_API_KEY", "PIXABAY_API_KEY"):
        if k in os.environ:
            out[k] = os.environ[k]
    return out


def redact(text: str, env: dict) -> str:
    """Strip every known secret out of a string before it is printed."""
    for v in env.values():
        if v and len(v) > 8:
            text = text.replace(v, "[key]")
    return text


def project_dir(project: str) -> pathlib.Path:
    d = WORK_ROOT / project
    d.mkdir(parents=True, exist_ok=True)
    return d
