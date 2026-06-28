import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthorPage from "./pages/AuthorPage";
import ExplorePage from "./pages/ExplorePage";
import HomePage from "./pages/HomePage";
import ImportPage from "./pages/ImportPage";
import LoginPage from "./pages/LoginPage";
import PaperPage from "./pages/PaperPage";
import RegisterPage from "./pages/RegisterPage";
import RelatedPapersPage from "./pages/RelatedPapersPage";
import SavedPage from "./pages/SavedPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/papers/:id" element={<PaperPage />} />
        <Route path="/papers/:id/related" element={<RelatedPapersPage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route
          path="/saved"
          element={
            <ProtectedRoute>
              <SavedPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/import"
          element={
            <ProtectedRoute adminOnly>
              <ImportPage />
            </ProtectedRoute>
          }
        />
        <Route path="/authors/:name" element={<AuthorPage />} />
      </Routes>
    </Layout>
  );
}
