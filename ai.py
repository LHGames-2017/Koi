from flask import Flask, request
from structs import *
from Dijkstra import *
import json
import numpy

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

def bot():
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

    m = remove_fog(deserialized_map)
    g = makeGraph(m)

    res = find_resource(m)
    print(res)
    for (rx,ry) in res:
        try:
            p = shortestPath(g, 10+10*20, rx+ry*20)
            print(p)
        except:
            print("except",rx,ry)
            continue


    print_map(m, x, y)


#    print(G)
#    P = shortestPath(G, 10+10*20, 10-5+5*20)
#    print(P)



    # return decision
    return create_move_action(Point(x+0,y+1))

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
    app.run(host="0.0.0.0", port=8080)
