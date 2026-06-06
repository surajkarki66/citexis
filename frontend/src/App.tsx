import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import AuthorPage from "./pages/AuthorPage";
import ExplorePage from "./pages/ExplorePage";
import HomePage from "./pages/HomePage";
import ImportPage from "./pages/ImportPage";
import PaperPage from "./pages/PaperPage";
import RelatedPapersPage from "./pages/RelatedPapersPage";
import SavedPage from "./pages/SavedPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/papers/:id" element={<PaperPage />} />
        <Route path="/papers/:id/related" element={<RelatedPapersPage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route path="/saved" element={<SavedPage />} />
        <Route path="/import" element={<ImportPage />} />
        <Route path="/authors/:name" element={<AuthorPage />} />
      </Routes>
    </Layout>
  );
}
