import type { AnalysisResult } from "@/lib/api";

interface HistoryListProps {
  analyses: AnalysisResult[];
  loading: boolean;
  error: string | null;
}

export default function HistoryList({ analyses, loading, error }: HistoryListProps) {
  return (
    <section className="history">
      <h2>Last analyses</h2>
      {loading && <p className="muted">Loading history...</p>}
      {error && (
        <p role="alert" className="error-message">
          {error}
        </p>
      )}
      {!loading && !error && analyses.length === 0 && (
        <p className="muted">No analyses yet.</p>
      )}
      {!loading && !error && analyses.length > 0 && (
        <ul className="history-list">
          {analyses.map((item) => (
            <li key={item.id ?? item.url}>
              <span className="history-url">{item.url}</span>
              <span className="history-title">{item.title ?? "No title"}</span>
              {item.analyzed_at && (
                <span className="history-date">
                  {new Date(item.analyzed_at).toLocaleString()}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
