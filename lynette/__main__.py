import sys, os
import argparse, json, time
import socket

from lynette_lib import parser_tree
from lynette_lib import collect
from lynette_lib.generate import Generator
from lynette_lib import aggregate
from lynette_lib import output
from lynette_lib import data_structure
from lynette_lib.clean import sh

class LynetteRunner():
    """Lynette编译器主运行类，负责协调整个编译流程。
    
    Attributes:
        sys_path (str): 系统路径，指向lynette包的安装目录
        component_path (str): 组件文件存储路径，用于存放编译中间文件
        output_dir (str): 输出目录，用于存放最终生成的P4文件
        debug_main (str): Debug模式下的主文件路径，如果为None则使用service模式
        service_conf (str): 服务配置文件路径，JSON格式
        service_json (dict): 解析后的服务配置字典
        input_path (str): 输入文件所在目录路径
        debug (str): 是否为debug模式，'yes'或'no'
        topo (dict): 网络拓扑信息字典
    """
    # @pysnooper.snoop()
    def __init__(self, sys_path, output_dir, service_conf, debug_main) -> None:
        """初始化LynetteRunner实例。
        
        Args:
            sys_path (str): 系统路径，指向lynette包的安装目录，用于定位组件和模板文件
            output_dir (str): 输出目录路径，用于存放最终生成的P4文件和表项文件
            service_conf (str): 服务配置文件路径，JSON格式，包含服务、应用和拓扑信息
            debug_main (str, optional): Debug模式下的主PNE文件路径。如果为None，则使用service模式编译
        """
        self.sys_path = sys_path.replace("/","//")
        self.component_path = self.sys_path  + '//component'
        self.output_dir = output_dir

        self.debug_main = debug_main
        self.service_conf = service_conf

        self.service_json = {}

        if self.debug_main == None:
            self.debug = 'no'
            input_path = os.path.dirname(os.path.abspath(self.service_conf))
        else:
            self.debug = 'yes'
            input_path = os.path.dirname(os.path.abspath(self.debug_main))
            
        self.input_path = input_path.replace("/","//")

    # @pysnooper.snoop()
    def run(self, if_p4=False, if_deploy=False, if_entry=False):
        """执行完整的编译流程。
        
        Args:
            if_p4 (bool, optional): 是否只编译P4文件。如果为True，在debug模式下编译完P4文件后直接退出。
                                    默认为False
            if_deploy (bool, optional): 是否部署代码到后端设备。如果为True，编译完成后会将P4文件发送到
                                       配置的后端设备。默认为False
            if_entry (bool, optional): 是否部署表项到后端设备。如果为True，编译完成后会将表项文件发送到
                                       配置的后端设备。默认为False
        """
        self.clean_component()

        if self.debug == 'yes':
            debug_main_name = self.debug_main.split("_main.pne")[0]
            self.compile_app()

            # 编译p4文件后直接退出
            if if_p4:
                self.compile_p4()
                exit(0)
            
            # 生成服务配置模板
            self.generate_service_conf(debug_main_name)

        # debug模式下依然需要以service为入口执行编译
        self.compile_service()


        if if_deploy:
            self.deploy_code()
        
        if if_entry:
            self.deploy_entry()


    def clean_component(self):
        """清理组件目录中的临时文件。
        
        删除component目录下所有子目录（topo、path、code、main）中的文件，
        以及component根目录下的文件，为新的编译做准备。
        """
        # folder_path = sys_parameter["sys_path"] + "component//topo"
        folder_path = self.component_path + "//topo"
        file_list = os.listdir(folder_path) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(folder_path, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path)

        # folder_path = sys_parameter["sys_path"] + "component//path"
        folder_path = self.component_path + "//path"
        file_list = os.listdir(folder_path) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(folder_path, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path)

        # folder_path = sys_parameter["sys_path"] + "component//code"
        folder_path = self.component_path + "//code"
        file_list = os.listdir(folder_path) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(folder_path, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path)

        # folder_path = sys_parameter["sys_path"] + "component//main"
        folder_path = self.component_path + "//main"
        file_list = os.listdir(folder_path) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(folder_path, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path)
        
        # folder_path = sys_parameter["sys_path"] + "component"
        folder_path = self.component_path
        file_list = os.listdir(folder_path) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(folder_path, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path)

    
    def compile_app(self):
        """编译应用文件（debug模式）。
        
        对debug模式下的主PNE文件进行预处理，将字符串中的引号替换为尖括号，
        以便后续解析处理。
        """
        # 预处理
        pre_code = ''
        with open(self.debug_main, "r") as f:
            pre_code = f.read()
        pre_code = pre_code.split('"')
        code = ''
        if len(pre_code) > 1:
            len_c = len(pre_code)
            code = pre_code[0] + "<" + pre_code[1] + ">" + pre_code[2]
            i = 3
            while i < len_c:
                code = code + "<" + pre_code[i] + ">" + pre_code[i+1]
                i = i + 2
        else:
            code = pre_code[0]
        with open(self.component_path + "//main//" + self.debug_main, "w") as f:
            f.write(code)


    def generate_service_conf(self, debug_main_name):
        """在debug模式下生成服务配置模板。
        
        该方法会解析debug模式下的PNE文件，提取应用信息，并自动生成service.json和path.json模板文件。
        
        Args:
            debug_main_name (str): 主PNE文件的名称（不含_main.pne后缀），用于生成服务配置的键名
        """  
        self.service_json = {debug_main_name:{"services":[]}}
        path = {}
        service_name_id = 1
        parser_tree_paremeter = {}
        parser_tree_paremeter["main_file_name"] = self.debug_main
        parser_tree_paremeter["input_path"] = self.input_path
        parser_tree_paremeter["sys_path"]   = self.sys_path
        forest = parser_tree.execute(parser_tree_paremeter)
        print("debug ",end = '')

        _, applications, _ = collect.execute(forest, self.input_path)
        for i in applications:
            self.service_json[debug_main_name]["services"].append({"service_name":"admin_" + str(service_name_id), "applications":[i]})
            path["admin_" + str(service_name_id)] = {"node1" :{"next": {"node2":12},"tables":6, "ip":"192.168.0.1"}}
            service_name_id = service_name_id + 1
        with open("service.json","w") as f:
            json.dump(self.service_json, f)
        if not os.path.exists("path"):
            os.makedirs("path")
        with open("path//path.json","w") as f:
            json.dump(path, f)

    def compile_p4(self):
        """编译P4文件（debug模式）。
        
        在debug模式下，直接从PNE文件中提取P4代码部分并输出。
        跳过前1行后，将剩余内容写入P4文件。
        """
        with open(self.debug_main, "r") as f_r:
            line_ahead = f_r.readline()

            line = line_ahead
            line_ahead = f_r.readline()

            line = line_ahead
            line_ahead = f_r.readline()
            with open(self.output_dir + "code.p4","w") as f_w:
                while line_ahead:
                    f_w.write(line)
                    line = line_ahead
                    line_ahead = f_r.readline()

    def compile_service(self):
        """编译服务（完整编译流程）。
        
        执行完整的编译流程：
        1. 解析PNE文件生成语法树
        2. 收集服务、应用和模块信息
        3. 生成P4代码片段
        4. 聚合代码到各个节点
        5. 输出最终的P4文件
        """
        # 读取服务配置
        users = self.read_service_conf()

        services = {}
        relation = {}

        for u in users:
            #1.对输入文件做语法树提取
            print(u + "_main.pne"+" ", end='')
            with open(self.input_path + "//log_out//log.txt","w") as file:
                file.write(u + "_main.pne"+" ")
            parser_tree_paremeter = {}
            parser_tree_paremeter["main_file_name"] = u + "_main.pne"
            parser_tree_paremeter["input_path"] = self.input_path
            parser_tree_paremeter["sys_path"]   = self.sys_path
            forest = parser_tree.execute(parser_tree_paremeter)

            #2.对程序组件做扫描提取
            print(u + "_main.pne"+" ",end='')
            with open(self.input_path + "//log_out//log.txt","a") as file:
                file.write(u + "_main.pne"+" ")
            _, applications, modules = collect.execute(forest,self.input_path)
            services_t = {}
            for s in self.service_json[u]["services"]:
                serv = data_structure.LYNETTE_SERVICE()
                serv.name = s["service_name"]
                for app in s["applications"]:
                    serv.application.append(app)
                    services_t[serv.name] = serv
            for s in services_t:
                if s not in services:
                    services[s] = services_t[s]

            #3.转译成p4语法，也包含宏替换
            print(u + "_main.pne"+" ",end='')
            with open(self.input_path + "//log_out//log.txt","a") as file:
                file.write(u + "_main.pne"+" ")
            generator = Generator(sys_path=self.sys_path)
            relation_t = generator.execute(services_t, applications, modules, self.input_path)
            for r in relation_t:
                if r not in relation:
                    relation[r] = relation_t[r]
        
        #4.出代码
        hdr_type_use = self.aggregate_code(relation, services)
        with open(self.input_path + "//log_out//log.txt","a") as file:
            file.write("All aggregate...\n")
        #5.出文件
        self.output_code(hdr_type_use)
        with open(self.input_path + "//log_out//log.txt","a") as file:
            file.write("ALL output...\n")
            file.write("ALL compile success!!\n")

    def read_service_conf(self):
        """读取服务配置文件。
        
        解析service.json文件，提取用户和服务信息，并对PNE文件进行预处理。
        
        Returns:
            list: 返回用户名称列表，每个用户对应一个主PNE文件
        """
        #todo_jjh: output pne name and users, check output in users
        users = []
        # 如果是debug模式，则可以避免重复读取服务配置
        if len(self.service_json) == 0:
            with open(self.service_conf, "r") as f:
                self.service_json = json.load(f)
            

        for i in self.service_json:
            if "main_file" not in self.service_json[i]['services'][0]:
                users.append(i)

        for f_main in users:
            pre_code = ''
            with open(f_main + "_main.pne","r") as f:
                pre_code = f.read()
            pre_code = pre_code.split('"')
            code = ''
            if len(pre_code) > 1:
                len_c = len(pre_code)
                code = pre_code[0] + ">-<" + pre_code[1] + ">-<" + pre_code[2]
                i = 3
                while i < len_c:
                    code = code + ">-<" + pre_code[i] + ">-<" + pre_code[i+1]
                    i = i + 2
            else:
                code = pre_code[0]
            with open( self.component_path + "//main//" + f_main + "_main.pne","w") as f:
                f.write(code)

        for i in self.service_json:
            if "main_file" in self.service_json[i]['services'][0]:
                users.append(i)
                main_file = self.service_json[i]['services'][0]["main_file"]
                with open(main_file,"r") as f:
                    pre_code = f.read()
                pre_code = pre_code.split('"')
                code = ''
                if len(pre_code) > 1:
                    len_c = len(pre_code)
                    code = pre_code[0] + ">-<" + pre_code[1] + ">-<" + pre_code[2]
                    i = 3
                    while i < len_c:
                        code = code + ">-<" + pre_code[i] + ">-<" + pre_code[i+1]
                        i = i + 2
                else:
                    code = pre_code[0]
                with open( self.component_path + "//main//" + i + "_main.pne","w") as f:
                    f.write(code)
        
        return users

    def aggregate_code(self, relation, services):
        """聚合代码片段到各个网络节点。
        
        根据网络拓扑和路径信息，将生成的代码片段分配到各个网络节点，并生成节点级别的Parser、
        Header和Deparser。
        
        Args:
            relation (dict): 代码片段关系字典，key为片段名称，value为LYNETTE_FRAG_RELATION对象，
                            包含片段的输入输出、变量文件、表数量等信息
            services (dict): 服务字典，key为服务名称，value为LYNETTE_SERVICE对象
        
        Returns:
            str: 返回使用的header类型名称，用于后续输出阶段
        """
        print("All ",end='')
        aggregate_parameter = {}
        aggregate_parameter["service_json_file"] = self.service_conf
        aggregate_parameter["if_debug"]          = self.debug
        aggregate_parameter["sys_path"]          = self.sys_path
        aggregate_parameter["input_path"]        = self.input_path
        return aggregate.execute(relation, services, aggregate_parameter)
    
    def output_code(self, header_name):
        """输出最终的P4代码文件。
        
        将聚合后的代码片段组合成完整的P4程序，包括Header、Parser、Control、Deparser等部分，
        并生成表项配置文件。
        
        Args:
            header_name (str): Header结构体的名称，用于生成P4代码中的header类型引用
        
        Returns:
            dict: 返回拓扑信息字典，包含所有节点的信息和配置
        """
        print("ALL ",end='')
        output_parameter = {}
        output_parameter["service_json_file"] = self.service_conf
        output_parameter["if_debug"]          = self.debug
        output_parameter["sys_path"]          = self.sys_path
        output_parameter["input_path"]        = self.input_path
        output_parameter["header_name"]       = header_name
        output_parameter["output_path"]       = self.output_dir
        self.topo = output.execute(output_parameter)
    
    def deploy_code(self):
        """部署P4代码到后端设备。
        
        遍历拓扑中的所有节点，将生成的P4文件转换为JSON格式后，
        通过TCP socket发送到各个节点的指定端口（默认13345）。
        """
        for node in self.topo:
            HOST = self.topo[node]["ip"]
            filename =  node + ".p4"
            jsonfile =  node + ".json"

            sh('p4test pne_out/%s --toJSON pne_out/%s' % (filename, jsonfile))

            PORT = 13345        # 端口号
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            
            with open("pne_out//" + jsonfile, 'rb') as f:
                s.sendall(jsonfile.encode())  # 发送文件名
                response = s.recv(1024)
                print("file recive:", response.decode())
                data = f.read(1024)
                while data:
                    s.sendall(data)
                    data = f.read(1024)
            
            time.sleep(2)
            s.close()

    def deploy_entry(self):
        """部署表项到后端设备。
        
        遍历拓扑中的所有节点，将生成的表项文件（JSON格式）通过TCP socket
        发送到各个节点的指定端口（默认13345）。
        优先查找flows目录下的表项文件，如果不存在则使用pne_out目录下的文件。
        """
        for node in self.topo:
            HOST = self.topo[node]["ip"]
            filename =  node + "_entry.json"

            if os.path.isdir("flows//"):
                filepath = "flows//"
            else:
                filepath = "pne_out//"

            PORT = 13345        # 端口号
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            
            with open(filepath + filename, 'rb') as f:
                s.sendall(filename.encode())  # 发送文件名
                response = s.recv(1024)
                print("file recive:", response.decode())
                data = f.read(1024)
                while data:
                    s.sendall(data)
                    data = f.read(1024)
            
            time.sleep(2)
            s.close()


def get_args():
    """解析命令行参数。

    Returns:
        argparse.Namespace: 包含所有解析后的命令行参数的命名空间对象。
        
    命令行参数说明：
    
    - ``--config`` (str): 服务配置文件路径。如果未指定，默认为 ``./service.json``。
                         该文件包含服务、应用和拓扑的配置信息。
    
    - ``--log-dir`` (str): 日志文件存储目录。如果未指定，默认为 ``./log/``。
    
    - ``--output-dir`` (str): 输出文件存储目录，用于存放生成的P4文件和表项文件。
                              如果未指定，默认为 ``./pne_out/``。
    
    - ``--debug-main`` (str): Debug模式下的主PNE文件路径。如果指定此参数，将只编译该文件，
                               不依赖service.json配置。用于快速测试单个PNE文件。
    
    - ``--verbosity`` (str): 设置输出信息的详细程度。如果未指定，默认为 ``info``。
                             可选值包括：debug, info, warning, error。
    
    - ``--clean`` (bool): 是否清理输出目录中的旧文件。如果指定，编译前会清空输出目录。
                          默认为True。
    
    - ``--target`` (str): 目标P4架构类型。可选值：v1model（软件交换机）或tna（硬件交换机）。
                          默认为 ``v1model``。
    
    - ``--entry`` (bool): 是否生成并部署表项到后端设备。如果指定，编译完成后会将表项文件
                         发送到配置的后端设备。默认为False。
    
    - ``--p4`` (bool): 是否只编译P4文件。在debug模式下，如果指定此参数，编译完P4文件后
                       直接退出，不进行后续的聚合和输出步骤。默认为False。
    
    - ``--check`` (bool): 是否使用p4test验证生成的P4代码。如果指定，会调用p4test生成
                          IR JSON文件进行验证。默认为False。
    
    - ``--deploy`` (bool): 是否部署P4代码到后端设备。如果指定，编译完成后会将P4文件发送到
                           配置的后端设备。默认为False。
    """

    cwd = os.getcwd()
    default_log_dir = os.path.join(cwd, 'log/')
    default_output_dir = os.path.join(cwd, 'pne_out/')
    default_target = 'v1model'

    parser = argparse.ArgumentParser()

    parser.add_argument('--config', help='Path to service configuration.',
                        type=str, required=False, default='./service.json')
    parser.add_argument('--log-dir', help='Generate logs in the specified folder.',
                        type=str, required=False, default=default_log_dir)
    parser.add_argument('--output-dir', help='Generate output of lynette in the specified folder.',
                        type=str, required=False, default=default_output_dir)
    parser.add_argument('--debug-main', help='Path to mian.pne file.',
                        type=str, required=False)
    parser.add_argument('--verbosity', help='Set messages verbosity.',
                        type=str, required=False, default='info')
    parser.add_argument('--clean', help='Cleans old files.',
                        action='store_true', required=False, default=True)
    parser.add_argument('--target', help='Target arch',
                        type=str, required=False, default=default_target)
    parser.add_argument('--entry', help='Send entries to back-end according to service config.',
                        action='store_true', required=False, default=False)
    parser.add_argument('--p4', help='Compile .p4 file.',
                        action='store_true', required=False, default=False)
    parser.add_argument('--check', help='Generate IR json via p4test.',
                        action='store_true', required=False, default=False)
    parser.add_argument('--deploy', help='Send .p4 to back-end according to service config.',
                        action='store_true', required=False, default=False)
    return parser.parse_args()

def main():
    """主函数，程序入口点。
    
    负责解析命令行参数，初始化LynetteRunner实例，并执行编译流程。
    """
    args = get_args()

    # clean output dir
    if args.clean:
        #argparse 会将命令行参数中的连字符 - 转换为下划线 _
        file_list = os.listdir(args.output_dir) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(args.output_dir, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path)

    sys_path = os.path.dirname(__file__)
    app = LynetteRunner(sys_path, args.output_dir, args.config, args.debug_main)
    # print(args.output_dir)
    app.run(if_p4=args.p4, if_deploy=args.deploy, if_entry=args.entry)

    print("ALL compile success!!")


if __name__ == '__main__':
    main()