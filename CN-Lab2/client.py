# -*- coding:utf-8 -*-
import socket
import thread
import server

from protocal import *


def new_client_socket(client_port, protocol):
    # 设置网络连接为ipv4， 传输层协议为tcp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 传输完成后立即回收该端口
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 任意ip均可以访问
    s.bind(('', client_port))

    p = protocol(s)
    p.receive_data()


if __name__ == '__main__':
    print "CLIENT"
    # 接收来自服务器端的数据
    thread.start_new_thread(new_client_socket, (CLIENT_PORT, Sr))
    # 从客户端向服务器端发送数据
    thread.start_new_thread(server.new_server_socket, (SERVER_PORT_EXTRA, CLIENT_PORT_EXTRA, 'data/client_send.txt', Gbn))


    while True:
        pass


