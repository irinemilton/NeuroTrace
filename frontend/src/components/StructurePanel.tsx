import { Search, Eye, EyeOff } from "lucide-react";
import { useMemo, useState } from "react";

export interface BrainRegion {
  id: string;
  name: string;
  leftName: string;
  rightName: string;
  category: string;
}

export const BRAIN_REGIONS: BrainRegion[] = [
  {
    id: "hippocampus",
    name: "Hippocampus",
    leftName: "Left_Hippocampus",
    rightName: "Right_Hippocampus",
    category: "Memory",
  },
  {
    id: "amygdala",
    name: "Amygdala",
    leftName: "Left_Amygdala",
    rightName: "Right_Amygdala",
    category: "Limbic",
  },
  {
    id: "thalamus",
    name: "Thalamus",
    leftName: "Left_Thalamus",
    rightName: "Right_Thalamus",
    category: "Deep Gray",
  },
  {
    id: "caudate",
    name: "Caudate",
    leftName: "Left_Caudate",
    rightName: "Right_Caudate",
    category: "Basal Ganglia",
  },
  {
    id: "putamen",
    name: "Putamen",
    leftName: "Left_Putamen",
    rightName: "Right_Putamen",
    category: "Basal Ganglia",
  },
  {
    id: "pallidum",
    name: "Pallidum",
    leftName: "Left_Pallidum",
    rightName: "Right_Pallidum",
    category: "Basal Ganglia",
  },
  {
    id: "lateral-ventricle",
    name: "Lateral Ventricles",
    leftName: "Left_Lateral_Ventricle",
    rightName: "Right_Lateral_Ventricle",
    category: "Ventricular",
  },
];

interface StructurePanelProps {
  selectedRegion: string | null;
  onSelectRegion: (region: BrainRegion | null) => void;
  showSurface: boolean;
  showRegions: boolean;
  showLabels: boolean;
  onShowSurfaceChange: (value: boolean) => void;
  onShowRegionsChange: (value: boolean) => void;
  onShowLabelsChange: (value: boolean) => void;
}

export default function StructurePanel({
  selectedRegion,
  onSelectRegion,
  showSurface,
  showRegions,
  showLabels,
  onShowSurfaceChange,
  onShowRegionsChange,
  onShowLabelsChange,
}: StructurePanelProps) {
  const [search, setSearch] = useState("");

  const filteredRegions = useMemo(() => {
    return BRAIN_REGIONS.filter((region) =>
      region.name.toLowerCase().includes(search.toLowerCase()),
    );
  }, [search]);

  return (
    <aside className="structure-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">ANATOMICAL ATLAS</span>
          <h2>Structures</h2>
        </div>
      </div>

      <div className="search-box">
        <Search size={16} />
        <input
          type="text"
          placeholder="Search structures..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <div className="structure-section">
        <div className="section-title">
          IMPORTANT REGIONS
        </div>

        <div className="region-list">
          {filteredRegions.map((region) => {
            const selected = selectedRegion === region.id;

            return (
              <button
                key={region.id}
                className={`region-item ${
                  selected ? "selected" : ""
                }`}
                onClick={() =>
                  onSelectRegion(selected ? null : region)
                }
              >
                <span
                  className={`region-dot ${
                    selected ? "active" : ""
                  }`}
                />

                <span className="region-name">
                  {region.name}
                </span>

                <span className="region-category">
                  {region.category}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="structure-section display-section">
        <div className="section-title">DISPLAY</div>

        <Toggle
          label="Brain surface"
          enabled={showSurface}
          onChange={onShowSurfaceChange}
        />

        <Toggle
          label="Segmented regions"
          enabled={showRegions}
          onChange={onShowRegionsChange}
        />

        <Toggle
          label="Region labels"
          enabled={showLabels}
          onChange={onShowLabelsChange}
        />
      </div>

      <div className="panel-footer">
        <div className="footer-stat">
          <strong>132</strong>
          <span>anatomical labels</span>
        </div>

        <div className="footer-stat">
          <strong>141</strong>
          <span>brain features</span>
        </div>
      </div>
    </aside>
  );
}

interface ToggleProps {
  label: string;
  enabled: boolean;
  onChange: (value: boolean) => void;
}

function Toggle({
  label,
  enabled,
  onChange,
}: ToggleProps) {
  return (
    <button
      className="display-toggle"
      onClick={() => onChange(!enabled)}
    >
      <span className="toggle-icon">
        {enabled ? (
          <Eye size={15} />
        ) : (
          <EyeOff size={15} />
        )}
      </span>

      <span>{label}</span>

      <span
        className={`toggle-switch ${
          enabled ? "on" : ""
        }`}
      >
        <span />
      </span>
    </button>
  );
}