import pyaudio as pa
import time
import sys
import asyncio
import websockets
import random
import json
import numpy as np
import os
#import soundfile as sf
from subprocess import call
from win_unicode_console import enable

class ClientSide:
    def __init__(self):

        self.SAMPLE_RATE = 16000
        # duration of signal frame, seconds
        self.FRAME_LEN = 0.5
        self.frame_overlap = 2*self.FRAME_LEN
        # number of audio channels (expect mono signal)
        self.CHANNELS = 1
        self.CHUNK_SIZE = int(self.FRAME_LEN*self.SAMPLE_RATE)
        self.offset=4
        self.empty_counter = 0
        self.sentece=""
        self.t3=0.0
        self.start=True
        self.resived_data=""
        self.CLIENT_ID = random.randint(1000,1000000)
        self.request_data=dict()
        self.step = 1
        self.char_cont = 0

    def printer(self,text):
                    enable()
                    print(text, end='')
                    sys.stdout.flush()
                    self.t3=time.time()
                    #self.sentece+=text
                    self.empty_counter = self.offset

    def config_audio(self):
        self.silence = []
        self.empty_counter = 0
        self.p = pa.PyAudio()
        print('Available audio input devices:')
        input_devices = []
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev.get('maxInputChannels'):
                input_devices.append(i)
                print(i, dev.get('name'))

        if len(input_devices):
            dev_idx = -2
            while dev_idx not in input_devices:
                print('Please type input device ID:')
                dev_idx = int(input_devices[-1])

        self.stream = self.p.open(format=pa.paInt16,
                        channels=self.CHANNELS,
                        rate= self.SAMPLE_RATE,
                        input=True,
                        input_device_index=dev_idx,
                        frames_per_buffer=self.CHUNK_SIZE)

    def close_stream(self):

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


    async def send_receive(self,URL="", auto_stop=False, stop_timer=20):
       self.config_audio()
       print(f'Connecting websocket to url ${URL}')
       async with websockets.connect(
           URL,
           #extra_headers=(("Authorization", auth_key),), #security!!!
           ping_interval=10,
           ping_timeout=60
       ) as _ws:
           await asyncio.sleep(0.01)
           print("Receiving SessionBegins ...")
           #session_begins = await _ws.recv()
           #print(session_begins)
           call('clear' if os.name =='posix' else 'cls')

           self.t1 = time.time()
           self.t2 = time.time()
           async def send():
               while True:
                   try:
                       #record_t1 = time.time()
                       data = self.stream.read(self.CHUNK_SIZE)
                       #record_t2 = time.time()
                       #print(record_t2 - record_t1)
                       #data = base64.b64encode(data)
                       signal = np.frombuffer(data, dtype=np.int16)
                       #print(len(signal))
                       self.step +=1
                       #signal2 = np.array(signal , dtype=np.float32)/2**15
                       #sf.write(f'/home/ahm/client_file{self.step}.wav', signal2, 16000)
                       json_data = {'CLIENT_ID': self.CLIENT_ID, 'matrix': signal.tolist(),
                                    "situation": self.start}
                       json_data = json.dumps(json_data)
                       await _ws.send(json_data)
                       del(json_data)
                       self.start = False
                   except websockets.exceptions.ConnectionClosedError as e:
                       print(e)
                       assert e.code == 4008
                       break
                   except Exception:
                       assert False, "Not a websocket 4008 error"
                   await asyncio.sleep(0.01)
               return True
           async def receive():
               while True:
                   try:
                       result_str = await _ws.recv()
                       result_str = json.loads(result_str)
                       text = result_str["txt"]
                       rescore_time = result_str["rescore time"]

                       if rescore_time:

                           call('clear' if os.name =='posix' else 'cls')

                       #sys.stdout.buffer.write(text.encode("utf-8"))
                       print(text, end='')

                   except websockets.exceptions.ConnectionClosedError as e:
                       print(e)
                       assert e.code == 4008
                       break
                   except Exception:
                       assert False, "Not a websocket 4008 error"
           async def controller(auto_stop, stop_timer):
               while self.stream.is_active():
                   if auto_stop and len(self.silence)>stop_timer:
                       self.goodbye()
                       _ws.close()
                       self.close_stream()
                       break
                   await asyncio.sleep(0.01)
           send_result, receive_result = await asyncio.gather(send(), receive(),
                                                              #controller(auto_stop, stop_timer)
                                                              )
