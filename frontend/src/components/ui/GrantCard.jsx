import { useState } from "react";
import { Calendar, DollarSign, FileText } from "lucide-react";
import { differenceInDays, parseISO } from "date-fns";

import Badge from "./Badge";
import Button from "./Button";

function scoreBadge(score) {
  const pct = Math.round(score * 100);

  let colorClass, textClass;
  if (score >= 0.8) {
    colorClass = "bg-emerald-500";
    textClass = "text-emerald-700";
  } else if (score >= 0.6) {
    colorClass = "bg-blue-500";
    textClass = "text-blue-700";
  } else {
    colorClass = "bg-slate-400";
    textClass = "text-slate-700";
  }

  return (
    <div className="flex items-center gap-2">
      <span className={`text-sm font-bold ${textClass}`}>
        {pct}% Match
      </span>
      <div className="bg-slate-100 rounded-full h-2 w-24 overflow-hidden">
        <div
          className={`h-2 rounded-full ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function deadlineBadge(deadline) {
  if (!deadline) {
    return <Badge variant="default">Rolling Deadline</Badge>;
  }

  const deadlineDate =
    typeof deadline === "string" ? parseISO(deadline) : deadline;
  const daysLeft = differenceInDays(deadlineDate, new Date());

  let color, label;
  if (daysLeft < 0) {
    color = "bg-slate-100 text-slate-500 border-slate-200";
    label = "Expired";
  } else if (daysLeft <= 7) {
    color = "bg-red-100 text-red-800 border-red-200";
    label = `${daysLeft}d left`;
  } else if (daysLeft <= 30) {
    color = "bg-amber-100 text-amber-800 border-amber-200";
    label = `${daysLeft}d left`;
  } else {
    color = "bg-emerald-100 text-emerald-800 border-emerald-200";
    label = `${daysLeft}d left`;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full border ${color}`}
    >
      <Calendar className="h-3 w-3" />
      {label}
    </span>
  );
}

function formatCurrency(amount) {
  if (amount == null) return null;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function GrantCard({ match, onGenerateLOI, isGenerating }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const grant = match.grant || {};
  const score = match.match_score ?? 0;

  const cleanReasoning = match.match_reasoning
    ? match.match_reasoning.replace(/Action:\s*.*$/i, '').trim()
    : "";

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300 transition-shadow duration-200 p-5 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-3">
        {scoreBadge(score)}
        {deadlineBadge(grant.deadline)}
      </div>

      {/* Body */}
      <h3 className="text-base font-bold text-navy-900 leading-snug">
        {grant.title || "Untitled Grant"}
      </h3>
      <p className="text-sm text-slate-500 mt-0.5">{grant.funder}</p>

      {cleanReasoning && (
        <div className="mt-2">
          <p className={`text-sm text-slate-600 leading-relaxed ${isExpanded ? "" : "line-clamp-2"}`}>
            {cleanReasoning}
          </p>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-emerald-600 hover:text-emerald-700 cursor-pointer font-medium mt-1 block"
          >
            {isExpanded ? "Read less" : "Read more"}
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-sm font-semibold text-navy-700">
          <DollarSign className="h-4 w-4 text-slate-400" />
          {formatCurrency(grant.max_amount) || (
            <span className="text-slate-400 font-normal">Amount TBD</span>
          )}
        </div>

        <Button
          variant="primary"
          size="sm"
          loading={isGenerating}
          disabled={isGenerating}
          onClick={() => onGenerateLOI(match.id)}
        >
          <FileText className="h-3.5 w-3.5" />
          {isGenerating ? "Drafting..." : "Draft LOI"}
        </Button>
      </div>
    </div>
  );
}
