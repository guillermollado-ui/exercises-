from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analyzer import analyze_url
from .config import get_settings
from .errors import (
    AnalyzerError,
    BlockedURLError,
    FetchConnectionError,
    FetchTimeoutError,
    InvalidURLError,
    NonHTMLContentError,
)
from .firestore_repo import get_recent_analyses, save_analysis
from .schemas import AnalysisResult, AnalyzeRequest, HealthResponse

settings = get_settings()

app = FastAPI(title="SEO Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_ERROR_STATUS_CODES = {
    InvalidURLError: 400,
    BlockedURLError: 400,
    NonHTMLContentError: 400,
    FetchTimeoutError: 504,
    FetchConnectionError: 502,
}


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(payload: AnalyzeRequest) -> AnalysisResult:
    try:
        fields = analyze_url(payload.url, settings.request_timeout_seconds)
    except AnalyzerError as exc:
        status_code = _ERROR_STATUS_CODES.get(type(exc), 400)
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    saved = save_analysis(payload.url, fields)
    return AnalysisResult(**saved)


@app.get("/api/analyses", response_model=list[AnalysisResult])
def list_analyses() -> list[AnalysisResult]:
    analyses = get_recent_analyses(limit=10)
    return [AnalysisResult(**item) for item in analyses]
