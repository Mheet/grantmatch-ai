import { useEffect, useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Sparkles, ArrowRight, Zap, Clock } from "lucide-react";

import { orgApi, matchesApi } from "../api";
import Navbar  from "../components/layout/Navbar";
import Button  from "../components/ui/Button";
import Card    from "../components/ui/Card";
import Spinner from "../components/ui/Spinner";
import Badge   from "../components/ui/Badge";
import useToast from "../hooks/useToast.jsx";

const MAX_GRANTS = 10;

export default function Dashboard() {
  const navigate = useNavigate();
  const orgId = localStorage.getItem("org_id");

  // ── Auth gate ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!orgId) navigate("/setup");
  }, [orgId, navigate]);

  // ── Fetch org ─────────────────────────────────────────────────────────
  const {
    data: org,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["org", orgId],
    queryFn: () => orgApi.get(orgId),
    enabled: !!orgId,
  });

  const { showToast, ToastComponent } = useToast();

  // ── Progress state ────────────────────────────────────────────────────
  const [progressCount, setProgressCount] = useState(0);
  const [showColdStart, setShowColdStart] = useState(false);
  const intervalRef = useRef(null);
  const coldStartRef = useRef(null);

  const startProgress = () => {
    setProgressCount(0);
    setShowColdStart(false);

    // Show cold-start warning after 8 seconds
    coldStartRef.current = setTimeout(() => setShowColdStart(true), 8000);

    // Simulate progress counter
    let count = 0;
    intervalRef.current = setInterval(() => {
      count += 1;
      if (count <= MAX_GRANTS) setProgressCount(count);
    }, 3000);
  };

  const stopProgress = () => {
    clearInterval(intervalRef.current);
    clearTimeout(coldStartRef.current);
    setShowColdStart(false);
    setProgressCount(0);
  };

  // ── Matching mutation ─────────────────────────────────────────────────
  const matching = useMutation({
    mutationFn: () => matchesApi.generate(orgId),
    onMutate: () => startProgress(),
    onSuccess: (data) => {
      stopProgress();
      showToast(
        `Matching complete! ${data.matched} matches found from ${data.processed} grants.`,
        "success"
      );
    },
    onError: () => {
      stopProgress();
      showToast("Failed to match grants. Please try again.", "error");
    },
  });

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(intervalRef.current);
      clearTimeout(coldStartRef.current);
    };
  }, []);

  // ── Loading state ─────────────────────────────────────────────────────
  if (!orgId) return null;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Card className="max-w-md text-center">
          <p className="text-navy-700 font-medium">Failed to load organization data.</p>
          <p className="text-sm text-slate-500 mt-1">Please check your connection and try again.</p>
        </Card>
      </div>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <>
    <div className="min-h-screen bg-slate-50">
      <Navbar orgName={org?.name} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-navy-900">
            Welcome back, {org?.name}
          </h1>
          <p className="mt-1 text-navy-500">
            Your AI-powered grant matching dashboard
          </p>
        </div>

        {/* Success — View Results link */}
        {matching.isSuccess && (
          <div className="mb-6 rounded-lg bg-emerald-50 border border-emerald-200 px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 text-emerald-600 flex-shrink-0" />
              <p className="text-sm font-semibold text-emerald-800">
                Matching complete — {matching.data.matched} matches found.
              </p>
            </div>
            <Link
              to="/grants"
              className="flex items-center gap-1 text-sm font-semibold text-emerald-700 hover:text-emerald-900 transition-colors"
            >
              View results <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}

        {/* AI Matching Card */}
        <Card hover>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-5 w-5 text-emerald-600" />
                <h2 className="text-lg font-semibold text-navy-900">
                  AI Grant Matching
                </h2>
                <Badge variant="new">
                  <Zap className="h-3 w-3" /> Groq-Powered
                </Badge>
              </div>
              <p className="text-sm text-navy-500 leading-relaxed">
                Our AI analyzes your mission, focus areas, and goals against
                hundreds of grant opportunities to surface the most relevant
                matches — ranked by alignment score.
              </p>
            </div>

            <div className="flex-shrink-0">
              <Button
                variant="primary"
                size="lg"
                loading={matching.isPending}
                disabled={matching.isPending}
                onClick={() => matching.mutate()}
              >
                {matching.isPending
                  ? progressCount > 0
                    ? `Analyzing grant ${progressCount} of ${MAX_GRANTS}...`
                    : "Starting AI engine..."
                  : "Run AI Matching Engine"}
              </Button>
            </div>
          </div>

          {/* Cold-start warning */}
          {matching.isPending && showColdStart && (
            <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 flex items-center gap-3">
              <Clock className="h-4 w-4 text-amber-600 flex-shrink-0" />
              <p className="text-sm text-amber-800">
                <span className="font-semibold">AI is waking up.</span>{" "}
                Free-tier hosting has a ~50 second cold start. This is a
                hosting limitation, not a bug — it'll speed up shortly.
              </p>
            </div>
          )}
        </Card>

        {/* Quick Stats */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <p className="text-sm text-slate-500">Focus Areas</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(org?.focus_areas || []).map((area) => (
                <Badge key={area}>{area}</Badge>
              ))}
              {(!org?.focus_areas || org.focus_areas.length === 0) && (
                <span className="text-sm text-slate-400">None set</span>
              )}
            </div>
          </Card>

          <Card>
            <p className="text-sm text-slate-500">Location</p>
            <p className="mt-1 text-lg font-semibold text-navy-800">
              {org?.location || "—"}
            </p>
          </Card>

          <Card>
            <p className="text-sm text-slate-500">Budget Range</p>
            <p className="mt-1 text-lg font-semibold text-navy-800">
              {org?.budget_range || "—"}
            </p>
          </Card>
        </div>
      </main>
    </div>
    {ToastComponent}
    </>
  );
}
