"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { analyzeUrl } from "@/lib/api";
import type { AnalysisResult } from "@/lib/api";

interface AnalyzeFormProps {
  onResult: (result: AnalysisResult) => void;
}

export default function AnalyzeForm({ onResult }: AnalyzeFormProps) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await analyzeUrl(url.trim());
      onResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="analyze-form">
      <label htmlFor="url-input">Page URL</label>
      <div className="analyze-form-row">
        <input
          id="url-input"
          type="url"
          required
          placeholder="https://example.com"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || url.trim() === ""}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>
      {error && (
        <p role="alert" className="error-message">
          {error}
        </p>
      )}
    </form>
  );
}
