# -*- coding:utf-8 -*-
import sys
import select
from random import random

# 设置在localhost进行测试
HOST = '127.0.0.1'
# 设置服务器端与客户端的端口号
SERVER_PORT = 10001
CLIENT_PORT = 10002
# 另开端口组实现双向通信
SERVER_PORT_EXTRA = 10003
CLIENT_PORT_EXTRA = 10004
# 单次读取数据大小
BUFFER_SIZE = 1024 * 2
# 窗口与包序号长度
WINDOWS_LENGTH = 8
SEQ_LENGTH = 10
# 最大延迟时间
MAX_TIME = 3


# 定义数据格式，其中存储着数据序号、数据信息以及当前数据处于神什么状态：未发送(0)，未确认(1)，已接收(2)
class Block(object):

    def __init__(self, msg, seq=0, state=0):
        self.seq = str(seq % SEQ_LENGTH)
        self.msg = msg
        self.state = state

    # 数据格式："序列号 数据"
    def __str__(self):
        return self.seq + ' ' + self.msg


# 建立一个GBN协议
class Gbn(object):

    def __init__(self, s):
        self.s = s

    # 数据发送方
    def send_data(self, path, port):

        # 计时和包序号初始化
        cnt_time = 0
        seq = 0

        # 设置发送数据窗口
        data_windows = []

        # 标记是否传输完数据
        # flag = 0

        # 打开待发送数据文件
        with open(path, 'r') as fl:

            # 开始发送数据
            while True:

                # 当超时后，将窗口内的数据更改为未发送状态
                if cnt_time > MAX_TIME:
                    print 'Time over.'
                    for block in data_windows:
                        block.state = 0

                # 窗口中数据少于最大容量时，尝试添加新数据
                while len(data_windows) < WINDOWS_LENGTH:
                    line = fl.readline().strip()

                    # 数据已发送完
                    if not line:
                        # sys.stdout.write('------END------\n')
                        # flag = 1
                        break

                    # 建立一个数据分组
                    block = Block(line, seq=seq)
                    data_windows.append(block) # 将这个数据分组放入窗口当中
                    seq += 1

                '''
                if flag == 1:
                    print 'All data were sent out.'
                    break
                '''
                # 窗口内无数据则退出总循环
                if not data_windows:
                    break

                # 遍历窗口内数据，如果存在未成功发送的则发送
                for block in data_windows:
                    if block.state == 0:
                        self.s.sendto(str(block), (HOST, port))
                        block.state = 1

                # 无阻塞socket连接监控
                r_list, w_list, e_list = select.select([self.s, ], [], [], 1)

                # 当发现当前socket接受到ACK数据
                if len(r_list) > 0:

                    # 收到一个ACK以后重置计时器
                    cnt_time = 0

                    msg, addr = self.s.recvfrom(BUFFER_SIZE)
                    # print 'hhh' + msg
                    sys.stdout.write('Just receive: ACK ' + msg.split()[1] + '\n')

                    # 对于在接收到的ACK序号之前的所有数据分组都被确认接收了，所以向后移动滑动窗口
                    for i in range(len(data_windows)):
                        if msg.split()[1] == data_windows[i].seq:
                            data_windows = data_windows[i+1:]
                            break
                else:
                    # 未收到数据则计时器加一
                    cnt_time += 1

        self.s.close()

    # 接收数据方
    def receive_data(self):

        # 记录上一个回执的ack的值
        last_ack = SEQ_LENGTH - 1
        data_received = []

        while True:

            # 无阻塞socket连接监控
            r_list, w_list, e_list = select.select([self.s, ], [], [], 1)

            # 接收数据
            if len(r_list) > 0:
                msg, addr = self.s.recvfrom(BUFFER_SIZE)
                # 提取该数据分组当中的序列号
                seq = int(msg.split()[0])
                # 如果当前接收到的数据分组序列号是连续的，则发送ACK数据
                if last_ack == (seq - 1) % SEQ_LENGTH:
                    # 丢包率为0.2，如果丢包了，就当没有接收该数据，重新进行监控
                    if random() < 0.2:
                        continue
                    # 没有丢包则发送确认帧
                    self.s.sendto('ACK ' + str(seq), addr)
                    last_ack = seq
                    # 判断数据是否重复
                    if seq not in data_received:
                        data_received.append(seq)
                        sys.stdout.write(msg + '\n')

                    while len(data_received) > WINDOWS_LENGTH:
                        data_received.pop(0)
                # 当收到的是不连续的序列号，则将该数据分组丢弃，重新发送上一个确认的ACK
                else:
                    print 'The block ' + str(seq) + ' is not that I want.'
                    self.s.sendto('ACK ' + str(last_ack), addr)
        self.s.close()


class Sr(object):

    def __init__(self, s):
        self.s = s

    def send_data(self, path, port):

        # 计时和包序号初始化
        time = 0
        seq = 0
        data_windows = []
        with open(path, 'r') as f:
            while True:

                # 当超时后，将窗口内第一个发送成功未确认的数据状态更改为未发送
                if time > MAX_TIME:
                    for block in data_windows:
                        if block.state == 1:
                            block.state = 0
                            break

                # 窗口中数据少于最大容量时，尝试添加新数据
                while len(data_windows) < WINDOWS_LENGTH:
                    line = f.readline().strip()
                    if not line:
                        break

                    block = Block(line, seq=seq)
                    data_windows.append(block)
                    seq += 1

                # 窗口内无数据则退出总循环
                if not data_windows:
                    break

                # 遍历窗口内数据，如果存在未成功发送的则发送
                for block in data_windows:
                    if block.state == 0:
                        self.s.sendto(str(block), (HOST, port))
                        block.state = 1

                r_list, w_list, e_list = select.select([self.s, ], [], [], 1)

                if len(r_list) > 0:

                    # 收到数据则重新计时
                    time = 0

                    msg, addr = self.s.recvfrom(BUFFER_SIZE)
                    sys.stdout.write('Just receive: ACK ' + msg.split()[1] + '\n')

                    # 收到数据后更改该数据包状态为已接收
                    for block in data_windows:
                        if msg.split()[1] == block.seq:
                            block.state = 2
                            break
                else:
                    # 未收到数据则计时器加一
                    time += 1

                # 当窗口中首个数据已接收时，窗口前移
                while data_windows[0].state == 2:
                    data_windows.pop(0)
                    # 如果此时数据窗口当中不再有数据时表明数据传输完毕
                    if not data_windows:
                        break
        self.s.close()

    def receive_data(self):

        # 窗口的初始序号
        seq = 0
        data_windows = {}

        while True:
            r_list, w_list, e_list = select.select([self.s, ], [], [], 1)

            if len(r_list) > 0:
                msg, addr = self.s.recvfrom(BUFFER_SIZE)
                ack = msg.split()[0]
                # 丢包率为0.2
                if random() < 0.2:
                    continue

                # 返回成功接收的包序号
                self.s.sendto('ACK ' + ack, addr)
                data_windows[ack] = msg.split()[1]

                # 滑动窗口
                while str(seq) in data_windows:
                    sys.stdout.write(str(seq) + ' ' + data_windows[str(seq)] + '\n')
                    data_windows.pop(str(seq))
                    seq = (seq + 1) % SEQ_LENGTH

        self.s.close()


