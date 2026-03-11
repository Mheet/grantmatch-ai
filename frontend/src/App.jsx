import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { supabase } from "./supabase";
import Spinner from "./components/ui/Spinner";

import Auth       from "./pages/Auth";
import Onboarding from "./pages/Onboarding";
import Dashboard  from "./pages/Dashboard";
import GrantsList from "./pages/GrantsList";
import LoiView    from "./pages/LoiView";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2, // 2 minutes
    },
  },
});

// ── Protected Route wrapper ─────────────────────────────────────────────────
function ProtectedRoute({ children }) {
  const [checking, setChecking] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setAuthenticated(!!data?.session);
      setChecking(false);
    });
  }, []);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/auth" replace />;
  }

  return children;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/"          element={<Navigate to="/auth" replace />} />
          <Route path="/auth"      element={<Auth />} />
          <Route path="/setup"     element={<Onboarding />} />
          <Route
            path="/dashboard"
            element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
          />
          <Route
            path="/grants"
            element={<ProtectedRoute><GrantsList /></ProtectedRoute>}
          />
          <Route
            path="/loi/:id"
            element={<ProtectedRoute><LoiView /></ProtectedRoute>}
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
