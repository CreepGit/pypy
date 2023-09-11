from __future__ import annotations

map = [
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
columns = len(map[0])
rows = len(map)

class Node:
    def __init__(self, x:int, y:int, came_from: Node):
        self.x = x
        self.y = y
        self.came_from = came_from
        self.g = None
        self.f = None
    
    def __eq__(self, o: Node):
        return hash(o) == hash(self)

    def __hash__(self):
        return hash((self.x, self.y))
    
    def __repr__(self):
        return f"<N:{self.x},{self.y}>"

    def corresponding_node_in_map(self):
        return map[self.y][self.x]

def get_neighbours(node: Node):
    offsets = [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1),]
    collect_neighbours: list[tuple] = []
    for offset in offsets:
        dx, dy = offset
        new_x, new_y = (dx+node.x, dy+node.y)
        if (new_x < 0): continue
        if (new_y < 0): continue
        if (new_x >= columns): continue
        if (new_y >= rows): continue
        collect_neighbours.append((new_x, new_y))
    return collect_neighbours

def h(node: Node, goal: Node):
    import math
    val = math.sqrt(node.x*node.x + goal.x*goal.x)
    return int(10*val)

def d(frm: Node, to: Node):
    """Distance function"""
    dx = abs(frm.x - to.x)
    dy = abs(frm.y - to.y)
    if (dx > 0 and dy > 0):
        # Both changed
        return 14 + to.corresponding_node_in_map() * 10
    return 10 + to.corresponding_node_in_map() * 10

def a_start(start: Node, goal: Node, hf: callable):
    open_set:set[Node] = set()
    open_set.add(start)

    start.g = 0

    f_score = {}
    f_score[start] = hf(start, goal)

    while len(open_set) > 0:
        current:Node = min(open_set, key=lambda n: f_score[n])
        if current == goal:
            print("Found goal")
            return current
        open_set.remove(current)

        for spot in get_neighbours(current):
            print(spot)
            neighbour_node: Node = Node(spot[0], spot[1], None)
            new_g_score = current.g + d(current, neighbour_node)
            if (new_g_score >= (neighbour_node.g or 10**6)):
                # This path is worse or same, skip it
                continue
            neighbour_node.came_from = current
            f_score[neighbour_node] = new_g_score + hf(neighbour_node, goal)
            neighbour_node.g = new_g_score
            neighbour_node.f = new_g_score + hf(neighbour_node, goal)
            open_set.add(neighbour_node)
    
    print("Ran out of nodes, FAILED")


start = Node(3, 3, None)
end = Node(11, 6, None)

goal = a_start(start, end, h)

walk_back = goal
while (walk_back):
    print(walk_back, walk_back.g, walk_back.f)
    map[walk_back.y][walk_back.x] = "o"

    walk_back = walk_back.came_from

def draw_map():
    for row in map:
        for item in row:
            if item == 0:
                print(".", end="")
            elif item == 9:
                print("[", end="")
            else:
                print(item, end="")
        print()
    print()

draw_map()
