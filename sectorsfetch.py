import pandas as pd
import yfinance as yf

def add_sector_industry(parquet_path="general_data.parquet", output_path="general_data_with_info.parquet"):
    # Load parquet
    df = pd.read_parquet(parquet_path)

    # Prepare new columns
    df["Sector"] = None
    df["Industry"] = None

    for idx, ticker in enumerate(df["Ticker"]):
        # Handle BRK.B exception
        yf_ticker = "BRK-B" if ticker == "BRK.B" else ticker

        try:
            info = yf.Ticker(yf_ticker).info
            df.at[idx, "Sector"] = info.get("sector", None)
            df.at[idx, "Industry"] = info.get("industry", None)

            print(f"[{idx+1}/{len(df)}] {ticker}: sector={df.at[idx,'Sector']} | industry={df.at[idx,'Industry']}")
        except Exception as e:
            print(f"[{idx+1}/{len(df)}] {ticker}: error fetching data → {e}")

    # Save updated parquet
    df.to_parquet(output_path, index=False)
    print(f"\n✅ Saved enriched parquet to: {output_path}")

if __name__ == "__main__":
    add_sector_industry()
