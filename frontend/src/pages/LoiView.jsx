import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Copy, Check, ExternalLink } from "lucide-react";

import { orgApi, matchesApi } from "../api";
import Navbar  from "../components/layout/Navbar";
import Button  from "../components/ui/Button";
import Card    from "../components/ui/Card";
import Badge   from "../components/ui/Badge";
import Spinner from "../components/ui/Spinner";

export default function LoiView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const orgId = localStorage.getItem("org_id");

  const [copied, setCopied] = useState(false);

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

  // ── Fetch matches, then find this one ─────────────────────────────────
  const { data: matches, isLoading } = useQuery({
    queryKey: ["matches", orgId],
    queryFn: () => matchesApi.list(orgId),
    enabled: !!orgId,
  });

  const match = matches?.find((m) => m.id === id);
  const loiText = match?.generated_loi;
  const grant = match?.grant || {};

  // ── Copy handler ──────────────────────────────────────────────────────
  const handleCopy = async () => {
    if (!loiText) return;
    await navigator.clipboard.writeText(loiText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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

  if (!match || !loiText) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar orgName={org?.name} />
        <div className="max-w-4xl mx-auto px-4 py-16 flex items-center justify-center">
          <Card className="text-center py-12 max-w-md">
            <p className="text-navy-700 font-medium">
              LOI not generated yet.
            </p>
            <p className="text-sm text-slate-500 mt-1 mb-5">
              Go back to your matched grants and click "Draft LOI" to generate
              a letter.
            </p>
            <Button variant="primary" onClick={() => navigate("/grants")}>
              Back to Grants
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar orgName={org?.name} />

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header row */}
        <div className="flex items-center justify-between mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/grants")}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Matches
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={handleCopy}
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy Letter
                </>
              )}
            </Button>

            {grant.source_url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(grant.source_url, "_blank")}
              >
                <ExternalLink className="h-4 w-4" />
                View Grant Source
              </Button>
            )}
          </div>
        </div>

        {/* Grant info bar */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <Badge variant="active">{grant.funder || "Unknown Funder"}</Badge>
          <span className="text-sm font-medium text-navy-700">
            {grant.title || "Untitled Grant"}
          </span>
        </div>

        {/* Document Card */}
        <Card padding="p-8 sm:p-12" className="mt-6">
          <div className="whitespace-pre-wrap font-sans text-slate-800 leading-relaxed text-base">
            {loiText}
          </div>
        </Card>
      </div>
    </div>
  );
}
