
from pathlib import Path
from functools import lru_cache
import json, joblib, numpy as np, pandas as pd, shap
ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'models/alzheimer/neurotrace_alzheimer_model.joblib'
META = ROOT / 'models/alzheimer/neurotrace_feature_metadata.json'
DATA = ROOT / 'data/processed/neurotrace_alzheimer_kaggle.csv'
@lru_cache(maxsize=1)
def _load():
    model = joblib.load(MODEL)
    features = json.loads(META.read_text(encoding='utf-8')).get('features', [])
    if len(features) != 141: raise RuntimeError(f'Expected 141 features, found {len(features)}')
    df = pd.read_csv(DATA)
    scaler = model.named_steps['scaler']; classifier = model.named_steps['classifier']
    background = scaler.transform(df[features].astype(float))
    explainer = shap.LinearExplainer(classifier, background, feature_names=features)
    return scaler, explainer, features
def explain_features(frame: pd.DataFrame, top_n: int = 10):
    scaler, explainer, features = _load()
    raw = explainer.shap_values(scaler.transform(frame[features].astype(float)))
    values = np.asarray(raw[-1] if isinstance(raw, list) else raw)
    if values.ndim == 3: values = values[0, -1, :]
    elif values.ndim == 2: values = values[0]
    else: values = values.reshape(-1)
    base = explainer.expected_value
    if np.ndim(base): base = np.asarray(base).reshape(-1)[-1]
    items = []
    for feature, value in zip(features, values):
        value = float(value)
        items.append({'feature': feature, 'shap_value': value, 'contribution': value, 'direction': 'AD' if value > 0 else 'Non-AD'})
    items.sort(key=lambda x: abs(x['shap_value']), reverse=True)
    return {'method': 'SHAP LinearExplainer', 'output_space': 'log-odds', 'base_value': float(base), 'features': items[:top_n]}
