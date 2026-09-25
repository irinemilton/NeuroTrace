import {
  BrainCircuit,
  ChevronRight,
  LockKeyhole,
  Sparkles,
} from "lucide-react";

interface ModelSummaryProps {
  modelReady?: boolean;
}

export default function ModelSummary({
  modelReady = false,
}: ModelSummaryProps) {
  return (
    <section className="model-summary">
      <div className="model-header">
        <div>
          <span className="eyebrow">
            MACHINE LEARNING
          </span>

          <h2>Model Analysis</h2>
        </div>

        <div className="model-status">
          <span
            className={`status-dot ${
              modelReady ? "ready" : "waiting"
            }`}
          />

          {modelReady
            ? "MODEL READY"
            : "WAITING FOR MODEL"}
        </div>
      </div>

      <div className="model-signal">
        <Sparkles size={14} />
        <span>NeuroTrace inference layer</span>
        <i />
        <strong>{modelReady ? "ONLINE" : "STANDBY"}</strong>
      </div>

      <div className="model-content">
        <div className="prediction-box">
          <span className="metric-label">
            CLASSIFIER OUTPUT
          </span>

          <div className="prediction-placeholder">
            <BrainCircuit size={20} />

            <span>
              {modelReady
                ? "Prediction available"
                : "Not available yet"}
            </span>
          </div>
        </div>

        <div className="confidence-box">
          <span className="metric-label">
            CONFIDENCE
          </span>

          <strong>—</strong>
        </div>

        <div className="explanation-box">
          <span className="metric-label">
            SIGNAL EXPLANATION
          </span>

          <div className="explanation-placeholder">
            <LockKeyhole size={15} />

            <span>
              SHAP analysis will appear after
              classifier training.
            </span>
          </div>
        </div>

        <button className="model-details-button">
          Analysis details
          <ChevronRight size={15} />
        </button>
      </div>

      <div className="model-disclaimer">
        NeuroTrace provides research-oriented
        machine-learning analysis. Model predictions
        are not definitive medical diagnoses.
      </div>
    </section>
  );
}