import { useMemo, useState } from "react";
import type { RecapResponse } from "./types";
import { generateRecap } from "./api";

const todayIso = new Date().toISOString().slice(0, 10);

export default function App() {
  const [repo, setRepo] = useState("owner/repo");
  const [since, setSince] = useState("2025-12-01");
  const [until, setUntil] = useState(todayIso);
  const [githubToken, setGithubToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recap, setRecap] = useState<RecapResponse | null>(null);

  const subtitle = useMemo(() => {
    if (!recap) {
      return "Turn your GitHub trail into a clean, shareable recap.";
    }
    return `${recap.metrics.prCount} PRs, ${recap.metrics.commitCount} commits, ${recap.metrics.noteCount} notes.`;
  }, [recap]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = githubToken.trim();
      const data = await generateRecap({
        repo,
        since,
        until,
        githubToken: token ? token : undefined
      });
      setRecap(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-text">
          <p className="eyebrow">AI Project Recap Storyboard</p>
          <h1>Turn project history into a narrative you can ship.</h1>
          <p className="subtitle">{subtitle}</p>
        </div>
        <div className="hero-card">
          <form onSubmit={onSubmit} className="form-grid">
            <label className="field">
              <span>Repository</span>
              <input
                value={repo}
                onChange={(event) => setRepo(event.target.value)}
                placeholder="owner/repo"
              />
            </label>
            <label className="field">
              <span>Since</span>
              <input
                type="date"
                value={since}
                onChange={(event) => setSince(event.target.value)}
              />
            </label>
            <label className="field">
              <span>Until</span>
              <input
                type="date"
                value={until}
                onChange={(event) => setUntil(event.target.value)}
              />
            </label>
            <label className="field">
              <span>GitHub PAT (optional)</span>
              <input
                type="password"
                value={githubToken}
                onChange={(event) => setGithubToken(event.target.value)}
                placeholder="ghp_..."
                autoComplete="off"
              />
              <span className="helper">Used only for this request.</span>
            </label>
            <button className="primary" type="submit" disabled={loading}>
              {loading ? "Drafting recap..." : "Generate recap"}
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </div>
      </header>

      <main className="content">
        {!recap ? (
          <section className="empty">
            <h2>Your storyboard will appear here.</h2>
            <p>
              The recap blends MCP data from GitHub with local notes to craft a
              narrative arc.
            </p>
          </section>
        ) : (
          <>
            <section className="summary">
              <div>
                <h2>{recap.summary.headline}</h2>
                <p>
                  {recap.project.title} · {recap.range.since} to {recap.range.until}
                </p>
              </div>
              <div className="metric-grid">
                <div>
                  <strong>{recap.metrics.prCount}</strong>
                  <span>PRs</span>
                </div>
                <div>
                  <strong>{recap.metrics.commitCount}</strong>
                  <span>Commits</span>
                </div>
                <div>
                  <strong>{recap.metrics.noteCount}</strong>
                  <span>Notes</span>
                </div>
              </div>
            </section>

            <section className="panels">
              <div className="panel">
                <h3>Highlights</h3>
                <ul>
                  {recap.summary.highlights.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="panel">
                <h3>Risks</h3>
                <ul>
                  {recap.summary.risks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="panel">
                <h3>Next steps</h3>
                <ul>
                  {recap.summary.next.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="chapters">
              {recap.chapters.map((chapter) => (
                <article className="chapter" key={chapter.title}>
                  <h3>{chapter.title}</h3>
                  <ol>
                    {chapter.beats.map((beat) => (
                      <li key={beat}>{beat}</li>
                    ))}
                  </ol>
                </article>
              ))}
            </section>

            <section className="timeline">
              <h3>Timeline</h3>
              <div className="timeline-grid">
                {recap.timeline.map((item, index) => (
                  <div className="timeline-card" key={`${item.date}-${index}`}>
                    <span className={`tag tag-${item.type}`}>{item.type}</span>
                    <h4>{item.title}</h4>
                    <p>{item.detail}</p>
                    <span className="date">{item.date}</span>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
