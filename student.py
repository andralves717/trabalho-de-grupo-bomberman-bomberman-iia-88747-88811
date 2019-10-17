import sys
import json
import asyncio
import websockets
import getpass
import os
import random
import math

from mapa import Map

# Next 2 lines are not needed for AI agent
# import pygame

# pygame.init()


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        key = None
        x1 = None
        y1 = None
        fuga = 0
        key_save = []
        destroyed = True

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server


                x, y = state['bomberman']

                walls = state['walls']
                if destroyed:
                    x2, y2 = minWall(walls,(x,y))
                    destroyed = False
                if(x < x2):
                    if(x2-x == 1):
                        if(mapa.map[x2][y+1] == 1):
                            break
                        else:
                            key = 'd'
                            key_save.append(key)
                    else:
                        key = 'd'
                        key_save.append(key)

                elif (x > x2):
                    if(x-x2 == 1):
                        if(mapa.map[x2][y+1] == 1):
                            break
                        else:
                            key = 'a'
                            key_save.append(key)
                    else:
                        key = 'a'
                        key_save.append(key)

                if (y < y2):
                    if(y2-y == 1):
                        if(mapa.map[y2][x+1] == 1):
                            break
                        else:
                            key = 's'
                            key_save.append(key)
                    else:
                        key = 's'
                        key_save.append(key)


                elif (y > y2):
                    if(y-y2 == 1):
                        if(mapa.map[y2][x+1] == 1):
                            break
                        else:
                            key = 'w'
                            key_save.append(key)
                    else:
                        key = 'w'
                        key_save.append(key)


                if(mapa.map[x+1][y] == mapa.map[x2][y2] | mapa.map[x-1][y] ==
                    mapa.map[x2][y2] | mapa.map[x][y-1] == mapa.map[x2][y2] | mapa.map[x][y+1] == mapa.map[x2][y2]):
                    if(key == 'B'):
                        for i in range(5):
                            if len(key_save) == 0:
                                break
                            keys2 = key_save.pop()
                            if(keys2 == 'd'):
                                key = 'a'
                            elif(keys2 == 'a'):
                                key = 'd'
                            elif(keys2 == 'w'):
                                key = 's'
                            elif(keys2 == 's'):
                                key = 'w'
                    else:
                        key = 'B'
                        destroyed = True
                '''
                if(aux == 1):
                    key = 'B'
                    for i in range(5):
                        if len(key_save) == 0:
                            break
                        keys2 = key_save.pop()
                        if(keys2 == 'd'):
                            key = 'a'
                        elif(keys2 == 'a'):
                            key = 'd'
                        elif(keys2 == 'w'):
                            key = 's'
                        elif(keys2 == 's'):
                            key = 'w'
                '''

                enemies = state['enemies']

                #if(len(walls) == 0):
                # for enemie in enemies:
                #     dist = calc_pos((x,y), enemie["pos"])
                #     if(dist <= 1):
                #         key = 'B'
                #         for i in range(5):
                #             if len(key_save) == 0:
                #                     break
                #             keys2 = key_save.pop()
                #             if(keys2 == 'd'):
                #                 key = 'a'
                #             elif(keys2 == 'a'):
                #                 key = 'd'
                #             elif(keys2 == 'w'):
                #                 key = 's'
                #             elif(keys2 == 's'):
                #                 key = 'w' 


                   # if(calc_pos((x,y), wall) <= 1):
                    #    if fuga == 0:
                     #       key = 'B'
                      #      fuga = 2
                       # elif fuga == 2:
                        #    key = random.choice("ad")
                         #   fuga = 1
                       # else:  
                        #    key = random.choice("ws")
                         #   fuga = 0

                x1 = x
                y1 = y



                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

def calc_pos(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2

    return math.hypot(x1-x2, y1-y2)


def minWall(walls, pos):
    if (walls == []):
        return 999,999
    m = minWall(walls[1:], pos)
    if m == None or calc_pos(pos,walls[0]) < calc_pos(pos,m):
        return walls[0]
    return m



# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
