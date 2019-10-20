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

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server


                x, y = state['bomberman']

                walls = state['walls']

                enemies = state['enemies']

                ex = state['exit']

                if(len(walls) != 0):
                    #if mapa.map[x2][y2]==0:
                    x2, y2 = minWall(walls,(x,y))
                    print("Próxima parede:")
                    print(x2,y2)
                    print ("\nparede:")
                    print (x2,y2)
                    print ("\nEU estou em:")
                    print (x,y)


                    kd = False

                    near = mapa.map[x+1][y] == mapa.map[x2][y2] or mapa.map[x-1][y] == mapa.map[x2][y2] or mapa.map[x][y-1] == mapa.map[x2][y2] or mapa.map[x][y+1] == mapa.map[x2][y2]
                    putBomb = [x+1, y] == [x2,y2] or [x-1,y] == [x2,y2] or [x,y-1] == [x2,y2] or [x,y+1] == [x2,y2]
                    
                    print(x2,y2)

                    if(near):
                        print("chega aqui?")
                        if fuga > 0:
                            if len(key_save) == 0:
                                continue
                            keys2 = key_save.pop()
                            key = keys2
                            kd = True
                            fuga -= 1
                        elif(putBomb):
                            print("vou por B")
                            key = 'B'
                            kd = True
                            fuga = 4
                            mapa.map[x2][y2]=0



                    if(x < x2 and not near and not kd and not mapa.is_stone((x+1,y))):
                        if(x2-x == 1):
                            if not mapa.is_stone((x2,y+1)) and not kd:
                                key = 'd'
                                key_save.append('a')
                                kd = True
                        else:
                            key = 'd'
                            key_save.append('a')
                            kd = True

                    elif (x > x2 and not near and not kd and not mapa.is_stone((x-1,y))):
                        if(x-x2 == 1):
                            if not mapa.is_stone((x2,y+1)) and not kd:
                                key = 'a'
                                key_save.append('d')
                                kd = True
                        else:
                            key = 'a'
                            key_save.append('d')
                            kd = True
                            
                    if (y < y2 and not near and not kd and not mapa.is_stone((x,y+1))):
                        if(y2-y == 1):
                            if not mapa.is_stone((x+1,y2)) and not kd:
                                key = 's'
                                key_save.append('w')
                                kd = True
                        else:
                            key = 's'
                            key_save.append('w')
                            kd = True


                    elif (y > y2 and not near and not kd and not mapa.is_stone((x,y-1))):
                        if(y-y2 == 1):
                            if not mapa.is_stone((x+1,y2)) and not kd:
                                key = 'w'
                                key_save.append('s')
                                kd = True
                        else:
                            key = 'w'
                            key_save.append('s')
                            kd = True

                    print("aaah")
                    print(key)
                # JUST IDEAS, WORKING ON IT

                elif (len(walls) == 0):
                    # for enemie in enemies:
                    #     dist = calc_pos((x,y), enemie['pos'])
                    #     x_e, y_e = enemie['pos']

                    #     if(x < x_e):
                    #         key = 'd'
                    #     if(x > x_e):
                    #         key = 'a'
                    #     if(y < y_e):
                    #         key = 's'
                    #     if(y > y_e):
                    #         key = 'w'

                    #     if(dist <= 2):
                    #         key = 'B'
                    print("ACABARAM AS PAREDES")
                    print(key)
                    print(x,y)


                    if(x < 1):
                        key = 'd'
                    if(x > 1):
                        key = 'a'
                    if(y < 1):
                        key = 's'
                    if(y > 1):
                        key = 'w'

                    
                    for enemie in enemies:
                        dist = calc_pos((1,1), enemie['pos'])

                        if(dist <= 3):
                            if fuga > 0:
                                key = 's'
                                fuga = 0
                            else:
                                key = 'B'
                                fuga = 2


                    # print(ex)
                    xi, yi = ex
                    if (len(enemies) == 0):
                        if(x < xi):
                            key = 'd'
                        if(x > xi):
                            key = 'a'
                        if(y < yi):
                            key = 's'
                        if(y > yi):
                            key = 'w'

                    
                                
                

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