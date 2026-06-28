import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const publicNav = [
  { to: "/", label: "Search" },
  { to: "/explore", label: "Explore" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const { user, isAdmin, logout } = useAuth();

  const nav = [
    ...publicNav,
    ...(user ? [{ to: "/saved", label: "Saved" }] : []),
    ...(isAdmin ? [{ to: "/import", label: "Import" }] : []),
  ];

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

          <div className="flex items-center gap-3">
            <nav className="flex items-center gap-1">
              {nav.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                    pathname === to || (to !== "/" && pathname.startsWith(`${to}/`))
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {label}
                </Link>
              ))}
            </nav>

            <div className="hidden h-6 w-px bg-slate-200 sm:block" />

            {user ? (
              <div className="flex items-center gap-2">
                <span className="hidden max-w-[10rem] truncate text-sm text-muted sm:inline">
                  {user.email}
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-muted">
        Citexis powered by Hybrid Search
      </footer>
    </div>
  );
}
