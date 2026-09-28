"use client";

import { useCallback, useEffect, useState } from "react";
import AnalyzeForm from "@/components/AnalyzeForm";
import ResultView from "@/components/ResultView";
import HistoryList from "@/components/HistoryList";
import { fetchRecentAnalyses } from "@/lib/api";
import type { AnalysisResult } from "@/lib/api";

export default function HomePage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const data = await fetchRecentAnalyses();
      setHistory(data);
    } catch (err) {
      setHistoryError(
        err instanceof Error ? err.message : "Could not load history."
      );
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  function handleResult(newResult: AnalysisResult) {
    setResult(newResult);
    loadHistory();
  }

  return (
    <main className="page">
      <h1>SEO Analyzer</h1>
      <p className="subtitle">
        Paste a URL to check its title, meta description, headings, and word count.
      </p>

      <AnalyzeForm onResult={handleResult} />

      {result && <ResultView result={result} />}

      <HistoryList analyses={history} loading={historyLoading} error={historyError} />
    </main>
  );
}
