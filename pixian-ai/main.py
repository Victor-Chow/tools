from PIL import Image
from pathlib import Path
import numpy as np
import websocket
import json


class PNG:

    def __init__(self, arr) -> None:
        self.arr = arr.ravel()
        self.k = 0
        self.state = 0

    def setPixel(self, t, e, i, s, n):
        self.arr[t] = i
        self.arr[t + 1] = s
        self.arr[t + 2] = n
        self.arr[t + 3] = e

    def nextByte(self):
        result = self.ary[self.iAry]
        self.iAry += 1
        return result
    
    def nextInt(self):
        result = (self.ary[self.iAry] << 24) | (self.ary[self.iAry + 1] << 16) | (self.ary[self.iAry + 2] << 8) | self.ary[self.iAry + 3]
        self.iAry += 4
        return result
    
    def done(self):
        t, e, i, s = img.width, 0, img.height, 0

        for n in range(img.height):
            for o in range(img.width):
                r = n * img.width + o
                if 255 & self.arr[4 * r + 3]:
                    if o < t:
                        t = o
                    if e <= o:
                        e = o + 1
                    if n < i:
                        i = n
                    if s <= n:
                        s = n + 1


    def append(self, ary):
        self.ary = ary
        self.iAry = 0
        if self.state == 0:
            self.state = 1
            self.nextByte()
            t = self.nextInt()
            i = self.nextInt()
        while self.iAry < len(self.ary):
            t = self.nextByte()
            e = (t >> 6) & 3
            i = 63 & t
            
            if e != 2:
                i |= self.nextByte() << 6
            
            i += 1
            
            if e == 0:
                self.k += i
            elif e == 1:
                for _ in range(i):
                    self.setPixel(4 * self.k, 0, 0, 0, 0)
                    self.k += 1
            elif e == 2 or e == 3:
                for _ in range(i):
                    self.setPixel(4 * self.k, self.nextByte(), self.nextByte(), self.nextByte(), self.nextByte())
                    self.k += 1

def send_file(file_path):

    file_size = file_path.stat().st_size
    img = Image.open(file_path)
    arr = np.array(img.convert('RGBA'))
    url = f'wss://pixian.ai/internal/websocket?lc=en-US&len={file_size}&w={img.width}&h={img.height}&model=0'


    ws = websocket.WebSocket()
    ws.connect(url)
    chunk_size = 14 * 1024               # 设置每次传送数据的最大大小（14.8KB）

    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            ws.send_binary(chunk)
    out = b''
    # arr = np.empty(0)
    # print(arr)
    png = PNG(arr)
    while 1:
        response = ws.recv()
        if isinstance(response, bytes):
            # print('response length:', len(response))
            out += response
            png.append(np.frombuffer(response, dtype=np.uint8))
        else:
            data = json.loads(response)
            if data['command'] == 9:
                break
            elif data['command'] == 10:
                print('error:', data['body']['errorMessageTr'])
                break
    print(ws.is_open())

    # png.done()
    img = Image.fromarray(arr, mode='RGBA')

    img.save( output_folder / file_path.with_suffix('.png').name)

if __name__ == '__main__':
    input_folder = Path(input("输入文件夹："))
    output_folder = Path(input("输出文件夹："))
    output_folder.mkdir(parents=True, exist_ok=True)
    for file_path in input_folder.iterdir():
        if file_path.is_dir():
            continue
        print(file_path.name + ' '*10, end='')
        try:
            send_file(file_path)
            print('成功')
        except:
            print("失败")
