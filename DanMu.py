import websocket
import ssl
import threading
import time
import datetime
import re
import json
import tkinter as tk
import requests
from lxml import etree

def main():
    create_window()

# 创建window
def create_window():
    window = tk.Tk()

    window.title('弹幕爬虫')
    window.geometry('600x600+1000+400')

    # 创建第一个容器
    fm1 = tk.Frame(window)
    fm1.pack(side=tk.TOP,fill=tk.X, expand=tk.YES)
    L1 = tk.Label(fm1, text="房间名:")
    global roomName
    roomName = tk.Listbox(fm1, width=30, height=1, fg="red", borderwidth=0)
    L1.pack(side=tk.LEFT)
    roomName.pack(side=tk.LEFT, padx=10)
    
    global roomNum
    roomNum = tk.Entry(fm1, fg='red', width=10)
    roomNum.bind('<Key-Return>', key_retun)
    L2 = tk.Label(fm1, text="房间号:")
    roomNum.pack(side=tk.RIGHT, padx=10)
    L2.pack(side=tk.RIGHT)
    

    # 创建第二个容器
    fm2 = tk.Frame(window)
    fm2.pack(side=tk.TOP, expand=tk.YES)
    global danmu_list
    danmu_list = tk.Listbox(fm2, width=450, height=28)
    danmu_list.pack()

    # 创建第三个容器
    fm3 = tk.Frame(window)
    fm3.pack(side=tk.TOP, expand=tk.YES)
    start = tk.Button(fm3, text='开始', bg='green', font=('Arial', 12), width=30, height=2, command = connect_threading, activebackground = "green")
    stop = tk.Button(fm3, text='停止', bg='green', font=('Arial', 12), width=30, height=2, command = stop_send, activebackground = "red")
    start.pack(side=tk.LEFT)
    stop.pack(side=tk.LEFT)
    
    window.mainloop()

# 回车事件
def key_retun(event):
    connect_threading()

# 连接弹幕websocket
def connect():
    global ws
    ws = websocket.WebSocketApp('wss://danmuproxy.douyu.com:8504/', 
    on_message=on_message, on_error=on_error, 
    on_close=on_close, on_open=on_open)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

# open接口
def on_open(ws):
    global chat_dic
    chat_dic = {}

    login()
    join_group()
    start_heartbeat()
    get_html()
    danmu_list.insert("0","已登入")
    print('open')

# 弹幕接口
def on_message(ws, message):
    res = message.decode(encoding='utf-8', errors='ignore')
    mes_handler(res)
    print(res)

# 错误接口
def on_error(ws, error):
    print(error)

# 关闭接口
def on_close(ws):
    save_thread = threading.Thread(target=save_json)
    save_thread.start()
    danmu_list.insert("0","已登出")
    print('close')

# 登入
def login():
    msg = 'type@=loginreq/roomid@=' + roomId + '/'
    send_msg(msg)

# 入组
def join_group():
    msg = 'type@=joingroup/rid@=' + roomId + '/gid@=-9999/'
    send_msg(msg)

# 心跳信息
def heartbeat():
    heartbeat_msg = 'type@=mrkl/'

    while True:
        send_msg(heartbeat_msg)
        for i in range(90):
            time.sleep(0.5)

# 斗鱼传输协议 参考https://open.douyu.com/source/api/63
def dy_encode(msg):
    data_len = len(msg) + 9
    msg_byte = msg.encode('utf-8')
    len_byte = int.to_bytes(data_len, 4, 'little')
    send_byte = bytearray([0xb1, 0x02, 0x00, 0x00])
    end_byte = bytearray([0x00])
    data = len_byte + len_byte + send_byte + msg_byte + end_byte

    return data

# 发送信息
def send_msg(msg):
    encodeMsg = dy_encode(msg)
    ws.send(encodeMsg)

# 停止接收
def stop_send():
    msg = 'type@=logout/'
    send_msg(msg)

# 弹幕处理
def mes_handler(res):
    mes_type = re.search('((?<=type@=)(.*?)(?=/))', res)
    if mes_type.group() == "chatmsg":
        r = re.search('(?P<Name>(?<=nn@=)(.*?)(?=/)).*(?P<Txt>(?<=txt@=)(.*?)(?=/)).*(?P<CardName>(?<=bnn@=)(.*?)(?=/)).*(?P<CardLevel>(?<=bl@=)(.*?)(?=/))', res)
        now_time = datetime.datetime.now()
        date1 = now_time.strftime('%Y-%m-%d %H:%M:%S')
        chat_dic[date1] = r.groupdict()
        mes_show(r.groupdict())
        # print(chat_dic)

# 显示弹幕
def mes_show(res):
    res_str = res["Name"] + "://" + res["Txt"] + "(" + res["CardLevel"] + "级" + res["CardName"] + ")"
    danmu_list.insert("0",res_str)

# 保存json至本地
def save_json():
    chat_json = json.dumps(chat_dic)
    with open('./a.txt','a') as f:
        f.write(chat_json)

# 连接线程
def connect_threading():
    global roomId
    roomId = roomNum.get()
    roomId_Check = re.search('(^[1-9]\d*$)', roomId)

    if roomId_Check != None:
        connect_thread = threading.Thread(target=connect)
        connect_thread.start()
    else:
        danmu_list.insert("0","输入的房间号必须为纯数字")

# 心跳信息线程
def start_heartbeat():
    heartbeat_thread = threading.Thread(target=heartbeat)
    heartbeat_thread.start()

def get_html():
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',  
        'referer': 'https://www.douyu.com/'
    }

    url = 'https://www.douyu.com/' + roomId
    response = requests.get(url, headers = header)
    response.encoding = 'utf-8'

    html = etree.HTML(response.text)
    get_roomName(html)

    # res = etree.tostring(html,encoding='utf-8')
    # print(res.decode('utf-8'))

def get_roomName(html):
    result = html.xpath('//h3[@class="Title-header"]/text()')
    name = result[0].strip()
    roomName.insert("0",name)

if __name__ == '__main__':
    main()