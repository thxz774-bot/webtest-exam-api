from pathlib import Path
from openpyxl import load_workbook

BASE = Path(__file__).resolve().parent.parent

TEMPLATE = BASE / "data" / "template.xlsx"

print("Abrindo:", TEMPLATE)

wb = load_workbook(TEMPLATE)

ws = wb["mod 1"]

for merged in ws.merged_cells.ranges:
    print(merged)