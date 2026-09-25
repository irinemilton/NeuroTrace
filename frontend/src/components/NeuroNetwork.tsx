import { useMemo, useState } from "react";
import { Brain, ChevronRight, Filter, MessageCircle, Minus, Plus, Search, X, Zap } from "lucide-react";

type NodeKind = "core" | "region" | "anomaly" | "subregion";

export interface NetworkNode {
  id: string;
  label: string;
  kind: NodeKind;
  x: number;
  y: number;
  parent?: string;
  volume: string;
  change: string;
  risk: "High" | "Moderate" | "Low" | "Normal";
}

const nodes: NetworkNode[] = [
  { id: "brain", label: "Whole Brain", kind: "core", x: 50, y: 52, volume: "1,248 cm³", change: "-1.2%", risk: "Moderate" },
  { id: "temporal", label: "Temporal Lobe", kind: "region", x: 24, y: 28, parent: "brain", volume: "48.2 cm³", change: "-2.1%", risk: "Moderate" },
  { id: "hippocampus", label: "Hippocampus", kind: "anomaly", x: 10, y: 13, parent: "temporal", volume: "3.1 cm³", change: "-5.8%", risk: "High" },
  { id: "amygdala", label: "Amygdala", kind: "subregion", x: 10, y: 43, parent: "temporal", volume: "1.8 cm³", change: "-0.4%", risk: "Low" },
  { id: "frontal", label: "Frontal Lobe", kind: "region", x: 76, y: 27, parent: "brain", volume: "62.1 cm³", change: "-1.2%", risk: "Low" },
  { id: "prefrontal", label: "Prefrontal Cortex", kind: "subregion", x: 91, y: 13, parent: "frontal", volume: "22.4 cm³", change: "-1.5%", risk: "Low" },
  { id: "parietal", label: "Parietal Lobe", kind: "region", x: 79, y: 75, parent: "brain", volume: "51.0 cm³", change: "-0.8%", risk: "Low" },
  { id: "occipital", label: "Occipital Lobe", kind: "region", x: 22, y: 78, parent: "brain", volume: "38.4 cm³", change: "+0.1%", risk: "Normal" },
];

interface NeuroNetworkProps {
  selectedRegion?: string | null;
  onSelectRegion?: (regionId: string | null) => void;
  onOpenAnalysis?: (regionId: string) => void;
}

export default function NeuroNetwork({
  selectedRegion = null,
  onSelectRegion,
  onOpenAnalysis,
}: NeuroNetworkProps) {
  const [activeId, setActiveId] = useState("brain");
  const [year, setYear] = useState(2024);
  const [zoom, setZoom] = useState(1);
  const [query, setQuery] = useState("");
  const [showRiskOnly, setShowRiskOnly] = useState(false);
  const [askText, setAskText] = useState("");
  const [askMessage, setAskMessage] = useState<string | null>(null);
  const resolvedActiveId = selectedRegion ?? activeId;
  const active = nodes.find((node) => node.id === resolvedActiveId) ?? nodes[0];
  const visibleNodes = useMemo(
    () => nodes.filter((node) => {
      const matchesQuery = node.label.toLowerCase().includes(query.toLowerCase());
      const matchesRisk = !showRiskOnly || node.risk === "High" || node.risk === "Moderate";
      return matchesQuery && matchesRisk;
    }),
    [query, showRiskOnly],
  );

  return (
    <section className="neuro-network-shell">
      <div className="neuro-network-toolbar">
        <div className="neuro-network-title"><Brain size={16} /><span>NEURAL TOPOLOGY</span><i /></div>
        <label className="neuro-network-search"><Search size={13} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find region..." /></label>
        <button className={showRiskOnly ? "active" : ""} onClick={() => setShowRiskOnly((value) => !value)}><Filter size={13} /> Risk focus</button>
        <button onClick={() => setZoom((value) => Math.min(1.25, value + .1))}><Plus size={13} /></button>
        <button onClick={() => setZoom((value) => Math.max(.8, value - .1))}><Minus size={13} /></button>
      </div>
      <div className="neuro-network-stage">
        <div className="neuro-network-grid" />
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ transform: `scale(${zoom})` }}>
          {nodes.filter((node) => node.parent).map((node) => {
            const parent = nodes.find((candidate) => candidate.id === node.parent);
            if (!parent) return null;
            return <line key={`${node.parent}-${node.id}`} x1={parent.x} y1={parent.y} x2={node.x} y2={node.y} className={node.kind === "anomaly" ? "risk-link" : "network-link"} />;
          })}
        </svg>
        <div className="neuro-network-nodes" style={{ transform: `scale(${zoom})` }}>
          {nodes.map((node) => {
            const visible = visibleNodes.some((item) => item.id === node.id);
            return <button key={node.id} className={`neuro-node ${node.kind} ${resolvedActiveId === node.id ? "selected" : ""} ${visible ? "" : "dimmed"}`} style={{ left: `${node.x}%`, top: `${node.y}%` }} onClick={() => { setActiveId(node.id); onSelectRegion?.(node.id === "brain" ? null : node.id); }}>
              <span className="neuro-node-orb"><b /></span><span className="neuro-node-label">{node.label}</span>
            </button>;
          })}
        </div>
        <div className="neuro-network-legend"><span><i className="core" /> Core</span><span><i className="region" /> Region</span><span><i className="anomaly" /> Attention</span></div>
        <div className="neuro-network-timeline"><span>2016</span><input type="range" min="2016" max="2024" value={year} onChange={(event) => setYear(Number(event.target.value))} /><span>{year}</span><span>2024</span></div>
      </div>
      <aside className="neuro-network-inspector">
        <button className="neuro-inspector-close" onClick={() => { setActiveId("brain"); onSelectRegion?.(null); }}><X size={14} /></button>
        <span className="dashboard-eyebrow">{active.kind.toUpperCase()} · {year} SCAN</span>
        <h3>{active.label}</h3>
        <p>Structural analytics from the selected MRI region and longitudinal measurement set.</p>
        <div className="neuro-inspector-metric"><span>Volumetric change</span><strong className={active.change.startsWith("-") ? "negative" : "positive"}>{active.change}</strong><em>{active.risk} risk</em></div>
        <div className="neuro-inspector-grid"><div><span>Total volume</span><strong>{active.volume}</strong></div><div><span>Voxel scale</span><strong>1 mm³</strong></div></div>
        <button className="neuro-inspector-link" onClick={() => onOpenAnalysis?.(active.id)}>Open detailed analysis <ChevronRight size={14} /></button>
      </aside>
      <div className="neuro-network-ask">
        <MessageCircle size={15} />
        <input value={askText} onChange={(event) => { setAskText(event.target.value); setAskMessage(null); }} onKeyDown={(event) => { if (event.key === "Enter" && askText.trim()) setAskMessage(`Workspace context ready for ${active.label}. Open analysis to inspect measured findings.`); }} placeholder={`Ask about ${active.label.toLowerCase()}...`} />
        <button onClick={() => { if (askText.trim()) setAskMessage(`Workspace context ready for ${active.label}. Open analysis to inspect measured findings.`); }}><Zap size={14} /> Analyze</button>
        {askMessage && <span className="neuro-network-response">{askMessage}</span>}
      </div>
    </section>
  );
}
