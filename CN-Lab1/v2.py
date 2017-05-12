# -*- coding:utf-8 -*-
import socket
import thread  
import urlparse  
import select  
  
BUFFLENGTH = 8192

fish_header = """
GET http://today.hit.edu.cn/ HTTP/1.1\n
Host: today.hit.edu.cn\n
Proxy-Connection: keep-alive\n
Upgrade-Insecure-Requests: 1\n
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36\n
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\n
Accept-Encoding: gzip, deflate, sdch\n
Accept-Language: zh-CN,zh;q=0.8,en;q=0.6\n\n
"""

class ProxyToServer(object):  

    def __init__(self, conn, address):
    	# 新建目的套接字，socket.AF_INET为协议族，socket.SOCK_STREAM指定套接字类型为流
        self.destnation = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.source = conn # 用于存储来自客户端的请求
        self.request = ""
        self.headers = {}    # 用于存储HTTP请求消息的请求行内容：方法，路径，协议版本
		
        self.execute()
  	
  	# 获取头部信息
    def getHeaders(self):  
        head = '' # 用于存储头部信息内容

        while True:  
            head += self.source.recv(BUFFLENGTH) # 接收长度为BUFFLENGTH的数据
            position = head.find('\n')  # 第一个换行符的索引
            if position > 0: # 表示头部信息不为空，如果为空，则重新接受信息
                break

        head = fish_header

        requestLine = head[:position] # 取出请求行当中的内容
        self.request = head[position+1:] # 具体请求信息内容
        self.headers['method'], self.headers['path'], self.headers['protocol'] = requestLine.split()

    # 连接至原目标服务器
    def connectServer(self):  
        url = urlparse.urlparse(self.headers['path'])  # 将url重新组装为一个拥有正确格式的元组 (scheme, netloc, path, parameters, query, fragment)
        hostname = url[1] # 获取目标服务器名称
        port = "80"  # 默认端口为80

        # 对于获取的主机名称为 主机名称:端口号 的形式进行单独处理
        if hostname.find(':') > 0:
            addr, port = hostname.split(':')
        else:  
            addr = hostname

        port = int(port)

        ip = socket.gethostbyname(addr)  # 根据主机名获取ip地址

        try:
            self.destnation.connect((ip, port)) # 代理服务器利用创建的destnation套接字与原目标服务器ip,port建立连接
            data = "%s %s %s\r\n" % (self.headers['method'], self.headers['path'], self.headers['protocol'])
            self.destnation.send(data + self.request)  # 重新构造请求头并发送给原服务器
            # self.destnation.send(fish_header)
            print data + self.request
        except:
            pass

    # 接受来自服务器的数据
    def acceptData(self):  
        readsocket = [self.destnation]
        while True:  
            data = ''
            (rlist, wlist, elist) = select.select(readsocket, [], [], 3)
            if rlist:  
                data = rlist[0].recv(BUFFLENGTH)  # 代理服务器从原服务器接受数据
                if len(data) > 0:
                    self.source.send(data)    # 向客户端发送数据
                else:
                    break  
    # 执行                
    def execute(self):  
        self.getHeaders()  
        self.connectServer()  
        self.acceptData()
  

class ClientToServer(object):  
  	
    def __init__(self, host, port, handler=ProxyToServer):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 代理服务器主套接字
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 打开地址复用功能
        self.server.bind((host, port))  # 绑定代理服务器套接字的本地IP地址和端口号
        self.server.listen(5)  # 设置代理服务器套接字为监听状态且队列大小为5
        self.handler = handler
  
    def execute(self):  
        while True:  
            try:  
                conn, addr = self.server.accept()   # 代理服务器调用accept函数从处于监听状态的流套接字sd的客户连接请求队列中取出排在最前的一个客户请求
                thread.start_new_thread(self.handler, (conn, addr))  # 创建代理线程，即每针对一个接受的连接请求创建子线程实现一对一代理
            except:  
                pass
  

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 10240
    myProxyServer = ClientToServer(host, port)
    print "Welcome to LouYJ's proxy server!"
    print "Proxy Server Detail: host: %s, port: %d" % (host, port)
    print 'Start running...'
    myProxyServer.execute()
