import { CheckCircle, AlertCircle, Info, X } from "lucide-react";

const ICONS = {
  success: <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0" />,
  error:   <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />,
  info:    <Info className="h-5 w-5 text-blue-500 flex-shrink-0" />,
};

const BORDER_COLORS = {
  success: "border-emerald-200",
  error:   "border-red-200",
  info:    "border-blue-200",
};

export default function Toast({ message, type = "info", onClose }) {
  if (!message) return null;

  return (
    <div className="fixed top-6 right-6 z-50 animate-slide-in">
      <div
        className={`bg-white shadow-lg border ${BORDER_COLORS[type] || BORDER_COLORS.info} rounded-lg p-4 flex items-center gap-3 max-w-md`}
      >
        {ICONS[type] || ICONS.info}
        <p className="text-sm text-slate-700 flex-1">{message}</p>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
