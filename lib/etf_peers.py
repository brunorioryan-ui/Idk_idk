ETF_PEER_GROUPS = {
    "US Large Cap Blend": ["SPY", "VOO", "IVV", "SCHB", "VTI"],
    "US Large Cap Growth": ["QQQ", "VUG", "IWF", "SCHG", "SPYG"],
    "US Large Cap Value": ["VTV", "IWD", "SCHV", "SPYV", "RPV"],
    "US Small Cap": ["IWM", "VB", "IJR", "SCHA", "VIOO"],
    "US Mid Cap": ["IJH", "VO", "MDY", "SCHM", "IWR"],
    "International Developed": ["EFA", "VEA", "SCHF", "IEFA", "SPDW"],
    "Emerging Markets": ["EEM", "VWO", "IEMG", "SCHE", "GEM"],
    "Global": ["VT", "ACWI", "SPGM", "VEU"],
    "Technology": ["XLK", "VGT", "IGV", "SOXX", "SMH"],
    "Financials": ["XLF", "VFH", "KBE", "KRE"],
    "Health Care": ["XLV", "VHT", "IBB", "XBI"],
    "Energy": ["XLE", "VDE", "OIH", "XOP"],
    "Industrials": ["XLI", "VIS", "IYJ"],
    "Consumer Discretionary": ["XLY", "VCR", "ITB"],
    "Consumer Staples": ["XLP", "VDC", "KXI"],
    "Utilities": ["XLU", "VPU", "IDU"],
    "Real Estate": ["XLRE", "VNQ", "IYR", "SCHH"],
    "Materials": ["XLB", "VAW", "MXI"],
    "Communication Services": ["XLC", "VOX", "IXP"],
    "Bonds Aggregate": ["BND", "AGG", "SCHZ", "IUSB"],
    "Bonds Short Term": ["BSV", "SHY", "VGSH", "SCHO"],
    "Bonds Long Term": ["BLV", "TLT", "VGLT", "SCHQ"],
    "Bonds Treasury": ["GOVT", "IEI", "IEF", "TLT"],
    "Bonds Corporate": ["LQD", "VCIT", "USIG"],
    "Bonds High Yield": ["HYG", "JNK", "USHY", "FALN"],
    "Commodities": ["DJP", "PDBC", "COMT"],
    "Gold": ["GLD", "IAU", "SGOL", "GLDM"],
    "Dividend": ["VYM", "DVY", "SCHD", "HDV", "DGRO"],
    "ESG": ["ESGU", "ESGV", "CRBN", "SUSL"],
    "Multi-Factor": ["QUAL", "MTUM", "USMV", "VLUE"],
    "ARK Innovation": ["ARKK", "ARKW", "ARKQ", "ARKG", "ARKF"],
}


def find_peer_group(ticker: str) -> tuple[str, list[str]]:
    """Find the peer group for a given ETF ticker."""
    for group, peers in ETF_PEER_GROUPS.items():
        if ticker.upper() in peers:
            return group, [p for p in peers if p != ticker.upper()]
    return "Similar ETFs", []


def get_cheaper_alternatives(ticker: str, expense_ratio: float | None, peers_data: list) -> list:
    """Return list of cheaper alternatives with savings info."""
    if expense_ratio is None:
        return []
    alternatives = []
    for peer in peers_data:
        peer_er = peer.get("expense_ratio")
        if peer_er is not None and peer_er < expense_ratio:
            savings_bps = (expense_ratio - peer_er) * 10000
            savings_100k = (expense_ratio - peer_er) * 100_000
            alternatives.append({
                **peer,
                "savings_bps": savings_bps,
                "savings_100k": savings_100k,
            })
    return sorted(alternatives, key=lambda x: x.get("expense_ratio", 999))
