import plantuml, re
server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/svg/')
from scratch.generate_attendance_diagram import puml_content

svg = server.processes(puml_content).decode('utf-8')
diamonds = re.findall(r'<polygon[^>]*fill="#FFF8E1"[^>]*>', svg)
print(f'Amber Decision Diamonds: {len(diamonds)}')

empty_diamonds = re.findall(r'<polygon[^>]*fill="(?:#FFFFFF|none|transparent)"[^>]*>', svg)
print(f'Empty polygons: {len(empty_diamonds)}')
