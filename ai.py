from flask import Flask, request
from structs import *
from Dijkstra import *
import json
import numpy
import math

app = Flask(__name__)

def create_action(action_type, target):
    actionContent = ActionContent(action_type, target.__dict__)
    return json.dumps(actionContent.__dict__)

def create_move_action(target):
    return create_action("MoveAction", target)

def create_attack_action(target):
    return create_action("AttackAction", target)

def create_collect_action(target):
    return create_action("CollectAction", target)

def create_steal_action(target):
    return create_action("StealAction", target)

def create_heal_action():
    return create_action("HealAction", "")

def create_purchase_action(item):
    return create_action("PurchaseAction", item)

def deserialize_map(serialized_map):
    """
    Fonction utilitaire pour comprendre la map
    """
    serialized_map = serialized_map[1:]
    rows = serialized_map.split('[')
    column = rows[0].split('{')
    deserialized_map = [[Tile() for x in range(40)] for y in range(40)]
    for i in range(len(rows) - 1):
        column = rows[i + 1].split('{')

        for j in range(len(column) - 1):
            infos = column[j + 1].split(',')
            end_index = infos[2].find('}')
            content = int(infos[0])
            x = int(infos[1])
            y = int(infos[2][:end_index])
            deserialized_map[i][j] = Tile(content, x, y)

    return deserialized_map

goback = False

def bot():
    global goback
    """
    Main de votre bot.
    """
    map_json = request.form["map"]

    # Player info

    encoded_map = map_json.encode()
    map_json = json.loads(encoded_map)
    p = map_json["Player"]
    pos = p["Position"]

    x = pos["X"]
    y = pos["Y"]

    house = p["HouseLocation"]
    player = Player(p["Health"], p["MaxHealth"], Point(x,y),
                    Point(house["X"], house["Y"]), p["Score"],
                    p["CarriedResources"], p["CarryingCapacity"])

    # Map
    serialized_map = map_json["CustomSerializedMap"]
    deserialized_map = deserialize_map(serialized_map)

    otherPlayers = []

    for players in map_json["OtherPlayers"]:
        player_info = players["Value"]
        p_pos = player_info["Position"]
        player_info = PlayerInfo(player_info["Health"],
                                     player_info["MaxHealth"],
                                     Point(p_pos["X"], p_pos["Y"]))

        otherPlayers.append(player_info)

    if house["X"] == x and house["Y"] == y:
        goback = False
    
    if player.CarriedRessources == player.CarryingCapacity:
        goback = True

    m = remove_fog(deserialized_map)
    g = makeGraph(m)

    print_map(m, x, y)
    print(player.CarriedRessources)

    if goback:
        return gohome(g, x, y, house, m)



    p = None
    res = find_resource(m)
    for (rx,ry) in res:
        dx = rx - 10
        dy = ry - 10
        d  = abs(dx) + abs(dy)

#        print(d,dx,dy,x,y)
        if d == 1:
            return create_collect_action(Point(x+dy,y+dx))

        try:
            p = shortestPath(g, 10+10*20, rx+ry*20)
        except:
            continue


#    print("res", res)
#    print("path", p)
    (mx, my) = d1_to_d2(p[1], m)

    dx = mx-10
    dy = my-10

#    print(mx, my,x,y)

    # return decision
    return create_move_action(Point(x+dy,y+dx))

def gohome(g, x, y, house, m):
    hx = house["X"]
    hy = house["Y"]

    dx = hx-x
    dy = hy-y

    p = shortestPath(g, 10+10*20, (10+dy)+(10+dx)*20)

    (mx, my) = d1_to_d2(p[1], m)

    dx = mx-10
    dy = my-10

    print(dx, dy, x, y)
    
    return create_move_action(Point(x+dy,y+dx))

def d1_to_d2(n, m):
    w = len(m[0])
    h = len(m)

    x = n % w
    y = n / w

    return (x, y)

def local_to_global(px, py, mx, my, m):
    w = len(m[0])
    h = len(m)

    ox = px - 10
    oy = py - 10

    x = mx + ox
    y = my + oy

    return (x, y)

def find_resource(m):
    w = len(m)
    h = len(m[0])

    res = []

    for j in range(0, h):
        for i in range(0, w):
            cell = m[j][i]

            if cell.Content == TileType.Resource:
                res.append((i,j))

    return res
                

def remove_fog(m):
    i = 0
    j = 0

    cell = m[0][i]
    while not (cell.Content == None):
        i+=1
        cell = m[0][i]
    
    cell = m[j][0]
    while not (cell.Content == None):
        j+=1
        cell = m[j][0]

    matrix = [[0]*i for n in range(j)]
    for jj in range(0, j):
        for ii in range(0, i):
            matrix[jj][ii] = m[jj][ii]

    print(i, j)
    return matrix

def print_map(m, x, y):
    for row in m:
        for tile in row:
            if tile.X == x and tile.Y == y:
                sys.stdout.write("p ")
                continue

            tile.printt()
        print(" ")

@app.route("/", methods=["POST"])
def reponse():
    """
    Point d'entree appelle par le GameServer
    """
    return bot()

if __name__ == "__main__":
    goback = False
    app.run(host="0.0.0.0", port=3000)
