import plantuml
import re

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/svg/')
from scratch.test_single_unified import single_puml

svg = server.processes(single_puml).decode('utf-8')

diamonds = re.findall(r'<polygon[^>]*fill="#FFF8E1"[^>]*>', svg)
print(f"Amber Decision Diamonds: {len(diamonds)}")

empty_diamonds = re.findall(r'<polygon[^>]*fill="(?:#FFFFFF|none|transparent)"[^>]*>', svg)
print(f"Empty polygons: {len(empty_diamonds)}")

# Check for fork bar
fork_bars = re.findall(r'<rect[^>]*fill="#263238"[^>]*>', svg)
print(f"Fork bars: {len(fork_bars)}")
