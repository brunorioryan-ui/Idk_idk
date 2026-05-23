import yfinance as yf
import streamlit as st
import requests
from datetime import datetime, timezone
import xml.etree.ElementTree as ET


def _time_ago(ts) -> str:
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            return ""
        now = datetime.now(tz=timezone.utc)
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 60:
            return "just now"
        elif secs < 3600:
            return f"{secs // 60}m ago"
        elif secs < 86400:
            return f"{secs // 3600}h ago"
        else:
            return f"{secs // 86400}d ago"
    except Exception:
        return ""


def _parse_rss(url: str, limit: int = 10) -> list:
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            description = (item.findtext("description") or "").strip()
            source = (item.findtext("{http://purl.org/dc/elements/1.1/}publisher")
                      or item.findtext("source") or "").strip()
            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "published": pub_date,
                    "publisher": source,
                    "summary": description[:200] if description else "",
                })
            if len(items) >= limit:
                break
        return items
    except Exception:
        return []


@st.cache_data(ttl=300)
def ticker_news(ticker: str, limit: int = 15) -> list:
    results = []
    try:
        t = yf.Ticker(ticker)
        raw = t.news or []
        for item in raw[:limit]:
            content = item.get("content", {})
            results.append({
                "title": content.get("title") or item.get("title", ""),
                "link": content.get("canonicalUrl", {}).get("url") or item.get("link", ""),
                "publisher": content.get("provider", {}).get("displayName") or item.get("publisher", ""),
                "published": content.get("pubDate") or item.get("providerPublishTime", ""),
                "summary": content.get("summary") or "",
                "time_ago": _time_ago(
                    content.get("pubDate") or item.get("providerPublishTime", "")
                ),
            })
    except Exception:
        pass

    if not results:
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        results = _parse_rss(rss_url, limit)
        for r in results:
            r["time_ago"] = _time_ago(r.get("published", ""))

    return results


@st.cache_data(ttl=300)
def market_news(limit: int = 20) -> list:
    results = []
    feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY&region=US&lang=en-US",
    ]
    for url in feeds:
        items = _parse_rss(url, limit)
        for item in items:
            item["time_ago"] = _time_ago(item.get("published", ""))
        results.extend(items)
        if len(results) >= limit:
            break

    if not results:
        try:
            t = yf.Ticker("SPY")
            raw = t.news or []
            for item in raw[:limit]:
                content = item.get("content", {})
                results.append({
                    "title": content.get("title") or item.get("title", ""),
                    "link": content.get("canonicalUrl", {}).get("url") or item.get("link", ""),
                    "publisher": content.get("provider", {}).get("displayName") or item.get("publisher", ""),
                    "published": content.get("pubDate") or item.get("providerPublishTime", ""),
                    "summary": content.get("summary") or "",
                    "time_ago": _time_ago(
                        content.get("pubDate") or item.get("providerPublishTime", "")
                    ),
                })
        except Exception:
            pass

    seen = set()
    unique = []
    for item in results:
        key = item.get("title", "")[:60]
        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:limit]
