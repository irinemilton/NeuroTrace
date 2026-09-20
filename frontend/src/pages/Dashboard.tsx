import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  Brain,
  CheckCircle2,
  CircleDashed,
  Database,
  RefreshCw,
  Server,
  Sparkles,
} from "lucide-react";

import {
  getProjectStatus,
  getSegmentationStatus,
  type ProjectStatus,
  type SegmentationStatus,
} from "../api/client";

export function Dashboard() {
  const [project, setProject] = useState<ProjectStatus | null>(null);
  const [segmentation, setSegmentation] =
    useState<SegmentationStatus | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (manual = false) => {
    try {
      if (manual) setRefreshing(true);

      const [projectData, segmentationData] = await Promise.all([
        getProjectStatus(),
        getSegmentationStatus(),
      ]);

      setProject(projectData);
      setSegmentation(segmentationData);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Unable to connect to the NeuroTrace backend.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!project?.segmentation_running) return;

    const timer = setInterval(() => {
      loadData();
    }, 5000);

    return () => clearInterval(timer);
  }, [project?.segmentation_running, loadData]);

  const total = project?.total_mri_subjects ?? 0;
  const completed = project?.segmented_subjects ?? 0;
  const remaining = Math.max(total - completed, 0);

  const progress =
    total > 0 ? Math.round((completed / total) * 100) : 0;

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <RefreshCw className="dashboard-loading-icon" />
          <span>Loading NeuroTrace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">

      {/* ================================================= */}
      {/* TOP BAR */}
      {/* ================================================= */}

      <header className="dashboard-topbar">

        <div className="dashboard-brand">

          <div className="dashboard-brand-icon">
            <Brain />
          </div>

          <div>
            <div className="dashboard-brand-name">
              NeuroTrace
            </div>

            <div className="dashboard-brand-subtitle">
              Neuroimaging Analysis Platform
            </div>
          </div>

        </div>

        <div className="dashboard-topbar-right">

          <div className="dashboard-pipeline-label">
            <span>Pipeline</span>
            <strong>UNesT Segmentation</strong>
          </div>

          <div
            className={`dashboard-status-pill ${
              error
                ? "offline"
                : project?.segmentation_running
                  ? "processing"
                  : "ready"
            }`}
          >
            <span className="dashboard-status-dot" />

            <span>
              {error
                ? "Offline"
                : project?.segmentation_running
                  ? "Processing"
                  : "Ready"}
            </span>
          </div>

        </div>

      </header>


      {/* ================================================= */}
      {/* MAIN */}
      {/* ================================================= */}

      <main className="dashboard-content">

        {/* ERROR */}

        {error && (
          <div className="dashboard-error">
            {error}
          </div>
        )}


        {/* ================================================= */}
        {/* HERO */}
        {/* ================================================= */}

        <section className="dashboard-hero-grid">

          <div className="dashboard-hero-card">

            <div className="dashboard-hero-header">

              <div>

                <div className="dashboard-eyebrow">
                  Research Workspace
                </div>

                <h1>
                  Brain MRI Analysis
                </h1>

                <p>
                  Monitor MRI processing, whole-brain segmentation,
                  quantitative measurements and machine-learning
                  analysis from a single workspace.
                </p>

              </div>

              <div className="dashboard-hero-icon">
                <Activity />
              </div>

            </div>


            <div className="dashboard-actions">

              <Link
                to="/analyze"
                className="dashboard-primary-button"
              >
                Open Brain Analysis
                <ArrowRight />
              </Link>

              <button
                onClick={() => loadData(true)}
                disabled={refreshing}
                className="dashboard-secondary-button"
              >
                <RefreshCw
                  className={refreshing ? "spinning" : ""}
                />

                Refresh
              </button>

            </div>

          </div>


          {/* ================================================= */}
          {/* PIPELINE */}
          {/* ================================================= */}

          <div className="dashboard-pipeline-card">

            <div className="dashboard-card-heading">

              <div>
                Current Pipeline
              </div>

              <Server />

            </div>

            <div className="dashboard-progress">

              <div className="dashboard-progress-numbers">

                <div>

                  <div className="dashboard-progress-count">
                    {completed}

                    <span>
                      / {total}
                    </span>
                  </div>

                  <div className="dashboard-progress-label">
                    subjects segmented
                  </div>

                </div>

                <div className="dashboard-progress-percent">
                  {progress}%
                </div>

              </div>


              <div className="dashboard-progress-track">

                <div
                  className="dashboard-progress-fill"
                  style={{
                    width: `${progress}%`,
                  }}
                />

              </div>


              <div className="dashboard-progress-footer">

                <span>
                  {completed} completed
                </span>

                <span>
                  {remaining} remaining
                </span>

              </div>

            </div>

          </div>

        </section>


        {/* ================================================= */}
        {/* METRICS */}
        {/* ================================================= */}

        <section className="dashboard-metrics">

          <Metric
            label="MRI Subjects"
            value={total}
            subtitle="Raw T1 dataset"
            icon={<Database />}
          />

          <Metric
            label="Segmented"
            value={completed}
            subtitle="UNesT outputs"
            icon={<CheckCircle2 />}
          />

          <Metric
            label="Remaining"
            value={remaining}
            subtitle="Awaiting processing"
            icon={<CircleDashed />}
          />

          <Metric
            label="ML Model"
            value={
              project?.model_available
                ? "READY"
                : "PENDING"
            }
            subtitle={
              project?.model_available
                ? "Prediction available"
                : "Training not started"
            }
            icon={<Sparkles />}
          />

        </section>


        {/* ================================================= */}
        {/* DATASET + SYSTEM */}
        {/* ================================================= */}

        <section className="dashboard-bottom-grid">

          {/* ================================================= */}
          {/* SUBJECT LIST */}
          {/* ================================================= */}

          <div className="dashboard-panel">

            <div className="dashboard-panel-header">

              <div>
                <div className="dashboard-eyebrow">
                  Dataset
                </div>

                <h2>
                  Segmentation Status
                </h2>
              </div>

              <div className="dashboard-auto-refresh">
                Auto-refresh · 5s
              </div>

            </div>


            <div className="dashboard-subject-list">

              {segmentation?.subjects.map((subject) => (

                <Link
                  key={subject.subject_id}
                  to={`/analyze/${subject.subject_id}`}
                  className="dashboard-subject"
                >

                  <div className="dashboard-subject-left">

                    <span
                      className={`dashboard-subject-dot ${
                        subject.segmentation_available
                          ? "complete"
                          : "processing"
                      }`}
                    />

                    <div>

                      <div className="dashboard-subject-id">
                        {subject.subject_id}
                      </div>

                      <div className="dashboard-subject-meta">
                        MRI available
                      </div>

                    </div>

                  </div>


                  <div className="dashboard-subject-right">

                    <span
                      className={`dashboard-subject-state ${
                        subject.segmentation_available
                          ? "complete"
                          : "processing"
                      }`}
                    >
                      {subject.segmentation_available
                        ? "Segmented"
                        : "Processing"}
                    </span>

                    <ArrowRight />

                  </div>

                </Link>

              ))}

            </div>

          </div>


          {/* ================================================= */}
          {/* SYSTEM STATUS */}
          {/* ================================================= */}

          <div className="dashboard-panel dashboard-system-panel">

            <div className="dashboard-eyebrow">
              System Status
            </div>

            <h2>
              NeuroTrace Services
            </h2>


            <div className="dashboard-system-list">

              <StatusRow
                label="MRI Dataset"
                value={
                  project?.raw_mri_available
                    ? "Available"
                    : "Unavailable"
                }
                good={project?.raw_mri_available}
              />

              <StatusRow
                label="Clinical Dataset"
                value={
                  project?.clinical_data_available
                    ? "Available"
                    : "Unavailable"
                }
                good={project?.clinical_data_available}
              />

              <StatusRow
                label="UNesT Pipeline"
                value={
                  project?.segmentation_running
                    ? "Processing"
                    : "Ready"
                }
                good
              />

              <StatusRow
                label="ML Classification"
                value={
                  project?.model_available
                    ? "Ready"
                    : "Not trained"
                }
                good={project?.model_available}
              />

            </div>


            <div className="dashboard-info-box">

              <Activity />

              <p>
                Segmentation status is read directly from the
                NeuroTrace processing directory. The dashboard
                refreshes automatically while UNesT is running.
              </p>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}


/* ============================================================
   METRIC
============================================================ */

function Metric({
  label,
  value,
  subtitle,
  icon,
}: {
  label: string;
  value: string | number;
  subtitle: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="dashboard-metric">

      <div>

        <div className="dashboard-metric-label">
          {label}
        </div>

        <div className="dashboard-metric-value">
          {value}
        </div>

        <div className="dashboard-metric-subtitle">
          {subtitle}
        </div>

      </div>

      <div className="dashboard-metric-icon">
        {icon}
      </div>

    </div>
  );
}


/* ============================================================
   STATUS ROW
============================================================ */

function StatusRow({
  label,
  value,
  good,
}: {
  label: string;
  value: string;
  good?: boolean;
}) {
  return (
    <div className="dashboard-status-row">

      <span>
        {label}
      </span>

      <div>

        <span
          className={`dashboard-system-dot ${
            good ? "good" : "warning"
          }`}
        />

        <strong>
          {value}
        </strong>

      </div>

    </div>
  );
}