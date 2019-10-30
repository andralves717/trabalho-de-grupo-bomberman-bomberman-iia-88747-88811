import sys
import json
import asyncio
import websockets
import getpass
import os
import random
import math

from mapa import Map, Tiles
from astar import *

kd = False
key_save = []
exact = False
fuga = 0


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
        global key_save
        global kd
        global exact
        global fuga

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server


                # states 
                x, y = state['bomberman']
                walls = state['walls']
                enemies = state['enemies']
                power_up = state['powerups']
                ex = state['exit']
                kd = False

                if len(state["bombs"]) > 0:
                    key = ""
                    kd = True

    
                if walls:

                    x2, y2 = minWall(walls, (x, y))
    
                    key = get_astar((x,y), (x2,y2), mapa)

                    putBomb = [x + 1, y] == [x2, y2] or [x - 1, y] == [x2, y2] or [x, y - 1] == [x2, y2] or [x,
                                                                                                            y + 1] == [
                                x2, y2]

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

                    
                    if enemies:
                        ene = min(enemies, key=lambda e: calc_pos((x, y), e['pos']))['pos']
                        dist = calc_pos((x, y), ene)
                        xe, ye = ene
                        if dist <= 3 and (x == xe or y == ye):
                            print("encontrei inimigo")
                            if fuga > 1:
                                print("foge 1")
                                if mapa.is_stone((x, y+1)):
                                    key = 'd'
                                else:
                                    key = 's'

                                if mapa.is_stone((x,y-1)):
                                    key = 'a'
                                else:
                                    key = 's'
                                fuga -= 1
                            elif fuga > 0:
                                if mapa.is_stone((x+1,y)):
                                    key = 's'
                                else:
                                    key = 'd'

                                if mapa.is_stone((x-1,y)):
                                    key = 'w'
                                else:
                                    key = 'd'
                                fuga = 0
                            else:
                                print("bomba de inimigo")
                                key = 'B'
                                fuga = 3



                else:
                    exact = True
                    
                    # para ir buscar a powerup
                    if (len(power_up) != 0):
                        key = get_astar((x, y), power_up[0][0], mapa)
                    else:
                        if enemies:
                            key = get_astar((x, y), (1, 1), mapa)

                    if enemies:
                        ene = min(enemies, key=lambda e: calc_pos((x, y), e['pos']))['pos']
                        dist = calc_pos((x, y), ene)
                        xe, ye = ene
                        if dist <= 3 and (x == xe or y == ye):
                            if fuga > 1:
                                if mapa.is_stone((x, y + 1)):
                                    key = 'd'
                                else:
                                    key = 's'
                                fuga -= 1
                            elif fuga > 0:
                                if mapa.is_stone((x + 1, y)):
                                    key = 's'
                                else:
                                    key = 'd'
                                fuga = 0
                            else:
                                key = 'B'
                                fuga = 3

                    #print(ex)
                    if len(enemies) == 0:
                        #print(kd)
                        key = get_astar((x, y), ex, mapa)
                    kd = True


                if not kd:
                    key = ""

                print("Final key")
                print(key)
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


# função para calcular a distância de uma posição a outra

def calc_pos(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2

    return math.hypot(x1 - x2, y1 - y2)


# função para calcular a parede mais próxima
# isto sai para o a star
def minWall(walls, pos):
    if not walls:
        return 999, 999
    m = minWall(walls[1:], pos)
    if m is None or calc_pos(pos, walls[0]) < calc_pos(pos, m):
        return walls[0]
    return m


# A função seguinte já não é necessária.
'''
def removeWalls(pos, walls, r):
    if r < 0:
        return walls
    x, y = pos
    if not walls.is_blocked((x + r, y), True):
        walls.map[x + r][y] = Tiles.PASSAGE
    if not walls.is_blocked((x - r, y), True):
        walls.map[x - r][y] == Tiles.PASSAGE
    if not walls.is_blocked((x, y + r), True):
        walls.map[x][y + r] == Tiles.PASSAGE
    if not walls.is_blocked((x, y - r), True):
        walls.map[x][y - r] == Tiles.PASSAGE
    return removeWalls((x, y), walls, r - 1)
'''
# função para implementar o algoritmo a_star

def get_astar(pos1,pos2,mapa):
    global exact
    path = astar(mapa.map, pos1, pos2)
    #print(path)

    if len(path) <= 1:
        if exact == True:
            return  moveToWalls(pos1,pos2,mapa)
        else:
            return ""  

    return moveToWalls(path[0],path[1],mapa)

# função para se mover até às paredes


def moveToWalls(pos1, pos2, mapa):
    x, y = pos1
    x2, y2 = pos2
    key = ""
    global kd
    global key_save

    #putBomb = [x + 1, y] == [x2, y2] or [x - 1, y] == [x2, y2] or [x, y - 1] == [x2, y2] or [x, y + 1] == [x2, y2]

    if y < y2  and not kd:
        key = 's'
        key_save.append('w')
        kd = True

    elif y > y2 and not kd:
        key = 'w'
        key_save.append('s')
        kd = True

    if x < x2 and not kd:
        key = 'd'
        key_save.append('a')
        kd = True

    elif x > x2 and not kd:
        key = 'a'
        key_save.append('d')
        kd = True

    # if x == x2 and ((y < y2 and mapa.is_stone((x, y + 1))) or (y > y2 and mapa.is_stone((x, y - 1)))):
    #     key = random.choice("ad")
    #     key_save.append('a' if key == 'd' else 'd')
    #     kd = True

    # elif y == y2 and ((x < x2 and mapa.is_stone((x + 1, y))) or (x > x2 and mapa.is_stone((x - 1, y)))):
    #     key = random.choice("ws")
    #     key_save.append('w' if key == 's' else 's')
        #kd = True

    return key



# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
