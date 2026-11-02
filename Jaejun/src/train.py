"""
Training entry point.

Expected input: one prepared CSV containing:
- config/features.json columns
- year
- target columns in config/targets.json

The repository intentionally keeps target construction and raw KNHANES extraction
separate, because those steps depend on the official KDRI definitions and source files.
"""
import argparse
import json
import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

ROOT = Path(__file__).resolve().parents[1]
FEATURES = json.loads((ROOT/"config/features.json").read_text(encoding="utf-8"))
TARGETS = json.loads((ROOT/"config/targets.json").read_text(encoding="utf-8"))

def build_model(nutrient):
    if nutrient == "vitamin_c":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    return HistGradientBoostingClassifier(
        max_iter=180, learning_rate=0.06, max_leaf_nodes=15, random_state=42
    )

def main(csv_path):
    df = pd.read_csv(csv_path)
    train = df[df.year.isin([2022, 2023])].dropna(subset=FEATURES)
    test = df[df.year.eq(2024)].dropna(subset=FEATURES)

    rows = []
    for nutrient, target in TARGETS.items():
        tr=train.dropna(subset=[target]); te=test.dropna(subset=[target])
        model=build_model(nutrient)
        model.fit(tr[FEATURES], tr[target].astype(int))
        p=model.predict_proba(te[FEATURES])[:,1]
        joblib.dump(model, ROOT/"models"/f"{nutrient}.joblib")
        rows.append({
            "nutrient":nutrient,
            "auc":roc_auc_score(te[target],p),
            "pr_auc":average_precision_score(te[target],p),
            "brier":brier_score_loss(te[target],p)
        })
    pd.DataFrame(rows).to_csv(ROOT/"reports"/"holdout_2024_metrics_retrained.csv",index=False)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("prepared_csv")
    args=ap.parse_args()
    main(args.prepared_csv)
