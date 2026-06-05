interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
}

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  loading,
  placeholder = "Search papers by topic, method, or keyword…",
}: SearchBarProps) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="relative w-full"
    >
      <div className="flex items-center rounded-2xl border border-slate-200 bg-white shadow-lg shadow-slate-200/50 transition-shadow focus-within:border-brand-300 focus-within:shadow-brand-100/50">
        <svg
          className="ml-5 h-5 w-5 shrink-0 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-transparent px-4 py-4 text-base outline-none placeholder:text-slate-400"
          autoFocus
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="mr-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
    </form>
  );
}
