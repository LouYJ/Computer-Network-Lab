# -*- coding:utf-8 -*-
import socket
import thread
import client
from protocal import *


def new_server_socket(server_port, client_port, path, protocol):
    # 设置网络连接为ipv4， 传输层协议为udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 传输完成后立即回收该端口
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 任意ip均可以访问
    s.bind(('', server_port))
    p = protocol(s)
    p.send_data(path, client_port)


if __name__ == '__main__':
    print "SERVER"
    # 服务器端向客户端发送数据
    thread.start_new_thread(new_server_socket, (SERVER_PORT, CLIENT_PORT, 'data/server_send.txt', Gbn))
    # 接收来自客户端的数据
    thread.start_new_thread(client.new_client_socket, (CLIENT_PORT_EXTRA, Sr))

    while True:
        pass

