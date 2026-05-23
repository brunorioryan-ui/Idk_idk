import base64
import os
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "logos"

TICKER_DOMAIN = {
    "AAPL": "apple.com", "MSFT": "microsoft.com", "GOOGL": "google.com", "GOOG": "google.com",
    "AMZN": "amazon.com", "META": "meta.com", "TSLA": "tesla.com", "NVDA": "nvidia.com",
    "BRK-B": "berkshirehathaway.com", "BRK-A": "berkshirehathaway.com",
    "UNH": "unitedhealthgroup.com", "XOM": "exxonmobil.com", "JNJ": "jnj.com",
    "JPM": "jpmorganchase.com", "V": "visa.com", "PG": "pg.com", "MA": "mastercard.com",
    "HD": "homedepot.com", "CVX": "chevron.com", "LLY": "lilly.com",
    "MRK": "merck.com", "ABBV": "abbvie.com", "PEP": "pepsico.com", "KO": "coca-cola.com",
    "AVGO": "broadcom.com", "COST": "costco.com", "ADBE": "adobe.com", "CRM": "salesforce.com",
    "TMO": "thermofisher.com", "MCD": "mcdonalds.com", "NKE": "nike.com", "ORCL": "oracle.com",
    "ACN": "accenture.com", "PM": "pmi.com", "AMD": "amd.com", "INTC": "intel.com",
    "QCOM": "qualcomm.com", "TXN": "ti.com", "NFLX": "netflix.com", "DIS": "disney.com",
    "BA": "boeing.com", "GE": "ge.com", "CAT": "caterpillar.com", "DE": "deere.com",
    "UPS": "ups.com", "FDX": "fedex.com", "SBUX": "starbucks.com", "WMT": "walmart.com",
    "TGT": "target.com", "AMGN": "amgen.com", "GILD": "gilead.com", "BMY": "bms.com",
    "PFE": "pfizer.com", "CVS": "cvshealth.com", "CI": "cigna.com", "HUM": "humana.com",
    "AXP": "americanexpress.com", "GS": "goldmansachs.com", "MS": "morganstanley.com",
    "BAC": "bankofamerica.com", "WFC": "wellsfargo.com", "C": "citigroup.com",
    "USB": "usbank.com", "PNC": "pnc.com", "TRV": "travelers.com",
    "LOW": "lowes.com", "TJX": "tjx.com", "BKNG": "booking.com", "MAR": "marriott.com",
    "GM": "gm.com", "F": "ford.com", "UBER": "uber.com", "LYFT": "lyft.com",
    "ABNB": "airbnb.com", "DASH": "doordash.com", "SNAP": "snap.com", "PINS": "pinterest.com",
    "TWTR": "twitter.com", "SPOT": "spotify.com", "RBLX": "roblox.com", "U": "unity.com",
    "PLTR": "palantir.com", "SNOW": "snowflake.com", "DDOG": "datadoghq.com",
    "NET": "cloudflare.com", "ZS": "zscaler.com", "CRWD": "crowdstrike.com",
    "PANW": "paloaltonetworks.com", "FTNT": "fortinet.com", "OKTA": "okta.com",
    "MU": "micron.com", "KLAC": "kla.com", "LRCX": "lamresearch.com", "AMAT": "appliedmaterials.com",
    "ADI": "analog.com", "MCHP": "microchip.com", "SWKS": "skyworksinc.com",
    "NOW": "servicenow.com", "WDAY": "workday.com", "TEAM": "atlassian.com",
    "ZM": "zoom.us", "DOCU": "docusign.com", "BILL": "bill.com",
    "SQ": "block.xyz", "PYPL": "paypal.com", "COIN": "coinbase.com",
    "SHOP": "shopify.com", "W": "wayfair.com", "ETSY": "etsy.com",
    "Z": "zillow.com", "OPEN": "opendoor.com",
    "T": "att.com", "VZ": "verizon.com", "TMUS": "t-mobile.com",
    "CHTR": "charter.com", "CMCSA": "comcast.com",
    "NEE": "nexteraenergy.com", "DUK": "duke-energy.com", "SO": "southerncompany.com",
    "D": "dominionenergy.com", "AEP": "aep.com",
    "LIN": "linde.com", "APD": "airproducts.com", "ECL": "ecolab.com",
    "AMT": "americantower.com", "PLD": "prologis.com", "EQIX": "equinix.com",
    "SPG": "simon.com", "O": "realtyincome.com",
    "BTC-USD": "bitcoin.org", "ETH-USD": "ethereum.org",
    # ETFs
    "SPY": "ssga.com", "QQQ": "invesco.com", "IWM": "blackrock.com",
    "DIA": "ssga.com", "VTI": "vanguard.com", "VOO": "vanguard.com",
    "XLK": "ssga.com", "XLF": "ssga.com", "XLV": "ssga.com",
    "XLE": "ssga.com", "XLI": "ssga.com", "XLY": "ssga.com",
    "XLP": "ssga.com", "XLU": "ssga.com", "XLRE": "ssga.com",
    "XLB": "ssga.com", "XLC": "ssga.com",
    "GLD": "ssga.com", "SLV": "blackrock.com", "USO": "uscfinvestments.com",
    "TLT": "blackrock.com", "HYG": "blackrock.com", "LQD": "blackrock.com",
    "ARKK": "ark-funds.com", "ARKG": "ark-funds.com",
}


def get_logo_path(ticker: str) -> Path | None:
    for ext in ("svg", "png", "ico", "jpg"):
        p = ASSETS_DIR / f"{ticker}.{ext}"
        if p.exists():
            return p
    return None


def get_logo_b64(ticker: str, fallback_size: int = 32) -> str | None:
    path = get_logo_path(ticker)
    if path is None:
        return None
    try:
        data = path.read_bytes()
        mime = {
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".jpg": "image/jpeg",
        }.get(path.suffix, "image/png")
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def logo_img_tag(ticker: str, size: int = 32, css_class: str = "") -> str:
    src = get_logo_b64(ticker)
    if src:
        cls = f' class="{css_class}"' if css_class else ""
        return f'<img src="{src}" width="{size}" height="{size}" style="border-radius:4px;object-fit:contain;"{cls}/>'
    initials = ticker.replace("^", "").replace("-", "")[:2].upper()
    colors = ["#5c9bd6", "#26a69a", "#ffa726", "#ab47bc", "#ef5350", "#42a5f5"]
    color = colors[sum(ord(c) for c in ticker) % len(colors)]
    return (
        f'<div style="width:{size}px;height:{size}px;background:{color};border-radius:4px;'
        f'display:inline-flex;align-items:center;justify-content:center;'
        f'font-size:{size // 2 - 2}px;font-weight:bold;color:white;">{initials}</div>'
    )
