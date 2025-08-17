import pandas as pd
general_data = pd.read_parquet("general_data.parquet", engine="pyarrow")
print(general_data.columns)
institutional_holders = pd.read_parquet("institutional_holders.parquet", engine="pyarrow")
print(institutional_holders.columns)