import { useState, useCallback, useRef } from "react";
import Toast from "../components/ui/Toast";

export default function useToast() {
  const [toast, setToast] = useState({ isOpen: false, message: "", type: "info" });
  const timeoutRef = useRef(null);

  const showToast = useCallback((message, type = "info") => {
    // Clear any existing timeout
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    setToast({ isOpen: true, message, type });

    timeoutRef.current = setTimeout(() => {
      setToast((prev) => ({ ...prev, isOpen: false }));
    }, 4000);
  }, []);

  const closeToast = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setToast((prev) => ({ ...prev, isOpen: false }));
  }, []);

  const ToastComponent = toast.isOpen ? (
    <Toast message={toast.message} type={toast.type} onClose={closeToast} />
  ) : null;

  return { showToast, ToastComponent };
}
