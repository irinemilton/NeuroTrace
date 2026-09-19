import { useState } from "react";

import TopBar from "../components/TopBar";
import BrainViewer from "../components/BrainViewer";

import StructurePanel, {
  BRAIN_REGIONS,
  type BrainRegion,
} from "../components/StructurePanel";

import AnalysisPanel from "../components/AnalysisPanel";
import ModelSummary from "../components/ModelSummary";

export default function BrainAnalysis() {
  const subjectId = "CRL-104";

  const [selectedRegion, setSelectedRegion] =
    useState<BrainRegion | null>(null);

  const [showSurface, setShowSurface] =
    useState(true);

  const [showRegions, setShowRegions] =
    useState(true);

  const [showLabels, setShowLabels] =
    useState(false);

  const selectedRegionId =
    selectedRegion?.id ?? null;

  function handleViewerRegionSelect(
    regionId: string | null,
  ) {
    if (!regionId) {
      setSelectedRegion(null);
      return;
    }

    const region = BRAIN_REGIONS.find(
      (item) => item.id === regionId,
    );

    setSelectedRegion(region ?? null);
  }

  return (
    <div className="app-shell">
      <TopBar subjectId={subjectId} />

      <main className="analysis-layout">

        {/* LEFT PANEL */}
        <StructurePanel
          selectedRegion={selectedRegionId}
          onSelectRegion={setSelectedRegion}
          showSurface={showSurface}
          showRegions={showRegions}
          showLabels={showLabels}
          onShowSurfaceChange={setShowSurface}
          onShowRegionsChange={setShowRegions}
          onShowLabelsChange={setShowLabels}
        />

        {/* CENTER 3D BRAIN */}
        <section className="brain-stage">

          <BrainViewer
            selectedRegion={selectedRegionId}
            showSurface={showSurface}
            showRegions={showRegions}
            showLabels={showLabels}
            onRegionSelect={
              handleViewerRegionSelect
            }
          />

          <div className="stage-info">
            <div>
              <span className="eyebrow">
                T1-WEIGHTED MRI
              </span>

              <strong>
                Interactive anatomical analysis
              </strong>
            </div>

            <div className="stage-resolution">
              1 mm
            </div>
          </div>

        </section>

        {/* RIGHT PANEL */}
        <AnalysisPanel
          selectedRegion={selectedRegion}
        />

      </main>

      {/* BOTTOM ML PANEL */}
      <ModelSummary
        modelReady={false}
      />
    </div>
  );
}