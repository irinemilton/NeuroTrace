import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";

import TopBar from "../components/TopBar";
import BrainViewer from "../components/BrainViewer";
import StructurePanel, {
  BRAIN_REGIONS,
  type BrainRegion,
} from "../components/StructurePanel";
import AnalysisPanel from "../components/AnalysisPanel";

const API = "http://127.0.0.1:8000";

/* =========================================================
   TYPES
   ========================================================= */

interface LivePrediction {
  prediction: number;
  classification: string;
  probability_ad: number;
  probability_non_ad: number;
  model: string;
  model_C?: number;
  features_used: number;

  explanation: Array<{
    feature: string;
    direction: string;
    contribution: number;
  }>;
}

interface LiveMeasurements {
  regions?: Record<
    string,
    {
      total_volume_mm3?: number;
      asymmetry_percent?: number;
    }
  >;
}

interface LiveResult {
  status: string;
  subject_id: string;
  mode: "quick" | "full" | string;
  input_filename: string;
  segmentation_process: string;
  mri_available: boolean;
  segmentation_available: boolean;
  feature_count: number;
  prediction: LivePrediction;
  measurements: LiveMeasurements;
  model_url: string;
  model_mesh_count: number;
  message?: string;
}

/* =========================================================
   COMPONENT
   ========================================================= */

export default function LiveDemoResult() {
  const navigate = useNavigate();

  const { subjectId = "" } = useParams<{
    subjectId: string;
  }>();

  /* =======================================================
     STATE
     ======================================================= */

  const [result, setResult] = useState<LiveResult | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [selectedRegion, setSelectedRegion] =
    useState<BrainRegion | null>(null);

  const [showSurface, setShowSurface] = useState(true);

  const [showRegions, setShowRegions] = useState(true);

  const [showLabels, setShowLabels] = useState(false);

  /* =======================================================
     LOAD LIVE RESULT
     ======================================================= */

  useEffect(() => {
    let cancelled = false;

    const loadResult = async () => {
      try {
        setLoading(true);
        setError(null);

        if (!subjectId) {
          throw new Error(
            "No live analysis subject ID was provided."
          );
        }

        const response = await fetch(
          `${API}/api/live-demo/result/${encodeURIComponent(
            subjectId
          )}`
        );

        let data: any = null;

        try {
          data = await response.json();
        } catch {
          throw new Error(
            `Unable to read the backend response (${response.status}).`
          );
        }

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              data?.message ||
              "Live analysis could not be loaded."
          );
        }

        if (!data) {
          throw new Error(
            "The backend returned an empty live analysis result."
          );
        }

        if (!cancelled) {
          setResult(data as LiveResult);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Live analysis could not be loaded."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadResult();

    return () => {
      cancelled = true;
    };
  }, [subjectId]);

  /* =======================================================
     REGION SELECTION
     ======================================================= */

  const handleRegionSelect = (regionId: string | null) => {
    if (!regionId) {
      setSelectedRegion(null);
      return;
    }

    const region = BRAIN_REGIONS.find(
      (item) => item.id === regionId
    );

    setSelectedRegion(region ?? null);
  };

  /* =======================================================
     LOADING
     ======================================================= */

  if (loading) {
    return (
      <div className="app-shell">
        <TopBar subjectId={subjectId || "LIVE"} />

        <div className="brain-overlay">
          <div className="brain-overlay-content">
            <Loader2 className="spinning" />

            <span className="eyebrow">
              LIVE ANALYSIS
            </span>

            <h2>
              Loading NeuroTrace result
            </h2>

            <p>
              Retrieving the processed MRI,
              measurements and model output.
            </p>
          </div>
        </div>
      </div>
    );
  }

  /* =======================================================
     ERROR
     ======================================================= */

  if (error || !result) {
    return (
      <div className="app-shell">
        <TopBar subjectId={subjectId || "LIVE"} />

        <div className="brain-overlay">
          <div className="brain-overlay-content">
            <h2>
              Unable to load live analysis
            </h2>

            <p>
              {error || "No result found."}
            </p>

            <button
              type="button"
              className="dashboard-secondary-button"
              onClick={() => navigate("/live-demo")}
            >
              <ArrowLeft />
              Back to Live Demo
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* =======================================================
     RESULT DATA
     ======================================================= */

  const measurements = result.measurements;
  const prediction = result.prediction;

  /* =======================================================
     LIVE GLB URL

     The backend stores generated GLBs in:

       frontend/public/models/live_demo/

     Therefore they are served by Vite at:

       http://localhost:3000/models/live_demo/...

     NOT by FastAPI on port 8000.
     ======================================================= */

  const liveModelUrl = result.model_url
    ? result.model_url.startsWith("http://") ||
      result.model_url.startsWith("https://")
      ? result.model_url
      : `${window.location.origin}${result.model_url}`
    : undefined;

  console.log(
    "NeuroTrace live GLB URL:",
    liveModelUrl
  );

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="app-shell">

      {/* ===================================================
          TOP BAR
          =================================================== */}

      <TopBar
        subjectId={result.subject_id}
      />

      {/* ===================================================
          STATUS BAR
          =================================================== */}

      <div className="analysis-status-bar">

        <span>
          MRI:{" "}
          <strong>
            {result.mode === "full"
              ? "Uploaded T1"
              : "Uploaded segmentation"}
          </strong>
        </span>

        <span className="status-separator">
          •
        </span>

        <span>
          Segmentation:{" "}
          <strong className="status-ready">
            {result.mode === "full"
              ? "UNesT complete"
              : "Pre-computed"}
          </strong>
        </span>

        <span className="status-separator">
          •
        </span>

        <span>
          3D Model:{" "}
          <strong>
            Subject-specific
          </strong>
        </span>

        <span className="status-separator">
          •
        </span>

        <span>
          ML Analysis:{" "}
          <strong className="status-ready">
            Complete
          </strong>
        </span>

      </div>

      {/* ===================================================
          MAIN ANALYSIS LAYOUT
          =================================================== */}

      <main className="analysis-layout">

        {/* =================================================
            STRUCTURE PANEL
            ================================================= */}

        <StructurePanel
          selectedRegion={
            selectedRegion?.id ?? null
          }

          onSelectRegion={
            setSelectedRegion
          }

          showSurface={
            showSurface
          }

          showRegions={
            showRegions
          }

          showLabels={
            showLabels
          }

          onShowSurfaceChange={
            setShowSurface
          }

          onShowRegionsChange={
            setShowRegions
          }

          onShowLabelsChange={
            setShowLabels
          }
        />

        {/* =================================================
            3D BRAIN
            ================================================= */}

        <section className="brain-stage">

          {liveModelUrl ? (
            <BrainViewer
              modelPath={liveModelUrl}

              selectedRegion={
                selectedRegion?.id ?? null
              }

              showSurface={
                showSurface
              }

              showRegions={
                showRegions
              }

              showLabels={
                showLabels
              }

              onRegionSelect={
                handleRegionSelect
              }
            />
          ) : (
            <div className="brain-overlay">
              <div className="brain-overlay-content">

                <h2>
                  3D model unavailable
                </h2>

                <p>
                  The live analysis did not
                  return a generated GLB model.
                </p>

              </div>
            </div>
          )}

          {/* Stage information */}

          <div className="stage-info">

            <div>

              <span className="eyebrow">
                LIVE T1-WEIGHTED MRI
              </span>

              <strong>
                {result.subject_id}
                {" · "}
                Interactive anatomical analysis
              </strong>

            </div>

            <div className="stage-resolution">
              1 mm
            </div>

          </div>

        </section>

        {/* =================================================
            ANALYSIS PANEL
            ================================================= */}

        <AnalysisPanel
          selectedRegion={
            selectedRegion
          }

          measurements={
            measurements
          }
        />

      </main>

      {/* ===================================================
          MACHINE LEARNING
          =================================================== */}

      <section className="live-analysis-result-card">

        <div className="live-analysis-result-header">

          <div>

            <span className="eyebrow">
              MACHINE LEARNING
            </span>

            <h2>
              Alzheimer Analysis
            </h2>

            <p>
              {prediction.features_used}{" "}
              MRI-derived features analyzed
              by the trained classifier.
            </p>

          </div>

          <div className="live-analysis-mode-badge">
            {result.mode === "full"
              ? "RAW MRI → UNesT"
              : "PRE-SEGMENTED"}
          </div>

        </div>

        <div className="live-analysis-metrics">

          {/* Prediction */}

          <div className="live-analysis-metric">

            <span>
              Prediction
            </span>

            <strong>
              {prediction.classification}
            </strong>

          </div>

          {/* AD probability */}

          <div className="live-analysis-metric">

            <span>
              AD probability
            </span>

            <strong>
              {(
                prediction.probability_ad *
                100
              ).toFixed(2)}
              %
            </strong>

          </div>

          {/* Non-AD probability */}

          <div className="live-analysis-metric">

            <span>
              Non-AD probability
            </span>

            <strong>
              {(
                prediction.probability_non_ad *
                100
              ).toFixed(2)}
              %
            </strong>

          </div>

          {/* Model */}

          <div className="live-analysis-metric">

            <span>
              Model
            </span>

            <strong>
              {prediction.model}
            </strong>

          </div>

        </div>

      </section>

      {/* ===================================================
          QUANTITATIVE MRI
          =================================================== */}

      <section className="live-analysis-result-card">

        <span className="eyebrow">
          QUANTITATIVE MRI
        </span>

        <h2>
          Regional measurements
        </h2>

        <div className="live-analysis-region-grid">

          {[
            [
              "hippocampus",
              "Hippocampus",
            ],
            [
              "amygdala",
              "Amygdala",
            ],
            [
              "thalamus",
              "Thalamus",
            ],
            [
              "caudate",
              "Caudate",
            ],
            [
              "putamen",
              "Putamen",
            ],
            [
              "pallidum",
              "Pallidum",
            ],
            [
              "lateral_ventricle",
              "Lateral ventricles",
            ],
          ].map(
            ([key, label]) => {

              const region =
                measurements?.regions?.[
                  key
                ];

              return (
                <div
                  className="live-analysis-region"
                  key={key}
                >

                  <span>
                    {label}
                  </span>

                  <strong>
                    {region?.total_volume_mm3 != null
                      ? Math.round(
                          region.total_volume_mm3
                        ).toLocaleString()
                      : "—"}{" "}
                    mm³
                  </strong>

                  <small>
                    Asymmetry{" "}
                    {region?.asymmetry_percent != null
                      ? `${Number(
                          region.asymmetry_percent
                        ).toFixed(1)}%`
                      : "—"}
                  </small>

                </div>
              );
            }
          )}

        </div>

      </section>

      {/* ===================================================
          MODEL EXPLANATION
          =================================================== */}

      <section className="live-analysis-result-card">

        <span className="eyebrow">
          MODEL EXPLANATION
        </span>

        <h2>
          Top feature contributions
        </h2>

        <div className="live-analysis-explanation-grid">

          {(prediction.explanation || []).map(
            (item, index) => (

              <div
                className="live-analysis-feature"
                key={`${item.feature}-${index}`}
              >

                <div>

                  <strong>
                    {item.feature}
                  </strong>

                  <small>
                    {item.direction}
                  </small>

                </div>

                <span>
                  {item.contribution >= 0
                    ? "+"
                    : ""}
                  {item.contribution.toFixed(4)}
                </span>

              </div>

            )
          )}

        </div>

      </section>

      {/* ===================================================
          ANALYSIS REPORT

          NOTE:
          ModelSummary was intentionally removed here.
          The real live ML result is already displayed above.
          =================================================== */}

      <section className="live-analysis-report-card">

        <span className="eyebrow">
          ANALYSIS SUMMARY
        </span>

        <h2>
          NeuroTrace Live Analysis Report
        </h2>

        <div className="live-analysis-report-grid">

          <div>

            <span>
              Input
            </span>

            <strong>
              {result.input_filename}
            </strong>

          </div>

          <div>

            <span>
              Segmentation
            </span>

            <strong>
              {result.mode === "full"
                ? "UNesT complete"
                : "Pre-computed segmentation"}
            </strong>

          </div>

          <div>

            <span>
              Features
            </span>

            <strong>
              {result.feature_count}
            </strong>

          </div>

          <div>

            <span>
              3D meshes
            </span>

            <strong>
              {result.model_mesh_count}
            </strong>

          </div>

        </div>

        <p>
          The displayed 3D model is generated
          from this uploaded analysis result.
          The ML output comes from the trained
          NeuroTrace classifier. Research and
          educational use only; not a clinical
          diagnosis.
        </p>

      </section>

      {/* ===================================================
          BACK BUTTON
          =================================================== */}

      <div className="live-analysis-back-row">

        <button
          type="button"
          className="dashboard-secondary-button"
          onClick={() =>
            navigate("/live-demo")
          }
        >

          <ArrowLeft />

          Analyze another MRI

        </button>

      </div>

    </div>
  );
}