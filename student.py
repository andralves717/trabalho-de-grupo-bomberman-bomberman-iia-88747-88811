import sys
import json
import asyncio
import websockets
import getpass
import os
import random
import math

from mapa import Map, Tiles

kd = False


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        key = None
        x2 = 1
        y2 = 1
        fuga = 0
        key_save = []
        global kd

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                x, y = state['bomberman']

                walls = state['walls']

                enemies = state['enemies']

                power_up = state['powerups']

                print("powerup:")
                print(power_up)

                ex = state['exit']
                kd = False

                print(state["bombs"])
                if len(state["bombs"]) > 0:
                    key = ""
                    kd = True

                if len(walls) != 0:

                    x2, y2 = minWall(walls, (x, y))
                    print("\nparede:")
                    print(x2, y2)
                    print("\nEU estou em:")
                    print(x, y)

                    putBomb = [x + 1, y] == [x2, y2] or [x - 1, y] == [x2, y2] or [x, y - 1] == [x2, y2] or [x,
                                                                                                             y + 1] == [
                                  x2, y2]

                    print(x2, y2)

                    if (fuga > 0):
                        if len(key_save) != 0:
                            keys2 = key_save.pop()
                            key = keys2
                            kd = True
                        fuga -= 1
                    elif putBomb:
                        print("vou por B")
                        key = 'B'
                        kd = True
                        fuga = 5
                        mapa = removeWalls((x, y), mapa, 4)
                        mapa.map[x2][y2] = 0

                    print(kd)
                    if x < x2 and not putBomb and not kd and not mapa.is_stone((x + 1, y)):
                        if x2 - x == 1:
                            if not mapa.is_stone((x2, y + 1)) and not kd:
                                key = 'd'
                                key_save.append('a')
                                kd = True
                        else:
                            key = 'd'
                            key_save.append('a')
                            kd = True

                    elif x > x2 and not putBomb and not kd and not mapa.is_stone((x - 1, y)):
                        if x - x2 == 1:
                            if not mapa.is_stone((x2, y + 1)) and not kd:
                                key = 'a'
                                key_save.append('d')
                                kd = True
                        else:
                            key = 'a'
                            key_save.append('d')
                            kd = True

                    if y < y2 and not putBomb and not kd and not mapa.is_stone((x, y + 1)):
                        if y2 - y == 1:
                            if not mapa.is_stone((x + 1, y2)) and not kd:
                                key = 's'
                                key_save.append('w')
                                kd = True
                        else:
                            key = 's'
                            key_save.append('w')
                            kd = True

                    elif y > y2 and not putBomb and not kd and not mapa.is_stone((x, y - 1)):
                        if y - y2 == 1:
                            if not mapa.is_stone((x + 1, y2)) and not kd:
                                key = 'w'
                                key_save.append('s')
                                kd = True
                        else:
                            key = 'w'
                            key_save.append('s')
                            kd = True

                    if x == x2 and ((y < y2 and mapa.is_stone((x, y + 1))) or (y > y2 and mapa.is_stone((x, y - 1)))):
                        key = random.choice("ad")
                        key_save.append('a' if key == 'd' else 'd')
                        kd = True

                    elif y == y2 and ((x < x2 and mapa.is_stone((x + 1, y))) or (x > x2 and mapa.is_stone((x - 1, y)))):
                        key = random.choice("ws")
                        key_save.append('w' if key == 's' else 's')
                        kd = True

                elif len(walls) == 0:
                    print("ACABARAM AS PAREDES")
                    print(key)
                    print(x, y)

                    # para ir buscar a powerup
                    if (len(power_up) != 0):
                        key = moveTo((x, y), power_up[0][0], mapa)
                    else:
                        key = moveTo((x, y), (1, 1), mapa)

                    for enemie in enemies:
                        dist = calc_pos((x, y), enemie['pos'])

                        if(dist <= 3):
                            if fuga > 0:
                                key = 's'
                                fuga = 0
                            else:
                                key = 'B'
                                fuga = 2
                            # put = True
                            # key = 'B'
                            # print("já pos bomba")

                            # if(mapa.map[x-1][y+1] == 0):
                            #     print("Keeey s?")
                            #     key = 's'
                            #     if(mapa.map[x+1][y] == 0):
                            #         key = 'd'
                            #         put = False

                            # if(put == False):
                            #     if(mapa.map[x-1][y] == 0):
                            #         key = 'a'
                            #         if(mapa.map[x][y-1] == 0):
                            #             key = 'w'

                    print(ex)
                    if (len(enemies) == 0):
                        key = moveTo((x, y), ex, mapa)
                    kd = True

                print("keeey")
                print(key)
                if not kd:
                    key = ""
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


def calc_pos(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2

    return math.hypot(x1 - x2, y1 - y2)


def minWall(walls, pos):
    if not walls:
        return 999, 999
    m = minWall(walls[1:], pos)
    if m == None or calc_pos(pos, walls[0]) < calc_pos(pos, m):
        return walls[0]
    return m


def removeWalls(pos, walls, r):
    if r < 0:
        return walls
    x, y = pos
    print(r)
    if not walls.is_blocked((x + r, y), True):
        walls.map[x + r][y] = 0
    if not walls.is_blocked((x - r, y), True):
        walls.map[x - r][y] == 0
    if not walls.is_blocked((x, y + r), True):
        walls.map[x][y + r] == 0
    if not walls.is_blocked((x, y - r), True):
        walls.map[x][y - r] == 0
    return removeWalls((x, y), walls, r - 1)


def moveTo(pos1, pos2, mapa):
    x, y = pos1
    x2, y2 = pos2
    key = ""
    global kd

    if x < x2 and not kd and not mapa.is_stone((x + 1, y)):
        key = 'd'
        #key_save.append('a')
        kd = True

    elif x > x2 and not kd and not mapa.is_stone((x - 1, y)):
        key = 'a'
        #key_save.append('d')
        kd = True

    if y < y2 and not kd and not mapa.is_stone((x, y + 1)):
        key = 's'
        #key_save.append('w')
        kd = True

    elif y > y2 and not kd and not mapa.is_stone((x, y - 1)):
        key = 'w'
        #key_save.append('s')
        kd = True

    if x == x2 and ((y < y2 and mapa.is_stone((x, y + 1))) or (y > y2 and mapa.is_stone((x, y - 1)))):
        key = random.choice("ad")
        #key_save.append('a' if key == 'd' else 'd')
        kd = True

    elif y == y2 and ((x < x2 and mapa.is_stone((x + 1, y))) or (x > x2 and mapa.is_stone((x - 1, y)))):
        key = random.choice("ws")
        #key_save.append('w' if key == 's' else 's')
        kd = True

    return key


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
