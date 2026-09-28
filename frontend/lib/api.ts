export interface AnalysisResult {
  id: string | null;
  url: string;
  title: string | null;
  meta_description: string | null;
  h1: string[];
  h2: string[];
  word_count: number;
  analyzed_at: string | null;
}

function getApiBaseUrl(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Configure it in frontend/.env.local."
    );
  }
  return apiUrl.replace(/\/$/, "");
}

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (data && typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // Response body wasn't JSON; fall through to the generic message.
  }
  return `Request failed with status ${response.status}`;
}

export async function analyzeUrl(url: string): Promise<AnalysisResult> {
  const response = await fetch(`${getApiBaseUrl()}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function fetchRecentAnalyses(): Promise<AnalysisResult[]> {
  const response = await fetch(`${getApiBaseUrl()}/api/analyses`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}
