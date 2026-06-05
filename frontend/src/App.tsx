import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import AuthorPage from "./pages/AuthorPage";
import ExplorePage from "./pages/ExplorePage";
import HomePage from "./pages/HomePage";
import PaperPage from "./pages/PaperPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/papers/:id" element={<PaperPage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route path="/authors/:name" element={<AuthorPage />} />
      </Routes>
    </Layout>
  );
}
