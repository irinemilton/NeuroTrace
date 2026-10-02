# NeuroTrace — Final Checklist

## Immediate
- [ ] Fresh Quick Analysis visual check
- [ ] Full Pipeline: T1 → UNesT → Features → ML → SHAP → 3D
- [ ] Rotate / zoom; surface/regions/labels toggles; region selection + measurements

## ML / Analysis
- [x] Real SHAP integrated
- [x] Subject-level SHAP values
- [x] Top SHAP features
- [x] SHAP UI
- [x] Coefficient explanation replaced
- [x] Evaluation metrics documented
- [ ] Verify SHAP on multiple subjects

### Longitudinal progression training

Progression models must be trained from real follow-up outcomes. The current
repository contains baseline clinical records and MRI features, but no
12-, 24-, or 36-month outcome labels, so the training command intentionally
stops until those labels are supplied.

```powershell
python -m src.ml.build_progression_dataset `
  --outcomes data/raw/Clinical_data/longitudinal_outcomes.csv
python -m src.ml.train_progression
```

The outcome file must contain `Subject_ID` plus one target for each horizon:
`outcome_12M`, `outcome_24M`, and `outcome_36M` (binary or categorical).
The builder combines these labels with the 141 MRI features and available
baseline clinical fields. Models are written to `models/progression`.

For inference:

```powershell
python -m src.ml.predict_progression `
  --features data/processed/brain_features.csv `
  --output data/processed/progression_predictions.csv
```

## UI / Cleanup
- [x] Redundant ModelSummary removed from Live Result
- [x] Old live GLBs archived
- [ ] Responsive/loading/error visual checks

## Final validation
- [ ] Quick: Segmentation → Features → ML → SHAP → 3D
- [ ] Full: T1 → UNesT → Features → ML → SHAP → 3D
- [ ] Same 3D geometry pipeline
- [x] Existing batch pipeline preserved
- [ ] Final end-to-end demo

## Expo / Report
- [ ] Architecture diagram; problem statement; dataset; UNesT; MRI features
- [x] Evaluation metrics
- [x] SHAP methodology
- [ ] Limitations; final PPT; final report
