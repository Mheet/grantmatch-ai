import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { orgApi } from "../api";
import Button  from "../components/ui/Button";
import Card    from "../components/ui/Card";

const FOCUS_OPTIONS = [
  "Education",
  "Health",
  "Environment",
  "Housing",
  "Advocacy",
  "Youth",
  "Research",
  "Arts",
];

const BUDGET_OPTIONS = [
  { value: "",               label: "Select budget range" },
  { value: "Under $100k",    label: "Under $100k" },
  { value: "$100k–$500k",    label: "$100k – $500k" },
  { value: "$500k–$2M",      label: "$500k – $2M" },
  { value: "Over $2M",       label: "Over $2M" },
];

export default function Onboarding() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    mission: "",
    location: "",
    budget_range: "",
    focus_areas: [],
  });

  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  // ── helpers ─────────────────────────────────────────────────────────────
  const update = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const toggleFocus = (area) =>
    setForm((prev) => ({
      ...prev,
      focus_areas: prev.focus_areas.includes(area)
        ? prev.focus_areas.filter((a) => a !== area)
        : [...prev.focus_areas, area],
    }));

  // ── submit ──────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await orgApi.create({
        ...form,
        focus_areas: form.focus_areas.length > 0 ? form.focus_areas : null,
        budget_range: form.budget_range || null,
        location: form.location || null,
      });
      localStorage.setItem("org_id", data.id);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // ── render ──────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        {/* Brand header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-navy-900 tracking-tight">
            Grant<span className="text-emerald-600">Match</span> AI
          </h1>
          <p className="mt-2 text-navy-500">
            Set up your organization profile to start finding grants
          </p>
        </div>

        <Card>
          <Card.Header>
            <Card.Title>Organization Profile</Card.Title>
            <Card.Description>
              Tell us about your nonprofit so our AI can find the best-fit
              grants for your mission.
            </Card.Description>
          </Card.Header>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Organization Name */}
            <div>
              <label
                htmlFor="org-name"
                className="block text-sm font-medium text-navy-700 mb-1"
              >
                Organization Name <span className="text-red-500">*</span>
              </label>
              <input
                id="org-name"
                type="text"
                required
                value={form.name}
                onChange={update("name")}
                placeholder="e.g. Code the Future"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm
                           text-navy-900 placeholder-slate-400
                           focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                           transition-colors"
              />
            </div>

            {/* Mission Statement */}
            <div>
              <label
                htmlFor="mission"
                className="block text-sm font-medium text-navy-700 mb-1"
              >
                Mission Statement <span className="text-red-500">*</span>
              </label>
              <textarea
                id="mission"
                required
                rows={4}
                value={form.mission}
                onChange={update("mission")}
                placeholder="Describe your organization's mission and goals..."
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm
                           text-navy-900 placeholder-slate-400 resize-none
                           focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                           transition-colors"
              />
            </div>

            {/* Location */}
            <div>
              <label
                htmlFor="location"
                className="block text-sm font-medium text-navy-700 mb-1"
              >
                Location
              </label>
              <input
                id="location"
                type="text"
                value={form.location}
                onChange={update("location")}
                placeholder="e.g. New York, NY"
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm
                           text-navy-900 placeholder-slate-400
                           focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                           transition-colors"
              />
            </div>

            {/* Budget Range */}
            <div>
              <label
                htmlFor="budget"
                className="block text-sm font-medium text-navy-700 mb-1"
              >
                Annual Budget Range
              </label>
              <select
                id="budget"
                value={form.budget_range}
                onChange={update("budget_range")}
                className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm
                           text-navy-900
                           focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
                           transition-colors"
              >
                {BUDGET_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Focus Areas — Toggle Tags */}
            <div>
              <label className="block text-sm font-medium text-navy-700 mb-2">
                Focus Areas
              </label>
              <div className="flex flex-wrap gap-2">
                {FOCUS_OPTIONS.map((area) => {
                  const selected = form.focus_areas.includes(area);
                  return (
                    <button
                      key={area}
                      type="button"
                      onClick={() => toggleFocus(area)}
                      className={`
                        px-3.5 py-1.5 rounded-full text-sm font-medium
                        border transition-all duration-150
                        ${
                          selected
                            ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                            : "bg-white text-navy-600 border-slate-300 hover:border-emerald-400 hover:text-emerald-700"
                        }
                      `}
                    >
                      {area}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Error message */}
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
              {loading ? "Creating profile..." : "Get Started"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
