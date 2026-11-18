"""
정적 호스팅용 wiki-data.json 번들 생성 스크립트.
AWS EC2 Nginx 정적 서빙이나 S3/CloudFront 배포 시 Python 백엔드 없이도
index.html만으로 위키피디아 포털을 동작시킬 수 있도록 openwiki/*.md를 JSON으로 패키징합니다.

실행: python3 build_static.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.wiki_loader import wiki_repo  # noqa: E402


def main():
    count = wiki_repo.reload()
    bundle = {
        "tree": wiki_repo.get_tree(),
        "pages": {slug: page.model_dump() for slug, page in wiki_repo.pages.items()},
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiki-data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    print(f"✅ 정적 위키 번들 생성 완료: {out_path} ({count}개 문서)")


if __name__ == "__main__":
    main()

