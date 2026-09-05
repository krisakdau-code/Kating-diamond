# app.py — Universal Trading Terminal (TradingView-Style Watchlist Icons & Color Ribbons)
import time
import datetime
import requests
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_lightweight_charts_ntf import renderLightweightCharts

try:
    import yfinance as yf
except ImportError:
    yf = None

# ──────────────────────────── CONFIG ────────────────────────────
st.set_page_config(
    page_title="Diamond Armor Universal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    BITKUB_API_KEY = st.secrets.get("BITKUB_API_KEY", "")
except Exception:
    BITKUB_API_KEY = ""

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update(BROWSER_HEADERS)

GLOBAL_MARKET = "🌐 Global (Yahoo)"

TF = {
    "1m":  {"sec": 60,     "rule": "1min", "base": None, "yf_iv": "1m",  "yf_range": "7d"},
    "3m":  {"sec": 180,    "rule": "3min", "base": "1m", "yf_iv": "5m",  "yf_range": "60d"},
    "5m":  {"sec": 300,    "rule": "5min", "base": None, "yf_iv": "5m",  "yf_range": "60d"},
    "15m": {"sec": 900,    "rule": "15min","base": None, "yf_iv": "15m", "yf_range": "60d"},
    "30m": {"sec": 1800,   "rule": "30min","base": None, "yf_iv": "30m", "yf_range": "60d"},
    "1h":  {"sec": 3600,   "rule": "1H",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "2h":  {"sec": 7200,   "rule": "2H",   "base": "1h", "yf_iv": "60m", "yf_range": "730d"},
    "4h":  {"sec": 14400,  "rule": "4H",   "base": None, "yf_iv": "60m", "yf_range": "730d"},
    "6h":  {"sec": 21600,  "rule": "6H",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "8h":  {"sec": 28800,  "rule": "8H",   "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "12h": {"sec": 43200,  "rule": "12H",  "base": "1h", "yf_iv": "1d",  "yf_range": "5y"},
    "1d":  {"sec": 86400,  "rule": "1D",   "base": None, "yf_iv": "1d",  "yf_range": "10y"},
    "3d":  {"sec": 259200, "rule": "3D",   "base": "1d", "yf_iv": "1d",  "yf_range": "10y"},
    "1w":  {"sec": 604800, "rule": "1W",   "base": None, "yf_iv": "1wk", "yf_range": "10y"},
}

UP, DOWN = "#26a69a", "#ef5350"

# ──────────────────────────── SYMBOL FETCHERS ────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_binance_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://api.binance.com/api/v3/ticker/price", timeout=5)
        if r.status_code == 200:
            symbols = [i["symbol"] for i in r.json() if i.get("symbol", "").endswith("USDT")]
            if len(symbols) > 50: return sorted(symbols)
    except Exception: pass
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT", "PEPEUSDT", "NEARUSDT"]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_bitkub_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://api.bitkub.com/api/market/ticker", timeout=5)
        if r.status_code == 200:
            symbols = [f"{k[4:]}_THB" if k.startswith("THB_") else k for k in r.json().keys()]
            if len(symbols) > 20: return sorted(symbols)
    except Exception: pass
    return ["BTC_THB", "ETH_THB", "KUB_THB", "SOL_THB", "DOGE_THB", "XRP_THB", "USDT_THB", "ADA_THB", "NEAR_THB"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_bybit_all_symbols() -> list:
    for cat in ("spot", "linear"):
        try:
            r = HTTP_SESSION.get(f"https://api.bybit.com/v5/market/tickers?category={cat}", timeout=5)
            if r.status_code == 200:
                items = r.json().get("result", {}).get("list", [])
                symbols = [i["symbol"] for i in items if i.get("symbol", "").endswith("USDT")]
                if len(symbols) > 50: return sorted(symbols)
        except Exception: pass
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "MNTUSDT", "XRPUSDT", "DOGEUSDT", "TONUSDT"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_okx_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT", timeout=5)
        if r.status_code == 200:
            items = r.json().get("data", [])
            symbols = [i["instId"] for i in items if i.get("instId", "").endswith("-USDT")]
            if len(symbols) > 50: return sorted(symbols)
    except Exception: pass
    return ["BTC-USDT", "ETH-USDT", "SOL-USDT", "OKB-USDT", "XRP-USDT", "DOGE-USDT"]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_mexc_all_symbols() -> list:
    try:
        r = HTTP_SESSION.get("https://api.mexc.com/api/v3/ticker/price", timeout=5)
        if r.status_code == 200:
            symbols = [i["symbol"] for i in r.json() if i.get("symbol", "").endswith("USDT")]
            if len(symbols) > 50: return sorted(symbols)
    except Exception: pass
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "MXUSDT", "DOGEUSDT", "PEPEUSDT", "SHIBUSDT"]

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_set_all_symbols() -> list:
    thai_stocks = [
        "2S", "7UP", "A", "AAV", "ABICO", "ABM", "ACAP", "ACC", "ACE", "ACG", "ADB", "ADD", "ADVANC", "AEC", "AEONTS", "AFC", "AGE", "AH", "AHC", "AI", "AIE", "AIRA", "AKR", "ALL", "ALLA", "ALPHAX", "ALT", "ALUCON", "AMANAH", "AMARIN", "AMATA", "AMATAV", "AMC", "ANAN", "AOT", "AP", "APCO", "APCS", "APEX", "APP", "APURE", "AQ", "AQUA", "ARIN", "ARIP", "ARROW", "ASAP", "ASEFA", "ASIA", "ASIAN", "ASIMAR", "ASK", "ASN", "ASP", "ASW", "ATP30", "AU", "AUCT", "AURA", "AWC", "AYUD",
        "B", "B52", "BA", "BAM", "BANPU", "BAY", "BBIK", "BBL", "BC", "BCH", "BCP", "BCPG", "BCT", "BDMS", "BEAUTY", "BEC", "BEM", "BEYOND", "BGC", "BGRIM", "BH", "BIG", "BIZ", "BJC", "BJCHI", "BKD", "BKI", "BLA", "BLAND", "BLISS", "BM", "BOL", "BPP", "BR", "BRI", "BROCK", "BROOK", "BRR", "BRRGIF", "BSBM", "BTG", "BTS", "BTSGIF", "BTW", "BWG", "BYD",
        "CAZ", "CBG", "CCET", "CCP", "CEN", "CENTEL", "CFRESH", "CGD", "CGH", "CHARAN", "CHEWA", "CHG", "CHO", "CHOTI", "CHOW", "CI", "CIG", "CIMBT", "CITY", "CIVIL", "CK", "CKP", "CM", "CMAN", "CMC", "CMO", "CMR", "CNT", "COLOR", "COMAN", "COM7", "CPALL", "CPF", "CPH", "CPL", "CPN", "CPNREIT", "CPR", "CPW", "CRANE", "CRC", "CRD", "CSC", "CSP", "CSR", "CSS", "CTW", "CWT",
        "D", "DCON", "DDD", "DELTA", "DEMCO", "DHOUSE", "DIMET", "DITTO", "DMT", "DOD", "DOHOME", "DRT", "DTCENT", "DUSIT",
        "EA", "EARTH", "EASON", "EASTW", "ECL", "EE", "EFORL", "EGCO", "EKH", "EMC", "EP", "EPG", "ERW", "ESSO", "ESTAR", "ETC", "ETE", "EVER",
        "F&D", "FANCY", "FE", "FLOYD", "FMT", "FN", "FNS", "FORTH", "FPI", "FPT", "FSMART", "FSS", "FTE", "FTREIT", "FUTUREPF",
        "GBX", "GC", "GCAP", "GEL", "GENCO", "GFPT", "GGC", "GIFT", "GL", "GLAND", "GLOBAL", "GLOCON", "GPI", "GPSC", "GRAMMY", "GRAND", "GREEN", "GSC", "GTB", "GULF", "GUNKUL",
        "HANA", "HARN", "HENG", "HFT", "HL", "HMPRO", "HTC", "HUMAN", "HYDRO",
        "ICHI", "ICN", "IFS", "IHL", "IIG", "III", "ILINK", "ILM", "IMH", "INET", "INGRS", "INOX", "INSURE", "INTUCH", "IP", "IRC", "IRPC", "IT", "ITD", "ITEL", "ITNS", "IVL",
        "J", "JAS", "JCK", "JCKH", "JCT", "JMART", "JMT", "JR", "JSP", "JTS", "JUBILE", "JWD",
        "KAMART", "KBANK", "KBS", "KC", "KCAR", "KCE", "KDH", "KEX", "KGI", "KIAT", "KISS", "KKP", "KROB", "KSL", "KTB", "KTC", "KTIS", "KWI", "KYE",
        "L&E", "LALIN", "LANNA", "LDC", "LEE", "LH", "LHFG", "LIT", "LOXLEY", "LPH", "LRH", "LST",
        "M", "MACO", "MAJOR", "MAKRO", "MALEE", "MATCH", "MATI", "MBAX", "MBK", "MC", "M-CHAI", "MCS", "MDX", "MEGA", "METCO", "MFC", "MGC", "MICRO", "MILL", "MINT", "MODERN", "MONO", "MOONG", "MORE", "MOSHI", "MSC", "MTC", "MTI", "MVP",
        "NATION", "NC", "NCH", "NCL", "NDR", "NER", "NETBAY", "NEWS", "NEX", "NFC", "NKI", "NNCL", "NOBLE", "NRF", "NSL", "NUSA", "NVD", "NYT",
        "ONEE", "OR", "ORI", "OSP", "OTO",
        "PACO", "PAP", "PATO", "PB", "PCSGH", "PDG", "PDJ", "PERM", "PF", "PG", "PHOL", "PICO", "PIMO", "PJW", "PK", "PL", "PLANB", "PLANET", "PLAT", "PLE", "PM", "PMTA", "PORT", "POST", "PR9", "PRAPAT", "PREB", "PRECHA", "PRIME", "PRIN", "PRINC", "PRM", "PROEN", "PROUD", "PSH", "PSL", "PT", "PTG", "PTL", "PTT", "PTTEP", "PTTGC", "PYLON",
        "Q-CON", "QH", "QLT", "QTC", "QTCG",
        "RATCH", "RBF", "RCL", "RICHY", "RJH", "ROJNA", "RP", "RPC", "RPH", "RS", "RWI",
        "S", "S11", "SABINA", "SABUY", "SAFARI", "SALEE", "SAM", "SAMART", "SAMCO", "SAMTEL", "SANKO", "SAPPE", "SAT", "SAUCE", "SAWAD", "SC", "SCB", "SCC", "SCCC", "SCGP", "SCI", "SCM", "SCN", "SCP", "SDC", "SE", "SE-ED", "SEAFCO", "SEAOIL", "SECURE", "SELIC", "SENA", "SENAJ", "SFT", "SGF", "SGP", "SHR", "SICT", "SIMAT", "SINGER", "SIRI", "SIS", "SISB", "SKE", "SKN", "SKR", "SKY", "SLP", "SMART", "SMT", "SNC", "SNP", "SO", "SOLAR", "SONIC", "SPA", "SPALI", "SPC", "SPCG", "SPRC", "SPVI", "SQ", "SR", "SRICHA", "SSC", "SSF", "SSP", "SSSC", "SST", "STA", "STANLY", "STAR", "STEC", "STGT", "STI", "STOWER", "STP", "STPI", "SUC", "SUN", "SUPER", "SUTHA", "SVI", "SVOA", "SWC", "SYNEX", "SYNTEC",
        "TACC", "TAE", "TAKUNI", "TAPAC", "TASCO", "TCAP", "TCC", "TCMC", "TEAM", "TEAMG", "TEGH", "TFG", "TFI", "TFM", "TFMAMA", "TGH", "TGPRO", "THAI", "THANI", "THCOM", "THE", "THG", "THIP", "THREL", "TIDLOR", "TIGER", "TIPH", "TISCO", "TITLE", "TK", "TKC", "TKN", "TKS", "TM", "TMC", "TMD", "TMI", "TMILL", "TMT", "TNDT", "TNH", "TNITY", "TNL", "TNP", "TNPC", "TNR", "TOA", "TOG", "TOP", "TOPP", "TPA", "TPAC", "TPBI", "TPCH", "TPIPL", "TPIPP", "TPLAS", "TPOLY", "TPP", "TPS", "TQR", "TRC", "TRITN", "TRT", "TRU", "TRUBB", "TRUE", "TSE", "TSTH", "TTA", "TTB", "TTCL", "TTW", "TU", "TVO", "TVT", "TWPC", "TYCN",
        "UAC", "UBE", "UBIS", "UEC", "UKEM", "UMI", "UMS", "UNIQ", "UPOIC", "UREKA", "UTP", "UV", "UVAN",
        "VARO", "VGI", "VIBHA", "VIH", "VL", "VNG", "VPO", "VRANDA",
        "WAVE", "WGE", "WHA", "WHAUP", "WICE", "WIN", "WINDOW", "WINNER", "WORK", "WP", "WPH",
        "XO", "XPG", "YGG", "YUASA", "ZIGA"
    ]
    return sorted([f"{s}.BK" for s in set(thai_stocks)])

DEFAULT_PRESETS = {
    "🟡 คริปโต (Crypto)": {
        "Bitkub": fetch_bitkub_all_symbols(),
        "Binance": fetch_binance_all_symbols(),
        "Bybit": fetch_bybit_all_symbols(),
        "OKX": fetch_okx_all_symbols(),
        "MEXC": fetch_mexc_all_symbols(),
    },
    "🇹🇭 หุ้นไทย (SET)": fetch_set_all_symbols(),
    "🇺🇸 หุ้นสหรัฐฯ (US Stocks)": ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "SPY", "QQQ", "PLTR", "AMD", "COIN"],
    "🇨🇳 หุ้นจีน (China)": ["600519.SS", "002594.SZ", "000001.SS", "601398.SS", "000858.SZ"],
    "🇻🇳 หุ้นเวียดนาม (Vietnam)": ["VNM.VN", "VIC.VN", "HPG.VN", "VCB.VN", "^VNINDEX"],
    "🟠 สินค้าโภคภัณฑ์ (Commodities)": ["GC=F", "SI=F", "CL=F", "BZ=F", "HG=F", "RR=F", "ZC=F"],
    "🟢 อัตราแลกเปลี่ยน (Forex)": ["USDTHB=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"]
}

COMMODITY_NAMES = {
    "GC=F": "ทองคำ", "SI=F": "เงิน", "CL=F": "น้ำมันWTI",
    "BZ=F": "น้ำมันBrent", "HG=F": "ทองแดง", "RR=F": "ข้าว", "ZC=F": "ข้าวโพด"
}

STAR_CATEGORIES = {
    "🔴 ดาวแดง": {"icon": "🔴", "symbol": "●", "color": "#ef5350"},
    "🟡 ดาวเหลือง": {"icon": "🟡", "symbol": "●", "color": "#f5c518"},
    "🟢 ดาวเขียว": {"icon": "🟢", "symbol": "●", "color": "#26a69a"},
    "🔵 ดาวฟ้า": {"icon": "🔵", "symbol": "●", "color": "#2962ff"},
    "🟣 ดาวม่วง": {"icon": "🟣", "symbol": "●", "color": "#ab47bc"}
}

# ──────────────────────────── SESSION STATES ────────────────────────────
if "star_watchlists" not in st.session_state:
    st.session_state["star_watchlists"] = {
        "🔴 ดาวแดง": ["BTC_THB", "NVDA", "ETH_THB"],
        "🟡 ดาวเหลือง": ["SOL_THB", "GC=F"],
        "🟢 ดาวเขียว": ["PTT.BK", "CL=F", "DELTA.BK"],
        "🔵 ดาวฟ้า": ["BTCUSDT", "TSLA"],
        "🟣 ดาวม่วง": ["USDTHB=X"]
    }
if "custom_symbols" not in st.session_state: st.session_state["custom_symbols"] = []
if "show_rsi" not in st.session_state: st.session_state["show_rsi"] = True
if "show_macd" not in st.session_state: st.session_state["show_macd"] = True
if "pane_order" not in st.session_state: st.session_state["pane_order"] = ["rsi", "macd"]

# ──────────────────────────── CSS UI ────────────────────────────
st.markdown("""
<style>
    [data-testid="stMainBlockContainer"],
    [data-testid="block-container"],
    .block-container {
        padding-top: 0.2rem !important; padding-bottom: 0rem !important;
        padding-left: 0px !important; padding-right: 0px !important;
        margin-left: 0px !important; margin-right: 0px !important;
        max-width: 100% !important; width: 100% !important;
    }
    [data-testid="stSidebar"] { border-right: 1px solid #2a2e39 !important; }
    [data-testid="stSidebarContent"] {
        padding-left: 0.5rem !important; padding-right: 0.5rem !important;
        padding-top: 0.6rem !important; max-height: 100vh !important; overflow-y: auto !important;
    }
    [data-testid="stSidebarContent"]::-webkit-scrollbar { width: 3px; }
    [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb { background: #2a2e39; border-radius: 3px; }
    div[data-testid="stHorizontalBlock"] { gap: 2px !important; }
    div[data-testid="column"] { padding: 0px !important; }
    div[data-testid="stExpander"] {
        border: 1px solid #2a2e39; border-radius: 6px;
        background-color: #131722; margin-bottom: 6px;
    }
    header[data-testid="stHeader"] { background: transparent !important; height: 1.2rem !important; }
    .stButton button { padding: 2px 4px !important; font-size: 11px !important; }

    /* ปุ่มติดดาวด้านซ้าย */
    div.st-key-qs_btn_0 button { border: 1.5px solid #ef5350 !important; color: #ef5350 !important; font-size: 14px !important; }
    div.st-key-qs_btn_1 button { border: 1.5px solid #f5c518 !important; color: #f5c518 !important; font-size: 14px !important; }
    div.st-key-qs_btn_2 button { border: 1.5px solid #26a69a !important; color: #26a69a !important; font-size: 14px !important; }
    div.st-key-qs_btn_3 button { border: 1.5px solid #2962ff !important; color: #2962ff !important; font-size: 14px !important; }
    div.st-key-qs_btn_4 button { border: 1.5px solid #ab47bc !important; color: #ab47bc !important; font-size: 14px !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #0e1117; padding: 2px; border-radius: 6px; }
    .stTabs [data-baseweb="tab"] { padding: 4px 8px !important; font-size: 11px !important; border-radius: 4px !important; }

    /* Header ตาราง Watchlist สไตล์ TradingView */
    .tv-wl-header {
        display: grid; 
        grid-template-columns: 0.7fr 1.8fr 1.5fr 1.3fr 1.3fr 0.4fr;
        padding: 6px 4px; font-size: 10px; font-weight: 600; color: #787b86;
        border-bottom: 1px solid #2a2e39; margin-bottom: 4px;
    }

    .pane-toolbar {
        background: #131722; border: 1px solid #2a2e39; border-bottom: none;
        border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 2px 8px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 11px; font-weight: 600; color: #d1d4dc; margin-top: 2px;
    }
    div[data-testid="column"]:has(div[data-testid="stExpander"]) {
        max-height: 89vh !important; overflow-y: auto !important;
        overflow-x: hidden !important; padding-right: 4px !important;
    }
    div[data-testid="column"]:has(div[data-testid="stExpander"])::-webkit-scrollbar { width: 4px; }
    div[data-testid="column"]:has(div[data-testid="stExpander"])::-webkit-scrollbar-thumb { background: #2a2e39; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────── ROUTER ────────────────────────────
def resolve_route(symbol: str, ui_market: str, ui_exchange: str):
    s = (symbol or "").upper()
    if s.endswith(".BK"):
        return "🇹🇭 หุ้นไทย (SET)", "Yahoo"
    if s.endswith("_THB") or s.startswith("THB_"):
        return "🟡 คริปโต (Crypto)", "Bitkub"
    if s.endswith("-USDT"):
        return "🟡 คริปโต (Crypto)", "OKX"
    if s.endswith("USDT"):
        ex = ui_exchange if ui_exchange in ("Binance", "Bybit", "MEXC") else "Binance"
        return "🟡 คริปโต (Crypto)", ex
    if "คริปโต" in ui_market:
        return GLOBAL_MARKET, "Yahoo"
    return ui_market, ui_exchange


def route_label(r_market: str, r_exchange: str) -> str:
    if "คริปโต" in r_market: return r_exchange
    if r_market == GLOBAL_MARKET: return "Yahoo"
    return r_market.split()[0]


# ──────────────────────────── RESAMPLE / GAP-FILL ────────────────────────────
def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    if df.empty: return df
    d = df.copy()
    d["datetime"] = pd.to_datetime(d["time"], unit="s")
    d = d.set_index("datetime")
    out = d.resample(rule).agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
    }).dropna()
    out["time"] = (out.index.astype("int64") // 10**9).astype("int64")
    return out.reset_index(drop=True)


def fill_empty_bars(df: pd.DataFrame, sec: int, max_fill: int = 20000) -> pd.DataFrame:
    if df.empty or len(df) < 2: return df
    base = df.drop_duplicates(subset=["time"]).sort_values("time").copy()
    base["time"] = (base["time"].astype("int64") // sec) * sec
    base = base.drop_duplicates(subset=["time"]).set_index("time")

    start, end = int(base.index[0]), int(base.index[-1])
    if (end - start) // sec > max_fill: return df

    full_idx = np.arange(start, end + sec, sec, dtype="int64")
    out = base.reindex(full_idx)
    synth = out["close"].isna().values

    out["close"]  = out["close"].ffill()
    out["open"]   = out["open"].fillna(out["close"])
    out["high"]   = out["high"].fillna(out["close"])
    out["low"]    = out["low"].fillna(out["close"])
    out["volume"] = out["volume"].fillna(0.0)
    out["is_synthetic"] = synth

    out = out.dropna(subset=["close"])
    out.index.name = "time"
    return out.reset_index()


# ──────────────────────────── BITKUB FETCH ────────────────────────────
def fetch_bitkub_raw(symbol: str, tf_code: str, sec: int, bars: int) -> pd.DataFrame:
    all_chunks = []
    curr_to = int(time.time())
    headers = dict(BROWSER_HEADERS)
    if BITKUB_API_KEY and len(BITKUB_API_KEY) > 20:
        headers["X-BTK-APIKEY"] = BITKUB_API_KEY

    total, max_loops = 0, 400
    window     = sec * 1000
    max_window = sec * 300000
    min_window = sec * 500
    empty_streak, oldest_seen = 0, None
    floor_ts = 1451606400

    for _ in range(max_loops):
        if total >= bars: break
        frm = max(curr_to - window, floor_ts)
        if frm >= curr_to: break

        try:
            r = HTTP_SESSION.get(
                "https://api.bitkub.com/tradingview/history",
                headers=headers,
                params={"symbol": symbol, "resolution": tf_code, "from": frm, "to": curr_to},
                timeout=5,
            )
            if r.status_code == 429:
                time.sleep(1.0); continue
            if r.status_code != 200: break
            j = r.json()
        except Exception: break

        status = j.get("s")
        if status == "no_data":
            nxt = j.get("nextTime")
            if nxt and int(nxt) < curr_to:
                curr_to = int(nxt) + sec
                window  = sec * 1000
            else:
                curr_to = frm - 1
                window  = min(window * 4, max_window)
            empty_streak += 1
            if empty_streak >= 10: break
            continue

        if status != "ok" or not j.get("t"): break
        t_list = j["t"]
        if not t_list: break

        all_chunks.append(pd.DataFrame({
            "time": t_list, "open": j["o"], "high": j["h"],
            "low": j["l"], "close": j["c"], "volume": j["v"],
        }))
        total += len(t_list)
        empty_streak = 0

        min_t = int(min(t_list))
        if oldest_seen is not None and min_t >= oldest_seen: break
        oldest_seen = min_t

        expected = max(1, window // sec)
        density  = len(t_list) / expected
        if density < 0.25:
            window = min(int(window * 3), max_window)
        elif len(t_list) >= 900:
            window = max(min_window, int(window * 0.6))

        curr_to = min_t - 1
        if len(t_list) < 200: break

    if not all_chunks: return pd.DataFrame()
    df = pd.concat(all_chunks, ignore_index=True)
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
    return df.dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)


# ──────────────────────────── OTHER EXCHANGES ────────────────────────────
def fetch_binance_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    out, end_ts = [], None
    while len(out) < bars:
        limit = min(1000, bars - len(out))
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_ts: params["endTime"] = end_ts
        try:
            r = HTTP_SESSION.get("https://api.binance.com/api/v3/klines", params=params, timeout=5)
            if r.status_code != 200: break
            k = r.json()
            if not k or not isinstance(k, list): break
            out = k + out
            new_end = k[0][0] - 1
            if end_ts and new_end >= end_ts: break
            end_ts = new_end
            if len(k) < limit: break
        except Exception: break

    if not out: return pd.DataFrame()
    df = pd.DataFrame(out, columns=["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"])
    df = df[["ot","open","high","low","close","volume"]].astype(float)
    df["time"] = (df["ot"] // 1000).astype("int64")
    return df[["time","open","high","low","close","volume"]].dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)


def fetch_bybit_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    m = {"1m":"1","3m":"3","5m":"5","15m":"15","30m":"30","1h":"60","2h":"120",
         "4h":"240","6h":"360","12h":"720","1d":"D","1w":"W"}
    b_iv = m.get(interval, "60")
    out, end_ts, category = [], None, "spot"

    while len(out) < bars:
        limit = min(1000, bars - len(out))
        params = {"category": category, "symbol": symbol, "interval": b_iv, "limit": limit}
        if end_ts: params["end"] = end_ts
        try:
            r = HTTP_SESSION.get("https://api.bybit.com/v5/market/kline", params=params, timeout=5)
            if r.status_code != 200: break
            k = r.json().get("result", {}).get("list", [])
            if not k and not out and category == "spot":
                category = "linear"; params["category"] = "linear"
                r = HTTP_SESSION.get("https://api.bybit.com/v5/market/kline", params=params, timeout=5)
                if r.status_code == 200:
                    k = r.json().get("result", {}).get("list", [])
            if not k: break
            out.extend(k)
            new_end = int(k[-1][0]) - 1
            if end_ts and new_end >= end_ts: break
            end_ts = new_end
            if len(k) < limit: break
        except Exception: break

    if not out: return pd.DataFrame()
    df = pd.DataFrame(out, columns=["time","open","high","low","close","volume","turnover"])
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = (pd.to_numeric(df["time"], errors="coerce") // 1000).astype("int64")
    return df[["time","open","high","low","close","volume"]].dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)


def fetch_okx_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    m = {"1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m","1h":"1H","2h":"2H",
         "4h":"4H","6h":"6H","12h":"12H","1d":"1D","1w":"1W"}
    bar_code = m.get(interval, "1H")
    out, after = [], None
    clean_sym = symbol if "-" in symbol else f"{symbol[:-4]}-USDT"

    while len(out) < bars:
        limit = min(300, bars - len(out))
        params = {"instId": clean_sym, "bar": bar_code, "limit": limit}
        if after: params["after"] = after
        try:
            r = HTTP_SESSION.get("https://www.okx.com/api/v5/market/candles", params=params, timeout=5)
            if r.status_code != 200: break
            k = r.json().get("data", [])
            if not k: break
            out.extend(k)
            new_after = k[-1][0]
            if after and new_after == after: break
            after = new_after
            if len(k) < limit: break
        except Exception: break

    if not out: return pd.DataFrame()
    cols = ["ts","open","high","low","close","volume","volCcy","volCcyQuote","confirm"]
    df = pd.DataFrame(out, columns=cols[:len(out[0])])
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = (pd.to_numeric(df["ts"], errors="coerce") // 1000).astype("int64")
    return df[["time","open","high","low","close","volume"]].dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)


def fetch_mexc_raw(symbol: str, interval: str, bars: int) -> pd.DataFrame:
    m = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"60m","4h":"4h","1d":"1d","1w":"1W"}
    m_iv = m.get(interval, "60m")
    out, end_ts = [], None
    while len(out) < bars:
        limit = min(1000, bars - len(out))
        params = {"symbol": symbol, "interval": m_iv, "limit": limit}
        if end_ts: params["endTime"] = end_ts
        try:
            r = HTTP_SESSION.get("https://api.mexc.com/api/v3/klines", params=params, timeout=5)
            if r.status_code != 200: break
            k = r.json()
            if not k or not isinstance(k, list): break
            out = k + out
            new_end = k[0][0] - 1
            if end_ts and new_end >= end_ts: break
            end_ts = new_end
            if len(k) < limit: break
        except Exception: break

    if not out: return pd.DataFrame()
    df = pd.DataFrame(out, columns=["ot","open","high","low","close","volume","ct","qv"][:len(out[0])])
    df = df[["ot","open","high","low","close","volume"]].astype(float)
    df["time"] = (df["ot"] // 1000).astype("int64")
    return df[["time","open","high","low","close","volume"]].dropna().drop_duplicates(subset=["time"]).sort_values("time").tail(bars).reset_index(drop=True)


# ──────────────────────────── YAHOO ────────────────────────────
def parse_yahoo_json(j: dict) -> pd.DataFrame:
    try:
        result = j.get("chart", {}).get("result", [])
        if not result: return pd.DataFrame()
        res = result[0]
        ts = res.get("timestamp", [])
        q = res.get("indicators", {}).get("quote", [{}])[0]
        if not ts or not q: return pd.DataFrame()
        o, h, l, c, v = q.get("open", []), q.get("high", []), q.get("low", []), q.get("close", []), q.get("volume", [])
        rows = []
        for i in range(len(ts)):
            if ts[i] is not None and i < len(c) and c[i] is not None:
                rows.append({
                    "time": ts[i],
                    "open": o[i] if (i < len(o) and o[i] is not None) else c[i],
                    "high": h[i] if (i < len(h) and h[i] is not None) else c[i],
                    "low":  l[i] if (i < len(l) and l[i] is not None) else c[i],
                    "close": c[i],
                    "volume": v[i] if (i < len(v) and v[i] is not None) else 0.0
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def fetch_yahoo_rest_api(symbol: str, tf: str, bars: int) -> pd.DataFrame:
    tf_info = TF.get(tf, TF["1d"])
    urls = [
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
    ]
    df = pd.DataFrame()

    for url in urls:
        try:
            r = HTTP_SESSION.get(url, params={"interval": tf_info["yf_iv"], "range": tf_info.get("yf_range", "60d")}, timeout=3.5)
            if r.status_code == 200:
                df = parse_yahoo_json(r.json())
                if not df.empty and len(df) >= 3: break
        except Exception: pass

    if df.empty or len(df) < 3:
        for fb in [{"interval":"1d","range":"5y"}, {"interval":"60m","range":"730d"}]:
            for url in urls:
                try:
                    r = HTTP_SESSION.get(url, params=fb, timeout=3.5)
                    if r.status_code == 200:
                        df = parse_yahoo_json(r.json())
                        if not df.empty and len(df) >= 3: break
                except Exception: pass
            if not df.empty and len(df) >= 3: break

    if (df.empty or len(df) < 3) and yf is not None:
        try:
            hist = yf.Ticker(symbol).history(period="2y", interval="1d")
            if not hist.empty:
                hist = hist.reset_index()
                tcol = "Datetime" if "Datetime" in hist.columns else "Date"
                hist["time"] = (pd.to_datetime(hist[tcol]).astype("int64") // 10**9).astype("int64")
                hist = hist.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
                df = hist[["time","open","high","low","close","volume"]]
        except Exception: pass

    if df.empty: return pd.DataFrame()

    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")
    df = df.dropna().drop_duplicates(subset=["time"]).sort_values("time")

    if tf_info["base"] is not None and len(df) > 50:
        df = resample_ohlcv(df, tf_info["rule"])
    return df.tail(bars).reset_index(drop=True)


# ──────────────────────────── UNIFIED FETCH ────────────────────────────
def fetch_ohlcv(market_type: str, exchange: str, symbol: str,
                tf: str, bars: int, fill_gaps: bool = False) -> pd.DataFrame:
    tf_info = TF[tf]

    if "คริปโต" in market_type:
        if exchange == "Bitkub":
            native = {"1m":"1","5m":"5","15m":"15","30m":"30","1h":"60","4h":"240","1d":"1D","1w":"1W"}
            if tf in native:
                df = fetch_bitkub_raw(symbol, native[tf], tf_info["sec"], bars)
            else:
                base_tf = tf_info["base"] or "1h"
                mult    = max(1, tf_info["sec"] // TF[base_tf]["sec"])
                df = fetch_bitkub_raw(symbol, native.get(base_tf, "60"),
                                      TF[base_tf]["sec"], min(bars * mult, 25000))
                if not df.empty: df = resample_ohlcv(df, tf_info["rule"])

            if fill_gaps and not df.empty:
                df = fill_empty_bars(df, tf_info["sec"]).tail(bars).reset_index(drop=True)

        elif exchange == "Binance":
            native = ["1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w"]
            if tf in native:
                df = fetch_binance_raw(symbol, tf, bars)
            else:
                base_tf = tf_info["base"] or "1h"
                mult    = max(1, tf_info["sec"] // TF[base_tf]["sec"])
                df = fetch_binance_raw(symbol, base_tf, min(bars * mult, 25000))
                if not df.empty: df = resample_ohlcv(df, tf_info["rule"])
        elif exchange == "Bybit":
            df = fetch_bybit_raw(symbol, tf, bars)
        elif exchange == "OKX":
            df = fetch_okx_raw(symbol, tf, bars)
        else:
            df = fetch_mexc_raw(symbol, tf, bars)
    else:
        df = fetch_yahoo_rest_api(symbol, tf, bars)

    if df is None or df.empty: return pd.DataFrame()
    return df.tail(bars).reset_index(drop=True)


# ──────────────────────────── TICKERS ────────────────────────────
@st.cache_data(ttl=5, show_spinner=False)
def get_bitkub_all_tickers() -> dict:
    out = {}
    for url in ("https://api.bitkub.com/api/v3/market/ticker", "https://api.bitkub.com/api/market/ticker"):
        try:
            r = HTTP_SESSION.get(url, timeout=3)
            if r.status_code != 200: continue
            res = r.json()
            data = res.get("result", res) if isinstance(res, dict) else res
            items = [(d.get("symbol", ""), d) for d in data if isinstance(d, dict)] if isinstance(data, list) else list(data.items())
            for k, v in items:
                if not k or not isinstance(v, dict): continue
                k = str(k).upper()
                base = k[4:] if k.startswith("THB_") else k.replace("_THB", "")
                if not base: continue
                out[f"{base}_THB"] = v
                out[f"THB_{base}"] = v
            if out: return out
        except Exception: pass
    return out


def bitkub_pick(symbol: str) -> dict:
    bk = get_bitkub_all_tickers()
    s = (symbol or "").upper()
    base = s[4:] if s.startswith("THB_") else s.replace("_THB", "")
    return bk.get(f"{base}_THB", {}) or bk.get(f"THB_{base}", {}) or {}


@st.cache_data(ttl=15, show_spinner=False)
def fetch_item_quote(sym: str) -> dict:
    try:
        s = (sym or "").upper()

        if s.endswith("_THB") or s.startswith("THB_"):
            d = bitkub_pick(s)
            if d:
                return {"price": float(d.get("last", 0)), "change": float(d.get("change", 0)),
                        "pct": float(d.get("percentChange", d.get("percent_change", 0))),
                        "vol": float(d.get("baseVolume", d.get("base_volume", 0)))}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        if s.endswith("USDT") and "-" not in s:
            r = HTTP_SESSION.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}", timeout=3)
            if r.status_code == 200:
                d = r.json()
                return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                        "pct": float(d["priceChangePercent"]), "vol": float(d["volume"])}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        if s.endswith("-USDT"):
            r = HTTP_SESSION.get(f"https://www.okx.com/api/v5/market/ticker?instId={s}", timeout=3)
            if r.status_code == 200:
                d = (r.json().get("data") or [{}])[0]
                if d:
                    p = float(d.get("last", 0)); op = float(d.get("open24h", p) or p)
                    chg = p - op; pct = (chg / op * 100) if op > 0 else 0
                    return {"price": p, "change": chg, "pct": pct, "vol": float(d.get("vol24h", 0))}
            return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}

        r = HTTP_SESSION.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d", timeout=3)
        if r.status_code == 200:
            meta = (r.json().get("chart", {}).get("result") or [{}])[0].get("meta", {})
            p = float(meta.get("regularMarketPrice", 0))
            prev = float(meta.get("chartPreviousClose", meta.get("previousClose", p)) or p)
            chg = p - prev; pct = (chg / prev * 100.0) if prev > 0 else 0.0
            if p > 0:
                return {"price": p, "change": chg, "pct": pct, "vol": float(meta.get("regularMarketVolume", 0))}
    except Exception: pass
    return {"price": 0.0, "change": 0.0, "pct": 0.0, "vol": 0.0}


def fmt_vol(v: float) -> str:
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.2f}M"
    if v >= 1e3: return f"{v/1e3:.1f}K"
    return f"{v:.0f}" if v > 0 else "0"

def fmt_price(p: float) -> str:
    if p >= 1000: return f"{p:,.2f}"
    if p >= 1: return f"{p:.4f}"
    return f"{p:.6f}" if p > 0 else "0.00"

def fmt_chg(c: float) -> str:
    s = "+" if c > 0 else ""
    if abs(c) >= 100: return f"{s}{c:,.2f}"
    if abs(c) >= 1: return f"{s}{c:.2f}"
    return f"{s}{c:.4f}" if abs(c) > 0 else "0.00"


def fetch_unified_ticker(market_type: str, exchange: str, symbol: str, df_last: pd.DataFrame) -> dict:
    try:
        if "คริปโต" in market_type:
            if exchange == "Bitkub":
                d = bitkub_pick(symbol)
                if d:
                    return {"price": float(d.get("last", 0)), "change": float(d.get("change", 0)),
                            "pct": float(d.get("percentChange", d.get("percent_change", 0))),
                            "bid": float(d.get("highestBid", d.get("highest_bid", 0))),
                            "ask": float(d.get("lowestAsk", d.get("lowest_ask", 0))),
                            "high": float(d.get("high24hr", d.get("high_24_hr", d.get("high", 0)))),
                            "low": float(d.get("low24hr", d.get("low_24_hr", d.get("low", 0)))),
                            "vol": float(d.get("baseVolume", d.get("base_volume", 0)))}
            elif exchange == "Binance":
                r = HTTP_SESSION.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                            "pct": float(d["priceChangePercent"]), "bid": float(d["bidPrice"]),
                            "ask": float(d["askPrice"]), "high": float(d["highPrice"]),
                            "low": float(d["lowPrice"]), "vol": float(d["volume"])}
            elif exchange == "Bybit":
                r = HTTP_SESSION.get(f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}", timeout=3)
                lst = r.json().get("result", {}).get("list", []) if r.status_code == 200 else []
                if not lst:
                    r = HTTP_SESSION.get(f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}", timeout=3)
                    lst = r.json().get("result", {}).get("list", []) if r.status_code == 200 else []
                if lst:
                    d = lst[0]; p = float(d.get("lastPrice", 0))
                    pct = float(d.get("price24hPcnt", 0)) * 100
                    prev = p / (1 + pct/100) if (1 + pct/100) != 0 else p
                    return {"price": p, "change": p - prev, "pct": pct,
                            "bid": float(d.get("bid1Price", p)), "ask": float(d.get("ask1Price", p)),
                            "high": float(d.get("highPrice24h", p)), "low": float(d.get("lowPrice24h", p)),
                            "vol": float(d.get("volume24h", 0))}
            elif exchange == "OKX":
                cs = symbol if "-" in symbol else f"{symbol[:-4]}-USDT"
                r = HTTP_SESSION.get(f"https://www.okx.com/api/v5/market/ticker?instId={cs}", timeout=3)
                if r.status_code == 200:
                    d = (r.json().get("data") or [{}])[0]
                    if d:
                        p = float(d.get("last", 0)); op = float(d.get("open24h", p) or p)
                        chg = p - op; pct = (chg / op * 100) if op > 0 else 0
                        return {"price": p, "change": chg, "pct": pct,
                                "bid": float(d.get("bidPx", p)), "ask": float(d.get("askPx", p)),
                                "high": float(d.get("high24h", p)), "low": float(d.get("low24h", p)),
                                "vol": float(d.get("vol24h", 0))}
            elif exchange == "MEXC":
                r = HTTP_SESSION.get(f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}", timeout=3)
                if r.status_code == 200:
                    d = r.json()
                    return {"price": float(d["lastPrice"]), "change": float(d["priceChange"]),
                            "pct": float(d["priceChangePercent"]), "bid": float(d["bidPrice"]),
                            "ask": float(d["askPrice"]), "high": float(d["highPrice"]),
                            "low": float(d["lowPrice"]), "vol": float(d["volume"])}
        else:
            q = fetch_item_quote(symbol)
            if q["price"] > 0:
                return {"price": q["price"], "change": q["change"], "pct": q["pct"],
                        "bid": q["price"]*0.9998, "ask": q["price"]*1.0002,
                        "high": q["price"]*1.01, "low": q["price"]*0.99, "vol": q["vol"]}

        if not df_last.empty and len(df_last) >= 2:
            last, prev = df_last.iloc[-1], df_last.iloc[-2]
            chg = last.close - prev.close
            return {"price": float(last.close), "change": float(chg),
                    "pct": float(chg / prev.close * 100.0) if prev.close else 0.0,
                    "bid": float(last.close*0.9998), "ask": float(last.close*1.0002),
                    "high": float(df_last.tail(24)["high"].max()),
                    "low": float(df_last.tail(24)["low"].min()),
                    "vol": float(df_last.tail(24)["volume"].sum())}
    except Exception: pass
    return {}


# ──────────────────────────── INDICATORS ────────────────────────────
def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_analytics(market_type: str, exchange: str, symbol: str) -> dict:
    try:
        if "คริปโต" in market_type and exchange == "Bitkub":
            df = fetch_bitkub_raw(symbol, "1D", 86400, 380)
        elif "คริปโต" in market_type and exchange in ["Binance", "MEXC"]:
            base = "https://api.binance.com" if exchange == "Binance" else "https://api.mexc.com"
            r = HTTP_SESSION.get(f"{base}/api/v3/klines",
                                 params={"symbol": symbol, "interval": "1d", "limit": 375}, timeout=5)
            raw = r.json()
            if not raw: return {}
            cols = ["ot","open","high","low","close","volume","ct","qv","n","tb","tq","ig"][:len(raw[0])]
            df = pd.DataFrame(raw, columns=cols)[["ot","open","high","low","close","volume"]].astype(float)
            df["time"] = (df["ot"] // 1000).astype("int64")
        elif "คริปโต" in market_type and exchange == "Bybit":
            df = fetch_bybit_raw(symbol, "1d", 380)
        elif "คริปโต" in market_type and exchange == "OKX":
            df = fetch_okx_raw(symbol, "1d", 380)
        else:
            df = fetch_yahoo_rest_api(symbol, "1d", 380)

        if df is None or df.empty: return {}
        df = df.dropna().sort_values("time").reset_index(drop=True)
        if len(df) < 15: return {}

        now_p, n = df.iloc[-1]["close"], len(df)
        def ret(b): return (((now_p / df.iloc[-1-b]["close"]) - 1.0) * 100.0) if n > b else 0.0

        r1w, r1m, r3m, r6m, r1y = ret(7), ret(30), ret(90), ret(180), ret(365)
        jan1 = int(datetime.datetime(datetime.datetime.now().year, 1, 1).timestamp())
        ytd_df = df[df["time"] >= jan1]
        rytd = (((now_p / ytd_df.iloc[0]["close"]) - 1.0) * 100.0) if not ytd_df.empty else r1m

        rsi_val = rsi_wilder(df["close"], 14).iloc[-1]
        ema20 = df["close"].ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-1]
        score = (1 if rsi_val > 55 else (-1 if rsi_val < 45 else 0)) + (1 if now_p > ema20 else -1) + (1 if ema20 > ema50 else -1)

        if score >= 2:    lbl, col, ang = "มีแรงซื้อ", UP, 45
        elif score <= -2: lbl, col, ang = "มีแรงขาย", DOWN, -45
        else:             lbl, col, ang = "เป็นกลาง", "#9aa0a6", 0

        return {"vol_30d_avg": df.tail(30)["volume"].mean(), "1W": r1w, "1M": r1m, "3M": r3m,
                "6M": r6m, "YTD": rytd, "1Y": r1y, "tech_label": lbl, "tech_color": col, "angle": ang}
    except Exception:
        return {}


def diamond_armor(df: pd.DataFrame, fast=21, slow=55, rsi_len=14):
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["rsi"] = rsi_wilder(df["close"], rsi_len)
    df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    up_cross = (df.ema_fast > df.ema_slow) & (df.ema_fast.shift() <= df.ema_slow.shift())
    dn_cross = (df.ema_fast < df.ema_slow) & (df.ema_fast.shift() >= df.ema_slow.shift())

    if "is_synthetic" in df.columns:
        real = ~df["is_synthetic"].fillna(False).astype(bool)
        up_cross &= real
        dn_cross &= real

    df["signal"] = np.select([up_cross & (df.rsi > 45), dn_cross & (df.rsi < 55)],
                             ["BUY", "SELL ALL"], default="")

    last, prev = df.iloc[-1], df.iloc[-2]
    stats = {
        "price": last.close,
        "change_pct": (last.close / prev.close - 1) * 100 if prev.close else 0.0,
        "rsi": last.rsi,
        "trend": "UP" if last.ema_fast > last.ema_slow else "DOWN",
        "buys": int((df.signal == "BUY").sum()),
        "sells": int((df.signal == "SELL ALL").sum()),
        "bars": len(df),
    }
    return df, stats


# ──────────────────────────── QUOTE CARD ────────────────────────────
def render_tv_quote_card(tk: dict, an: dict, symbol: str, label_name: str):
    if not tk:
        st.caption("กำลังเชื่อมต่อข้อมูลราคา...")
        return

    c_color = UP if tk["change"] >= 0 else DOWN
    bg_pill = "rgba(38, 166, 154, 0.15)" if tk["change"] >= 0 else "rgba(239, 83, 80, 0.15)"
    sign = "+" if tk["change"] >= 0 else ""
    span = tk["high"] - tk["low"]
    ratio = max(0, min(100, ((tk["price"] - tk["low"]) / span * 100) if span > 0 else 50))
    vol_30d = f"{an.get('vol_30d_avg', 0):,.2f}" if an else "-"

    def p_box(lbl, val):
        col = UP if val >= 0 else DOWN
        bg = "rgba(38, 166, 154, 0.12)" if val >= 0 else "rgba(239, 83, 80, 0.12)"
        s = "+" if val >= 0 else ""
        return f"""<div style="background:{bg}; border:1px solid {col}40; border-radius:4px; padding:4px 2px; text-align:center;">
<div style="font-size:11px; font-weight:700; color:{col}; font-family:monospace;">{s}{val:.2f}%</div>
<div style="font-size:9px; color:#787b86;">{lbl}</div></div>"""

    grid_perf = ""
    if an:
        grid_perf = f"""<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:4px; margin-bottom:10px;">
{p_box('1W', an.get('1W',0))}{p_box('1M', an.get('1M',0))}{p_box('3M', an.get('3M',0))}
{p_box('6M', an.get('6M',0))}{p_box('YTD', an.get('YTD',0))}{p_box('1Y', an.get('1Y',0))}</div>"""
    else:
        grid_perf = """<div style="font-size:10px; color:#787b86; padding:6px 0;">ไม่มีข้อมูลย้อนหลังเพียงพอ</div>"""

    t_angle = an.get("angle", 0) if an else 0
    t_label = an.get("tech_label", "เป็นกลาง") if an else "เป็นกลาง"
    t_color = an.get("tech_color", "#9aa0a6") if an else "#9aa0a6"

    st.markdown(f"""<div style="background-color:#131722; border-radius:6px; padding:8px 6px; color:#d1d4dc; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
<span style="font-size:13px; font-weight:700; color:#fff;">{symbol}</span>
<span style="background:#2a2e39; color:#9aa0a6; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:600;">{label_name}</span></div>
<div style="font-size:9px; color:#787b86; margin-bottom:6px;">ตลาดเปิดสด</div>
<div style="font-size:20px; font-weight:700; color:#fff; letter-spacing:-0.5px; line-height:1.1;">{tk['price']:,.2f}</div>
<div style="display:inline-block; margin-top:3px; margin-bottom:8px; background:{bg_pill}; color:{c_color}; padding:1px 5px; border-radius:3px; font-size:10px; font-weight:700;">{sign}{tk['change']:,.2f} &nbsp; ({sign}{tk['pct']:.2f}%)</div>
<div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-bottom:8px; font-family:monospace;">
<div style="background:rgba(41,98,255,0.1); border:1px solid rgba(41,98,255,0.4); border-radius:4px; padding:3px; text-align:center;">
<div style="font-size:8px; color:#2962ff; font-weight:600;">BID (ซื้อ)</div>
<div style="font-size:10px; color:#d1d4dc; font-weight:700;">{tk['bid']:,.2f}</div></div>
<div style="background:rgba(239,83,80,0.1); border:1px solid rgba(239,83,80,0.4); border-radius:4px; padding:3px; text-align:center;">
<div style="font-size:8px; color:#ef5350; font-weight:600;">ASK (ขาย)</div>
<div style="font-size:10px; color:#d1d4dc; font-weight:700;">{tk['ask']:,.2f}</div></div></div>
<div style="font-size:9px; color:#787b86; margin-bottom:2px; font-weight:600;">ช่วง 24 ชม.</div>
<div style="display:flex; justify-content:space-between; font-size:9px; font-family:monospace; color:#9aa0a6; margin-bottom:2px;">
<span>{tk['low']:,.2f}</span><span>{tk['high']:,.2f}</span></div>
<div style="background:#2a2e39; height:3px; border-radius:2px; position:relative; margin-bottom:8px;">
<div style="position:absolute; left:{ratio}%; top:-3px; width:9px; height:9px; background:#fff; border:2px solid #2962ff; border-radius:50%; transform:translateX(-50%);"></div></div>
<div style="display:flex; justify-content:space-between; font-size:9px; padding:2px 0;">
<span style="color:#787b86;">ปริมาณ (24h)</span><span style="color:#d1d4dc; font-family:monospace; font-weight:600;">{tk['vol']:,.2f}</span></div>
<div style="display:flex; justify-content:space-between; font-size:9px; padding:2px 0; margin-bottom:8px;">
<span style="color:#787b86;">เฉลี่ย (30 วัน)</span><span style="color:#d1d4dc; font-family:monospace; font-weight:600;">{vol_30d}</span></div>
<div style="font-size:10px; font-weight:700; color:#fff; margin-bottom:4px; border-top:1px solid #2a2e39; padding-top:6px;">ประสิทธิภาพ</div>
{grid_perf}
<div style="font-size:10px; font-weight:700; color:#fff; margin-bottom:2px;">ทางเทคนิค</div>
<div style="text-align:center; margin-top:-4px;">
<svg width="130" height="68" viewBox="0 0 140 75">
<path d="M 15 70 A 55 55 0 0 1 125 70" fill="none" stroke="#2a2e39" stroke-width="8" stroke-linecap="round"/>
<path d="M 15 70 A 55 55 0 0 1 50 25" fill="none" stroke="{DOWN}" stroke-width="8" stroke-linecap="round"/>
<path d="M 90 25 A 55 55 0 0 1 125 70" fill="none" stroke="{UP}" stroke-width="8" stroke-linecap="round"/>
<g transform="translate(70, 70) rotate({t_angle})">
<line x1="0" y1="0" x2="0" y2="-50" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="0" cy="0" r="4" fill="#fff"/></g></svg>
<div style="font-size:12px; font-weight:700; color:{t_color}; margin-top:-6px;">{t_label}</div></div>
</div>""", unsafe_allow_html=True)


# ──────────────────────────── CHART BUILDER ────────────────────────────
def build_charts(df, symbol, tf, show_ema, show_vol, show_sig, label_size,
                 show_rsi, show_macd, pane_order, main_h, rsi_h, macd_h):
    d = df.copy()
    d["time"] = d["time"] + (7 * 3600)  # GMT+7

    ts_opts = {
        "borderColor": "#2a2e39", "timeVisible": True,
        "secondsVisible": tf in ("1m", "3m", "5m"),
        "fixLeftEdge": False, "rightOffset": 5,
        "handleScroll": {"mouseWheel": True, "pressedMouseMove": True,
                         "horzTouchDrag": True, "vertTouchDrag": True},
        "handleScale": {"axisPressedMouseMove": True, "mouseWheel": True, "pinch": True},
    }
    base_chart = {
        "layout": {"background": {"type": "solid", "color": "#0e1117"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#1c2030"}, "horzLines": {"color": "#1c2030"}},
        "crosshair": {"mode": 0},
        "rightPriceScale": {"borderColor": "#2a2e39"},
        "timeScale": ts_opts,
    }
    charts = []

    candles = d[["time","open","high","low","close"]].to_dict("records")
    price_series = [{"type": "Candlestick", "data": candles,
                     "options": {"upColor": UP, "downColor": DOWN, "borderVisible": False,
                                 "wickUpColor": UP, "wickDownColor": DOWN}}]

    if show_sig:
        markers = []
        for r in d[d.signal != ""].itertuples():
            is_buy = r.signal == "BUY"
            markers.append({"time": int(r.time), "position": "belowBar" if is_buy else "aboveBar",
                            "color": UP if is_buy else DOWN,
                            "shape": "arrowUp" if is_buy else "arrowDown",
                            "text": r.signal, "size": label_size})
        price_series[0]["markers"] = markers

    if show_ema:
        for col, color in (("ema_fast", "#f5c518"), ("ema_slow", "#8e7bff")):
            price_series.append({"type": "Line",
                                 "data": d[["time", col]].rename(columns={col: "value"}).to_dict("records"),
                                 "options": {"color": color, "lineWidth": 2, "priceLineVisible": False}})

    if show_vol:
        vol = [{"time": int(r.time), "value": float(r.volume),
                "color": UP + "80" if r.close >= r.open else DOWN + "80"} for r in d.itertuples()]
        price_series.append({"type": "Histogram", "data": vol,
                             "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol"},
                             "priceScale": {"scaleMargins": {"top": 0.8, "bottom": 0}}})

    charts.append({"chart": {**base_chart, "height": main_h,
                             "watermark": {"visible": True, "text": f"{symbol} · {tf}",
                                           "fontSize": 42, "color": "rgba(255,255,255,0.05)"}},
                   "series": price_series})

    def make_rsi_pane():
        rsi_data = d[["time","rsi"]].rename(columns={"rsi": "value"}).to_dict("records")
        mk = lambda v: [{"time": int(t), "value": v} for t in d["time"]]
        return {"chart": {**base_chart, "height": rsi_h,
                          "watermark": {"visible": True, "text": "RSI (14)", "fontSize": 18,
                                        "color": "rgba(0, 188, 212, 0.08)"}},
                "series": [
                    {"type": "Line", "data": mk(70.0), "options": {"color": "rgba(239,83,80,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                    {"type": "Line", "data": mk(50.0), "options": {"color": "rgba(120,123,134,0.3)", "lineWidth": 1, "lineStyle": 3, "priceLineVisible": False}},
                    {"type": "Line", "data": mk(30.0), "options": {"color": "rgba(38,166,154,0.4)", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False}},
                    {"type": "Line", "data": rsi_data, "options": {"color": "#00bcd4", "lineWidth": 2, "priceLineVisible": True}},
                ]}

    def make_macd_pane():
        macd_line = d[["time","macd"]].rename(columns={"macd": "value"}).to_dict("records")
        sig_line  = d[["time","macd_sig"]].rename(columns={"macd_sig": "value"}).to_dict("records")
        hist = [{"time": int(r.time), "value": float(r.macd_hist),
                 "color": UP + "90" if r.macd_hist >= 0 else DOWN + "90"} for r in d.itertuples()]

        mk_markers = []
        m_prev, s_prev = d["macd"].shift(), d["macd_sig"].shift()
        cross_up = (m_prev <= s_prev) & (d["macd"] > d["macd_sig"])
        cross_dn = (m_prev >= s_prev) & (d["macd"] < d["macd_sig"])
        for t in d.loc[cross_up, "time"]:
            mk_markers.append({"time": int(t), "position": "belowBar", "color": "#00E676", "shape": "circle", "size": 1})
        for t in d.loc[cross_dn, "time"]:
            mk_markers.append({"time": int(t), "position": "aboveBar", "color": "#FF1744", "shape": "circle", "size": 1})
        mk_markers.sort(key=lambda x: x["time"])

        line_macd = {"type": "Line", "data": macd_line,
                     "options": {"color": "#00e676", "lineWidth": 2, "priceLineVisible": False}}
        if mk_markers: line_macd["markers"] = mk_markers

        return {"chart": {**base_chart, "height": macd_h,
                          "watermark": {"visible": True, "text": "MACD (12, 26, 9)", "fontSize": 18,
                                        "color": "rgba(0, 230, 118, 0.08)"}},
                "series": [
                    {"type": "Histogram", "data": hist, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "macd_hist"}},
                    line_macd,
                    {"type": "Line", "data": sig_line, "options": {"color": "#ff5252", "lineWidth": 2, "priceLineVisible": False}},
                ]}

    for p in pane_order:
        if p == "rsi" and show_rsi:     charts.append(make_rsi_pane())
        elif p == "macd" and show_macd: charts.append(make_macd_pane())

    return charts


# ──────────────────────────── SIDEBAR ────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ ตั้งค่าตลาด")
    market_type = st.selectbox("หมวดหมู่สินทรัพย์", list(DEFAULT_PRESETS.keys()), index=0)

    exchange = "Binance"
    if "คริปโต" in market_type:
        exchange = st.radio("Exchange", ["Bitkub", "Binance", "Bybit", "OKX", "MEXC"], horizontal=True)
        raw_options = DEFAULT_PRESETS[market_type].get(exchange, [])
    else:
        raw_options = DEFAULT_PRESETS.get(market_type, [])

    available_symbols = sorted(set(raw_options + st.session_state["custom_symbols"]))
    if not available_symbols: available_symbols = ["BTC_THB"]

    if "current_symbol" not in st.session_state or not st.session_state["current_symbol"]:
        st.session_state["current_symbol"] = available_symbols[0]

    if st.session_state["current_symbol"] not in available_symbols:
        available_symbols = sorted(set(available_symbols + [st.session_state["current_symbol"]]))

    cur_idx = available_symbols.index(st.session_state["current_symbol"])
    picked = st.selectbox("🔍 ค้นหา / เลือกสินทรัพย์:", available_symbols, index=cur_idx)
    if picked != st.session_state["current_symbol"]:
        st.session_state["current_symbol"] = picked
        st.rerun()

    with st.expander("➕ เพิ่ม Ticker อื่นๆ"):
        new_ticker = st.text_input("ชื่อย่อ Ticker:", placeholder="เช่น SIRI, CPALL, BDMS.BK, PLTR")
        if st.button("บันทึก Ticker") and new_ticker:
            sym_clean = new_ticker.strip().upper()
            if market_type == "🇹🇭 หุ้นไทย (SET)" and not sym_clean.endswith(".BK"):
                sym_clean = f"{sym_clean}.BK"
            if sym_clean not in st.session_state["custom_symbols"]:
                st.session_state["custom_symbols"].append(sym_clean)
            st.session_state["current_symbol"] = sym_clean
            st.rerun()

    cur_sym = st.session_state["current_symbol"]
    _rm, _re = resolve_route(cur_sym, market_type, exchange)
    st.caption(f"📡 แหล่งข้อมูล: **{route_label(_rm, _re)}**")

    st.markdown("---")
    st.caption(f"⭐ ติดดาวให้กับ: **{cur_sym}**")

    # แผงปุ่มติดดาว 5 สี คมชัด ไม่ตกหล่น
    star_cols = st.columns(5)
    for i, (cat_label, cat_info) in enumerate(STAR_CATEGORIES.items()):
        with star_cols[i]:
            has = cur_sym in st.session_state["star_watchlists"][cat_label]
            btn_text = "★" if has else cat_info["symbol"]
            if st.button(btn_text, key=f"qs_btn_{i}", use_container_width=True, help=f"{cat_label}"):
                if has: st.session_state["star_watchlists"][cat_label].remove(cur_sym)
                else:   st.session_state["star_watchlists"][cat_label].append(cur_sym)
                st.rerun()

    st.markdown("---")
    tf = st.selectbox("Timeframe", list(TF.keys()), index=0)
    bars = st.slider("จำนวนแท่ง", 300, 25000, 3000, step=500)
    fill_gaps = st.checkbox(
        "🧩 เติมแท่งว่าง (เหรียญสภาพคล่องต่ำ)", value=False,
        help="ทำให้แกนเวลาต่อเนื่อง แต่ RSI จะเข้าหา 50 และ MACD แบนราบ (Bitkub เท่านั้น)"
    )

    st.markdown("---")
    auto = st.checkbox("🟢 Auto-refresh", True)
    every = st.slider("ความถี่ (วิ)", 3, 60, 5, step=1, disabled=not auto)
    reload_btn = st.button("🔄 โหลดใหม่ทั้งหมด")

    st.markdown("---")
    show_ema = st.checkbox("EMA 21 / 55", True)
    show_vol = st.checkbox("Volume", True)
    st.session_state["show_rsi"]  = st.checkbox("ช่อง RSI (14)", value=st.session_state["show_rsi"])
    st.session_state["show_macd"] = st.checkbox("ช่อง MACD", value=st.session_state["show_macd"])
    show_sig = st.checkbox("Signals (BUY/SELL)", True)
    label_size = st.slider("ขนาด label", 0, 3, 1)

    # ──────────────────────────── ควบคุมความสูงและการจัดการหน้าต่างย่อย ────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎛️ ปรับแต่งหน้าต่างกราฟ")
    if st.button("⇵ สลับตำแหน่ง RSI / MACD", use_container_width=True):
        st.session_state["pane_order"] = list(reversed(st.session_state["pane_order"]))
        st.rerun()

    main_h = st.slider("ความสูงกราฟหลัก", 300, 800, 500, step=50)
    rsi_h  = st.slider("ความสูง RSI", 80, 400, 140, step=20) if st.session_state["show_rsi"] else 140
    macd_h = st.slider("ความสูง MACD", 80, 400, 140, step=20) if st.session_state["show_macd"] else 140


# ──────────────────────────── RENDER ────────────────────────────
@st.fragment(run_every=every if auto else None)
def dashboard():
    symbol = st.session_state.get("current_symbol", "BTC_THB")
    r_market, r_exchange = resolve_route(symbol, market_type, exchange)
    label_display = route_label(r_market, r_exchange)

    state_key = f"{r_market}_{r_exchange}_{symbol}_{tf}_{bars}_{fill_gaps}"

    if ("df_data" not in st.session_state) or (st.session_state.get("active_key") != state_key) or reload_btn:
        with st.spinner(f"กำลังโหลดข้อมูล {symbol} …"):
            df = fetch_ohlcv(r_market, r_exchange, symbol, tf, bars, fill_gaps)
        st.session_state["df_data"] = df
        st.session_state["active_key"] = state_key
    else:
        df_latest = fetch_ohlcv(r_market, r_exchange, symbol, tf, 5, False)
        if not df_latest.empty and not st.session_state["df_data"].empty:
            merged = pd.concat([st.session_state["df_data"], df_latest], ignore_index=True)
            st.session_state["df_data"] = (merged.dropna(subset=["close"])
                                                 .drop_duplicates(subset=["time"], keep="last")
                                                 .sort_values("time").tail(bars).reset_index(drop=True))

    df = st.session_state.get("df_data", pd.DataFrame())

    if df.empty or len(df) < 3:
        st.warning(f"ไม่พบข้อมูลสำหรับ {symbol} ({label_display}) — หากตลาดปิดทำการ ให้เลือก Timeframe เป็น 1h หรือ 1d ครับ")
        return

    df, stats = diamond_armor(df)

    if len(df) < bars * 0.5:
        st.caption(f"⚠️ ได้ {len(df):,} แท่ง จาก {bars:,} ที่ขอ — {symbol} มีสภาพคล่องต่ำ "
                   f"ลองใช้ TF 15m/1h หรือเปิด 'เติมแท่งว่าง'")

    trend_color = UP if stats["trend"] == "UP" else DOWN
    chg_color = UP if stats["change_pct"] >= 0 else DOWN

    st.markdown(f"""
    <div style="background-color:#0D0F14; border:1px solid #2A2E39; border-radius:4px; padding:5px 12px;
    font-family:monospace; font-size:11px; color:#D1D4DC; margin-bottom:2px; line-height:1.4;
    display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="color:#00bcd4; font-weight:bold; font-size:12px;">📈 กำลังแสดง: {symbol}</span> &nbsp;
            <span style="background:#2a2e39; padding:1px 6px; border-radius:3px; font-size:10px; color:#9aa0a6;">{label_display}</span> &nbsp;|&nbsp;
            ราคา: <b>{stats['price']:,.2f}</b> &nbsp;|&nbsp;
            เปลี่ยน: <span style="color:{chg_color}; font-weight:bold;">{stats['change_pct']:+.2f}%</span> &nbsp;|&nbsp;
            RSI: <b>{stats['rsi']:.1f}</b> &nbsp;|&nbsp;
            เทรนด์: <span style="color:{trend_color}; font-weight:bold;">{stats['trend']}</span> &nbsp;|&nbsp;
            แท่ง: <b>{stats['bars']:,}</b> &nbsp;|&nbsp;
            BUY: <span style="color:{UP}; font-weight:bold;">{stats['buys']}</span> &nbsp;|&nbsp;
            SELL: <span style="color:{DOWN}; font-weight:bold;">{stats['sells']}</span>
        </div>
        <div style="font-size:10px; color:#787b86;">● LIVE ({time.strftime('%H:%M:%S')})</div>
    </div>""", unsafe_allow_html=True)

    charts = build_charts(df, symbol, tf, show_ema, show_vol, show_sig, label_size,
                          st.session_state["show_rsi"], st.session_state["show_macd"],
                          st.session_state["pane_order"], main_h, rsi_h, macd_h)

    if "panel_open" not in st.session_state: st.session_state["panel_open"] = True
    if "panel_size" not in st.session_state: st.session_state["panel_size"] = "ปกติ"
    size_map = {"เล็ก": [4.3, 0.7], "ปกติ": [3.7, 1.1], "กว้าง": [3.1, 1.4]}

    if st.session_state["panel_open"]:
        col_chart, col_quote = st.columns(size_map[st.session_state["panel_size"]])

        with col_chart:
            for p in st.session_state["pane_order"]:
                if p == "rsi" and st.session_state["show_rsi"]:
                    st.markdown('<div class="pane-toolbar"><span>📉 RSI (14) Indicator</span></div>', unsafe_allow_html=True)
                elif p == "macd" and st.session_state["show_macd"]:
                    st.markdown('<div class="pane-toolbar"><span>📊 MACD (12, 26, 9) Indicator</span></div>', unsafe_allow_html=True)

            renderLightweightCharts(charts, key=(
                f"chart_{r_market}_{r_exchange}_{symbol}_{tf}_{fill_gaps}_"
                f"{st.session_state['panel_open']}_{st.session_state['panel_size']}_"
                f"{st.session_state['show_rsi']}_{st.session_state['show_macd']}_"
                f"{main_h}_{rsi_h}_{macd_h}_{st.session_state['pane_order']}"
            ))

        with col_quote:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])
            with c1:
                if st.button("เล็ก", use_container_width=True): st.session_state["panel_size"] = "เล็ก"; st.rerun()
            with c2:
                if st.button("ปกติ", use_container_width=True): st.session_state["panel_size"] = "ปกติ"; st.rerun()
            with c3:
                if st.button("กว้าง", use_container_width=True): st.session_state["panel_size"] = "กว้าง"; st.rerun()
            with c4:
                if st.button("⏩ ย่อ", use_container_width=True): st.session_state["panel_open"] = False; st.rerun()

            with st.expander("⭐ รายการที่น่าสนใจ (Watchlist)", expanded=True):
                star_names = list(STAR_CATEGORIES.keys())
                tabs = st.tabs(star_names)
                for idx, cat_name in enumerate(star_names):
                    with tabs[idx]:
                        items = st.session_state["star_watchlists"][cat_name]
                        if not items:
                            st.caption("ยังไม่มีสินทรัพย์ในหมวดนี้ (กดปุ่มดาวที่เมนูด้านซ้ายเพื่อเพิ่ม)")
                        else:
                            st.markdown("""<div class="tv-wl-header">
                                <span></span>
                                <span>สัญลักษณ์</span>
                                <span style="text-align:right;">ล่าสุด</span>
                                <span style="text-align:right;">เปลี่ยน</span>
                                <span style="text-align:right;">เปลี่ยน%</span>
                                <span></span></div>""", unsafe_allow_html=True)

                            for s_item in list(items):
                                q = fetch_item_quote(s_item)
                                s_lbl = COMMODITY_NAMES.get(s_item, s_item.replace("_THB","").replace("-USDT","").replace("USDT","").replace(".BK",""))
                                val_col = UP if q["change"] >= 0 else DOWN
                                sign = "+" if q["change"] >= 0 else ""
                                tag_color = STAR_CATEGORIES[cat_name]["color"]

                                # ดึงโลโก้เหรียญทรงกลมสไตล์ TradingView พร้อม Fallback สำหรับหุ้น
                                clean_code = s_lbl.replace("=F", "").replace("=X", "")
                                clean_lower = clean_code.lower()
                                fallback_avatar = f"https://ui-avatars.com/api/?name={clean_code}&background=1e222d&color=d1d4dc&rounded=true&bold=true&size=64"
                                icon_url = f"https://assets.coincap.io/assets/icons/{clean_lower}@2x.png"

                                img_html = f"""<div style="display:flex; align-items:center; justify-content:center; height:28px; gap:4px;">
                                    <div style="width:3px; height:18px; border-radius:2px; background-color:{tag_color}; flex-shrink:0;"></div>
                                    <img src="{icon_url}" onerror="this.onerror=null;this.src='{fallback_avatar}';" style="width:20px; height:20px; border-radius:50%; object-fit:cover; background:#1c2030; border:1px solid #2a2e39;">
                                </div>"""

                                c_ico, a, b, c, dcol, f = st.columns([0.7, 1.8, 1.5, 1.3, 1.3, 0.4])
                                with c_ico:
                                    st.markdown(img_html, unsafe_allow_html=True)
                                with a:
                                    if st.button(f"{s_lbl}", key=f"wl_{cat_name}_{s_item}", use_container_width=True, help=f"ดูกราฟ {s_item}"):
                                        st.session_state["current_symbol"] = s_item
                                        st.rerun()
                                with b:
                                    st.markdown(f"<div style='font-family:monospace; font-size:11px; font-weight:600; text-align:right; padding-top:4px; color:#fff;'>{fmt_price(q['price'])}</div>", unsafe_allow_html=True)
                                with c:
                                    st.markdown(f"<div style='font-family:monospace; font-size:10px; font-weight:600; text-align:right; padding-top:4px; color:{val_col};'>{fmt_chg(q['change'])}</div>", unsafe_allow_html=True)
                                with dcol:
                                    st.markdown(f"<div style='font-family:monospace; font-size:10px; font-weight:600; text-align:right; padding-top:4px; color:{val_col};'>{sign}{q['pct']:.2f}%</div>", unsafe_allow_html=True)
                                with f:
                                    if st.button("✖", key=f"del_{cat_name}_{s_item}", help=f"ลบออกจาก {cat_name}"):
                                        st.session_state["star_watchlists"][cat_name].remove(s_item)
                                        st.rerun()

            with st.expander("📊 ข้อมูลตลาด 24h & เทคนิค", expanded=True):
                tk_data = fetch_unified_ticker(r_market, r_exchange, symbol, df)
                an_data = fetch_market_analytics(r_market, r_exchange, symbol)
                render_tv_quote_card(tk_data, an_data, symbol, label_display)

    else:
        col_chart, col_dock = st.columns([0.965, 0.035])
        with col_chart:
            renderLightweightCharts(charts, key=f"chart_{r_market}_{r_exchange}_{symbol}_{tf}_closed_{st.session_state['show_rsi']}_{st.session_state['show_macd']}")
        with col_dock:
            if st.button("◀", help="คลิกเพื่อเปิดแผงตลาดกลับมา", use_container_width=True):
                st.session_state["panel_open"] = True
                st.rerun()


dashboard()