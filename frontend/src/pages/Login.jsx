import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const { login, isAuthenticated, user } = useAuth();
  const [email, setEmail] = useState('aarav.student@disha.edu');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    const dest = user?.role === 'TEACHER' ? '/teacher' : user?.role === 'AUTHORITY' ? '/authority' : '/student';
    return <Navigate to={dest} replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const loggedIn = await login(email, password);
      toast.success(`Welcome back, ${loggedIn.name}`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card glass-panel">
        <p className="eyebrow">DISHA Platform</p>
        <h1>Sign in</h1>
        <p className="subtitle">Data-Driven Student Intervention & Academic Performance</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="auth-foot">
          Demo seed password: <code>password123</code>
        </p>
        <p className="auth-foot">
          No account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
