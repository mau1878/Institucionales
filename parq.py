import pandas as pd
general_data = pd.read_parquet("general_data.parquet", engine="pyarrow")
print(general_data.columns)