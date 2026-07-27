import { useState } from "react";
import { User, Mail, Lock, Shield, Building2 } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";

const ROLE_OPTIONS = [
  { value: "STUDENT", label: "Student", hint: "Access personal dashboard" },
  { value: "TEACHER", label: "Teacher", hint: "Monitor class trends" },
  { value: "AUTHORITY", label: "Authority", hint: "View department analytics" },
];

const TEST_CREDENTIALS = [
  { role: "Student", email: "aarav.student@disha.edu" },
  { role: "Teacher", email: "rajan.teacher@disha.edu" },
  { role: "Authority", email: "nalini.authority@disha.edu" },
];

export default function Register() {
  const { register, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "STUDENT",
    department: "Computer Science",
  });
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    const dest =
      user?.role === "TEACHER"
        ? "/teacher"
        : user?.role === "AUTHORITY"
          ? "/authority"
          : "/student";
    return <Navigate to={dest} replace />;
  }

  const handleChange = (key, value) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const created = await register(form);
      toast.success("Account created");
      navigate(
        created.role === "TEACHER"
          ? "/teacher"
          : created.role === "AUTHORITY"
            ? "/authority"
            : "/student",
        { replace: true },
      );
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        position: "relative",
      }}
    >
      <div
        style={{
          position: "fixed",
          top: "15%",
          left: "10%",
          width: "400px",
          height: "400px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(99,102,241,0.08), transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "fixed",
          bottom: "15%",
          right: "10%",
          width: "300px",
          height: "300px",
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(139,92,246,0.06), transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{ width: "100%", maxWidth: "920px" }}
        className="animate-fade-in"
      >
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "18px",
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              boxShadow: "0 8px 32px rgba(99, 102, 241, 0.45)",
            }}
          >
            <User color="white" size={30} />
          </div>
          <h1
            style={{
              fontSize: "32px",
              fontWeight: "900",
              color: "#f1f5f9",
              fontFamily: "Space Grotesk, sans-serif",
              margin: "0 0 8px",
              background: "linear-gradient(135deg, #6366f1, #8b5cf6, #c084fc)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Create account
          </h1>
          <p style={{ color: "#64748b", fontSize: "14px", margin: 0 }}>
            Register to access the DISHA student risk platform.
          </p>
        </div>

        <div className="glass-card" style={{ padding: "32px" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1.15fr 0.85fr",
              gap: "24px",
              alignItems: "start",
            }}
          >
            <form
              onSubmit={handleSubmit}
              className="auth-form"
              style={{ margin: 0, gap: "14px" }}
            >
              <div className="form-group">
                <label className="form-label">Full name</label>
                <div style={{ position: "relative" }}>
                  <User
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "#64748b",
                    }}
                  />
                  <input
                    value={form.name}
                    onChange={(e) => handleChange("name", e.target.value)}
                    required
                    className="form-input"
                    placeholder=""
                    style={{ paddingLeft: "38px" }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Email</label>
                <div style={{ position: "relative" }}>
                  <Mail
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "#64748b",
                    }}
                  />
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    required
                    className="form-input"
                    placeholder=""
                    style={{ paddingLeft: "38px" }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <div style={{ position: "relative" }}>
                  <Lock
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "#64748b",
                    }}
                  />
                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) => handleChange("password", e.target.value)}
                    required
                    className="form-input"
                    placeholder="Create a secure password"
                    style={{ paddingLeft: "38px" }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Role</label>
                <div style={{ position: "relative" }}>
                  <Shield
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "#64748b",
                      pointerEvents: "none",
                    }}
                  />
                  <select
                    value={form.role}
                    onChange={(e) => handleChange("role", e.target.value)}
                    className="form-input"
                    style={{ paddingLeft: "38px", appearance: "none" }}
                  >
                    {ROLE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Department</label>
                <div style={{ position: "relative" }}>
                  <Building2
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "#64748b",
                    }}
                  />
                  <input
                    value={form.department}
                    onChange={(e) => handleChange("department", e.target.value)}
                    required
                    className="form-input"
                    placeholder="Computer Science"
                    style={{ paddingLeft: "38px" }}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
                style={{
                  width: "100%",
                  justifyContent: "center",
                  marginTop: "6px",
                }}
              >
                {loading ? "Creating…" : "Register"}
              </button>
            </form>
          </div>

          <p className="auth-foot" style={{ marginTop: "18px" }}>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
