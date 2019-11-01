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
powerup_save = []
det = False
count = 0


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
        global det
        global powerup_save
        global count

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
                bombs = state['bombs']
                bomb = None
                bomb_time = 0
                key = ''
                level = state['level']

                if bombs:
                    bomb = min(bombs, key=lambda b: calc_pos((x, y), b[0]))

                    bomb_pos_x, bomb_pos_y = bomb[0]
                    bomb_time = bomb[1]
                kd = False

                if power_up:
                    power_up_x, power_up_y = power_up[0][0]
                    if (power_up_x, power_up_y) == (x + 1, y):
                        key_save.append('a')
                        key = 'd'
                        if power_up[0][1] == "Detonator":
                            det = True
                        powerup_save.append(power_up[0][1])
                    elif (power_up_x, power_up_y) == (x - 1, y):
                        key_save.append('d')
                        key = 'a'
                        if power_up[0][1] == "Detonator":
                            det = True
                        powerup_save.append(power_up[0][1])
                    elif (power_up_x, power_up_y) == (x, y + 1):
                        key_save.append('w')
                        key = 's'
                        if power_up[0][1] == "Detonator":
                            det = True
                        powerup_save.append(power_up[0][1])
                    elif (power_up_x, power_up_y) == (x, y - 1):
                        key_save.append('s')
                        key = 'w'
                        if power_up[0][1] == "Detonator":
                            det = True
                        powerup_save.append(power_up[0][1])
                    else:
                        key = get_astar((x, y), (power_up_x, power_up_y), mapa)
                        if key == 'w' and minWall(walls, (x, y)) == (x, y - 1):
                            if bomb:
                                key = foge_dai(mapa, (x, y), (x, y - 1))
                            else:
                                key_save.pop()
                                key = 'B'
                        elif key == 's' and minWall(walls, (x, y)) == (x, y + 1):
                            if bomb:
                                key = foge_dai(mapa, (x, y), (x, y + 1))
                            else:
                                key_save.pop()
                                key = 'B'
                        elif key == 'a' and minWall(walls, (x, y)) == (x - 1, y):
                            if bomb:
                                key = foge_dai(mapa, (x, y), (x - 1, y))
                            else:
                                key_save.pop()
                                key = 'B'
                        elif key == 'd' and minWall(walls, (x, y)) == (x + 1, y):
                            if bomb:
                                key = foge_dai(mapa, (x, y), (x + 1, y))
                            else:
                                key_save.pop()
                                key = 'B'

                    kd = True

                ### ENQUANTO TIVER PAREDES ###
                if walls and not kd:

                    x2, y2 = minWall(walls, (x, y))

                    putBomb = (x + 1, y) == (x2, y2) or (x - 1, y) == (x2, y2) \
                              or (x, y - 1) == (x2, y2) or (x, y + 1) == (x2, y2)

                    if putBomb:
                        key = 'B'
                        kd = True

                    ### SE ENCONTRAR INIMIGOS ###
                    if enemies and not putBomb:

                        ene = sorted(enemies, key=lambda e: calc_pos((x, y), e['pos']))
                        eneO = [e for e in ene if e['name'] != ("Balloom" or "Doll")]

                        dist = calc_pos((x, y), ene[0]['pos'])

                        dist_ene = 3

                        ### INIMIGOS ONEAL ###
                        if eneO:
                            key = get_astar((x, y), (eneO[0]['pos'][0], eneO[0]['pos'][1]), mapa)
                            kd = True
                        if ene[0]['name'] == ("Oneal" or "Minvo"):
                            dist_ene = 1
                        if dist <= dist_ene:
                            if bomb_time > 0 and bomb:
                                key = foge_dai(mapa, (x, y), (bomb_pos_x, bomb_pos_y), walls)
                                kd = True
                            else:
                                if ene[0]['pos'][0] == x or ene[0]['pos'][1] == y:
                                    key = 'B'
                                    kd = True

                    if bomb_time > 0 and bomb:
                        key = foge_dai(mapa, (x, y), (bomb_pos_x, bomb_pos_y), walls)
                        kd = True

                    if not kd:
                        key = get_astar((x, y), (x2, y2), mapa)
                        kd = True


                ### QUANDO ACABAREM AS PAREDES ###
                elif not kd:

                    # para ir buscar a powerup
                    if power_up:
                        power_up_x, power_up_y = power_up[0][0]
                        key = get_astar((x, y), (power_up_x, power_up_y), mapa)
                        if power_up[0][1] == "Detonator":
                            det = True
                    else:
                        if enemies and (x, y) != (1, 1):
                            key = get_astar((x, y), (1, 1), mapa)

                    if enemies:
                        ene = min(enemies, key=lambda e: calc_pos((x, y), e['pos']))['pos']
                        dist = calc_pos((x, y), ene)
                        xe, ye = ene
                        if dist <= 3 and (x == xe or y == ye):
                            if bomb_time > 0 and bomb:
                                key = foge_dai(mapa, (x, y), (bomb_pos_x, bomb_pos_y), walls)
                                kd = True
                            else:
                                if xe == x or ye == y:
                                    key = 'B'
                                    kd = True
                        kd = True

                    if len(enemies) == 0:
                        ex_x, ex_y = ex
                        key = get_astar((x, y), (ex_x, ex_y), mapa)
                    kd = True

                if not kd:
                    key = ""

                if len(enemies) == 0 and ex and (len(powerup_save) == level and power_up == []):
                    ex_x, ex_y = ex
                    key = get_astar((x, y), (ex_x, ex_y), mapa)
                    if key == 'w' and (x2, y2) == (x,y-1):
                        if bomb:
                            key_save.pop()
                            key = foge_dai(mapa, (x, y), (x, y-1), walls)
                        else:
                            key = 'B'
                    elif key == 's' and (x2, y2) == (x,y+1):
                        if bomb:
                            key_save.pop()
                            key = foge_dai(mapa, (x, y), (x, y+1), walls)
                        else:
                            key = 'B'
                    elif key == 'a' and (x2, y2) == (x-1,y):
                        if bomb:
                            key_save.pop()
                            key = foge_dai(mapa, (x, y), (x-1, y), walls)
                        else:
                            key = 'B'
                    elif key == 'd' and (x2, y2) == (x+1, y):
                        if bomb:
                            key_save.pop()
                            key = foge_dai(mapa, (x, y), (x+1, y), walls)
                        else:
                            key = 'B'
                kd = True

                if count >= 20:
                    key = 'A'
                    count = 0
                count += 1


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


# função para implementar o algoritmo a_star

def get_astar(pos1, pos2, mapa):
    global exact
    path = astar(mapa.map, pos1, pos2)

    return moveToWalls(path[0], path[1], mapa)


# função para se mover até às paredes


def moveToWalls(pos1, pos2, mapa):
    x, y = pos1
    x2, y2 = pos2
    global key_save

    if y < y2:
        key_save.append('w')
        return 's'
    elif y > y2:
        key_save.append('s')
        return 'w'
    if x < x2:
        key_save.append('a')
        return 'd'
    elif x > x2:
        key_save.append('d')
        return 'a'

    return ''


def foge_dai(mapa, pos, bomb_pos, walls, canto=False):
    global key_save
    global det
    bomb_pos_x, bomb_pos_y = bomb_pos
    x, y = pos
    if (bomb_pos_x, bomb_pos_y) == (x, y):
        if canto:
            key_save.append('w')
            return 's'
        return key_save.pop()
    elif bomb_pos_x == x:
        if not mapa.is_stone((x + 1, y)) and not [x+1,y] in walls:
            key_save.append('a')
            return 'd'
        elif not mapa.is_stone((x - 1, y)) and not [x-1,y] in walls:
            key_save.append('d')
            return 'a'
        else:
            if bomb_pos_y > y:
                key_save.append('s')
                return 'w'
            else:
                key_save.append('w')
                return 's'
    elif bomb_pos_y == y:
        if not mapa.is_stone((x, y + 1)) and not [x,y+1] in walls:
            key_save.append('w')
            return 's'
        elif not mapa.is_stone((x, y - 1)) and not [x,y-1] in walls:
            key_save.append('s')
            return 'w'
        else:
            if bomb_pos_x > x:
                key_save.append('d')
                return 'a'
            else:
                key_save.append('a')
                return 'd'
    else:
        if det:
            return 'A'
        return ''


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
