import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./Login.css";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

interface LoginFormData {
  email: string;
  password: string;
}

const Login: React.FC = () => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await axios.get(`${API_BASE}/auth/me`, {
          timeout: 5000,
          withCredentials: true,
        });
        if (res.data.user) {
          navigate("/");
        }
      } catch (err) {
        // Not authenticated, continue
      }
    };
    checkAuth();
  }, [navigate, API_BASE]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `${API_BASE}/auth/login`,
        formData,
        {
          timeout: 10000,
          withCredentials: true,
        }
      );
      
      if (response.data.access_token) {
        // Store token if needed, then redirect
        localStorage.setItem("token", response.data.access_token);
        navigate("/");
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Welcome to NexusForge</h2>
        <p className="login-subtitle">
          Sign in to your autonomous software development workspace
        </p>
        
        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email" className="label">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input"
              required
              autoFocus
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password" className="label">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="input"
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary w-full"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
          
          <div className="login-footer">
            <p className="login-footer-text">
              Don't have an account?{" "}
              <a href="/register" className="login-link">
                Register here
              </a>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;