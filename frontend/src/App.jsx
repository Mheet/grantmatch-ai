import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

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

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/"          element={<Onboarding />} />
          <Route path="/setup"     element={<Onboarding />} />
          <Route path="/dashboard" element={<Dashboard />}  />
          <Route path="/grants"    element={<GrantsList />}  />
          <Route path="/loi/:id"   element={<LoiView />}     />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
