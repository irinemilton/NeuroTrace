# NeuroTrace — Alzheimer ML Evaluation

Model: Logistic Regression, C=0.01, class_weight=balanced
Input: 141 MRI-derived features; labeled subjects: 72; 52 Non-AD / 20 AD.

| Model | Accuracy | ROC-AUC |
|---|---:|---:|
| Logistic Regression — 141 features | 0.7657 ± 0.0869 | 0.8077 ± 0.1055 |
| Random Forest | 0.6810 ± 0.0681 | 0.7702 ± 0.1122 |
| SVM | 0.7095 ± 0.0607 | 0.7736 ± 0.1330 |

SHAP LinearExplainer is used for subject-level explanations of the existing StandardScaler → LogisticRegression pipeline. Positive SHAP values move the model output toward AD; negative values move it toward Non-AD. SHAP values are model explanations, not causal explanations or clinical diagnoses.
