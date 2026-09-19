import {
  Activity,
  ArrowLeftRight,
  Brain,
  Ruler,
} from "lucide-react";
import type { BrainRegion } from "./StructurePanel";

interface AnalysisPanelProps {
  selectedRegion: BrainRegion | null;
}

const DEMO_MEASUREMENTS: Record<
  string,
  {
    left: number;
    right: number;
    asymmetry: number;
  }
> = {
  hippocampus: {
    left: 3084,
    right: 3052,
    asymmetry: 1.0,
  },

  amygdala: {
    left: 1042,
    right: 1047,
    asymmetry: 0.5,
  },

  thalamus: {
    left: 5301,
    right: 5304,
    asymmetry: 0.1,
  },

  caudate: {
    left: 3120,
    right: 3090,
    asymmetry: 1.0,
  },

  putamen: {
    left: 4380,
    right: 4421,
    asymmetry: 0.9,
  },

  pallidum: {
    left: 1380,
    right: 1392,
    asymmetry: 0.9,
  },

  "lateral-ventricle": {
    left: 11250,
    right: 10980,
    asymmetry: 2.4,
  },
};

export default function AnalysisPanel({
  selectedRegion,
}: AnalysisPanelProps) {
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

          <h2>Explore the MRI</h2>

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
    );
  }

  const measurement =
    DEMO_MEASUREMENTS[selectedRegion.id];

  return (
    <aside className="analysis-panel">
      <div className="analysis-header">
        <div>
          <span className="eyebrow">
            SELECTED STRUCTURE
          </span>

          <h2>{selectedRegion.name}</h2>
        </div>

        <div className="structure-icon">
          <Brain size={19} />
        </div>
      </div>

      <div className="measurement-block">
        <div className="measurement-heading">
          <Ruler size={16} />
          MRI-derived volume
        </div>

        <div className="bilateral-grid">
          <Measurement
            label="LEFT"
            value={
              measurement
                ? `${measurement.left.toLocaleString()}`
                : "—"
            }
          />

          <Measurement
            label="RIGHT"
            value={
              measurement
                ? `${measurement.right.toLocaleString()}`
                : "—"
            }
          />
        </div>

        <div className="unit-label">
          mm³
        </div>
      </div>

      <div className="asymmetry-card">
        <div className="asymmetry-title">
          <ArrowLeftRight size={15} />
          Bilateral asymmetry
        </div>

        <div className="asymmetry-value">
          {measurement
            ? `${measurement.asymmetry}%`
            : "—"}
        </div>
      </div>

      <div className="analysis-info">
        <div className="info-row">
          <span>Region</span>
          <strong>{selectedRegion.category}</strong>
        </div>

        <div className="info-row">
          <span>Measurement source</span>
          <strong>3D segmentation</strong>
        </div>

        <div className="info-row">
          <span>Analysis type</span>
          <strong>Structural MRI</strong>
        </div>
      </div>

      <div className="analysis-note">
        <Activity size={15} />

        <span>
          Measurements are derived from the
          segmented T1-weighted MRI and are intended
          for research analysis.
        </span>
      </div>
    </aside>
  );
}

function OverviewStat({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  return (
    <div className="overview-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function Measurement({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="measurement">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}