import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { AlertCircle, Sparkles, ArrowRight } from "lucide-react";

import { orgApi, matchesApi, loiApi } from "../api";
import Navbar    from "../components/layout/Navbar";
import Button    from "../components/ui/Button";
import Card      from "../components/ui/Card";
import Spinner   from "../components/ui/Spinner";
import GrantCard from "../components/ui/GrantCard";

export default function GrantsList() {
  const navigate = useNavigate();
  const orgId = localStorage.getItem("org_id");

  const [currentMatchId, setCurrentMatchId] = useState(null);

  // ── Auth gate ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!orgId) navigate("/setup");
  }, [orgId, navigate]);

  // ── Fetch org (for Navbar) ────────────────────────────────────────────
  const { data: org } = useQuery({
    queryKey: ["org", orgId],
    queryFn: () => orgApi.get(orgId),
    enabled: !!orgId,
  });

  // ── Fetch matches ─────────────────────────────────────────────────────
  const {
    data: matches,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["matches", orgId],
    queryFn: () => matchesApi.list(orgId),
    enabled: !!orgId,
  });

  // ── LOI mutation ──────────────────────────────────────────────────────
  const loiMutation = useMutation({
    mutationFn: (matchId) => loiApi.generate(matchId),
    onSuccess: () => {
      navigate(`/loi/${currentMatchId}`);
    },
    onError: () => {
      setCurrentMatchId(null);
    },
  });

  const handleGenerateLOI = (matchId) => {
    setCurrentMatchId(matchId);
    loiMutation.mutate(matchId);
  };

  // ── Guards ────────────────────────────────────────────────────────────
  if (!orgId) return null;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar orgName={org?.name} />
        <div className="flex items-center justify-center py-32">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar orgName={org?.name} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Error banner (LOI generation failure) */}
        {loiMutation.isError && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 px-5 py-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-800">
                LOI generation failed
              </p>
              <p className="text-sm text-red-700">
                {loiMutation.error?.response?.data?.detail ||
                  "An unexpected error occurred. Please try again."}
              </p>
            </div>
          </div>
        )}

        {/* Data fetch error */}
        {isError && (
          <Card className="text-center py-12">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-3" />
            <p className="text-navy-700 font-medium">
              Failed to load matches.
            </p>
            <p className="text-sm text-slate-500 mt-1">
              Please check your connection and try again.
            </p>
          </Card>
        )}

        {/* Empty state */}
        {!isError && matches?.length === 0 && (
          <div className="flex flex-col items-center justify-center text-center py-24 px-4 bg-gradient-to-br from-emerald-50 to-white rounded-2xl border border-emerald-100 mt-8">
            <div className="bg-white shadow-sm p-6 rounded-full mb-6">
              <Sparkles className="w-12 h-12 text-emerald-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              No Grant Matches Yet
            </h2>
            <p className="text-slate-500 max-w-md mx-auto mb-8 leading-relaxed">
              Run the AI matching engine to discover grants tailored to your
              mission.
            </p>
            <Button
              variant="primary"
              onClick={() => navigate("/dashboard")}
            >
              Go to Dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Match feed */}
        {!isError && matches?.length > 0 && (
          <>
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-bold text-navy-900">
                Your Matched Grants
              </h1>
              <p className="mt-1 text-navy-500">
                {matches.length} grant{matches.length !== 1 ? "s" : ""} matched
                to your mission
              </p>
            </div>

            <div className="space-y-4">
              {matches.map((match) => (
                <GrantCard
                  key={match.id}
                  match={match}
                  onGenerateLOI={handleGenerateLOI}
                  isGenerating={
                    loiMutation.isPending && currentMatchId === match.id
                  }
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
