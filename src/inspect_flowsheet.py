import pandas as pd
from pathlib import Path

input_file = "data/raw/nurseCharting.csv.gz"
output_file = "data/processed/flowsheet_metrics.csv"

Path("data/processed").mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_file)

metrics = (
    df.groupby(
        [
            "nursingchartcelltypecat",
            "nursingchartcelltypevallabel",
            "nursingchartcelltypevalname"
        ],
        dropna=False
    )
    .size()
    .reset_index(name="record_count")
    .sort_values("record_count", ascending=False)
)

metrics.to_csv(output_file, index=False)

print("Distinct flowsheet metrics:", len(metrics))
print(metrics.head(20))
print("\nSaved to:", output_file)