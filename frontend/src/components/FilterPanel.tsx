import type { SearchFilters } from "../types";

interface FilterPanelProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

export default function FilterPanel({ filters, onChange }: FilterPanelProps) {
  return (
    <aside className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="text-sm font-semibold text-slate-900">Filters</h2>
      <div className="mt-4 space-y-4">
        <div>
          <label className="block text-xs font-medium text-muted">Year from</label>
          <input
            type="number"
            min={1900}
            max={2100}
            value={filters.year_min ?? ""}
            onChange={(e) =>
              onChange({
                ...filters,
                year_min: e.target.value ? Number(e.target.value) : null,
              })
            }
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400"
            placeholder="e.g. 2015"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted">Year to</label>
          <input
            type="number"
            min={1900}
            max={2100}
            value={filters.year_max ?? ""}
            onChange={(e) =>
              onChange({
                ...filters,
                year_max: e.target.value ? Number(e.target.value) : null,
              })
            }
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400"
            placeholder="e.g. 2024"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted">Venue</label>
          <input
            type="text"
            value={filters.venue ?? ""}
            onChange={(e) =>
              onChange({ ...filters, venue: e.target.value || null })
            }
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400"
            placeholder="e.g. NeurIPS"
          />
        </div>
      </div>
    </aside>
  );
}
