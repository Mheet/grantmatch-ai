const colorMap = {
  // Match score ranges
  high:    "bg-emerald-100 text-emerald-800 border-emerald-200",
  medium:  "bg-amber-100 text-amber-800 border-amber-200",
  low:     "bg-red-100 text-red-800 border-red-200",
  // Status variants
  new:     "bg-blue-100 text-blue-800 border-blue-200",
  active:  "bg-emerald-100 text-emerald-800 border-emerald-200",
  default: "bg-slate-100 text-slate-700 border-slate-200",
};

/**
 * Automatically pick a color based on a match score (0–1).
 */
function scoreVariant(score) {
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "medium";
  return "low";
}

export default function Badge({
  children,
  variant = "default",
  score,
  className = "",
}) {
  const resolvedVariant = score !== undefined ? scoreVariant(score) : variant;

  return (
    <span
      className={`
        inline-flex items-center
        px-2.5 py-0.5
        text-xs font-medium
        rounded-full border
        ${colorMap[resolvedVariant] || colorMap.default}
        ${className}
      `}
    >
      {children}
    </span>
  );
}
