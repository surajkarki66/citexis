import { Link, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "Search" },
  { to: "/explore", label: "Explore" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-900 text-white text-sm font-bold">
              C
            </div>
            <span className="font-serif text-xl text-brand-900 group-hover:text-brand-600 transition-colors">
              Citexis
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {nav.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                  pathname === to
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-muted">
        Hybrid search powered by Elasticsearch + Pinecone
      </footer>
    </div>
  );
}
