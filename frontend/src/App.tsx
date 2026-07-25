import { Container } from "@mui/material";
import { Navigate, Route, Routes } from "react-router-dom";
import AppHeader from "./components/AppHeader";
import EngagementListPage from "./pages/EngagementListPage";
import ExpertApplicationPage from "./pages/ExpertApplicationPage";
import ImportPage from "./pages/ImportPage";

export default function App() {
  return (
    <>
      <AppHeader />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/engagements" replace />} />
          <Route path="/engagements" element={<EngagementListPage />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/expert-application" element={<ExpertApplicationPage />} />
        </Routes>
      </Container>
    </>
  );
}
