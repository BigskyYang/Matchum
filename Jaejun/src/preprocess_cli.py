
import json
import argparse
from pathlib import Path
from .preprocess_survey import preprocess_survey_response

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_json", help="Raw survey response JSON")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    raw = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    out = preprocess_survey_response(raw)

    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)

if __name__ == "__main__":
    main()
