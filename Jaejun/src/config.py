from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
CONFIG_DIR = ROOT / "config"

FEATURES = json.loads((CONFIG_DIR / "features.json").read_text(encoding="utf-8"))
TARGETS = json.loads((CONFIG_DIR / "targets.json").read_text(encoding="utf-8"))
RISK_THRESHOLDS = json.loads((CONFIG_DIR / "risk_thresholds.json").read_text(encoding="utf-8"))
MODEL_MANIFEST = json.loads((CONFIG_DIR / "model_manifest.json").read_text(encoding="utf-8"))
