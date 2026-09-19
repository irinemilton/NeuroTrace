import {
  Brain,
  CheckCircle2,
  ScanLine,
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