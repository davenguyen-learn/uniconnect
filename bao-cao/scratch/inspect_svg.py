with open('Images/test_cond_none.svg', 'r', encoding='utf-8') as f:
    c = f.read()

import re
polygons = re.findall(r'<polygon[^>]*points="([^"]*)"[^>]*fill="([^"]*)"', c)
for pts, fill in polygons:
    pt_list = pts.strip().split(',')
    print(f"Polygon fill={fill} points_count={len(pt_list)}")
