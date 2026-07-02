import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_KB_NAME = "ai读书 个人成长"
DEFAULT_WORKSPACE_ID = "demo-workspace"
DEFAULT_CATEGORY = "情报知识中心"


def utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")


def find_node() -> str:
    node = shutil.which("node")
    if node:
        return node
    fallback = Path("C:/Program Files/nodejs/node.exe")
    if fallback.exists():
        return str(fallback)
    raise RuntimeError("未找到 Node.js，请先安装 Node.js v18+。")


def skill_script() -> str:
    script = Path.home() / ".codex" / "skills" / "ima-skills" / "ima_api.cjs"
    if not script.exists():
        raise RuntimeError(f"未找到 ima 技能脚本：{script}")
    return str(script)


class ImaClient:
    def __init__(self) -> None:
        self.node = find_node()
        self.script = skill_script()

    def post(self, api_path: str, body: dict) -> dict:
        result = subprocess.run(
            [self.node, self.script, api_path, json.dumps(body, ensure_ascii=False)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45,
        )
        output = result.stdout.strip() or result.stderr.strip()
        if result.returncode != 0:
            raise RuntimeError(output or f"ima API 调用失败：{api_path}")
        if not output:
            return {"code": 0, "msg": "success", "data": {}}
        data = json.loads(output)
        if data.get("code") != 0:
            raise RuntimeError(data.get("msg") or output)
        return data


def find_knowledge_base(client: ImaClient, name: str) -> dict:
    response = client.post(
        "openapi/wiki/v1/search_knowledge_base",
        {"query": name, "cursor": "", "limit": 20},
    )
    candidates = response.get("data", {}).get("info_list", [])
    exact = [item for item in candidates if item.get("kb_name") == name or item.get("name") == name]
    if exact:
        return exact[0]
    if candidates:
        return candidates[0]
    raise RuntimeError(f"未找到 ima 知识库：{name}")


def list_all_knowledge(client: ImaClient, kb_id: str, folder_id: str | None = None) -> list[dict]:
    items: list[dict] = []
    cursor = ""
    while True:
        body = {"knowledge_base_id": kb_id, "cursor": cursor, "limit": 50}
        if folder_id:
            body["folder_id"] = folder_id
        response = client.post("openapi/wiki/v1/get_knowledge_list", body)
        data = response.get("data", {})
        for item in data.get("knowledge_list", []):
            if item.get("folder_id") and not item.get("media_id"):
                items.extend(list_all_knowledge(client, kb_id, item["folder_id"]))
            elif item.get("media_id"):
                items.append(item)
        if data.get("is_end", True):
            break
        cursor = data.get("next_cursor") or ""
        if not cursor:
            break
    return items


def fetch_url_text(url: str, headers: dict | None = None) -> str:
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=20) as response:
        body = response.read()
        content_type = response.headers.get("content-type", "")
        charset = response.headers.get_content_charset() or "utf-8"
    if "text" not in content_type and "json" not in content_type and "html" not in content_type:
        return ""
    try:
        return body.decode(charset)
    except UnicodeDecodeError:
        return body.decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|h[1-6]|li|section|article)>", "\n", text, flags=re.I)
    text = unescape(re.sub(r"<[^>]+>", " ", text))
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    blocked = ("var ", "function ", "window.", "document.", "wx.", "ICP备案", "版权所有")
    useful = [line for line in lines if len(line) >= 8 and not line.startswith(blocked)]
    cleaned = "\n".join(useful)[:12000]
    blocked_pages = ("当前环境异常", "完成验证后即可继续访问")
    if any(marker in cleaned for marker in blocked_pages):
        return ""
    return cleaned


def get_item_text(client: ImaClient, item: dict) -> str:
    media_id = item.get("media_id")
    if not media_id:
        return ""
    response = client.post("openapi/wiki/v1/get_media_info", {"media_id": media_id})
    data = response.get("data", {})
    if data.get("media_type") == 11:
        note_id = (data.get("notebook_ext_info") or {}).get("notebook_id")
        if not note_id:
            return ""
        note = client.post(
            "openapi/note/v1/get_doc_content",
            {"note_id": note_id, "target_content_format": 0},
        )
        return json.dumps(note.get("data", {}), ensure_ascii=False)
    url_info = data.get("url_info") or {}
    url = url_info.get("url")
    if not url:
        return ""
    return fetch_url_text(url, url_info.get("headers"))


def summarize(text: str, title: str) -> str:
    compact = " ".join(clean_text(text).split())
    if compact:
        return compact[:300]
    return f"来自 ima 知识库的条目：{title}"


def upsert_source(conn: sqlite3.Connection, workspace_id: str, kb_name: str, category: str) -> str:
    source_name = f"ima：{kb_name}"
    source_url = f"ima://knowledge-base/{kb_name.replace(' ', '-')}"
    now = utcnow()
    row = conn.execute(
        """
        select id from knowledge_sources
        where workspace_id = ? and name = ? and source_type = 'ima_knowledge_base'
        """,
        (workspace_id, source_name),
    ).fetchone()
    if row:
        source_id = row["id"]
        conn.execute(
            """
            update knowledge_sources
            set url = ?, crawl_frequency = 'manual', category = ?, credibility_level = 'medium',
                status = 'active', last_crawled_at = ?, updated_at = ?
            where id = ?
            """,
            (source_url, category, now, now, source_id),
        )
        return source_id
    source_id = str(uuid.uuid4())
    conn.execute(
        """
        insert into knowledge_sources
        (workspace_id, organization_id, name, source_type, url, crawl_frequency, category,
         credibility_level, status, last_crawled_at, id, created_at, updated_at)
        values (?, null, ?, 'ima_knowledge_base', ?, 'manual', ?, 'medium', 'active', ?, ?, ?, ?)
        """,
        (workspace_id, source_name, source_url, category, now, source_id, now, now),
    )
    return source_id


def upsert_item(conn: sqlite3.Connection, source_id: str, item: dict, raw_text: str, category: str) -> str:
    title = (item.get("title") or "未命名 ima 知识条目")[:500]
    media_id = item.get("media_id")
    url = f"ima://media/{media_id or uuid.uuid4()}"
    now = utcnow()
    raw_text = clean_text(raw_text)
    if not raw_text:
        raw_text = f"来自 ima 知识库的条目：{title}"
    summary = summarize(raw_text, title)
    metadata_tags = json.dumps(["ima", "个人成长", "AI读书"], ensure_ascii=False)
    compliance = json.dumps({"risk_level": "low", "risk_items": []}, ensure_ascii=False)

    row = conn.execute(
        "select id from knowledge_items where source_id = ? and url = ?",
        (source_id, url),
    ).fetchone()
    if row:
        item_id = row["id"]
        conn.execute(
            """
            update knowledge_items
            set title = ?, crawled_at = ?, raw_text = ?, summary = ?, category = ?,
                tags = ?, compliance_risk = ?, credibility_score = 65, status = 'active',
                updated_at = ?
            where id = ?
            """,
            (title, now, raw_text, summary, category, metadata_tags, compliance, now, item_id),
        )
        return "updated"

    conn.execute(
        """
        insert into knowledge_items
        (source_id, organization_id, title, url, author, published_at, crawled_at, raw_text,
         summary, category, tags, audiences, pain_points, topic_suggestions, compliance_risk,
         credibility_score, status, id, created_at, updated_at)
        values (?, null, ?, ?, null, null, ?, ?, ?, ?, ?, null, null, null, ?, 65, 'active', ?, ?, ?)
        """,
        (
            source_id,
            title,
            url,
            now,
            raw_text,
            summary,
            category,
            metadata_tags,
            compliance,
            str(uuid.uuid4()),
            now,
            now,
        ),
    )
    return "created"


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync an ima knowledge base into intelligence center.")
    parser.add_argument("--kb-name", default=DEFAULT_KB_NAME)
    parser.add_argument("--workspace-id", default=DEFAULT_WORKSPACE_ID)
    parser.add_argument("--category", default=DEFAULT_CATEGORY)
    parser.add_argument("--db", default="health_media.db")
    args = parser.parse_args()

    client = ImaClient()
    kb = find_knowledge_base(client, args.kb_name)
    kb_id = kb.get("kb_id") or kb.get("id")
    if not kb_id:
        raise RuntimeError("ima 知识库搜索结果缺少 ID。")

    items = list_all_knowledge(client, kb_id)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        source_id = upsert_source(conn, args.workspace_id, args.kb_name, args.category)
        created = updated = failed = 0
        for item in items:
            try:
                try:
                    raw_text = get_item_text(client, item)
                except Exception:
                    raw_text = ""
                action = upsert_item(conn, source_id, item, raw_text, args.category)
                created += action == "created"
                updated += action == "updated"
            except Exception as exc:
                failed += 1
                print(f"跳过：{item.get('title') or item.get('media_id')}：{exc}", file=sys.stderr)
        conn.commit()
    finally:
        conn.close()

    print(
        json.dumps(
            {
                "knowledge_base": args.kb_name,
                "found_items": len(items),
                "created": created,
                "updated": updated,
                "failed": failed,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
