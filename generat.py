def generate_mac(server_id, vne_id, port):
# 固定OUI部分
oui = [0x02, 0x1A, 0x3B]
# 服务器ID（7位）
1 / 2
 ss = server_id & 0x7F
# 虚拟网元ID（5位）
vv = vne_id & 0x1F
# 端口号（2位）
pp = port & 0x03
# 组合MAC地址
mac = oui + [ss, vv, pp]
return ":".join(f"{x:02X}" for x in mac)
# 示例：服务器5，虚拟网元12，端口2
print(generate_mac(5, 12, 2)) # 输出：02:1A:3B:05:0C:02