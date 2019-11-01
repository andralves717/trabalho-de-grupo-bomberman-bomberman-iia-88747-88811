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
#powerup_save = []
det = False


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
        #global powerup_save


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
                    coiso = (bomb_pos_x, bomb_pos_y) == (x, y)
                kd = False

                if power_up:
                    #print(power_up[0][0])
                    power_up_x, power_up_y = power_up[0][0]
                    if (power_up_x, power_up_y)  == (x+1,y):
                        key_save.append('a')
                        key = 'd'
                        # powerup_save.append(power_up)
                        # if power_up[0][1] == "Detonator":
                        #     det = True
                    elif (power_up_x, power_up_y)  == (x-1,y):
                        key_save.append('d')
                        key = 'a'
                        # powerup_save.append(power_up)
                        # if power_up[0][1] == "Detonator":
                        #     det = True
                    elif (power_up_x, power_up_y)  == (x,y+1):
                        key_save.append('w')
                        key = 's'
                        # powerup_save.append(power_up)
                        # if power_up[0][1] == "Detonator":
                        #     det = True
                    elif (power_up_x, power_up_y)  == (x,y-1):
                        key_save.append('s')
                        key = 'w'
                        # powerup_save.append(power_up)
                        # if power_up[0][1] == "Detonator":
                        #     det = True
                    else:
                        key = get_astar((x, y), (power_up_x, power_up_y) , mapa)
                        #powerup_save.append(power_up)
                        # if power_up[0][1] == "Detonator":
                        #     det = True
                    kd = True

                ### ENQUANTO TIVER PAREDES ###
                if walls and not kd:
                    
                    x2, y2 = minWall(walls, (x, y))
                    # print("MinWall:", (x2,y2))
                    

                    putBomb = (x + 1, y) == (x2, y2) or (x - 1, y) == (x2, y2) \
                              or (x, y - 1) == (x2, y2) or (x, y + 1) == (x2, y2)

                    if putBomb and not det:
                            print("vou por B")
                            key = 'B'
                            kd = True
        

                    ### SE ENCONTRAR INIMIGOS ###
                    if enemies and not putBomb:
                        eneO = None

                        ene = min(enemies, key=lambda e: calc_pos((x, y), e['pos']))

                        ### LEVELS ABOVE 1 ###
                        if level != 1:
                            
                            eneO = min([e for e in enemies if (e['name'] == "Oneal")],key=lambda e: calc_pos((x, y), e['pos']))

                        #eneO = min(en, key=lambda e: calc_pos((x, y), e['pos']))
                        dist = calc_pos((x, y), ene['pos'])
                        xe, ye = eneO['pos']
                        dist_ene = 3

                        ### INIMIGOS ONEAL ###
                        if eneO:
                            print("««««««««««««««««««««««««««««««««««««««««««")
                            key = get_astar((x, y), (xe, ye), mapa)
                            kd = True
                        if ene['name'] == "Oneal":
                            dist_ene = 1
                        if dist <= dist_ene:
                            if bomb_time > 0 and bomb:
                                key = foge_dai(mapa, (x, y), (bomb_pos_x, bomb_pos_y))
                                kd = True
                            else:
                                key = 'B'
                                kd = True
                        
                    if bomb_time > 0 and bomb:
                        key = foge_dai(mapa, (x, y), (bomb_pos_x, bomb_pos_y))
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
                        #powerup_save.append(power_up)
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
                            if bomb:
                                key = foge_dai(mapa, (x,y), (bomb_pos_x, bomb_pos_y), True)
                            else:
                                key = 'B'
                        kd = True

                    if len(enemies) == 0:
                        ex_x, ex_y = ex
                        key = get_astar((x, y), (ex_x, ex_y), mapa)
                    kd = True

                if not kd:
                    key = ""

                if len(enemies) == 0 and ex and power_up:
                        ex_x, ex_y = ex
                        key = get_astar((x, y), (ex_x, ex_y), mapa)
                kd = True


                safe = True
                #for pwup in powerup_save:

                if det:
                    print(safe)
                    if putBomb:
                        print("this B")
                        key = 'B'
                        # kd = True
                        safe = False
                    if bomb:
                        print(safe)
                        print("não chega aqui")
                        key = foge_dai(mapa,(x,y),(bomb_pos_x,bomb_pos_y))
                        print("não chega aqui 2")
                    if calc_pos((x,y),(bomb_pos_x,bomb_pos_y)) > 2:
                        safe = True
                        print("SAFE: ",safe)
                    elif safe:
                        key = 'A'
                        print(key)
                        safe = False
                                
                
                    
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
    # print(path)

    return moveToWalls(path[0], path[1], mapa)


# função para se mover até às paredes


def moveToWalls(pos1, pos2, mapa):
    x, y = pos1
    x2, y2 = pos2
    key = ""
    global key_save

    if y < y2:
        key = 's'
        key_save.append('w')

    elif y > y2:
        key = 'w'
        key_save.append('s')

    if x < x2:
        key = 'd'
        key_save.append('a')
    elif x > x2:
        key = 'a'
        key_save.append('d')

    return key


def foge_dai(mapa, pos, bomb_pos, canto=False):
    global key_save
    bomb_pos_x, bomb_pos_y = bomb_pos
    x, y = pos
    if (bomb_pos_x, bomb_pos_y) == (x, y):
        if canto:
            key_save.append('w')
            return 's'
        return key_save.pop()
    elif bomb_pos_x == x:
        if not mapa.is_stone((x + 1, y)):
            key_save.append('a')
            return 'd'
        elif not mapa.is_stone((x - 1, y)):
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
        if not mapa.is_stone((x, y + 1)):
            key_save.append('w')
            return 's'
        elif not mapa.is_stone((x, y - 1)):
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
        return ''


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
