import socket, os
import argparse
import pysnooper

# @pysnooper.snoop()
def deploy_json(file, ip, port):
    HOST = ip
    PORT = port        # 端口号

    filename = os.path.basename(file)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    with open(file, 'rb') as f:
        s.sendall(filename.encode())  # 发送文件名
        response = s.recv(1024)
        print("file recive:", response.decode())
        data = f.read(1024)
        while data:
            s.sendall(data)
            data = f.read(1024)

    s.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to file to deploy.',
                    type=str, required=True)
    parser.add_argument('--ip', help='IP addr.',
                    type=str, required=True)
    parser.add_argument('--port', help='Port.',
                    type=int, required=False, default=13345)

    args = parser.parse_args()

    if os.path.isfile(args.config):
        deploy_json(args.config, args.ip, args.port)
    else:
        print("Error file path!")

    

if __name__ == '__main__':
    main()