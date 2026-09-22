import plantuml
import re

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/svg/')
from scratch.generate_pure_uml import p1, p2

svg1 = server.processes(p1).decode('utf-8')
svg2 = server.processes(p2).decode('utf-8')

print("=== PART 1 SVG ELEMENTS ===")
diamonds_1 = re.findall(r'<polygon[^>]*fill="#FFF8E1"[^>]*>', svg1)
print(f"Amber decision diamonds count: {len(diamonds_1)}")
for d in diamonds_1:
    print(" ", d)

empty_1 = re.findall(r'<polygon[^>]*fill="(?:#FFFFFF|none|transparent)"[^>]*>', svg1)
print(f"Empty polygons count: {len(empty_1)}")

print("\n=== PART 2 SVG ELEMENTS ===")
diamonds_2 = re.findall(r'<polygon[^>]*fill="#FFF8E1"[^>]*>', svg2)
print(f"Amber decision diamonds count: {len(diamonds_2)}")
for d in diamonds_2:
    print(" ", d)

empty_2 = re.findall(r'<polygon[^>]*fill="(?:#FFFFFF|none|transparent)"[^>]*>', svg2)
print(f"Empty polygons count: {len(empty_2)}")

# Check for fork bar
fork_bars = re.findall(r'<rect[^>]*fill="#263238"[^>]*>', svg2)
print(f"Fork bars count in Part 2: {len(fork_bars)}")
