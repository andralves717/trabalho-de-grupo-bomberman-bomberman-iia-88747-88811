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
exact = False
fuga = 0
det = False
powerup_save = []
ene_save = []


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
        global kd
        global exact
        global powerup_save
        global det
        hasGoal = False
        global ene_save
        ene_save= []

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                # states
                x, y = state['bomberman']
                pos = x, y
                walls = state['walls']
                enemies = state['enemies']
                power_up = state['powerups']
                ex = state['exit']
                bombs = state['bombs']
                bomb = None
                bomb_time = 0
                # key = ''
                level = state['level']
                if state['lives'] == 0:
                    return
                kd = False
                steps = state['step']

                #### não mexer aqui ####
                if bombs:
                    bomb = min(bombs, key=lambda b: calc_pos(pos, b[0]))
                    bomb_time = bomb[1]
                # Enquanto tiver paredes...
                if walls:
                    # parede mais próxima
                    x2, y2 = minWall(walls, pos)

                    # locais onde pode colocar a bomba (à volta da parede)
                    putBomb = (x + 1, y) == (x2, y2) or (x - 1, y) == (x2, y2) \
                              or (x, y - 1) == (x2, y2) or (x, y + 1) == (x2, y2)

                    # se não está atrás dos inimigos, vai destruindo paredes
                    if not kd:
                        key = get_astar(pos, (x2, y2), mapa)
                        kd = True

                    # Se entretanto encontrar inimigos e não tiver posto nenhuma bomba...
                    if enemies:
                        key_tmp = killnemies(pos, enemies, mapa, steps, (x2, y2), kd, det)
                        if key_tmp != '':
                            key = key_tmp
                            kd = True

                    #### não mexer aqui ####
                    # quando encontra uma power_up, vai buscá-la e esta é guardada no powerup_save
                    if power_up:

                        power_up_x, power_up_y = power_up[0][0]
                        if ex:
                            mapa.map[ex[0]][ex[1]] = 1
                        key = get_astar(pos, (power_up_x, power_up_y), mapa)
                        kd = True

                        if power_up[0][1] == "Detonator":
                            det = True

                        if len(powerup_save) == level - 1:
                            powerup_save.append(power_up[0][1])

                    if len(powerup_save) != level and ex:
                        ex_x, ex_y = ex
                        mapa.map[ex_x][ex_y] = 1

                    # # se estiver num dos locais possíveis, coloca a bomba
                    if putBomb:
                        key = 'B'
                        kd = True


                ### QUANDO ACABAREM AS PAREDES ###
                else:
                    # para ir buscar a powerup
                    if power_up:
                        power_up_x, power_up_y = power_up[0][0]
                        if ex:
                            mapa.map[ex[0]][ex[1]] = 1
                        key = get_astar(pos, (power_up_x, power_up_y), mapa)
                        kd = True

                        if power_up[0][1] == "Detonator":
                            det = True

                        if len(powerup_save) == (level - 1):
                            powerup_save.append(power_up[0][1])

                    else:
                        if enemies and pos != mapa.bomberman_spawn:
                            key = get_astar(pos, mapa.bomberman_spawn, mapa)
                            kd = True

                    if enemies:
                        if pos == mapa.bomberman_spawn:
                            ene = min(enemies, key=lambda e: calc_pos(pos, e['pos']))['pos']
                            dist = calc_pos(pos, ene)
                            xe, ye = ene
                            if dist <= 3 and (x == xe or y == ye):
                                key = 'B'
                            kd = True
                        else:
                            key_tmp = killnemies(pos, enemies, mapa, steps, (x2, y2), kd, det)
                            if key_tmp != '':
                                key = key_tmp
                                kd = True


                if not kd:
                    key = ''

                if len(enemies) == 0 and ex and len(powerup_save) == level and not power_up:
                    ex_x, ex_y = ex
                    key = get_astar(pos, (ex_x, ex_y), mapa)

                    if putBomb:
                        key = 'B'
                        kd = True

                kd = True

                if level == 15:
                    if len(enemies) == 0:
                        return

                if bomb and bomb_time > 0 and not hasGoal:
                    goal = is_free(pos, enemies, walls, mapa, 5)
                    hasGoal = True
                if bomb and bomb_time > 0 and pos != goal:
                    key = get_astar(pos, goal, mapa)
                    kd = True
                elif bomb and bomb_time > 0 and not det:
                    key = ''
                    kd = True
                elif not bomb:
                    hasGoal = False
                elif goal == pos and det:
                    key = 'A'
                    kd = True
                    hasGoal = False

                if ex:
                    ex_x, ex_y = ex
                    mapa.map[ex_x][ex_y] = 0

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
    path = astar(mapa.map, pos1, pos2)
    if len(path) < 2:
        path[1] = path[0]

    return moveToWalls(path[0], path[1], mapa)


# função para se mover até às paredes
def moveToWalls(pos1, pos2, mapa):
    x, y = pos1
    x2, y2 = pos2
    key = ''
    global kd
    kd = False

    if y < y2:
        key = 's'

    elif y > y2:
        key = 'w'

    if x < x2:
        key = 'd'

    elif x > x2:
        key = 'a'

    return key


def in_range(pos, ene, raio, mapa):
    bx, by = ene
    cx, cy = pos

    if by == cy:
        for r in range(raio + 1):
            if mapa.is_stone((bx + r, by)):
                break  # protected by stone to the right
            if (cx, cy) == (bx + r, by):
                return True
        for r in range(raio + 1):
            if mapa.is_stone((bx - r, by)):
                break  # protected by stone to the left 
            if (cx, cy) == (bx - r, by):
                return True
    if bx == cx:
        for r in range(raio + 1):
            if mapa.is_stone((bx, by + r)):
                break  # protected by stone in the bottom
            if (cx, cy) == (bx, by + r):
                return True
        for r in range(raio + 1):
            if mapa.is_stone((bx, by - r)):
                break  # protected by stone in the top
            if (cx, cy) == (bx, by - r):
                return True

    return False


def is_free(pos, enemies, walls, mapa, raio):
    x, y = pos
    key = ''
    global kd
    # kd = False
    if raio == 0:
        return pos

    if not [x, y + 1] in walls and mapa.map[x][y + 1] != 1 and not enemies_on_sight((x, y + 1), enemies, raio):
        if not [x + 1, y + 1] in walls and mapa.map[x + 1][y + 1] != 1 and not enemies_on_sight((x + 1, y + 1), enemies,
                                                                                                raio):
            return x + 1, y + 1
        if not [x - 1, y + 1] in walls and mapa.map[x - 1][y + 1] != 1 and not enemies_on_sight((x - 1, y + 1), enemies,
                                                                                                raio):
            return x - 1, y + 1
        if not [x, y + 2] in walls and mapa.map[x][y + 2] != 1 and not enemies_on_sight((x, y + 2), enemies, raio):
            if not [x + 1, y + 2] in walls and mapa.map[x + 1][y + 2] != 1 and not enemies_on_sight((x + 1, y + 2),
                                                                                                    enemies, raio):
                return x + 1, y + 2
            if not [x - 1, y + 2] in walls and mapa.map[x - 1][y + 2] != 1 and not enemies_on_sight((x - 1, y + 2),
                                                                                                    enemies, raio):
                return x - 1, y + 2
                # kd = True

    if not [x + 1, y] in walls and mapa.map[x + 1][y] != 1 and not enemies_on_sight((x + 1, y), enemies, raio):
        if not [x + 1, y + 1] in walls and mapa.map[x + 1][y + 1] != 1 and not enemies_on_sight((x + 1, y + 1), enemies,
                                                                                                raio):
            return x + 1, y + 1
        if not [x + 1, y - 1] in walls and mapa.map[x + 1][y - 1] != 1 and not enemies_on_sight((x + 1, y - 1), enemies,
                                                                                                raio):
            return x + 1, y - 1
        if not [x + 2, y] in walls and mapa.map[x + 2][y] != 1 and not enemies_on_sight((x + 2, y), enemies, raio):
            if not [x + 2, y + 1] in walls and mapa.map[x + 2][y + 1] != 1 and not enemies_on_sight((x + 2, y + 1),
                                                                                                    enemies, raio):
                return x + 2, y + 1
            if not [x + 2, y - 1] in walls and mapa.map[x + 2][y - 1] != 1 and not enemies_on_sight((x + 2, y - 1),
                                                                                                    enemies, raio):
                return x + 2, y - 1
    # kd = True

    if not [x - 1, y] in walls and mapa.map[x - 1][y] != 1 and not enemies_on_sight((x - 1, y), enemies, raio):
        if not [x - 1, y + 1] in walls and mapa.map[x - 1][y + 1] != 1 and not enemies_on_sight((x - 1, y + 1), enemies,
                                                                                                raio):
            return x - 1, y + 1
        if not [x - 1, y - 1] in walls and mapa.map[x - 1][y - 1] != 1 and not enemies_on_sight((x - 1, y - 1), enemies,
                                                                                                raio):
            return x - 1, y - 1
        if not [x - 2, y] in walls and mapa.map[x - 2][y] != 1 and not enemies_on_sight((x - 2, y), enemies, raio):
            if not [x - 2, y + 1] in walls and mapa.map[x - 2][y + 1] != 1 and not enemies_on_sight((x - 2, y + 1),
                                                                                                    enemies, raio):
                return x - 2, y + 1
            if not [x - 2, y - 1] in walls and mapa.map[x - 2][y - 1] != 1 and not enemies_on_sight((x - 2, y - 1),
                                                                                                    enemies, raio):
                return x - 2, y - 1
                # kd = True

    if not [x, y - 1] in walls and mapa.map[x][y - 1] != 1 and not enemies_on_sight((x, y - 1), enemies, raio):
        if not [x + 1, y - 1] in walls and mapa.map[x + 1][y - 1] != 1 and not enemies_on_sight((x + 1, y - 1), enemies,
                                                                                                raio):
            return x + 1, y - 1
        if not [x - 1, y - 1] in walls and mapa.map[x - 1][y - 1] != 1 and not enemies_on_sight((x - 1, y - 1), enemies,
                                                                                                raio):
            return x - 1, y - 1
        if not [x, y - 2] in walls and mapa.map[x][y - 2] != 1 and not enemies_on_sight((x, y - 2), enemies, raio):
            if not [x + 1, y - 2] in walls and mapa.map[x + 1][y - 2] != 1 and not enemies_on_sight((x + 1, y - 2),
                                                                                                    enemies, raio):
                return x + 1, y - 2
            if not [x - 1, y - 2] in walls and mapa.map[x - 1][y - 2] != 1 and not enemies_on_sight((x - 1, y - 2),
                                                                                                    enemies, raio):
                return x - 1, y - 2
        # kd = True

    return is_free(pos, enemies, walls, mapa, raio - 1)


def enemies_on_sight(pos, enemies, raio):
    x, y = pos
    global kd
    # kd = True

    for ene in enemies:
        dist = calc_pos(pos, ene['pos'])

        if dist <= raio:
            return True
    return False

def killnemies(pos, enemies, mapa, steps, wall_pos, kd, det):
    x, y = pos
    x2, y2 = wall_pos
    key = ''
    # devolve a posição do inimigo mais próximo
    ene = sorted(enemies, key=lambda e: calc_pos((x, y), e['pos']))
    xe, ye = ene[0]['pos']

    # devolve qualquer inimigo que não seja do tipo Balloom ou Doll
    eneO = [e for e in enemies if e['name'] != ("Balloom" or "Doll")]

    # calcula a distância desde a posição atual do bomberman até à posição do inimigo mais próximo
    dist = calc_pos((x, y), ene[0]['pos'])

    # distância padrão do inimigo
    dist_ene = 3

    # se o inimigo for do tipo Oneal ou Minvo, a distância passa a ser 1
    if ene[0]['name'] == ("Oneal" or "Minvo" or "Kondoria" or "Ovapi" or "Pass"):
        dist_ene = 1

    # se o inimigo for de qualquer tipo que não Balloom ou Doll, então vai atrás dele
    if eneO:
        key = get_astar((x, y), (eneO[0]['pos'][0], eneO[0]['pos'][1]), mapa)
        kd = True
    elif det:
        key = get_astar((x, y), (ene[0]['pos'][0], ene[0]['pos'][1]), mapa)
        kd = True

    # se a distância ao inimigo for menor ou igual que a distância predefinida para o mesmo
    if dist <= dist_ene:
        # kd = False
        # se o inimigo estiver no mesmo eixo dos x ou do y, então põe bomba

        if (ene[0]['pos'][0] == x and not (mapa.is_stone((x, y - 1)) or mapa.is_stone((x, y + 1)))) or (ene[0]['pos'][1] == y and not (mapa.is_stone((x - 1, y)) or mapa.is_stone((x + 1, y)))):
            key = 'B'
            kd = True
        elif check_diag((x, y), (xe, ye)):
            key = 'B'
            kd = True

        if steps % 300 < 5:
            ene_save.append(len(enemies))
            if len(ene_save) < 5:
                if len(enemies) == ene_save[:-6]:
                    key = get_astar((x, y), (x2, y2), mapa)
                    kd = True
    if kd:
        return key
    else:
        return ""


def check_diag(pos, enemies):
    x, y = pos
    return ((x + 1, y + 1) == enemies) or ((x + 1, y - 1) == enemies) or ((x - 1, y + 1) == enemies) or ((x - 1, y - 1) == enemies)


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
