import {
  Brain,
  CheckCircle2,
  ScanLine,
  Activity,
  Bell,
  Search,
} from "lucide-react";

interface TopBarProps {
  subjectId: string;
}

export default function TopBar({ subjectId }: TopBarProps) {
  return (
    <header className="top-bar">
      <div className="brand-section">
        <div className="brand-icon">
          <Brain size={22} strokeWidth={1.8} />
        </div>

        <div>
          <div className="brand-name">NeuroTrace</div>
          <div className="brand-subtitle">
            AI-assisted brain MRI analysis
          </div>
        </div>
      </div>

      <div className="top-status">
        <div className="top-command-icons" aria-label="Workspace controls">
          <button type="button" title="Analysis activity"><Activity size={15} /></button>
          <button type="button" title="Notifications"><Bell size={15} /></button>
          <button type="button" title="Search structures"><Search size={15} /></button>
        </div>
        <div className="subject-info">
          <span className="status-label">SUBJECT</span>
          <span className="subject-value">{subjectId}</span>
        </div>

        <div className="status-pill">
          <CheckCircle2 size={14} />
          MRI PROCESSED
        </div>

        <div className="status-pill">
          <ScanLine size={14} />
          SEGMENTATION READY
        </div>
      </div>
    </header>
  );
}