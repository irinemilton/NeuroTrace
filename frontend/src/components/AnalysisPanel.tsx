import {
  Activity,
  ArrowLeftRight,
  Brain,
  Ruler,
} from "lucide-react"

import type { BrainRegion } from "./StructurePanel"
import type { SubjectMeasurements } from "../api/client"


// ============================================================
// PROPS
// ============================================================

interface AnalysisPanelProps {
  selectedRegion: BrainRegion | null
  measurements?: SubjectMeasurements | null
}


// ============================================================
// LOCAL MEASUREMENT TYPE
// ============================================================

interface Measurement {
  left: number | null
  right: number | null
  asymmetry: number | null
  total: number | null
}


// ============================================================
// REGION MAPPING
// ============================================================
//
// Maps the frontend BrainRegion ID to the region key
// returned by the NIfTI measurement API.
//

const REGION_MEASUREMENT_KEYS: Record<string, string> = {
  hippocampus: "hippocampus",
  amygdala: "amygdala",
  thalamus: "thalamus",
  caudate: "caudate",
  putamen: "putamen",
  pallidum: "pallidum",
  "lateral-ventricle": "lateral_ventricle",
}


// ============================================================
// COMPONENT
// ============================================================

export default function AnalysisPanel({
  selectedRegion,
  measurements,
}: AnalysisPanelProps) {

  // ==========================================================
  // NO REGION SELECTED
  // ==========================================================

  if (!selectedRegion) {
    return (
      <aside className="analysis-panel">

        <div className="analysis-empty">

          <div className="empty-icon">
            <Brain size={28} />
          </div>

          <span className="eyebrow">
            BRAIN OVERVIEW
          </span>

          <h2>
            Explore the MRI
          </h2>

          <p>
            Select an anatomical structure from the
            atlas to inspect its MRI-derived
            measurements.
          </p>

          <div className="overview-grid">

            <OverviewStat
              value="132"
              label="Anatomical labels"
            />

            <OverviewStat
              value="141"
              label="Extracted features"
            />

            <OverviewStat
              value="1 mm"
              label="MRI voxel size"
            />

            <OverviewStat
              value="T1"
              label="MRI modality"
            />

          </div>

        </div>

      </aside>
    )
  }


  // ==========================================================
  // GET SELECTED REGION MEASUREMENT
  // ==========================================================

  const measurement = getMeasurement(
    measurements,
    selectedRegion.id,
  )


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <aside className="analysis-panel">

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div className="analysis-header">

        <div>

          <span className="eyebrow">
            SELECTED STRUCTURE
          </span>

          <h2>
            {selectedRegion.name}
          </h2>

        </div>

        <div className="structure-icon">
          <Brain size={19} />
        </div>

      </div>


      {/* ================================================== */}
      {/* VOLUME */}
      {/* ================================================== */}

      <div className="measurement-block">

        <div className="measurement-heading">
          <Ruler size={16} />
          MRI-derived volume
        </div>

        <div className="bilateral-grid">

          <Measurement
            label="LEFT"
            value={formatVolume(
              measurement.left,
            )}
          />

          <Measurement
            label="RIGHT"
            value={formatVolume(
              measurement.right,
            )}
          />

        </div>

        <div className="unit-label">
          mm³
        </div>

      </div>


      {/* ================================================== */}
      {/* ASYMMETRY */}
      {/* ================================================== */}

      <div className="asymmetry-card">

        <div className="asymmetry-title">

          <ArrowLeftRight size={15} />

          Bilateral asymmetry

        </div>

        <div className="asymmetry-value">

          {formatAsymmetry(
            measurement.asymmetry,
          )}

        </div>

      </div>


      {/* ================================================== */}
      {/* EXTRA INFORMATION */}
      {/* ================================================== */}

      <div className="analysis-info">

        <div className="info-row">

          <span>
            Region
          </span>

          <strong>
            {selectedRegion.category}
          </strong>

        </div>


        <div className="info-row">

          <span>
            Measurement source
          </span>

          <strong>
            NIfTI segmentation
          </strong>

        </div>


        <div className="info-row">

          <span>
            Analysis type
          </span>

          <strong>
            Structural MRI
          </strong>

        </div>


        {measurement.total !== null && (
          <div className="info-row">

            <span>
              Total volume
            </span>

            <strong>
              {formatVolume(
                measurement.total,
              )}{" "}
              mm³
            </strong>

          </div>
        )}

      </div>


      {/* ================================================== */}
      {/* RESEARCH NOTE */}
      {/* ================================================== */}

      <div className="analysis-note">

        <Activity size={15} />

        <span>
          Measurements are derived from the
          segmented T1-weighted MRI and are
          intended for research analysis.
        </span>

      </div>

    </aside>
  )
}


// ============================================================
// GET REGION MEASUREMENT
// ============================================================

function getMeasurement(
  measurements:
    | SubjectMeasurements
    | null
    | undefined,
  regionId: string,
): Measurement {

  const empty: Measurement = {
    left: null,
    right: null,
    asymmetry: null,
    total: null,
  }


  // ----------------------------------------------------------
  // No measurement data available
  // ----------------------------------------------------------

  if (!measurements) {
    return empty
  }


  // ----------------------------------------------------------
  // Convert frontend region ID to API region key
  // ----------------------------------------------------------

  const measurementKey =
    REGION_MEASUREMENT_KEYS[regionId]


  if (!measurementKey) {
    return empty
  }


  // ----------------------------------------------------------
  // Get region from API response
  // ----------------------------------------------------------

  const region =
    measurements.regions[measurementKey]


  if (!region) {
    return empty
  }


  // ----------------------------------------------------------
  // Return actual NIfTI measurements
  // ----------------------------------------------------------

  return {
    left: region.left.volume_mm3,
    right: region.right.volume_mm3,
    asymmetry: region.asymmetry_percent,
    total: region.total_volume_mm3,
  }
}


// ============================================================
// FORMAT VOLUME
// ============================================================

function formatVolume(
  value: number | null,
): string {

  if (value === null) {
    return "—"
  }

  return Math.round(
    value,
  ).toLocaleString()
}


// ============================================================
// FORMAT ASYMMETRY
// ============================================================

function formatAsymmetry(
  value: number | null,
): string {

  if (value === null) {
    return "—"
  }

  return `${value.toFixed(1)}%`
}


// ============================================================
// UI COMPONENTS
// ============================================================

function OverviewStat({
  value,
  label,
}: {
  value: string
  label: string
}) {
  return (
    <div className="overview-stat">

      <strong>
        {value}
      </strong>

      <span>
        {label}
      </span>

    </div>
  )
}


function Measurement({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="measurement">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  )
}