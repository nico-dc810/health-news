import email.utils
import re
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from html import unescape

from app.services.compliance import review_content
from app.services.material_analyzer import analyze_material_text


@dataclass
class CrawledEntry:
    title: str
    url: str
    raw_text: str
    author: str | None = None
    published_at: datetime | None = None


def crawl_source(url: str, source_type: str) -> list[CrawledEntry]:
    content = _fetch_url(url)
    if source_type == "rss" or _looks_like_feed(content):
        return _parse_feed(content, fallback_url=url)
    return _parse_html_entries(content, url)


def analyze_knowledge_entry(
    entry: CrawledEntry,
    *,
    category: str | None,
    credibility_level: str,
) -> dict:
    material_analysis = analyze_material_text(entry.raw_text, "外部知识")
    compliance = review_content(entry.raw_text)
    credibility_score = _credibility_score(credibility_level, entry.url)

    return {
        "summary": material_analysis["summary"],
        "category": category,
        "tags": material_analysis["tags"],
        "audiences": material_analysis["audiences"],
        "pain_points": material_analysis["pain_points"],
        "topic_suggestions": material_analysis["topics"],
        "compliance_risk": {
            "risk_level": compliance["risk_level"],
            "risk_items": compliance["risk_items"],
        },
        "credibility_score": credibility_score,
        "status": "pending_review" if compliance["risk_level"] != "low" else "active",
    }


def _fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HealthMediaKnowledgeBot/0.1 (+https://localhost)",
            "Accept": "application/rss+xml, application/xml, text/html, text/plain",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = response.read()
            charset = response.headers.get_content_charset() or _detect_charset(body)
            return _decode_body(body, charset)
    except (TimeoutError, OSError, urllib.error.URLError) as exc:
        raise ValueError(f"无法抓取知识源：{exc}") from exc


def _detect_charset(body: bytes) -> str | None:
    head = body[:2000].decode("ascii", errors="ignore")
    match = re.search(r"charset=[\"']?([\w.-]+)", head, flags=re.I)
    if match:
        return match.group(1)
    return None


def _decode_body(body: bytes, charset: str | None) -> str:
    candidates = [charset, "utf-8", "gb18030", "big5"]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        normalized = candidate.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return body.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


def _looks_like_feed(content: str) -> bool:
    head = content[:500].lower()
    return "<rss" in head or "<feed" in head or "<rdf" in head


def _parse_feed(content: str, fallback_url: str) -> list[CrawledEntry]:
    root = ET.fromstring(content)
    entries: list[CrawledEntry] = []
    for item in root.findall(".//item"):
        title = _node_text(item, "title") or "未命名知识条目"
        link = _node_text(item, "link") or fallback_url
        description = _node_text(item, "description") or _node_text(item, "summary") or ""
        author = _node_text(item, "author") or _node_text(item, "creator")
        published_at = _parse_datetime(_node_text(item, "pubDate") or _node_text(item, "published"))
        entries.append(
            CrawledEntry(
                title=unescape(_strip_tags(title)).strip(),
                url=link.strip(),
                raw_text=unescape(_strip_tags(description)).strip(),
                author=author,
                published_at=published_at,
            )
        )

    if entries:
        return entries[:20]

    for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = _node_text(entry, "{http://www.w3.org/2005/Atom}title") or "未命名知识条目"
        link_node = entry.find("{http://www.w3.org/2005/Atom}link")
        link = link_node.attrib.get("href") if link_node is not None else fallback_url
        summary = (
            _node_text(entry, "{http://www.w3.org/2005/Atom}summary")
            or _node_text(entry, "{http://www.w3.org/2005/Atom}content")
            or ""
        )
        published_at = _parse_datetime(_node_text(entry, "{http://www.w3.org/2005/Atom}published"))
        entries.append(
            CrawledEntry(
                title=unescape(_strip_tags(title)).strip(),
                url=link,
                raw_text=unescape(_strip_tags(summary)).strip(),
                published_at=published_at,
            )
        )
    return entries[:20]


def _parse_html_page(content: str, url: str) -> CrawledEntry:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", content, flags=re.I | re.S)
    title = _clean_title(unescape(_strip_tags(title_match.group(1)))) if title_match else url
    article_html = _extract_article_html(content)
    text = _html_to_readable_text(article_html)
    text = _trim_article_boilerplate(text, title)
    return CrawledEntry(title=title, url=url, raw_text=text[:6000])


def _parse_html_entries(content: str, url: str) -> list[CrawledEntry]:
    page_entry = _parse_html_page(content, url)
    links = _extract_article_links(content, url)
    is_index_like = _looks_like_index_page(page_entry.raw_text, links)
    if not is_index_like:
        return [page_entry]

    entries: list[CrawledEntry] = []
    for link_url, link_title in links[:12]:
        try:
            article = _parse_html_page(_fetch_url(link_url), link_url)
        except Exception:
            continue
        if _is_useful_article(article.raw_text):
            if article.title == link_url or len(article.title) > 120:
                article.title = link_title
            entries.append(article)
        if len(entries) >= 8:
            break

    return entries or [page_entry]


def _extract_article_html(content: str) -> str:
    cleaned = re.sub(r"<(script|style|noscript|svg|form)[^>]*>.*?</\1>", " ", content, flags=re.I | re.S)
    cleaned = re.sub(r"<(header|nav|footer|aside)[^>]*>.*?</\1>", " ", cleaned, flags=re.I | re.S)
    candidates = []
    for pattern in [
        r"<article[^>]*>(.*?)</article>",
        r"<div[^>]+class=[\"'][^\"']*(?:article|content|main|detail|news|post|text|正文)[^\"']*[\"'][^>]*>(.*?)</div>",
        r"<main[^>]*>(.*?)</main>",
    ]:
        for match in re.finditer(pattern, cleaned, flags=re.I | re.S):
            html = next((group for group in match.groups() if group), "")
            text = _html_to_readable_text(html)
            if len(text) > 180:
                candidates.append((len(text), html))
    if candidates:
        candidates.sort(reverse=True, key=lambda item: item[0])
        return candidates[0][1]
    return cleaned


def _html_to_readable_text(content: str) -> str:
    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.I)
    content = re.sub(r"</p\s*>", "\n", content, flags=re.I)
    content = re.sub(r"</div\s*>", "\n", content, flags=re.I)
    text = unescape(_strip_tags(content))
    lines = [_clean_text(line) for line in text.splitlines()]
    lines = [line for line in lines if _is_content_line(line)]
    text = " ".join(lines) if lines else _clean_text(text)
    return _remove_repeated_noise(text)


def _extract_article_links(content: str, base_url: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", content, flags=re.I | re.S):
        href, title_html = match.groups()
        title = _clean_text(unescape(_strip_tags(title_html)))
        absolute_url = urllib.parse.urljoin(base_url, href)
        if not _looks_like_article_link(absolute_url, title):
            continue
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        links.append((absolute_url, title[:160]))
    return links


def _looks_like_index_page(text: str, links: list[tuple[str, str]]) -> bool:
    if len(links) >= 4:
        return True
    nav_words = ["首页", "新闻", "人物", "专题", "栏目", "登录", "注册"]
    return sum(1 for word in nav_words if word in text[:800]) >= 4


def _is_useful_article(text: str) -> bool:
    if len(text) < 180:
        return False
    sentence_count = sum(text.count(mark) for mark in ["。", "！", "？", ".", "!", "?"])
    return sentence_count >= 3


def _looks_like_article_link(url: str, title: str) -> bool:
    if not title or len(title) < 8:
        return False
    blocked = ["首页", "登录", "注册", "关于我们", "联系我们", "广告", "视频", "图片"]
    if any(word == title or word in title[:8] for word in blocked):
        return False
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    article_hints = ["news", "article", "view", "item", "content", "detail", ".html", "id=", "itemid"]
    return any(hint in url.lower() for hint in article_hints) or len(title) >= 14


def _is_content_line(line: str) -> bool:
    if len(line) < 10:
        return False
    blocked = ["首页", "登录", "注册", "联系我们", "版权所有", "ICP备案", "免责声明", "上一篇", "下一篇"]
    if any(word in line for word in blocked) and len(line) < 50:
        return False
    return True


def _remove_repeated_noise(text: str) -> str:
    chunks = []
    seen = set()
    for chunk in re.split(r"\s{2,}|(?<=。)\s*", text):
        chunk = _clean_text(chunk)
        if not chunk:
            continue
        key = chunk[:50]
        if key in seen:
            continue
        seen.add(key)
        chunks.append(chunk)
    return " ".join(chunks)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _clean_title(title: str) -> str:
    cleaned = _clean_text(title)
    for separator in ["--", "_", "|", "｜"]:
        if separator in cleaned:
            cleaned = cleaned.split(separator)[0].strip()
    return cleaned[:160] or title


def _trim_article_boilerplate(text: str, title: str) -> str:
    cleaned = text
    compact_title = title.split("--")[0].strip()
    for prefix in [title, compact_title]:
        if prefix and cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip(" -_｜|")

    markers = ["[来源：", "来源：", "发布时间", "更新时间", "正文", "导读"]
    positions = [cleaned.find(marker) for marker in markers if cleaned.find(marker) != -1]
    if positions:
        position = min(positions)
        if 0 <= position < 500:
            cleaned = cleaned[position:]

    cleaned = re.sub(r"\[[^\]]{1,40}\]", " ", cleaned)
    cleaned = re.sub(r"DSC颇具价值的直销资讯平台|世界（中国）直销品牌节", " ", cleaned)
    return _clean_text(cleaned)


def _node_text(node: ET.Element, tag: str) -> str | None:
    child = node.find(tag)
    if child is not None and child.text:
        return child.text
    return None


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def _credibility_score(level: str, url: str) -> int:
    base = {"high": 85, "medium": 65, "low": 40}.get(level, 60)
    if any(domain in url for domain in [".gov", ".edu", "nhc.gov", "samr.gov"]):
        base += 10
    return min(base, 100)
