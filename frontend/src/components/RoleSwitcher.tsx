import { useNavigate } from "react-router-dom";

type Role = "doctor" | "patient" | "caretaker";

export default function RoleSwitcher({ role }: { role: Role }) {
  const navigate = useNavigate();

  return (
    <label className="role-switcher">
      <span>View as</span>
      <select value={role} onChange={(event) => navigate(event.target.value === "doctor" ? "/dashboard" : `/${event.target.value}`)}>
        <option value="doctor">Doctor dashboard</option>
        <option value="patient">Patient dashboard</option>
        <option value="caretaker">Caretaker dashboard</option>
      </select>
    </label>
  );
}
