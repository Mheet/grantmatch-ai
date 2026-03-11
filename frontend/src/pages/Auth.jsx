import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signUp, signIn } from "../supabase";
import { orgApi } from "../api";
import Button from "../components/ui/Button";
import Card   from "../components/ui/Card";

export default function Auth() {
  const navigate = useNavigate();

  const [mode, setMode]       = useState("signin"); // "signin" | "signup"
  const [email, setEmail]     = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "signup") {
        // ── Sign Up ───────────────────────────────────────────────────
        const { data, error: authError } = await signUp(email, password);
        if (authError) throw authError;

        // User created — send them to onboarding to create their org
        navigate("/setup");
      } else {
        // ── Sign In ───────────────────────────────────────────────────
        const { data, error: authError } = await signIn(email, password);
        if (authError) throw authError;

        // Try to fetch existing org for this user
        try {
          const org = await orgApi.getMe();
          localStorage.setItem("org_id", org.id);
          navigate("/dashboard");
        } catch {
          // No org yet — send to onboarding
          navigate("/setup");
        }
      }
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const isSignUp = mode === "signup";

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Brand header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight">
            Grant<span className="text-emerald-600">Match</span> AI
          </h1>
          <p className="mt-2 text-navy-500">
            {isSignUp
              ? "Create your account to get started"
              : "Sign in to your account"}
          </p>
        </div>

        <Card>
          <Card.Header>
            <Card.Title>{isSignUp ? "Sign Up" : "Sign In"}</Card.Title>
            <Card.Description>
              {isSignUp
                ? "Enter your email and choose a password"
                : "Welcome back — enter your credentials"}
            </Card.Description>
          </Card.Header>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label
                htmlFor="auth-email"
                className="block text-sm font-medium text-navy-700 mb-1"
              >
                Email <span className="text-red-500">*</span>
              </label>
              <input
                id="auth-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@organization.org"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm
                           text-navy-900 placeholder-slate-400
                           focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                           transition-colors"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="auth-password"
                className="block text-sm font-medium text-navy-700 mb-1"
              >
                Password <span className="text-red-500">*</span>
              </label>
              <input
                id="auth-password"
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm
                           text-navy-900 placeholder-slate-400
                           focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                           transition-colors"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full"
            >
              {loading
                ? isSignUp ? "Creating account..." : "Signing in..."
                : isSignUp ? "Create Account" : "Sign In"}
            </Button>
          </form>

          {/* Toggle */}
          <p className="text-sm text-center text-slate-500 mt-5">
            {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              onClick={() => { setMode(isSignUp ? "signin" : "signup"); setError(null); }}
              className="text-emerald-600 hover:text-emerald-700 font-medium cursor-pointer"
            >
              {isSignUp ? "Sign In" : "Sign Up"}
            </button>
          </p>
        </Card>
      </div>
    </div>
  );
}
