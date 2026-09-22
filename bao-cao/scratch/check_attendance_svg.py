import re

with open('bao-cao/scratch/attendance.svg', 'r', encoding='utf-8') as f:
    svg_data = f.read()

polygons = re.findall(r'<polygon[^>]*fill="([^"]*)"', svg_data)
from collections import Counter
print("Polygon fills distribution:", Counter(polygons))

# Let's check how decision diamonds are represented
paths = re.findall(r'<path[^>]*fill="([^"]*)"', svg_data)
print("Path fills distribution:", Counter(paths))
