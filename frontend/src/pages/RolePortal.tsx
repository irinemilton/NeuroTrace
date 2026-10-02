import { Brain, HeartHandshake, Stethoscope } from "lucide-react";
import { Link } from "react-router-dom";
import RoleSwitcher from "../components/RoleSwitcher";

export default function RolePortal() {
  return <div className="role-portal"><div className="role-portal-header"><div className="wellbeing-brand"><div className="wellbeing-brand-mark"><Brain /></div><div><strong>NeuroTrace</strong><span>Secure care workspace</span></div></div><RoleSwitcher role="patient" /></div><main><span className="wellbeing-eyebrow">WELCOME TO NEUROTRACE</span><h1>Choose your care space</h1><p>Select the dashboard that matches your role. Doctor analysis remains available from the existing doctor dashboard.</p><div className="role-choice-grid"><Link to="/dashboard" className="role-choice"><Stethoscope /><strong>Doctor dashboard</strong><span>MRI analysis, segmentation, features, and progression models.</span></Link><Link to="/patient" className="role-choice"><Brain /><strong>Patient dashboard</strong><span>Memory games, daily routine, and encouraging progress.</span></Link><Link to="/caretaker" className="role-choice"><HeartHandshake /><strong>Caretaker dashboard</strong><span>Medication follow-up, safety, care team, and emergency support.</span></Link></div></main></div>;
}
