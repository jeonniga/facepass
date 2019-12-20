#!/usr/bin/env python3

"""
Created on Tue Dec 18 02:52:16 2018

sudo apt install python3-pip
pip install dropbox
pip install websockets
pip install pymongo
pip install cognitive_face
pip install asyncws

@author: seedp
"""
import time
import asyncio
import asyncws
import websockets

import pymongo

import cognitive_face as CF
KEY = ''  # Replace with a valid Subscription Key here.
CF.Key.set(KEY)

BASE_URL = 'https://eastasia.api.cognitive.microsoft.com/face/v1.0'  # Replace with your regional Base URL
CF.BaseUrl.set(BASE_URL)

import dropbox

strcode = ' '

@asyncio.coroutine
def echo(websocket):
    while True:
        frame = yield from websocket.recv()
        print(frame)
        if frame is None:
            break

        if frame == 'OPEN':
            yield from websocket.send('Door Open')
            print('Door Open')

        yield from websocket.send(frame)
        dbx = dropbox.Dropbox('') #dropbox api key here
        useraccount = dbx.users_get_current_account()
        print(useraccount.email)
        for entry in dbx.files_list_folder('/pictures').entries:
           try:
               if entry.name==frame :
                   conn = pymongo.MongoClient('localhost', 27017)
                   db = conn.get_database('facepass')
                   collection = db.get_collection('facepass')
                   dbresults = collection.find({"account":useraccount.email})
                   print(dbresults)
                   for result in dbresults:
                       strcode = result['code']
                       print('strcode:', strcode)

                   metadata, f = dbx.files_download('/pictures/'+entry.name)
                   out = open('./pictures/target/'+entry.name, 'wb')
                   out.write(f.content)
                   out.close()
                   print(metadata)
                   img_url1 = './pictures/original/'+entry.name
                   result1 = CF.face.detect(img_url1, landmarks=True, attributes='age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise')
                   faceId1 = result1[0]['faceId']
                   print('Original:', faceId1)

                   img_url2 = './pictures/target/'+entry.name
                   result2 = CF.face.detect(img_url2, landmarks=True, attributes='age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise')
                   faceId2 = result2[0]['faceId']
                   print('Target:',faceId2)
                   result = CF.face.verify(faceId1, another_face_id=faceId2)
                   print('O vs T :', result)

                   msg = str(result['isIdentical'])+","+strcode
                   print(msg)
                   yield from websocket.send(msg)
           except Exception as e:
               print("Error:" + e)
               continue

loop = asyncio.get_event_loop()
server = loop.run_until_complete(
    asyncws.start_server(echo, '0.0.0.0', 8765))
try:
    loop.run_forever()
except KeyboardInterrupt as e:
    server.close()
    loop.run_until_complete(server.wait_closed())
finally:
    loop.close()
