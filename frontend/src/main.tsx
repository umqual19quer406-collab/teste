import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";        // mínimo (sem tema do Vite)
import "./styles/app.css";   // seu tema do ERP
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);