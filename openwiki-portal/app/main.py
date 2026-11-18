"""
OpenWiki Wikipedia Portal — FastAPI 진입점.

GitHub 저장소 내 OpenWiki(.md) 폴더를 읽어 위키피디아 형태의 웹 홈페이지(index.html)와
실시간 검색/백링크/GitHub 동기화 REST API를 제공합니다.

실행: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import os
import random
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from app.wiki_loader import wiki_repo
except ImportError:
    from wiki_loader import wiki_repo

PORTAL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML_PATH = os.path.join(PORTAL_ROOT, "index.html")
WIKI_DATA_JSON_PATH = os.path.join(PORTAL_ROOT, "wiki-data.json")

app = FastAPI(
    title="OpenWiki Wikipedia Portal",
    description="LangChain OpenWiki(.md) 기반 위키피디아 스타일 지식 백과 웹 포털",
    version="1.0.0",
)


class GitHubSyncRequest(BaseModel):
    mode: str = Field(default="local", description="'local' (디스크 재스캔) 또는 'github' (GitHub 저장소 동기화)")
    repo: Optional[str] = Field(default=None, example="langchain-ai/openwiki")
    branch: str = Field(default="main", example="main")
    folder_path: str = Field(default="openwiki", example="openwiki")
    token: Optional[str] = Field(default=None, description="Private 저장소용 GitHub Token (선택)")


@app.get("/", response_class=HTMLResponse)
def serve_home():
    """루트 index.html (위키피디아 스타일 SPA) 반환"""
    if os.path.isfile(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)


@app.get("/wiki-data.json")
def serve_static_bundle():
    """정적 모드 호환용 JSON 번들 반환"""
    if os.path.isfile(WIKI_DATA_JSON_PATH):
        return FileResponse(WIKI_DATA_JSON_PATH, media_type="application/json")
    return {"pages": {k: v.model_dump() for k, v in wiki_repo.pages.items()}, "tree": wiki_repo.get_tree()}


@app.get("/api/info")
def api_info():
    return {
        "status": "ok",
        "service": "OpenWiki Wikipedia Portal",
        "wiki_dir": wiki_repo.wiki_dir,
        "total_pages": len(wiki_repo.pages),
        "last_synced_at": wiki_repo.last_synced_at,
        "source_info": wiki_repo.source_info,
    }


@app.get("/api/wiki/tree")
def get_wiki_tree():
    """사이드바 카테고리 트리 및 전체 문서 통계 반환"""
    return wiki_repo.get_tree()


@app.get("/api/wiki/page")
def get_wiki_page(slug: str = Query(default="index", description="조회할 마크다운 문서 slug (예: index, architecture/overview)")):
    """특정 마크다운 문서의 메타데이터, 본문, 목차(TOC), 인포박스, 백링크 반환"""
    page = wiki_repo.get_page(slug)
    if not page:
        raise HTTPException(status_code=404, detail=f"문서를 찾을 수 없습니다: {slug}")
    return page


@app.get("/api/wiki/search")
def search_wiki(q: str = Query(..., min_length=1, description="검색어")):
    """전체 .md 문서 대상 실시간 전문 검색"""
    return {"query": q, "results": wiki_repo.search(q)}


@app.get("/api/wiki/random")
def get_random_page():
    """임의의 위키 문서(Random Article) 1개 반환"""
    if not wiki_repo.pages:
        raise HTTPException(status_code=404, detail="색인된 위키 문서가 없습니다.")
    slug = random.choice(list(wiki_repo.pages.keys()))
    return {"slug": slug, "title": wiki_repo.pages[slug].title}


@app.post("/api/wiki/sync")
def sync_wiki(req: GitHubSyncRequest):
    """
    로컬 openwiki/ 폴더를 재스캔하거나, 원격 GitHub 저장소 폴더의 .md 파일을 동기화합니다.
    """
    if req.mode == "github":
        target_repo = req.repo or os.getenv("GITHUB_REPO", "").strip()
        if not target_repo:
            raise HTTPException(status_code=400, detail="GitHub 저장소 이름(owner/repo)을 입력해주세요.")
        try:
            return wiki_repo.sync_from_github(
                repo=target_repo,
                branch=req.branch,
                folder_path=req.folder_path,
                token=req.token,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"GitHub 동기화 실패: {str(e)}")

    count = wiki_repo.reload()
    return {
        "status": "reloaded",
        "mode": "local",
        "total_indexed_pages": count,
        "synced_at": wiki_repo.last_synced_at,
    }

