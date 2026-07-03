import React from "react";
import { NavLink } from "react-router-dom";
import { GaugeCircle, Shield, User } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        <span className="brand-mark">
          <GaugeCircle size={18} />
        </span>
        Skill Gap Analyzer
      </NavLink>
      <div className="navbar-links">
        <NavLink
          to="/admin"
          className={({ isActive }) =>
            "navbar-link" + (isActive ? " active" : "")
          }
        >
          <Shield size={15} />
          Admin
        </NavLink>
        <NavLink
          to="/employee"
          className={({ isActive }) =>
            "navbar-link" + (isActive ? " active" : "")
          }
        >
          <User size={15} />
          Employee
        </NavLink>
      </div>
    </nav>
  );
}
