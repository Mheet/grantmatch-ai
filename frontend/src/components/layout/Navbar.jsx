import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { User, LogOut } from "lucide-react";
import { signOut } from "../../supabase";

export default function Navbar({ orgName }) {
  const navigate = useNavigate();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const handleLogout = async () => {
    await signOut();
    localStorage.removeItem("org_id");
    navigate("/auth");
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav className="sticky top-0 z-30 w-full bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left — Brand */}
          <a href="/dashboard" className="flex items-center gap-2 group">
            <span className="text-xl font-extrabold tracking-tight text-navy-900">
              Grant<span className="text-emerald-600">Match</span>{" "}
              <span className="font-medium text-navy-400">AI</span>
            </span>
          </a>

          {/* Right — Org + Avatar Dropdown */}
          {orgName && (
            <div className="relative flex items-center gap-3" ref={dropdownRef}>
              <span className="hidden sm:inline text-sm font-medium text-navy-600 truncate max-w-[150px]">
                {orgName}
              </span>

              {/* Avatar */}
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center justify-center h-9 w-9 rounded-full bg-emerald-100 text-emerald-700 hover:bg-emerald-200 transition-colors cursor-pointer"
              >
                <User className="h-4 w-4" />
              </button>

              {/* Dropdown */}
              {isDropdownOpen && (
                <div className="absolute right-0 top-12 w-56 bg-white rounded-lg border border-slate-200 shadow-lg py-2 z-50">
                  <div className="px-4 py-2">
                    <p className="text-sm font-bold text-navy-900 truncate">
                      {orgName}
                    </p>
                  </div>
                  <div className="border-t border-slate-100 my-1" />
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
