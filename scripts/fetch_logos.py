#!/usr/bin/env python3
"""
Download logos for top US tickers into assets/logos/<TICKER>.<ext>.

Sources tried in order:
1. simple-icons via jsdelivr CDN (SVG, white-filled for dark mode)
2. vectorlogo.zone
3. Apple touch icon from company domain
4. Google faviconV2 (size=256)
5. DuckDuckGo icons
"""

import os
import re
import sys
import time
import requests
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "logos"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

TICKER_DOMAIN = {
    "AAPL": "apple.com", "MSFT": "microsoft.com", "GOOGL": "google.com", "GOOG": "google.com",
    "AMZN": "amazon.com", "META": "meta.com", "TSLA": "tesla.com", "NVDA": "nvidia.com",
    "UNH": "unitedhealthgroup.com", "XOM": "exxonmobil.com", "JNJ": "jnj.com",
    "JPM": "jpmorganchase.com", "V": "visa.com", "PG": "pg.com", "MA": "mastercard.com",
    "HD": "homedepot.com", "CVX": "chevron.com", "LLY": "lilly.com",
    "MRK": "merck.com", "ABBV": "abbvie.com", "PEP": "pepsico.com", "KO": "coca-cola.com",
    "AVGO": "broadcom.com", "COST": "costco.com", "ADBE": "adobe.com", "CRM": "salesforce.com",
    "TMO": "thermofisher.com", "MCD": "mcdonalds.com", "NKE": "nike.com", "ORCL": "oracle.com",
    "ACN": "accenture.com", "PM": "pmi.com", "AMD": "amd.com", "INTC": "intel.com",
    "QCOM": "qualcomm.com", "TXN": "ti.com", "NFLX": "netflix.com", "DIS": "disney.com",
    "BA": "boeing.com", "GE": "ge.com", "CAT": "caterpillar.com",
    "UPS": "ups.com", "FDX": "fedex.com", "SBUX": "starbucks.com", "WMT": "walmart.com",
    "TGT": "target.com", "AMGN": "amgen.com", "GILD": "gilead.com",
    "PFE": "pfizer.com", "CVS": "cvshealth.com",
    "AXP": "americanexpress.com", "GS": "goldmansachs.com", "MS": "morganstanley.com",
    "BAC": "bankofamerica.com", "WFC": "wellsfargo.com", "C": "citigroup.com",
    "LOW": "lowes.com", "BKNG": "booking.com",
    "UBER": "uber.com", "ABNB": "airbnb.com",
    "PLTR": "palantir.com", "SNOW": "snowflake.com", "DDOG": "datadoghq.com",
    "NET": "cloudflare.com", "ZS": "zscaler.com", "CRWD": "crowdstrike.com",
    "PANW": "paloaltonetworks.com", "OKTA": "okta.com",
    "MU": "micron.com", "AMAT": "appliedmaterials.com",
    "NOW": "servicenow.com", "WDAY": "workday.com", "TEAM": "atlassian.com",
    "ZM": "zoom.us", "PYPL": "paypal.com", "SHOP": "shopify.com",
    "T": "att.com", "VZ": "verizon.com", "TMUS": "t-mobile.com",
    "CMCSA": "comcast.com", "NEE": "nexteraenergy.com",
    "SPY": "ssga.com", "QQQ": "invesco.com", "VOO": "vanguard.com",
    "VTI": "vanguard.com", "GLD": "ssga.com", "TLT": "blackrock.com",
    "XLK": "ssga.com", "XLF": "ssga.com", "XLV": "ssga.com",
    "XLE": "ssga.com", "XLI": "ssga.com", "XLY": "ssga.com",
    "XLP": "ssga.com", "XLU": "ssga.com", "XLRE": "ssga.com",
    "XLB": "ssga.com", "XLC": "ssga.com",
    "ARKK": "ark-funds.com",
}

SIMPLE_ICONS_MAP = {
    "AAPL": "apple", "MSFT": "microsoft", "GOOGL": "google", "GOOG": "google",
    "AMZN": "amazon", "META": "meta", "TSLA": "tesla", "NVDA": "nvidia",
    "ADBE": "adobeacrobatreader", "CRM": "salesforce", "NFLX": "netflix",
    "INTC": "intel", "AMD": "amd", "QCOM": "qualcomm",
    "UBER": "uber", "ABNB": "airbnb", "PYPL": "paypal",
    "SHOP": "shopify", "SNAP": "snapchat", "PINS": "pinterest",
    "ZM": "zoom", "SPOT": "spotify",
    "NET": "cloudflare", "OKTA": "okta",
    "TEAM": "atlassian", "NOW": "servicenow",
    "MCD": "mcdonalds", "SBUX": "starbucks", "NKE": "nike",
    "V": "visa", "MA": "mastercard", "AXP": "americanexpress",
    "GS": "goldmansachs", "JPM": "jpmorgan",
    "WMT": "walmart", "TGT": "target",
    "T": "att", "VZ": "verizon",
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; logo-fetcher/1.0)"})


def _get(url, timeout=8, stream=False):
    try:
        r = SESSION.get(url, timeout=timeout, stream=stream)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def _is_real_image(data: bytes, mime: str = "") -> bool:
    if len(data) < 64:
        return False
    if b"<html" in data[:200].lower():
        return False
    return True


def _fill_svg_white(svg_bytes: bytes) -> bytes:
    text = svg_bytes.decode("utf-8", errors="replace")
    text = re.sub(r'fill="(?!none)[^"]*"', 'fill="#ffffff"', text)
    if 'fill=' not in text:
        text = text.replace("<svg", '<svg fill="#ffffff"', 1)
    return text.encode()


def try_simple_icons(ticker: str) -> bytes | None:
    slug = SIMPLE_ICONS_MAP.get(ticker)
    if not slug:
        return None
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
    r = _get(url)
    if r and r.content:
        return _fill_svg_white(r.content)
    return None


def try_domain_apple_touch(domain: str) -> bytes | None:
    url = f"https://{domain}/apple-touch-icon.png"
    r = _get(url)
    if r and _is_real_image(r.content):
        return r.content
    url2 = f"https://{domain}/apple-touch-icon-precomposed.png"
    r2 = _get(url2)
    if r2 and _is_real_image(r2.content):
        return r2.content
    return None


def try_google_favicon(domain: str) -> bytes | None:
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
    r = _get(url)
    if r and _is_real_image(r.content):
        return r.content
    return None


def try_duckduckgo(domain: str) -> bytes | None:
    url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    r = _get(url)
    if r and _is_real_image(r.content, "ico"):
        return r.content
    return None


def fetch_logo(ticker: str) -> tuple[bytes | None, str]:
    domain = TICKER_DOMAIN.get(ticker)

    # 1. simple-icons
    data = try_simple_icons(ticker)
    if data:
        return data, "svg"

    if domain:
        # 2. Apple touch icon
        data = try_domain_apple_touch(domain)
        if data:
            return data, "png"

        # 3. Google favicon
        data = try_google_favicon(domain)
        if data:
            return data, "png"

        # 4. DuckDuckGo
        data = try_duckduckgo(domain)
        if data:
            return data, "ico"

    return None, ""


def main():
    tickers = list(TICKER_DOMAIN.keys())
    print(f"Fetching logos for {len(tickers)} tickers into {ASSETS_DIR}")

    success, skipped, failed = 0, 0, 0
    for ticker in tickers:
        # Skip if already downloaded
        existing = any((ASSETS_DIR / f"{ticker}.{ext}").exists() for ext in ("svg", "png", "ico"))
        if existing:
            skipped += 1
            continue

        data, ext = fetch_logo(ticker)
        if data and ext:
            out_path = ASSETS_DIR / f"{ticker}.{ext}"
            out_path.write_bytes(data)
            print(f"  ✓ {ticker}.{ext} ({len(data):,} bytes)")
            success += 1
        else:
            print(f"  ✗ {ticker} — no logo found")
            failed += 1

        time.sleep(0.1)

    print(f"\nDone: {success} downloaded, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
