import pandas as pd
from pathlib import Path

input_file = "data/processed/flowsheet_metrics.csv"
output_file = "data/processed/flowsheet_mapping.csv"

df = pd.read_csv(input_file)

df["standard_domain"] = ""
df["standard_metric"] = ""
df["ai_reason"] = ""
df["mapping_status"] = "PENDING"
df["mapping_source"] = ""

df.to_csv(output_file, index=False)

print(f"Created {len(df)} mappings")
print(df.head(10))