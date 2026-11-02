# v1.2 Candidate Architecture

## Status
Candidate only. Do not replace the current official service model yet.

## Why this exists
The original full-information model used same-day 24h recall-derived food-group
information, which is not equivalent to what the web service can collect.

The new candidate uses habitual food-frequency questions validated using
KNHANES 2012-2016 FFQ.

## Mini-FFQ inputs
1. meat
2. fish/seafood
3. egg
4. legumes/tofu/soy products
5. milk/dairy

All are collected using the same 8-level frequency scale.

## Validation
2012-2015 train -> 2016 independent validation.
2025 KDRI-compatible thresholds were applied where units were directly comparable.

Strict 10-nutrient mean performance:
- demographic only AUC: 0.613
- + 3Q mini-FFQ AUC: 0.848
- + 5Q mini-FFQ AUC: 0.877
- + 5Q PR-AUC: 0.750
- + 5Q Brier: 0.106

## Included nutrient-risk outputs
- protein
- calcium
- iron
- phosphorus
- vitamin B1
- vitamin B2
- vitamin C
- fiber
- potassium
- sodium excess

## Not yet included
- magnesium
- zinc
- folate: not available as calculated FFQ nutrient values in these files
- vitamin A: excluded from strict validation because historical FFQ vitamin-A
  unit is not assumed identical to current VA_RAE

## Next gate before production
Obtain KNHANES 2012-2016 ALL files and test, in the SAME population:
1. lifestyle-only
2. lifestyle + 3Q mini-FFQ
3. lifestyle + 5Q mini-FFQ

Only after this incremental validation should the mini-FFQ module be promoted
into the official service inference path.
