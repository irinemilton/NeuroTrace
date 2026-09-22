import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import TopBar from "../components/TopBar";

import BrainViewer from "../components/BrainViewer";

import StructurePanel, {
  BRAIN_REGIONS,
  type BrainRegion,
} from "../components/StructurePanel";

import AnalysisPanel from "../components/AnalysisPanel";

import ModelSummary from "../components/ModelSummary";

import {
  getSubject,
  getSubjectMeasurements,
  listSubjects,
  analyzeSubject,
  getSubjectExplanation,

  type Subject,
  type SubjectDetails,
  type SubjectMeasurementsResponse,
  type AnalysisResult,
  type ExplanationResult,
} from "../api/client";


/* ============================================================
   BRAIN ANALYSIS
============================================================ */

export default function BrainAnalysis() {

  const navigate = useNavigate();

  const {
    subjectId: routeSubjectId,
  } = useParams<{
    subjectId: string;
  }>();


  /* ==========================================================
     STATE
  ========================================================== */

  const [subjects, setSubjects] =
    useState<Subject[]>([]);

  const [subject, setSubject] =
    useState<SubjectDetails | null>(null);

  const [measurements, setMeasurements] =
    useState<SubjectMeasurementsResponse | null>(null);

  const [analysis, setAnalysis] =
    useState<AnalysisResult | null>(null);

  const [explanation, setExplanation] =
    useState<ExplanationResult | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [analysisLoading, setAnalysisLoading] =
    useState(false);

  const [explanationLoading, setExplanationLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [analysisError, setAnalysisError] =
    useState<string | null>(null);

  const [explanationError, setExplanationError] =
    useState<string | null>(null);

  const [selectedRegion, setSelectedRegion] =
    useState<BrainRegion | null>(null);

  const [showSurface, setShowSurface] =
    useState(true);

  const [showRegions, setShowRegions] =
    useState(true);

  const [showLabels, setShowLabels] =
    useState(false);


  /* ==========================================================
     FIND INITIAL SUBJECT
  ========================================================== */

  useEffect(() => {

    if (routeSubjectId) {
      return;
    }

    let cancelled = false;

    async function findInitialSubject() {

      try {

        setLoading(true);
        setError(null);

        const availableSubjects =
          await listSubjects();

        if (cancelled) {
          return;
        }

        setSubjects(
          availableSubjects,
        );

        /*
         * Prefer a subject that already has
         * UNesT segmentation.
         */

        const firstReadySubject =
          availableSubjects.find(
            (item) =>
              item.segmentation_available,
          );

        /*
         * Otherwise use the first MRI subject.
         */

        const firstSubject =
          firstReadySubject ??
          availableSubjects[0];

        if (!firstSubject) {

          setError(
            "No MRI subjects are available.",
          );

          return;
        }

        navigate(
          `/analyze/${encodeURIComponent(
            firstSubject.subject_id,
          )}`,
          {
            replace: true,
          },
        );

      } catch (err) {

        console.error(
          "Failed to find initial subject:",
          err,
        );

        if (!cancelled) {

          setError(
            "Unable to load available subjects.",
          );

        }

      } finally {

        if (!cancelled) {
          setLoading(false);
        }

      }
    }

    findInitialSubject();

    return () => {
      cancelled = true;
    };

  }, [
    routeSubjectId,
    navigate,
  ]);


  /* ==========================================================
     LOAD SELECTED SUBJECT
  ========================================================== */

  useEffect(() => {

    if (!routeSubjectId) {
      return;
    }

    let cancelled = false;

    async function loadSubject() {

      setLoading(true);

      setError(null);

      setSubject(null);

      setMeasurements(null);

      setAnalysis(null);

      setExplanation(null);

      setAnalysisError(null);

      setExplanationError(null);


      try {

        /*
         * First load the subject itself.
         *
         * This is intentionally NOT done with
         * Promise.all because measurements require
         * completed segmentation.
         */

        const data =
          await getSubject(
            routeSubjectId,
          );

        if (cancelled) {
          return;
        }

        setSubject(data);


        /*
         * Only request quantitative measurements
         * when UNesT segmentation exists.
         */

        if (
          data.segmentation_available
        ) {

          try {

            const measurementData =
              await getSubjectMeasurements(
                routeSubjectId,
              );

            if (!cancelled) {

              setMeasurements(
                measurementData,
              );

            }

          } catch (measurementError) {

            console.error(
              "Failed to load measurements:",
              measurementError,
            );

            /*
             * Measurement failure should not
             * destroy the entire subject page.
             */

            if (!cancelled) {
              setMeasurements(null);
            }

          }

        }

      } catch (err) {

        console.error(
          "Failed to load subject:",
          err,
        );

        if (!cancelled) {

          setSubject(null);

          setMeasurements(null);

          setError(
            "Unable to load subject information.",
          );

        }

      } finally {

        if (!cancelled) {
          setLoading(false);
        }

      }

    }

    loadSubject();

    return () => {
      cancelled = true;
    };

  }, [routeSubjectId]);


  /* ==========================================================
     RUN ML ANALYSIS
  ========================================================== */

  useEffect(() => {

    if (!routeSubjectId) {
      return;
    }

    let cancelled = false;

    async function runAnalysis() {

      setAnalysisLoading(true);

      setAnalysisError(null);

      setAnalysis(null);

      setExplanation(null);

      setExplanationError(null);


      try {

        const result =
          await analyzeSubject(
            routeSubjectId,
          );

        if (cancelled) {
          return;
        }

        setAnalysis(result);

      } catch (err) {

        console.error(
          "Failed to run Alzheimer analysis:",
          err,
        );

        if (!cancelled) {

          setAnalysis(null);

          setAnalysisError(
            "Unable to run Alzheimer ML analysis.",
          );

        }

      } finally {

        if (!cancelled) {
          setAnalysisLoading(false);
        }

      }

    }

    runAnalysis();

    return () => {
      cancelled = true;
    };

  }, [routeSubjectId]);


  /* ==========================================================
     LOAD MODEL EXPLANATION
  ========================================================== */

  const predictionAvailable =
    analysis?.prediction_available === true &&
    analysis?.prediction != null;


  useEffect(() => {

    if (
      !routeSubjectId ||
      !predictionAvailable
    ) {
      return;
    }

    let cancelled = false;

    async function loadExplanation() {

      setExplanationLoading(true);

      setExplanationError(null);

      try {

        const result =
          await getSubjectExplanation(
            routeSubjectId,
          );

        if (cancelled) {
          return;
        }

        setExplanation(result);

      } catch (err) {

        console.error(
          "Failed to load model explanation:",
          err,
        );

        if (!cancelled) {

          setExplanation(null);

          setExplanationError(
            "Model explanation is currently unavailable.",
          );

        }

      } finally {

        if (!cancelled) {
          setExplanationLoading(false);
        }

      }

    }

    loadExplanation();

    return () => {
      cancelled = true;
    };

  }, [
    routeSubjectId,
    predictionAvailable,
  ]);


  /* ==========================================================
     SUBJECT ID
  ========================================================== */

  const subjectId =
    routeSubjectId ??
    subject?.subject_id ??
    "";


  /* ==========================================================
     REGION SELECTION
  ========================================================== */

  const selectedRegionId =
    selectedRegion?.id ?? null;


  function handleViewerRegionSelect(
    regionId: string | null,
  ) {

    if (!regionId) {

      setSelectedRegion(null);

      return;
    }

    const region =
      BRAIN_REGIONS.find(
        (item) =>
          item.id === regionId,
      );

    setSelectedRegion(
      region ?? null,
    );
  }


  /* ==========================================================
     DERIVED STATUS
  ========================================================== */

  const segmentationReady =
    subject?.segmentation_available === true;

  const prediction =
    analysis?.prediction ?? null;


  const confidence =
    prediction
      ? Math.max(
          prediction.probability_ad,
          prediction.probability_non_ad,
        )
      : null;


  /* ==========================================================
     NO ROUTE SUBJECT
  ========================================================== */

  if (
    !loading &&
    !routeSubjectId &&
    !error
  ) {

    return (

      <div className="app-shell">

        <TopBar subjectId="—" />

        <div className="brain-overlay">

          <div className="brain-overlay-content">

            <div className="brain-overlay-icon">
              🧠
            </div>

            <span className="eyebrow">
              NEUROTRACE
            </span>

            <h2>
              Selecting subject
            </h2>

            <p>
              Finding an available MRI
              subject for analysis.
            </p>

          </div>

        </div>

      </div>

    );
  }


  /* ==========================================================
     ERROR
  ========================================================== */

  if (
    !loading &&
    error &&
    !subject
  ) {

    return (

      <div className="app-shell">

        <TopBar
          subjectId={
            subjectId || "—"
          }
        />

        <div className="brain-overlay">

          <div className="brain-overlay-content">

            <div className="brain-overlay-icon">
              ⚠️
            </div>

            <span className="eyebrow">
              NEUROTRACE
            </span>

            <h2>
              Unable to load analysis
            </h2>

            <p>
              {error}
            </p>

          </div>

        </div>

      </div>

    );
  }


  /* ==========================================================
     RENDER
  ========================================================== */

  return (

    <div className="app-shell">

      {/* ======================================================
          TOP BAR
      ====================================================== */}

      <TopBar
        subjectId={subjectId}
      />


      {/* ======================================================
          MAIN ANALYSIS
      ====================================================== */}

      <main className="analysis-layout">


        {/* ====================================================
            STRUCTURE PANEL
        ==================================================== */}

        <StructurePanel

          selectedRegion={
            selectedRegionId
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


        {/* ====================================================
            3D BRAIN VIEWER
        ==================================================== */}

        <section className="brain-stage">

          <BrainViewer

            subjectId={
              subjectId
            }

            selectedRegion={
              selectedRegionId
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

            segmentationAvailable={
              segmentationReady
            }

            onRegionSelect={
              handleViewerRegionSelect
            }

          />


          {/* ==================================================
              LOADING OVERLAY
          ================================================== */}

          {loading && (

            <div className="brain-overlay">

              <div className="brain-overlay-content">

                <div className="brain-overlay-icon">
                  🧠
                </div>

                <span className="eyebrow">
                  LOADING
                </span>

                <h2>
                  Loading brain data
                </h2>

                <p>
                  Retrieving MRI information
                  for{" "}

                  <strong>
                    {subjectId}
                  </strong>.
                </p>

              </div>

            </div>

          )}


          {/* ==================================================
              SEGMENTATION PROCESSING
          ================================================== */}

          {!loading &&
            subject &&
            !segmentationReady && (

              <div className="brain-overlay segmentation-overlay">

                <div className="brain-overlay-content">

                  <div className="brain-overlay-icon">
                    🧠
                  </div>

                  <span className="eyebrow">
                    PROCESSING
                  </span>

                  <h2>
                    Segmentation in progress
                  </h2>

                  <p>
                    The MRI for{" "}

                    <strong>
                      {subjectId}
                    </strong>{" "}

                    has not finished
                    anatomical segmentation
                    yet.
                  </p>

                  <p className="overlay-secondary">
                    The 3D subject-specific
                    visualization will become
                    available when segmentation
                    is complete.
                  </p>

                </div>

              </div>

            )}


          {/* ==================================================
              STAGE INFORMATION
          ================================================== */}

          <div className="stage-info">

            <div>

              <span className="eyebrow">
                T1-WEIGHTED MRI
              </span>

              <strong>
                {subjectId}
                {" · "}
                Interactive anatomical analysis
              </strong>

            </div>

            <div className="stage-resolution">
              1 mm
            </div>

          </div>

        </section>


        {/* ====================================================
            ANALYSIS PANEL
        ==================================================== */}

        <AnalysisPanel

          selectedRegion={
            selectedRegion
          }

          measurements={
            measurements?.measurements ??
            null
          }

        />

      </main>


      {/* ======================================================
          MACHINE LEARNING
      ====================================================== */}

      <section
        className="model-summary"
        style={{
          marginTop: "12px",
        }}
      >

        <div className="model-header">

          <div>
            <span className="eyebrow">
              MACHINE LEARNING
            </span>

            <h2>
              Model Analysis
            </h2>
          </div>

          <div className="model-status">
            <span
              className={`status-dot ${
                predictionAvailable
                  ? "ready"
                  : "waiting"
              }`}
            />

            {predictionAvailable
              ? "MODEL READY"
              : "ANALYSIS PENDING"}
          </div>

        </div>


        {predictionAvailable &&
          prediction && (

            <div className="model-content">

              {/* PREDICTION */}

              <div className="prediction-box">

                <span className="eyebrow">
                  MODEL PREDICTION
                </span>

                <div
                  style={{
                    marginTop: "8px",
                    fontSize: "18px",
                    fontWeight: 650,
                    color: "#17202a",
                  }}
                >
                  {prediction.classification}
                </div>

                <div
                  style={{
                    marginTop: "6px",
                    display: "flex",
                    gap: "10px",
                    flexWrap: "wrap",
                    color: "#8b969f",
                    fontSize: "9px",
                  }}
                >
                  <span>
                    AD {(prediction.probability_ad * 100).toFixed(2)}%
                  </span>

                  <span>
                    Non-AD{" "}
                    {(prediction.probability_non_ad * 100).toFixed(2)}%
                  </span>
                </div>

              </div>


              {/* CONFIDENCE */}

              <div className="confidence-box">

                <span className="eyebrow">
                  CONFIDENCE
                </span>

                <strong>
                  {confidence !== null
                    ? `${(confidence * 100).toFixed(2)}%`
                    : "—"}
                </strong>

              </div>


              {/* EXPLANATION */}

              <div className="explanation-box">

                <span className="eyebrow">
                  MODEL EXPLANATION
                </span>

                {!explanationLoading &&
                  !explanationError &&
                  explanation &&
                  explanation.features.length > 0 && (

                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "7px",
                        marginTop: "9px",
                      }}
                    >

                      {explanation.features
                        .slice(0, 3)
                        .map((item) => {

                          const topFeatures =
                            explanation.features.slice(0, 3);

                          const maxMagnitude =
                            Math.max(
                              ...topFeatures.map((feature) =>
                                Math.abs(
                                  feature.contribution,
                                ),
                              ),
                            );

                          const width =
                            maxMagnitude > 0
                              ? Math.max(
                                  8,
                                  (Math.abs(item.contribution) /
                                    maxMagnitude) *
                                    100,
                                )
                              : 8;

                          return (
                            <div
                              key={item.feature}
                              style={{
                                display: "grid",
                                gridTemplateColumns:
                                  "minmax(0, 1fr) 45px",
                                gap: "8px",
                                alignItems: "center",
                              }}
                            >

                              <div style={{ minWidth: 0 }}>

                                <div
                                  style={{
                                    fontSize: "8px",
                                    color: "#68747f",
                                    whiteSpace: "nowrap",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                  }}
                                  title={item.feature}
                                >
                                  {item.feature}
                                </div>

                                <div
                                  style={{
                                    height: "3px",
                                    marginTop: "3px",
                                    borderRadius: "999px",
                                    background: "#edf0f2",
                                    overflow: "hidden",
                                  }}
                                >
                                  <div
                                    style={{
                                      width: `${width}%`,
                                      height: "100%",
                                      borderRadius: "999px",
                                      background:
                                        item.direction === "AD"
                                          ? "#b86b6b"
                                          : "#6b91b8",
                                    }}
                                  />
                                </div>

                              </div>

                              <span
                                style={{
                                  textAlign: "right",
                                  fontSize: "8px",
                                  color: "#8b969f",
                                  fontVariantNumeric:
                                    "tabular-nums",
                                }}
                              >
                                {item.contribution >= 0 ? "+" : ""}
                                {item.contribution.toFixed(3)}
                              </span>

                            </div>
                          );
                        })}

                    </div>
                  )}

                {explanationLoading && (
                  <div className="explanation-placeholder">
                    Calculating feature contributions...
                  </div>
                )}

                {!explanationLoading &&
                  explanationError && (
                    <div className="explanation-placeholder">
                      {explanationError}
                    </div>
                  )}

              </div>


              {/* MODEL DETAILS */}

              <div
                className="model-details-button"
                style={{
                  justifyContent: "center",
                  cursor: "default",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  gap: "4px",
                }}
              >
                <span>
                  {prediction.model}
                </span>

                <span
                  style={{
                    color: "#9ba4ab",
                    fontSize: "8px",
                  }}
                >
                  C: {prediction.model_C} ·{" "}
                  {prediction.features_used} features
                </span>
              </div>

            </div>
          )}


        {!predictionAvailable && (
          <div
            style={{
              marginTop: "14px",
              padding: "12px",
              border: "1px solid #e6eaed",
              borderRadius: "11px",
              background: "#fafbfc",
              color: "#8b969f",
              fontSize: "10px",
            }}
          >
            {analysisLoading
              ? "Running Alzheimer analysis..."
              : analysisError ??
                analysis?.message ??
                "Prediction is not available yet."}
          </div>
        )}

        <div className="model-disclaimer">
          Feature contributions describe model associations,
          not causal or clinical conclusions.
        </div>

      </section>


      {/* ======================================================
          ANALYSIS SUMMARY / REPORT
      ====================================================== */}

      <section
        className="model-summary"
        style={{
          marginTop: "12px",
        }}
      >

        <div className="model-header">

          <div>
            <span className="eyebrow">
              ANALYSIS SUMMARY
            </span>

            <h2>
              NeuroTrace Report
            </h2>
          </div>

          <div
            style={{
              color: "#9ba4ab",
              fontSize: "8px",
              fontWeight: 700,
              letterSpacing: "0.08em",
            }}
          >
            {subjectId}
          </div>

        </div>


        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(4, minmax(0, 1fr))",
            gap: "9px",
            marginTop: "14px",
          }}
        >

          <div className="prediction-box">
            <span className="eyebrow">
              MRI
            </span>

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 600,
                color: "#52616d",
              }}
            >
              {subject?.mri_available
                ? "T1-weighted"
                : "Unavailable"}
            </div>

            <div
              style={{
                marginTop: "4px",
                color: "#9ba4ab",
                fontSize: "8px",
              }}
            >
              3D structural MRI
            </div>
          </div>


          <div className="prediction-box">
            <span className="eyebrow">
              SEGMENTATION
            </span>

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 600,
                color: "#52616d",
              }}
            >
              {subject?.segmentation_available
                ? "UNesT complete"
                : "Unavailable"}
            </div>

            <div
              style={{
                marginTop: "4px",
                color: "#9ba4ab",
                fontSize: "8px",
              }}
            >
              Whole-brain anatomical labels
            </div>
          </div>


          <div className="prediction-box">
            <span className="eyebrow">
              FEATURES
            </span>

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 600,
                color: "#52616d",
              }}
            >
              {prediction?.features_used ?? 141}
            </div>

            <div
              style={{
                marginTop: "4px",
                color: "#9ba4ab",
                fontSize: "8px",
              }}
            >
              MRI-derived measurements
            </div>
          </div>


          <div className="prediction-box">
            <span className="eyebrow">
              ML RESULT
            </span>

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 650,
                color: "#52616d",
              }}
            >
              {prediction?.classification ?? "Pending"}
            </div>

            <div
              style={{
                marginTop: "4px",
                color: "#9ba4ab",
                fontSize: "8px",
              }}
            >
              {confidence !== null
                ? `${(confidence * 100).toFixed(2)}% model probability`
                : "Awaiting analysis"}
            </div>
          </div>

        </div>


        {/* REGIONAL MEASUREMENTS */}

        <div
          style={{
            marginTop: "16px",
            paddingTop: "14px",
            borderTop: "1px solid #edf0f2",
          }}
        >

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "10px",
            }}
          >

            <div>
              <span className="eyebrow">
                QUANTITATIVE MRI
              </span>

              <div
                style={{
                  marginTop: "5px",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#52616d",
                }}
              >
                Regional measurements
              </div>
            </div>

            <span
              style={{
                color: "#9ba4ab",
                fontSize: "8px",
              }}
            >
              mm³
            </span>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(4, minmax(0, 1fr))",
              gap: "9px",
            }}
          >

            {[
              ["Hippocampus", "hippocampus"],
              ["Amygdala", "amygdala"],
              ["Thalamus", "thalamus"],
              ["Caudate", "caudate"],
              ["Putamen", "putamen"],
              ["Pallidum", "pallidum"],
              ["Lateral ventricles", "lateral_ventricle"],
            ].map(([label, key]) => {

              const region =
                measurements?.measurements?.regions?.[
                  key
                ];

              const volume =
                region?.total_volume_mm3;

              const asymmetry =
                region?.asymmetry_percent;

              return (
                <div
                  key={key}
                  className="prediction-box"
                  style={{
                    minHeight: "62px",
                    padding: "10px",
                  }}
                >

                  <span
                    style={{
                      display: "block",
                      color: "#7d8993",
                      fontSize: "8px",
                      fontWeight: 600,
                    }}
                  >
                    {label}
                  </span>

                  <strong
                    style={{
                      display: "block",
                      marginTop: "6px",
                      color: "#52616d",
                      fontSize: "13px",
                    }}
                  >
                    {typeof volume === "number"
                      ? volume.toLocaleString()
                      : "—"}
                  </strong>

                  {typeof asymmetry === "number" && (
                    <span
                      style={{
                        display: "block",
                        marginTop: "3px",
                        color: "#9ba4ab",
                        fontSize: "7px",
                      }}
                    >
                      Asymmetry{" "}
                      {asymmetry.toFixed(1)}%
                    </span>
                  )}

                </div>
              );
            })}

          </div>

        </div>


        {/* REPORT OVERVIEW */}

        <div
          style={{
            marginTop: "16px",
            paddingTop: "14px",
            borderTop: "1px solid #edf0f2",
            display: "grid",
            gridTemplateColumns:
              "1.3fr 1fr",
            gap: "12px",
          }}
        >

          <div className="explanation-box">

            <span className="eyebrow">
              ANALYSIS OVERVIEW
            </span>

            <p
              style={{
                margin:
                  "9px 0 0",
                color: "#68747f",
                fontSize: "9px",
                lineHeight: 1.6,
              }}
            >
              NeuroTrace combines the subject's
              T1-weighted MRI, UNesT anatomical
              segmentation, quantitative regional
              measurements, and the trained
              Alzheimer classification model into
              one subject-level analysis.
            </p>

          </div>


          <div className="explanation-box">

            <span className="eyebrow">
              MODEL
            </span>

            <div
              style={{
                marginTop: "9px",
                display: "grid",
                gap: "5px",
                color: "#68747f",
                fontSize: "9px",
              }}
            >
              <span>
                Algorithm:{" "}
                <strong>
                  {prediction?.model ?? "—"}
                </strong>
              </span>

              <span>
                Regularization:{" "}
                <strong>
                  C = {prediction?.model_C ?? "—"}
                </strong>
              </span>

              <span>
                Features:{" "}
                <strong>
                  {prediction?.features_used ?? "—"}
                </strong>
              </span>
            </div>

          </div>

        </div>


        <div className="model-disclaimer">
          This summary is generated from the available MRI,
          segmentation, measurements, and model output for this
          subject. It is intended for research and educational use,
          not clinical diagnosis.
        </div>

      </section>


      {/* ======================================================
          RESEARCH DISCLAIMER
      ====================================================== */}

      <div
        style={{
          margin: "12px 24px 20px",
          padding: "10px 14px",
          borderRadius: "10px",
          background: "rgba(255,255,255,0.025)",
          fontSize: "9px",
          lineHeight: 1.5,
          opacity: 0.5,
        }}
      >
        NeuroTrace is a research and educational
        neuroimaging system. The displayed ML
        prediction and MRI measurements are not
        a clinical diagnosis.
      </div>

    </div>
  );
}