import plantuml

s = plantuml.PlantUML('http://www.plantuml.com/plantuml/img/')

code = """@startdot
graph G {
  node [fontname="Arial", fontsize=10];
  user [shape=box, label="User", style=filled, fillcolor="#E1F5FE", color="#0288D1"];
  create [shape=diamond, label="Create", style=filled, fillcolor="#E1F5FE", color="#0288D1"];
  u_id [shape=ellipse, label=<<u>ID</u>>, style=filled, fillcolor="#E1F5FE", color="#0288D1"];
  user -- create [label="1"];
  user -- u_id;
}
@enddot"""

try:
    data = s.processes(code)
    print("DOT SUCCESS, len =", len(data))
    with open("scratch/test_dot.png", "wb") as f:
        f.write(data)
except Exception as e:
    print("DOT FAILED:", e)
