import { useEffect, useState } from "react";
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
  type Subject,
  type SubjectDetails,
  type SubjectMeasurementsResponse,
} from "../api/client";


// ==========================================================
// BRAIN ANALYSIS
// ==========================================================

export default function BrainAnalysis() {
  const navigate = useNavigate();

  const {
    subjectId: routeSubjectId,
  } = useParams<{
    subjectId: string;
  }>();


  // ==========================================================
  // STATE
  // ==========================================================

  const [subjects, setSubjects] =
    useState<Subject[]>([]);

  const [subject, setSubject] =
    useState<SubjectDetails | null>(null);

  const [measurements, setMeasurements] =
    useState<SubjectMeasurementsResponse | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [selectedRegion, setSelectedRegion] =
    useState<BrainRegion | null>(null);

  const [showSurface, setShowSurface] =
    useState(true);

  const [showRegions, setShowRegions] =
    useState(true);

  const [showLabels, setShowLabels] =
    useState(false);


  // ==========================================================
  // FIND SUBJECT WHEN /analyze IS USED
  // ==========================================================

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

        // Prefer the first segmented subject.
        const firstReadySubject =
          availableSubjects.find(
            (item) =>
              item.segmentation_available,
          );

        // Otherwise use the first MRI subject.
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


  // ==========================================================
  // LOAD SELECTED SUBJECT
  // ==========================================================

  useEffect(() => {
    if (!routeSubjectId) {
      return;
    }

    let cancelled = false;

    async function loadSubject() {
      setLoading(true);
      setError(null);

      // Clear measurements from the previous subject
      // while the new subject is loading.
      setMeasurements(null);

      try {

        const [
          data,
          measurementData,
        ] = await Promise.all([
          getSubject(routeSubjectId),
          getSubjectMeasurements(
            routeSubjectId,
          ),
        ]);

        if (!cancelled) {
          setSubject(data);
          setMeasurements(
            measurementData,
          );
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


  // ==========================================================
  // SUBJECT ID
  // ==========================================================

  const subjectId =
    routeSubjectId ??
    subject?.subject_id ??
    "";


  // ==========================================================
  // REGION SELECTION
  // ==========================================================

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


  // ==========================================================
  // NO ROUTE SUBJECT
  // ==========================================================

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


  // ==========================================================
  // ERROR
  // ==========================================================

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


  // ==========================================================
  // SUBJECT READY
  // ==========================================================

  const segmentationReady =
    subject?.segmentation_available === true;


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="app-shell">

      <TopBar
        subjectId={subjectId}
      />


      {/* ================================================== */}
      {/* STATUS BAR */}
      {/* ================================================== */}

      <div className="analysis-status-bar">

        {loading && (
          <span>
            Loading subject information...
          </span>
        )}

        {!loading &&
          subject && (
            <>
              <span>
                MRI:{" "}
                <strong>
                  {subject.mri_available
                    ? "Available"
                    : "Unavailable"}
                </strong>
              </span>

              <span className="status-separator">
                •
              </span>

              <span>
                Segmentation:{" "}
                <strong
                  className={
                    segmentationReady
                      ? "status-ready"
                      : "status-processing"
                  }
                >
                  {segmentationReady
                    ? "Ready"
                    : "Processing"}
                </strong>
              </span>

              <span className="status-separator">
                •
              </span>

              <span>
                3D Model:{" "}
                <strong>
                  {segmentationReady
                    ? "Subject-specific"
                    : "Waiting"}
                </strong>
              </span>
            </>
          )}

      </div>


      {/* ================================================== */}
      {/* MAIN ANALYSIS */}
      {/* ================================================== */}

      <main className="analysis-layout">


        {/* ================================================= */}
        {/* LEFT ATLAS */}
        {/* ================================================= */}

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


        {/* ================================================= */}
        {/* 3D BRAIN */}
        {/* ================================================= */}

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


          {/* ------------------------------------------------ */}
          {/* LOADING OVERLAY */}
          {/* ------------------------------------------------ */}

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


          {/* ------------------------------------------------ */}
          {/* SEGMENTATION PROCESSING */}
          {/* ------------------------------------------------ */}

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


          {/* ------------------------------------------------ */}
          {/* STAGE INFORMATION */}
          {/* ------------------------------------------------ */}

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


        {/* ================================================= */}
        {/* RIGHT ANALYSIS */}
        {/* ================================================= */}

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


      <ModelSummary
        modelReady={false}
      />

    </div>
  );
}