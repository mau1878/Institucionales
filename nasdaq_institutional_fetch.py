import requests
import pandas as pd
import time
import concurrent.futures
import logging
import re
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'es-AR,es;q=0.9,de-DE;q=0.8,de;q=0.7,es-419;q=0.6',
    'dnt': '1',
    'origin': 'https://www.nasdaq.com',
    'priority': 'u=1, i',
    'referer': 'https://www.nasdaq.com/',
    'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
}

tickers = [
    "PKX", "WB", "TEF", "TMUS", "PINS", "SPCE", "MSTR", "HL", "BKNG", "HMY",
    "ABEV", "ACN", "AEM", "TWLO", "BSBR", "VIST", "BRFS", "AIG", "PAAS", "SQ",
    "ABNB", "KGC", "BBD", "MRVL", "BP", "X", "MUX", "TX", "TSLA", "SPGI",
    "DOCU", "EA", "ADI", "GFI", "YY", "NEM", "DOW", "AMX", "LAC", "ARCO",
    "ARKK", "JNJ", "SHOP", "GE", "COST", "GILD", "QCOM", "RIO", "TXN", "ERIC",
    "NIO", "TSM", "SNOW", "AMAT", "MA", "FDX", "ROKU", "VALE", "BCS", "META",
    "UL", "COIN", "OXY", "JPM", "NOK", "GS", "MMM", "MELI", "HWM", "PEP",
    "MU", "HMC", "CAAP", "XOM", "ADBE", "TRIP", "DIA", "BAC", "PLTR", "GOLD",
    "QQQ", "GM", "ETSY", "LVS", "NFLX", "ORCL", "WMT", "SHEL", "DIS", "CDE",
    "UAL", "XLE", "HPQ", "EEM", "DD", "ABBV", "RTX", "BBVA", "BIIB", "AXP",
    "NU", "DEO", "MOS", "BABA", "GLOB", "SPOT", "AMD", "BMY", "SPY", "NXE",
    "MO", "RBLX", "RIOT", "C", "BHP", "SLB", "SBUX", "PYPL", "NKE", "AAL",
    "USB", "CRM", "GPRK", "HON", "V", "NVDA", "KO", "BRK.B", "ZM", "ABT",
    "AAPL", "AVGO", "CVX", "INTC", "VZ", "SYY", "XLF", "IWM", "F", "T",
    "KEEL", "KMB", "BA", "UGP", "UNH", "CSCO", "CAT", "HAL", "GOOGL", "MRK",
    "BG", "DAL", "UBER", "AAP", "CAH", "WBA", "MSI", "MSFT", "TGT", "INFY",
    "GGB", "ERJ", "HSY", "HD", "PHG", "IBN", "FCX", "AEG", "AZN", "WFC",
    "BKR", "EWZ", "MCD", "GSK", "LMT", "TM", "EBAY", "FSLR", "IBM", "CL",
    "VOD", "PANW", "JD", "PSX", "LLY", "BIOX", "BK", "SDA", "PFE", "SAN",
    "AMZN", "UNP", "SONY", "PAGS", "GLW", "BIDU", "CCL", "RACE", "ITUB",
    "PG", "NTES", "AMGN", "LRCX", "STNE", "PBR", "CAR", "UPST", "TV", "BB",
    "LYG", "DE", "LAR", "HUT", "MRNA", "ADP", "STLA", "IP", "SE", "MDLZ",
    "CVS", "SATL", "SID", "ISRG", "EQNR", "JMIA", "GT", "TS", "PM", "SCHW",
    "SWKS", "ARM", "DHR", "ORLY", "TJX", "ADGO", "SHPW", "DESP", "NTCO",
    "CBRD", "IBIT", "FXI", "ETHA", "GLD", "SH", "IEUR", "IBB", "VEA", "IVE",
    "IVW", "XLC", "XLY", "XLB", "XLI", "XLK", "XLV", "XLP", "XLRE", "BAK",
    "LND", "TIMB", "VIV", "SUZ", "ELP", "SBS", "EBR", "BBAR", "BMA", "CEPU",
    "CRESY", "EDN", "GGAL", "IRS", "LOMA", "PAM", "SUPV", "TEO", "TGS", "YPF",
    "ASML", "TEAM", "AI", "CLS", "CEG", "DECK", "RGTI", "PDD", "NOW", "TEM",
    "PATH", "VRTX", "VST", "XPEV", "PSQ", "VIG", "SLV", "IJH", "EWJ",
    "ANF", "XLU", "SPXL", "URA", "CIBR", "SMH", "B", "USO", "EFA", "IEMG",
    "ACWI", "GDX", "IWDA", "TQQQ", "VXX", "ITA", "SPHQ", "HOOD", "CRWV", "OKLO",
    "RKLB", "ALAB", "ASTS", "IREN", "ECL", "COPX", "ILF", "IVV", "ESGU", "ICLN",
    "EWY", "XME", "RSP", "CRWD", "ANET", "O", "GLNG", "SNDK", "NBIS", "HIMS",
    "ONDS", "COP", "NEE", "MP", "CCJ", "FISV"
]

# Carpeta destino: raíz del repo (relativo), o la que se pase por env var OUTPUT_DIR
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", ".")

institutional_data = []
general_data = []


def clean_number(value):
    """Convierte strings tipo '$1,234,567', '(1,234)' o 'NEW' a float. None si no se puede."""
    if value is None or value in ("N/A", "", "NEW"):
        return None
    s = str(value).strip()
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[^0-9.\-]", "", s)
    if s in ("", "-"):
        return None
    try:
        num = float(s)
        return -abs(num) if negative else num
    except ValueError:
        return None


def fetch_all_pages(ticker, base_params):
    all_data = []
    offset = 0
    params = base_params.copy()
    url = f"https://api.nasdaq.com/api/company/{ticker}/institutional-holdings"
    while True:
        params['offset'] = offset
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            data = response.json()

            holders_info = data.get("data", {}).get("holdingsTransactions", {}).get("table", {}).get("rows", [])
            if not holders_info:
                break

            for holder in holders_info:
                all_data.append([
                    ticker,
                    holder.get("ownerName", "N/A"),
                    holder.get("date", "N/A"),
                    clean_number(holder.get("sharesHeld")),
                    clean_number(holder.get("sharesChange")),
                ])

            total_records = int(data.get("data", {}).get("holdingsTransactions", {}).get("totalRecords", 0) or 0)
            if len(all_data) >= total_records:
                break
            offset += len(holders_info)
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error fetching data for {ticker} at offset {offset}: {e}")
            break

    return all_data


def fetch_ticker_data(ticker):
    logging.info(f"Starting data fetch for ticker: {ticker}")
    base_params = {
        'limit': '100',
        'type': 'TOTAL',
        'sortColumn': 'marketValue',
    }
    url = f"https://api.nasdaq.com/api/company/{ticker}/institutional-holdings"
    try:
        response = requests.get(url, params=base_params, headers=headers, timeout=30)
        data = response.json()

        general_info = data.get("data", {}).get("ownershipSummary", {})
        total_shares = clean_number(general_info.get("ShareoutstandingTotal", {}).get("value"))
        institutional_pct = clean_number(general_info.get("SharesOutstandingPCT", {}).get("value"))
        holdings_value = clean_number(general_info.get("TotalHoldingsValue", {}).get("value"))

        general_row = [ticker, total_shares, institutional_pct, holdings_value]

        inst_rows = fetch_all_pages(ticker, base_params)

        time.sleep(1)
        logging.info(f"Completed data fetch for ticker: {ticker}")
        return general_row, inst_rows

    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None, None


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_ticker_data, tickers)

    for general_row, inst_rows in results:
        if general_row is not None:
            general_data.append(general_row)
        if inst_rows is not None:
            institutional_data.extend(inst_rows)

    inst_df = pd.DataFrame(
        institutional_data,
        columns=["Ticker", "Owner Name", "Date", "Shares Held", "Shares Change"],
    )
    inst_df["Date"] = pd.to_datetime(inst_df["Date"], errors="coerce")

    gen_df = pd.DataFrame(
        general_data,
        columns=["Ticker", "Total Shares Outstanding", "Institutional Ownership %", "Total Holdings Value"],
    )

    inst_path = os.path.join(OUTPUT_DIR, "institutional_holders.parquet")
    gen_path = os.path.join(OUTPUT_DIR, "general_data.parquet")

    # Acumular histórico: si ya existe el parquet, concatenar y deduplicar
    # (mismo Ticker+Owner+Date se pisa con el dato más reciente).
    if os.path.exists(inst_path):
        existing_inst = pd.read_parquet(inst_path)
        inst_df = pd.concat([existing_inst, inst_df], ignore_index=True)
        inst_df = inst_df.drop_duplicates(subset=["Ticker", "Owner Name", "Date"], keep="last")

    inst_df.to_parquet(inst_path, index=False)
    gen_df.to_parquet(gen_path, index=False)

    logging.info(f"Data fetching complete. Saved {inst_path} and {gen_path}.")


if __name__ == "__main__":
    main()
