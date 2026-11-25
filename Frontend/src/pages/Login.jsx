
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { signInWithGoogle } = useAuth();
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [error, setError] = useState("");

  async function handleGoogleLogin() {
    setIsSigningIn(true);
    setError("");

    const { error } = await signInWithGoogle();

    if (error) {
      setError(error.message);
      setIsSigningIn(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#0f172a",
      color: "#ffffff",
      fontFamily: "Arial, sans-serif",
      padding: "20px"
    }}>
      <div style={{
        width: "100%",
        maxWidth: "420px",
        padding: "40px",
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: "16px",
        textAlign: "center"
      }}>
        <h1 style={{ marginBottom: "10px" }}>
          FinResearch AI
        </h1>

        <p style={{ color: "#94a3b8", marginBottom: "30px" }}>
          Sign in to access your research workspace.
        </p>

        <button
          onClick={handleGoogleLogin}
          disabled={isSigningIn}
          style={{
            width: "100%",
            padding: "14px",
            borderRadius: "8px",
            border: "none",
            background: "#ffffff",
            color: "#1e293b",
            fontSize: "15px",
            fontWeight: "600",
            cursor: isSigningIn ? "not-allowed" : "pointer",
            opacity: isSigningIn ? 0.7 : 1
          }}
        >
          {isSigningIn ? "Redirecting..." : "Continue with Google"}
        </button>

        {error && (
          <p style={{ color: "#f87171", marginTop: "16px" }}>
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
