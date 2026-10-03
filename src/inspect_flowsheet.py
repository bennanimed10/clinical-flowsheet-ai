from pathlib import Path

data_file = Path("data/raw/nurseCharting.csv.gz")

print("Looking for:")
print(data_file)

print("Exists:", data_file.exists())