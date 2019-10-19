import sys
import json
import asyncio
import websockets
import getpass
import os
import random
import math

from mapa import Map

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
        destroyed = True

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server


                x, y = state['bomberman']

                walls = state['walls']
                print(mapa.map[x2][y2])
                if mapa.map[x2][y2]==0:
                    x2, y2 = minWall(walls,(x,y))
                    print("Próxima parede:")
                    print(x2,y2)
                    destroyed = False
                print ("\nparede:")
                print (x2,y2)
                print ("\nEU estou em:")
                print (x,y)
                print (mapa.map[x+1][y] == mapa.map[x2][y2])


                kd = False

                putBomb = mapa.map[x+1][y] == mapa.map[x2][y2] or mapa.map[x-1][y] == mapa.map[x2][y2] or mapa.map[x][y-1] == mapa.map[x2][y2] or mapa.map[x][y+1] == mapa.map[x2][y2]
                if(putBomb):
                    print("chega aqui?")
                    if fuga > 0:
                        if len(key_save) == 0:
                            continue
                        keys2 = key_save.pop()
                        if(keys2 == 'd' and not kd):
                            key = 'a'
                            kd = True
                        elif(keys2 == 'a' and not kd):
                            key = 'd'
                            kd = True
                        elif(keys2 == 'w' and not kd):
                            key = 's'
                            kd = True
                        elif(keys2 == 's' and not kd):
                            key = 'w'
                            kd = True
                        fuga -= 1
                    else:
                        print("vou por B")
                        key = 'B'
                        kd = True
                        fuga = 5
                        mapa.map[x2][y2]=0
                        #destroyed = True
                print(key)
                if(x < x2 and not putBomb and not kd and not mapa.is_stone((x+1,y))):
                    if(x2-x == 1):
                        if not mapa.is_stone((x2,y+1)) and not kd:
                            key = 'd'
                            key_save.append(key)
                            kd = True
                    else:
                        print ("meh")
                        key = 'd'
                        key_save.append(key)
                        kd = True

                elif (x > x2 and not putBomb and not kd and not mapa.is_stone((x-1,y))):
                    if(x-x2 == 1):
                        if not mapa.is_stone((x2,y+1)) and not kd:
                            key = 'a'
                            key_save.append(key)
                            kd = True
                    else:
                        key = 'a'
                        key_save.append(key)
                        kd = True
                print (key)
                if (y < y2 and not putBomb and not kd and not mapa.is_stone((x,y+1))):
                    if(y2-y == 1):
                        if not mapa.is_stone((x+1,y2)) and not kd:
                            key = 's'
                            key_save.append(key)
                            kd = True
                    else:
                        key = 's'
                        key_save.append(key)
                        kd = True


                elif (y > y2 and not putBomb and not kd and not mapa.is_stone((x,y-1))):
                    if(y-y2 == 1):
                        if not mapa.is_stone((x+1,y2)) and not kd:
                            key = 'w'
                            key_save.append(key)
                            kd = True
                    else:
                        key = 'w'
                        key_save.append(key)
                        kd = True

                enemies = state['enemies']
                print (key)
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
