import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, ArrowRight } from "lucide-react";

import { orgApi, matchesApi, loiApi } from "../api";
import Navbar    from "../components/layout/Navbar";
import Button    from "../components/ui/Button";
import Card      from "../components/ui/Card";
import Spinner   from "../components/ui/Spinner";
import GrantCard from "../components/ui/GrantCard";
import useToast  from "../hooks/useToast.jsx";

export default function GrantsList() {
  const navigate = useNavigate();
  const orgId = localStorage.getItem("org_id");
  const queryClient = useQueryClient();

  const [currentMatchId, setCurrentMatchId] = useState(null);
  const { showToast, ToastComponent } = useToast();

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
    onSuccess: (_data, matchId) => {
      // Invalidate cache so LoiView fetches fresh data with generated_loi
      queryClient.invalidateQueries({ queryKey: ["matches", orgId] });
      navigate(`/loi/${matchId}`);
    },
    onError: () => {
      setCurrentMatchId(null);
      showToast("Failed to draft LOI. Please try again.", "error");
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
    <>
    <div className="min-h-screen bg-slate-50">
      <Navbar orgName={org?.name} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">


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

        {/* Smart empty state — explains why 0 matches */}
        {!isError && matches?.length === 0 && (
          <div className="flex flex-col items-center justify-center text-center py-24 px-4 bg-gradient-to-br from-emerald-50 to-white rounded-2xl border border-emerald-100 mt-8">
            <div className="bg-white shadow-sm p-6 rounded-full mb-6">
              <Sparkles className="w-12 h-12 text-emerald-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              No Grant Matches Yet
            </h2>
            <p className="text-slate-500 max-w-lg mx-auto mb-3 leading-relaxed">
              The AI couldn't find strong matches above the 60% alignment
              threshold. This usually means your profile needs more detail.
            </p>
            <div className="text-sm text-slate-400 max-w-md mx-auto mb-8 space-y-1">
              <p>💡 Try adding more <strong>focus areas</strong> to your profile</p>
              <p>💡 Make your <strong>mission statement</strong> more specific</p>
              <p>💡 Run matching again after new grants are scraped</p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                onClick={() => navigate("/dashboard")}
              >
                Go to Dashboard
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate("/setup")}
              >
                Edit Profile
              </Button>
            </div>
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
    {ToastComponent}
    </>
  );
}
