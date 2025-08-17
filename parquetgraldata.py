import pandas as pd

def preview_general_data(parquet_path="general_data.parquet", n=10):
    try:
        df = pd.read_parquet(parquet_path)

        print("\n=== Primeras filas ===")
        print(df.head(n))

        print("\n=== Información general ===")
        print(f"Filas: {len(df)}")
        print(f"Columnas: {len(df.columns)}")
        print("Nombres de columnas:", list(df.columns))

        print("\n=== Tipos de datos ===")
        print(df.dtypes)

        print("\n=== Valores faltantes por columna ===")
        print(df.isna().sum())

    except Exception as e:
        print(f"Error al leer el archivo parquet: {e}")

def preview_institutional_holders(parquet_path="institutional_holders.parquet", n=10):
    try:
        df = pd.read_parquet(parquet_path)

        print("\n=== Primeras filas ===")
        print(df.head(n))

        print("\n=== Información general ===")
        print(f"Filas: {len(df)}")
        print(f"Columnas: {len(df.columns)}")
        print("Nombres de columnas:", list(df.columns))

        print("\n=== Tipos de datos ===")
        print(df.dtypes)

        print("\n=== Valores faltantes por columna ===")
        print(df.isna().sum())

    except Exception as e:
        print(f"Error al leer el archivo parquet: {e}")
if __name__ == "__main__":
    preview_general_data()
    preview_institutional_holders()
