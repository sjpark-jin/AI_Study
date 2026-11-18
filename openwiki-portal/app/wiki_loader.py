"""
OpenWiki Markdown Graph Loader & GitHub Sync Engine.

LangChain OpenWiki(OKF) 형식의 .md 파일들을 로컬 디렉터리 또는 원격 GitHub 저장소 폴더에서
재귀적으로 읽어와 YAML Front Matter, 목차(TOC), 위키 링크([[...]] / .md), 역참조 백링크(Backlinks),
카테고리 트리 및 전문 검색 인덱스를 구축합니다.
"""
import os
import re
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote
import requests
from pydantic import BaseModel, Field

log = logging.getLogger("wiki_loader")

WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.MULTILINE)


class WikiHeading(BaseModel):
    level: int
    text: str
    anchor: str


class WikiLinkRef(BaseModel):
    slug: str
    title: str


class WikiPage(BaseModel):
    slug: str
    file_path: str
    title: str
    category: str = "미분류"
    tags: List[str] = Field(default_factory=list)
    updated: str = ""
    okf_version: str = "0.2"
    summary: str = ""
    infobox: Dict[str, str] = Field(default_factory=dict)
    content: str
    headings: List[WikiHeading] = Field(default_factory=list)
    outbound_links: List[str] = Field(default_factory=list)
    backlinks: List[WikiLinkRef] = Field(default_factory=list)
    word_count: int = 0


def slugify_heading(text: str) -> str:
    cleaned = re.sub(r"`([^`]+)`", r"\1", text).strip().lower()
    cleaned = re.sub(r"[^\w\s가-힣-]", "", cleaned)
    return re.sub(r"\s+", "-", cleaned)


def parse_front_matter(raw_text: str) -> Tuple[Dict[str, Any], str]:
    """
    외부 PyYAML 의존성 없이도 YAML Front Matter(기본 키-값, 리스트, 1단 중첩 dict `infobox`)를
    안정적으로 파싱합니다.
    """
    text = raw_text.lstrip("\ufeff")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, raw_text

    lines = text.splitlines()
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break

    if end_idx is None:
        return {}, raw_text

    meta_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\r\n")
    meta: Dict[str, Any] = {}
    current_nested_key: Optional[str] = None

    for line in meta_lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        # 1단 들여쓰기 (예: infobox 하위 키)
        if (line.startswith("  ") or line.startswith("\t")) and current_nested_key:
            sub = line.strip()
            if sub.startswith("- "):
                if not isinstance(meta[current_nested_key], list):
                    meta[current_nested_key] = []
                meta[current_nested_key].append(sub[2:].strip().strip('"').strip("'"))
            elif ":" in sub:
                k, v = sub.split(":", 1)
                if not isinstance(meta[current_nested_key], dict):
                    meta[current_nested_key] = {}
                meta[current_nested_key][k.strip()] = v.strip().strip('"').strip("'")
            continue

        current_nested_key = None
        if ":" not in line:
            continue
        key, raw_val = line.split(":", 1)
        key = key.strip()
        val = raw_val.strip()

        if val == "":
            meta[key] = {}
            current_nested_key = key
        elif val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",") if x.strip()]
            meta[key] = items
        else:
            meta[key] = val.strip('"').strip("'")

    return meta, body


def normalize_slug(raw_target: str, current_slug: str = "") -> str:
    target = unquote(raw_target.split("#", 1)[0].strip())
    if target.endswith(".md"):
        target = target[:-3]
    if target.startswith("./"):
        base_dir = os.path.dirname(current_slug)
        target = os.path.normpath(os.path.join(base_dir, target))
    elif target.startswith("../"):
        base_dir = os.path.dirname(current_slug)
        target = os.path.normpath(os.path.join(base_dir, target))
    target = target.replace("\\", "/").strip("/")
    return target


class WikiRepository:
    def __init__(self, wiki_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_wiki = os.path.join(base_dir, "openwiki")
        env_wiki = os.getenv("WIKI_DIR", "").strip()
        if wiki_dir:
            self.wiki_dir = os.path.abspath(wiki_dir)
        elif env_wiki:
            self.wiki_dir = os.path.abspath(os.path.join(base_dir, env_wiki)) if not os.path.isabs(env_wiki) else env_wiki
        else:
            self.wiki_dir = default_wiki

        self.pages: Dict[str, WikiPage] = {}
        self.last_synced_at: str = ""
        self.source_info: Dict[str, str] = {"mode": "local", "location": self.wiki_dir}
        self.reload()

    def reload(self) -> int:
        """로컬 WIKI_DIR 폴더의 모든 .md 파일을 다시 읽고 백링크 그래프를 구축합니다."""
        os.makedirs(self.wiki_dir, exist_ok=True)
        loaded: Dict[str, WikiPage] = {}

        for root, _, files in os.walk(self.wiki_dir):
            for fname in sorted(files):
                if not fname.lower().endswith(".md"):
                    continue
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.wiki_dir).replace("\\", "/")
                slug = rel_path[:-3]  # remove .md

                with open(full_path, "r", encoding="utf-8") as f:
                    raw = f.read()

                meta, body = parse_front_matter(raw)
                headings: List[WikiHeading] = []
                for m in HEADING_RE.finditer(body):
                    level = len(m.group(1))
                    h_text = m.group(2).strip()
                    headings.append(WikiHeading(level=level, text=h_text, anchor=slugify_heading(h_text)))

                # 기본 제목 추론: front matter title -> 첫 H1 -> 파일명
                title = str(meta.get("title", "")).strip()
                if not title and headings:
                    title = headings[0].text
                if not title:
                    title = os.path.basename(slug)

                # 아웃바운드 링크 수집 ([[WikiLink]] 및 [text](path.md))
                outbound: List[str] = []
                for wm in WIKI_LINK_RE.finditer(body):
                    target_slug = normalize_slug(wm.group(1), slug)
                    if target_slug and target_slug not in outbound and target_slug != slug:
                        outbound.append(target_slug)
                for mm in MD_LINK_RE.finditer(body):
                    href = mm.group(2)
                    if href.startswith("http://") or href.startswith("https://"):
                        continue
                    target_slug = normalize_slug(href, slug)
                    if target_slug and target_slug not in outbound and target_slug != slug:
                        outbound.append(target_slug)

                infobox_raw = meta.get("infobox", {})
                infobox = {str(k): str(v) for k, v in infobox_raw.items()} if isinstance(infobox_raw, dict) else {}
                tags_raw = meta.get("tags", [])
                tags = [str(t) for t in tags_raw] if isinstance(tags_raw, list) else []

                loaded[slug] = WikiPage(
                    slug=slug,
                    file_path=rel_path,
                    title=title,
                    category=str(meta.get("category", "미분류")),
                    tags=tags,
                    updated=str(meta.get("updated", "")),
                    okf_version=str(meta.get("okf_version", "0.2")),
                    summary=str(meta.get("summary", "")),
                    infobox=infobox,
                    content=body,
                    headings=headings,
                    outbound_links=outbound,
                    backlinks=[],
                    word_count=len(body.split()),
                )

        # 역참조 백링크(Backlinks) 계산
        for src_slug, page in loaded.items():
            for target_slug in page.outbound_links:
                if target_slug in loaded:
                    loaded[target_slug].backlinks.append(WikiLinkRef(slug=src_slug, title=page.title))

        self.pages = loaded
        self.last_synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return len(self.pages)

    def sync_from_github(
        self,
        repo: str,
        branch: str = "main",
        folder_path: str = "openwiki",
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        GitHub REST Contents API를 통해 지정된 저장소의 특정 폴더 내 .md 파일들을
        재귀적으로 내려받아 WIKI_DIR에 저장하고 인덱스를 갱신합니다.
        """
        repo = repo.strip().strip("/")
        folder_path = folder_path.strip().strip("/")
        headers = {"Accept": "application/vnd.github+json"}
        gh_token = (token or os.getenv("GITHUB_TOKEN", "")).strip()
        if gh_token:
            headers["Authorization"] = f"Bearer {gh_token}"

        downloaded_files: List[str] = []

        def fetch_dir(api_path: str):
            url = f"https://api.github.com/repos/{repo}/contents/{api_path}"
            resp = requests.get(url, params={"ref": branch}, headers=headers, timeout=15)
            resp.raise_for_status()
            items = resp.json()
            if not isinstance(items, list):
                items = [items]

            for item in items:
                item_type = item.get("type")
                item_path = item.get("path", "")
                if item_type == "dir":
                    fetch_dir(item_path)
                elif item_type == "file" and item_path.lower().endswith(".md"):
                    dl_url = item.get("download_url")
                    if not dl_url:
                        continue
                    file_resp = requests.get(dl_url, headers=headers, timeout=15)
                    file_resp.raise_for_status()

                    rel = item_path[len(folder_path) :].lstrip("/") if folder_path and item_path.startswith(folder_path) else item_path
                    local_dest = os.path.join(self.wiki_dir, rel)
                    os.makedirs(os.path.dirname(local_dest), exist_ok=True)
                    with open(local_dest, "w", encoding="utf-8") as f:
                        f.write(file_resp.text)
                    downloaded_files.append(rel)

        fetch_dir(folder_path)
        total_count = self.reload()
        self.source_info = {"mode": "github", "location": f"{repo}@{branch}/{folder_path}"}
        return {
            "status": "synced",
            "repo": repo,
            "branch": branch,
            "folder_path": folder_path,
            "downloaded_count": len(downloaded_files),
            "downloaded_files": downloaded_files,
            "total_indexed_pages": total_count,
            "synced_at": self.last_synced_at,
        }

    def get_tree(self) -> Dict[str, Any]:
        categories: Dict[str, List[Dict[str, str]]] = {}
        for slug, page in sorted(self.pages.items(), key=lambda x: (0 if x[0] == "index" else (1 if x[0] == "logs" else 2), x[1].title)):
            cat = page.category or "미분류"
            categories.setdefault(cat, []).append(
                {
                    "slug": slug,
                    "title": page.title,
                    "file_path": page.file_path,
                    "updated": page.updated,
                }
            )
        return {
            "total_pages": len(self.pages),
            "last_synced_at": self.last_synced_at,
            "source_info": self.source_info,
            "categories": categories,
            "all_slugs": list(self.pages.keys()),
        }

    def get_page(self, slug: str) -> Optional[WikiPage]:
        clean = normalize_slug(slug)
        if clean in self.pages:
            return self.pages[clean]
        # index 폴백
        if not clean and "index" in self.pages:
            return self.pages["index"]
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return []
        results = []
        for slug, page in self.pages.items():
            score = 0
            if q in page.title.lower():
                score += 10
            if any(q in t.lower() for t in page.tags):
                score += 6
            if q in page.summary.lower():
                score += 4
            body_lower = page.content.lower()
            hits = body_lower.count(q)
            if hits > 0:
                score += min(hits, 10)

            if score > 0:
                idx = body_lower.find(q)
                if idx != -1:
                    start = max(0, idx - 55)
                    end = min(len(page.content), idx + 115)
                    snippet = ("..." if start > 0 else "") + page.content[start:end].replace("\n", " ") + ("..." if end < len(page.content) else "")
                else:
                    snippet = page.summary or page.content[:140].replace("\n", " ")

                results.append(
                    {
                        "slug": slug,
                        "title": page.title,
                        "category": page.category,
                        "snippet": snippet,
                        "score": score,
                    }
                )
        results.sort(key=lambda r: r["score"], reverse=True)
        return results


# 싱글톤 인스턴스
wiki_repo = WikiRepository()

