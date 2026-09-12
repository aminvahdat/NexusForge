import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./Register.css";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

interface RegisterFormData {
  email: string;
  password: string;
  username?: string;
}

const Register: React.FC = () => {
  const [formData, setFormData] = useState<RegisterFormData>({
    email: "",
    password: "",
    username: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
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
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await axios.post(
        `${API_BASE}/auth/register`,
        {
          email: formData.email,
          password: formData.password,
          username: formData.username || formData.email.split('@')[0],
        },
        {
          timeout: 10000,
        }
      );
      
      if (response.data.access_token) {
        setSuccess("Registration successful! Please sign in.");
        // Auto-login after registration
        localStorage.setItem("token", response.data.access_token);
        setTimeout(() => navigate("/"), 1500);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h2 className="register-title">Create Account</h2>
        <p className="register-subtitle">
          Join NexusForge and start building with AI agents
        </p>
        
        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}
        
        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="register-form">
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
            <label htmlFor="username" className="label">
              Username (optional)
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username || ""}
              onChange={handleChange}
              className="input"
              placeholder="Leave blank to use email prefix"
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
              minLength={8}
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary w-full"
            disabled={loading}
          >
            {loading ? "Creating account..." : "Register"}
          </button>
          
          <div className="register-footer">
            <p className="register-footer-text">
              Already have an account?{" "}
              <a href="/login" className="register-link">
                Sign in here
              </a>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;