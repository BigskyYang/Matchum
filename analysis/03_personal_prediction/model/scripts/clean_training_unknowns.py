"""Prepare a separate cleaned table for a future re-fit, never mutate frozen models.

Usage: python scripts/clean_training_unknowns.py input.csv cleaned.csv
The output keeps missing values. Fit the imputer and estimator only on training
rows, rebuild risk bands with the documented split, and re-evaluate all metrics.
"""
import argparse
import json
from pathlib import Path
import pandas as pd

def clean_table(df):
    df=df.copy(); counts={}
    for c in ('식습관_LS_FRUIT','식습관_LS_VEG2'):
        if c not in df:raise ValueError(f'Missing required column: {c}')
        bad=df[c].notna() & ~df[c].isin(range(1,10))
        counts[c]=int(bad.sum());df.loc[bad,c]=float('nan')
    return df,counts

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');args=p.parse_args()
    if Path(args.input).resolve()==Path(args.output).resolve():raise SystemExit('Use a separate output file')
    df,counts=clean_table(pd.read_csv(args.input,low_memory=False));df.to_csv(args.output,index=False)
    print(json.dumps({'rows':len(df),'unknowns_replaced_with_missing':counts,'models_retrained':False},ensure_ascii=False))
