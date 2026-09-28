import type { AnalysisResult } from "@/lib/api";

export default function ResultView({ result }: { result: AnalysisResult }) {
  return (
    <section className="result-card">
      <h2>Results for {result.url}</h2>
      <dl>
        <dt>Title</dt>
        <dd>{result.title ?? <em>Not found</em>}</dd>

        <dt>Meta description</dt>
        <dd>{result.meta_description ?? <em>Not found</em>}</dd>

        <dt>Word count</dt>
        <dd>{result.word_count}</dd>
      </dl>

      <div className="heading-lists">
        <div>
          <h3>H1 ({result.h1.length})</h3>
          {result.h1.length ? (
            <ul>
              {result.h1.map((heading, index) => (
                <li key={index}>{heading}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">None found</p>
          )}
        </div>
        <div>
          <h3>H2 ({result.h2.length})</h3>
          {result.h2.length ? (
            <ul>
              {result.h2.map((heading, index) => (
                <li key={index}>{heading}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">None found</p>
          )}
        </div>
      </div>
    </section>
  );
}
