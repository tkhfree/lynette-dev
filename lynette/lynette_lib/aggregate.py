from lark import Lark, Tree, Token
from lynette.lynette_lib import data_structure
from lynette.lynette_lib.grammar.grammar_define import grammar_define
from lynette.lynette_lib.grammar.grammar_header import grammar_header
from lynette.lynette_lib.grammar.grammar_parser import grammar_parser
import json, copy

type_dict_global = {}
const_dict_global = {}
# debug = 'no', json_file = ''
def execute(relation:dict, services:dict, aggregate_parameter):
    print("aggregate...")

    construct_type_dict_global(aggregate_parameter)

    #根据path.json重构topo和path
    with open(aggregate_parameter["input_path"] + "//path//path.json","r") as file:
        path_json = json.load(file)
    with open(aggregate_parameter["sys_path"] + "//component//path//path.json",'w') as file:
        path = {}
        for s in path_json:
            path[s] = []
            for node in path_json[s]:
                path[s].append(node)
        json.dump(path,file)
    with open(aggregate_parameter["sys_path"] + "//component//topo//topo.json",'w') as file:
        topo = {}
        for s in path_json:
            for node in path_json[s]:
                if node not in topo:
                    topo[node] = {"next":{},"tables":0,"ip":"0.0.0.0","resource":"CPU"}
                for node_n in path_json[s][node]["next"]:
                    if node_n not in topo[node]["next"]:
                        topo[node]["next"][node_n] = path_json[s][node]["next"][node_n]
            for node in path_json[s]:
                if node in topo:
                    topo[node]["tables"] = path_json[s][node]["tables"]
            for node in path_json[s]:
                if node in topo:
                    topo[node]["ip"] = path_json[s][node]["ip"]
            for node in path_json[s]:
                if node in topo and "resource" in path_json[s][node]:
                    topo[node]["resource"] = path_json[s][node]["resource"]
        json.dump(topo,file)
    

    topo = {}
    with open(aggregate_parameter["sys_path"] + "//component//topo//topo.json",'r') as file:
        topo = json.load(file)
    relation_node_frag = {}
    for node in topo:
        relation_node_frag[node] = []

    path = {}
    with open(aggregate_parameter["sys_path"] + "//component//path//path.json",'r') as file:
        path = json.load(file)
    
    #对全服务/全节点执行运算
    #这里在划分的时候要么整数线性规划要么sat，样例情况特殊写了个特例算法
    frag_to_service_name = {}
    for s in services:
        service = services[s]
        service_name = service.name
        service_path = path[service_name]
        #计算一下当前app的head和tail切片是什么
        app_i = 0
        app_num = len(service.application) - 1
        frag = service_name + "_" + service.application[app_i]
        app_head = frag + "_0"
        app_tail = frag + "_" + str(relation[frag])
        app_user_id = 1
        #开始下放
        for node in service_path:
            #先放head
            relation_node_frag[node].append(app_head)
            frag_to_service_name[app_head] = service_name
            topo[node]["tables"] = topo[node]["tables"] - relation[app_head].table_num
            topo[node]["tables"] = topo[node]["tables"] - relation[app_tail].table_num
            #如果user切片还没够到tail,并且node里面还有空间
            app_user = frag + "_" + str(app_user_id)
            while app_user_id < relation[frag] and topo[node]["tables"] >= relation[app_user].table_num:
                relation_node_frag[node].append(app_user)
                frag_to_service_name[app_user] = service_name
                topo[node]["tables"] = topo[node]["tables"] - relation[app_user].table_num
                app_user_id = app_user_id + 1
                app_user = frag + "_" + str(app_user_id)
            #最后放tail
            relation_node_frag[node].append(app_tail)
            frag_to_service_name[app_tail] = service_name
            #如果user切片够到tail了，并且还有其他的app
            if app_user_id == relation[frag] and app_i < app_num:
                app_i = app_i  + 1
                frag = service_name + "_" + service.application[app_i]
                app_head = frag + "_0"
                app_tail = frag + "_" + str(relation[frag])
                app_user_id = 1
    
    #检查一下每个节点都有什么切片 
    if 1 == 0:
        for node in relation_node_frag:
            print(node,relation_node_frag[node])

    #输出节点和app的映射关系
    with open(aggregate_parameter["input_path"] + "//path_out//path-result.json","w") as file:
        answer = {}
        for s in services:
            s_name = s
            answer[s_name] = {}
            this_path = path[s_name]
            apps = services[s_name].application
            for node in this_path:
                if node not in answer[s_name]:
                    answer[s_name][node] = []
                    for i in apps:
                        if i in relation_node_frag[node][0]:
                            answer[s_name][node].append(i)
        json.dump(answer,file,indent=2)


    #根据映射关系构造文件，主要是control部分
    #先清空一下历史文件
    # 指定要删除的文件夹路径
    folder_path = aggregate_parameter["sys_path"] + "//component//code"
    # 获取该文件夹下的所有文件名列表
    #开始按节点输出
    for node in relation_node_frag:
        #先组合一下var文件
        var_file = {}
        for frag in relation_node_frag[node]:
            for var in relation[frag].varfile:
                var_file[var] = 1
        
        #生成var文件
        with open(folder_path + "//" + node + "_control","w") as file_w:
            for var in var_file:
                with open(aggregate_parameter["sys_path"] + "//component//" + var,"r") as file_r:
                    line = file_r.readline()
                    while line :
                        file_w.write(line)
                        line = file_r.readline()
            file_w.write("\n")
            for frag in relation_node_frag[node]:
                with open(aggregate_parameter["sys_path"] + "//component//" + frag + "_tem.pne","r") as file_r:
                    line = file_r.readline()
                    while line :
                        file_w.write(line)
                        line = file_r.readline()

        #生成action
        with open(folder_path + "//" + node + "_control","a") as file_w:
            for frag in relation_node_frag[node]:
                with open(aggregate_parameter["sys_path"] + "//component//" + frag + "_action.pne","r") as file_r:
                    line = file_r.readline()
                    while line :
                        if line.find('Next') != -1:
                            tt = frag.split('_')
                            print("ag 555",tt)
                            tt = tt[0]
                            next_node = path[tt].index(node) + 1
                            if next_node == len(path[tt]):
                                next_node = 0
                            else:
                                next_node = path[tt][next_node]
                            if next_node in topo[node]['next']:
                                next_node = topo[node]['next'][next_node]
                            line = line.replace('Next',str(next_node))
                        file_w.write(line)
                        line = file_r.readline()
            file_w.write("\n")
        
        #生成table
        with open(folder_path + "//" + node + "_control","a") as file_w:
            for frag in relation_node_frag[node]:
                with open(aggregate_parameter["sys_path"] + "//component//" + frag + "_table.pne","r") as file_r:
                    line = file_r.readline()
                    while line : 
                        file_w.write(line)
                        line = file_r.readline()
            file_w.write("\n")

        #生成reg
        with open(folder_path + "//" + node + "_control","a") as file_w:
            for frag in relation_node_frag[node]:
                with open(aggregate_parameter["sys_path"] + "//component//" + frag + "_reg.pne","r") as file_r:
                    line = file_r.readline()
                    while line :
                        file_w.write(line)
                        line = file_r.readline()
            file_w.write("\n")

        #生成control
        with open(folder_path + "//" + node + "_control","a") as file_w:
            file_w.write("apply {\n")
            file_w.write("\n    /*******************************************/\n\n") 
            for frag in relation_node_frag[node]:
                with open(aggregate_parameter["sys_path"] + "//component//" + frag + "_control.pne","r") as file_r:
                    line = file_r.readline()
                    while line :
                        if line.find('Next') != -1:
                            tt = frag.split('_')
                            print("ag 555",tt)
                            tt = tt[0]
                            next_node = path[tt].index(node) + 1
                            if next_node == len(path[tt]):
                                next_node = 0
                            else:
                                next_node = path[tt][next_node]
                            if next_node in topo[node]['next']:
                                next_node = topo[node]['next'][next_node]
                            line = line.replace('Next',str(next_node))
                        file_w.write("    ")
                        file_w.write(line)
                        line = file_r.readline()
                    file_w.write("\n    /*******************************************/\n\n")
            file_w.write("}\n")

        #生成entry
        with open(folder_path + "//" + node + "_entry","a") as file_w:
            entry = {}
            entry["target"] = node
            entry["entries"] = []
            for frag in relation_node_frag[node]:
                with open(aggregate_parameter["sys_path"] + "//component//" + frag + "_entry.pne","r") as file_r:
                    line = file_r.readline()
                    while line:
                        if len(line) > 10:
                            e = json.loads(line)
                            for v in e['action_params']:
                                for vi in e['action_params'][v]:
                                    if vi == '_Next':
                                        e['action_params'][v] = ['0']
                                        index = path[frag_to_service_name[frag]].index(node)
                                        if index+1 < len(path[frag_to_service_name[frag]]):
                                            e['action_params'][v] = [str(topo[node]['next'][path[frag_to_service_name[frag]][index+1]])]
                                        else:
                                            if aggregate_parameter["if_debug"] == 'no':
                                                with open(aggregate_parameter["input_path"] + "//" + aggregate_parameter["service_json_file"],"r") as f_r:
                                                    serv_json = json.load(f_r)
                                                for user in serv_json:
                                                    for serv in serv_json[user]["services"]:
                                                        if "service_hosts" in serv:
                                                            if serv["service_name"] == frag_to_service_name[frag]:
                                                                for h in serv["service_hosts"][-1]["ports"]:
                                                                    e['action_params'][v] = [str(serv["service_hosts"][-1]["ports"][h])]
                            entry["entries"].append(e)
                        line = file_r.readline()
            json.dump(entry,file_w,indent=2)

    #整理每个node上的hdr都有什么
    relation_node_hdr = {}
    for node in relation_node_frag:
        hdr_list = {}

        #先看输入有什么，其实是读取了什么
        for frag in relation_node_frag[node]:
            for input in relation[frag].input:
                input = input.split(".")
                if input[0] == "hdr":
                    hdr_list[input[1]] = 1 
        
        #先看输出有什么，其实是写入了什么
        for frag in relation_node_frag[node]:
            for output in relation[frag].output:
                output = output.split(".")
                if output[0] == "hdr":
                    hdr_list[output[1]] = 1 

        relation_node_hdr[node] = hdr_list
    
    #解析parser，根据需要生成独立小parser，这是个大工程
    #需要处理的有五部分：hdr定义，hdr结构体的构造，gmeta的内容，parser树的重新构建，deparser的重建
    #gmeta这个东西有点异议，暂时不处理
    #遵循 解析 - 提取 - 生成 老三步
    
    #先针对hdr定义，hdr结构体的构造
    tree = aggregate_parse_header(aggregate_parameter)

    #提取header和struct组件,gmeta其实也是一种结构体
    header,struct = aggregate_collect_header(tree)

    #解析parser树
    tree = aggregate_parse_parser(aggregate_parameter)

    #提取输出二元组，看看叫什么以及类型是什么
    hdr_type, hdr_name, meta_type, meta_name = aggregate_collect_sys_data(tree)

    hdr_type_return = hdr_type

    #提取deparser，说真的写着写着我感觉自己在制毒
    deparser = aggregate_collect_deparser(tree,hdr_type,hdr_name,struct)

    #构建解析树，通常来讲，这东西应该是个树，避免成环
    #至于成环了怎么办，凉拌
    parser = aggregate_collect_parser(tree,hdr_type,hdr_name,struct)

    #针对每个节点开始构建节点级别的parser
    #在这个过程中需要记录header里面都用到什么了
    relation_node_hdr_uses = {}
    for node in relation_node_hdr:
        relation_node_hdr_use = []
        parser_node = copy.deepcopy(parser)
        parser_node_have = {}
        parser_node_no_have = {}
        #开始划分树
        for pn in parser_node:
            have = 0
            for protocol in relation_node_hdr[node]:
                if protocol in parser_node[pn].protocol:
                    have = 1
            if have == 0 and pn != "start":
                parser_node_no_have[pn] = parser_node[pn]
            else:
                parser_node_have[pn] = parser_node[pn]
        #对于不在节点上的parser节点，做好善后
        for pn in parser_node_no_have:
            for pn_rely in parser_node_no_have[pn].rely:
                if pn_rely in parser_node_have:
                    parser_node_have[pn_rely].next.pop(pn)
        #记录一下用到了那些hdr
        for pn in parser_node_have:
            if parser_node_have[pn].exact not in relation_node_hdr_use and parser_node_have[pn].exact != '':
                relation_node_hdr_use.append(parser_node_have[pn].exact)
        relation_node_hdr_uses[node] = relation_node_hdr_use

        #开始实际生成parser
        with open(folder_path + "//" + node + "_parser","a") as file:
            for pn in parser_node_have:
                file.write("    state ")
                file.write(pn)
                file.write(" {\n")
                #exact
                if parser_node_have[pn].exact != '':
                    file.write("        pkt.extract(")
                    file.write(hdr_name + "." + parser_node_have[pn].exact)
                    file.write(");\n")
                #ins
                for ins in  parser_node_have[pn].ins:
                    ins = ins.children[0]
                    if ins.data == "tmp_def":
                        tmp_type = ins.children[0].children[0].value
                        tmp_name = ins.children[1].children[0].value
                        file.write("        ")
                        file.write(tmp_type)
                        file.write(" ")
                        file.write(tmp_name)
                        file.write(";\n")
                    elif ins.data == "lookahead":
                        if ins.children[0].children[0].data == "name":
                            assign = ins.children[0].children[0].children[0].value
                        else:
                            print("error-aggragate_execute what lookahead",ins.children[0].children[0].data)
                            exit()
                        ahead_type = ins.children[1].children[0].value
                        file.write("        ")
                        file.write(assign)
                        file.write(" = pkt.lookahead<")
                        file.write(ahead_type)
                        file.write(">();\n")
                    elif ins.data == "advance":
                        file.write("        pkt.advance(")
                        ins = ins.children[0]
                        if ins.data == "data":
                            ins = ins.children[0].children[0].value
                            if ins in const_dict_global:
                                ins = const_dict_global[ins]
                            file.write(ins)
                        elif ins.data == "data_plus":
                            ins_h = ins.children[0].children[0].children[0].value
                            if ins_h in const_dict_global:
                                ins_h = const_dict_global[ins_h]
                            file.write(ins_h)
                            int_t = ins.children[1].children[0].value
                            file.write(" * ")
                            file.write(int_t)
                        file.write(");\n")
                    elif ins.data == "assign":
                        file.write("        ")
                        left = ins.children[0].children[0]
                        right = ins.children[1].children[0]
                        data = left
                        if data.data == "name_field":
                            first = data.children[0].value
                            if first == hdr_name or first == meta_name:
                                int_i = 0
                                while int_i < len(data.children):
                                    if int_i != 0:
                                        file.write(".")
                                    file.write(data.children[int_i].value)
                                    int_i = int_i + 1
                            else:
                                print("error-aggragate_execute 999")
                                exit()
                        elif data.data == "name":
                            d = data.children[0].value
                            if d in const_dict_global:
                                d = const_dict_global[d]
                            file.write(d)
                        else:
                            print("error-aggragate_execute 9991")
                            exit()
                        file.write(" = ")
                        data = right
                        if data.data == "name_field":
                            first = data.children[0].value
                            if first == hdr_name or first == meta_name:
                                int_i = 0
                                while int_i < len(data.children):
                                    if int_i != 0:
                                        file.write(".")
                                    file.write(data.children[int_i].value)
                                    int_i = int_i + 1
                            else:
                                print("error-aggragate_execute 9992")
                                exit()
                        elif data.data == "name":
                            d = data.children[0].value
                            if d in const_dict_global:
                                d = const_dict_global[d]
                            file.write(d)
                        else:
                            print("error-aggragate_execute 9993")
                            print(data.data)
                            exit()
                        file.write(";\n")
                    else:
                        print("error-aggragate_execute what ins",ins.data)
                        exit()
                #trans
                if parser_node_have[pn].select == "":
                    file.write("        transition ")
                    if parser_node_have[pn].next == {}:
                        file.write("accept")
                    else:
                        for stat in parser_node_have[pn].next:
                            file.write(stat)
                    file.write(";\n")
                else:
                    file.write("        transition select(")
                    select = parser_node_have[pn].select.children[0]
                    if select.data == "name_field":
                        first = select.children[0].value
                        if first == hdr_name:
                            int_i = 0
                            while int_i < len(select.children):
                                if int_i != 0:
                                    file.write(".")
                                file.write(select.children[int_i].value)
                                int_i = int_i + 1
                        elif first == "pkt":
                            second = select.children[1].value
                            if second == "in_port":
                                file.write("im.ingress_port")
                            else:
                                print("error-aggragate_execute 8888")
                        else:
                            int_i = 0
                            while int_i < len(select.children):
                                if int_i != 0:
                                    file.write(".")
                                file.write(select.children[int_i].value)
                                int_i = int_i + 1
                    elif select.data == "aheaddata":
                        file.write("pkt.lookahead<")
                        file.write(select.children[0].value)
                        file.write(">()")
                    else:
                        print("error-aggragate_execute select what",select.data)
                        exit()
                    file.write(") {\n")
                    if parser_node_have[pn].next == {}:
                        file.write("            default: accept;\n")
                    else:
                        for next in parser_node_have[pn].next:
                            file.write("            ")
                            if parser_node_have[pn].next[next] in const_dict_global:
                                cond = const_dict_global[parser_node_have[pn].next[next]]
                            else:
                                cond = parser_node_have[pn].next[next]
                            file.write(cond)
                            file.write(": ")
                            file.write(next)
                            file.write(";\n")
                    file.write("        }\n")
                file.write("    }\n")

    #根据用到的hdr生成header
    for node in relation_node_hdr_uses:
        with open(folder_path + "//" + node + "_header","w") as file:
            if relation_node_hdr_uses[node] != []:
                for hdr in relation_node_hdr_uses[node]:
                    file.write("header ")
                    hdr_t = struct[hdr_type][hdr]
                    file.write(hdr_t)
                    file.write(" {\n")
                    for f in header[hdr_t]:
                        file.write("    ")
                        file.write(header[hdr_t][f])
                        file.write(" ")
                        file.write(f)
                        file.write(";\n")
                    file.write("}\n")
    
    #生成struct
    for node in relation_node_hdr_uses:
        with open(folder_path + "//" + node + "_header","a") as file:
            file.write("\n")
            for s in struct:
                if s != hdr_type:
                    file.write("struct ")
                    file.write(s)
                    file.write(" {\n")
                    for f in struct[s]:
                        file.write("    ")
                        file.write(struct[s][f])
                        file.write(" ")
                        file.write(f)
                        file.write(";\n")
                    file.write("}\n")
                else:
                    file.write("struct ")
                    file.write(s)
                    file.write(" {\n")
                    for f in struct[s]:
                        if f in relation_node_hdr_uses[node]:
                            file.write("    ")
                            file.write(struct[s][f])
                            file.write(" ")
                            file.write(f)
                            file.write(";\n")
                    file.write("}\n")

    #生成deparser
    for node in relation_node_hdr_uses:
        with open(folder_path + "//" + node + "_deparser","a") as file:
            file.write("    apply{ \n")
            for hdr in deparser:
                if hdr in relation_node_hdr_uses[node]:
                    file.write("        pkt.emit(")
                    file.write(hdr_name)
                    file.write(".")
                    file.write(hdr)
                    file.write(");\n")
            file.write("    } \n")

    return hdr_type_return



#提取解析树
def aggregate_collect_parser(tree:Tree,hdr_type:str,hdr_name:str,struct:dict):
    nodet = []
    nodes = {}
    for t in tree.children:
        if t.data == "nodes":
            nodet = t
    for n in nodet.children:
        node = data_structure.LYNETTE_PARSER_NODE()
        node_name = n.children[0].children[0].value
        node.name = node_name
        #找当前节点对应的header，有可能没有
        for exact in n.children:
            if exact.data == "exact":
                tem = exact.children[0].children[0].value
                if tem != hdr_name:
                    print("error-aggregate_collect_parser 74514")
                    exit()
                tem = exact.children[0].children[1].value
                if tem not in struct[hdr_type]:
                    print("error-aggregate_collect_parser 74515",tem)
                    exit()
                node.exact = tem
        #找当前节点的后续节点，可能没有
        for tras in n.children:
            if tras.data == "trans":
                tras = tras.children[0]
                if tras.data == "transition":
                    tras = tras.children[0].children[0].value
                    node.next[tras] = 'default'
                elif tras.data == "transition_select":
                    for data in tras.children:
                        if data.data == "data":
                            node.select = data
                    for transition_entry in tras.children:
                        if transition_entry.data == "transition_entry":
                            next_node = transition_entry.children[1].children[0].value
                            cond = transition_entry.children[0].children[0]
                            if cond.data == "int":
                                cond = cond.children[0].value
                            else:
                                cond = cond.children[0].value
                                if cond != 'default':
                                    if cond not in const_dict_global:
                                        print("error-aggregate_collect_parser 777888")
                                        print(cond)
                                        exit()
                                    cond = const_dict_global[cond]
                            node.next[next_node] = cond
        #记录指令
        for ins in n.children:
            if ins.data == "ins":
                node.ins.append(ins)
        #把这个节点记录下来
        nodes[node_name] = node

    #找所有节点的后置协议,暂时认为树是无环的
    if "start" in nodes: 
        for node in nodes:
            if nodes[node].exact != "":
                nodes[node].protocol.append(nodes[node].exact)
        if_change = 1
        while if_change == 1:
            if_change = 0
            for node in nodes:
                node = nodes[node]
                for next_node in node.next:
                    if next_node != "accept":
                        for protocol in nodes[next_node].protocol:
                            if protocol not in node.protocol:
                                if_change = 1
                                node.protocol.append(protocol)
    else:
        print("error-aggregate_collect_parser no start")
        exit()

    #找所有节点的前驱节点
    for node in nodes:
        for next_node in nodes[node].next:
            if next_node != "accept":
                nodes[next_node].rely.append(node)

    return nodes

#提取输出二元组，看看叫什么以及类型是什么
def aggregate_collect_sys_data(tree:Tree):
    hdr_name = ''
    hdr_type = ''
    meta_name = ''
    meta_type = ''
    for par in tree.children:
        if par.data == "par_hdr":
            hdr_type = par.children[0].children[0].value
            hdr_name = par.children[1].children[0].value
        if par.data == "par_gmeta":
            meta_type = par.children[0].children[0].value
            meta_name = par.children[1].children[0].value
    return hdr_type, hdr_name, meta_type, meta_name

#提取deparser,deparser的name损失掉了，至少3.22我没头绪怎么给它用起来
def aggregate_collect_deparser(tree:Tree,hdr_type:str,hdr_name:str,struct:dict):
    deparser_ans = []
    for deparser in tree.children:
        if deparser.data == "deparser":
            for d_i in deparser.children:
                if d_i.data == 'deparser_hdr':
                    d_i = d_i.children[0]
                    if len(d_i.children) > 2:
                        print("error-aggregate_collect_deparser 74514")
                        exit()
                    hdr = d_i.children[0].value
                    protocol = d_i.children[1].value
                    if hdr != hdr_name:
                        print("error-aggregate_collect_deparser 74516")
                        exit()
                    if protocol not in struct[hdr_type]:
                        print("error-aggregate_collect_deparser 74517")
                        exit()
                    deparser_ans.append(protocol)
    return deparser_ans

#解析parser，把树返回回来
def aggregate_parse_parser(aggregate_parameter):
    parser = Lark(grammar_parser)
    with open(aggregate_parameter["input_path"] + '//include//parser.pne','r') as file:
        code = file.read()
        tree = parser.parse(code)
        return tree

#针对header和struct做组件提取,环境需要高于3.6，因为只有3.6以后字典是有序的
def aggregate_collect_header(tree:Tree):
    #先提取一下header
    header_ts = {}
    global type_dict_global
    for header in tree.children:
        if header.data == "header":
            header_t_name = ''
            header_t = {}
            for h_def in header.children:
                if h_def.data == "header_name":
                    header_t_name = h_def.children[0].value
                else:
                    name_t = h_def.children[1].value
                    type_t = h_def.children[0].value
                    if type_t[:4] != "bit<":
                        if type_t in type_dict_global:
                            type_t = type_dict_global[type_t]
                        else:
                            print("error-aggregate_collect_header what type",type_t)
                            exit()
                    header_t[name_t] = type_t
            header_ts[header_t_name] = header_t

    #然后提取一下struct,我觉得struct套struct是个很弱智的行为
    struct_ts = {}
    for struct in tree.children:
        if struct.data == "struct":
            struct_t_name = ''
            struct_t = {}
            for s_def in struct.children:
                if s_def.data == "struct_name":
                    struct_t_name = s_def.children[0].value
                else:
                    name_t = s_def.children[1].value
                    type_t = s_def.children[0].value
                    if type_t[:4] != "bit<":
                        if type_t in header_ts:
                            pass
                        elif type_t in type_dict_global:
                            type_t = type_dict_global[type_t]
                        elif type_t in struct_ts:
                            #我不想支持这个东西
                            pass
                        else:
                            print("error-aggregate_collect_header what type")
                            print(type_t)
                            exit()
                    struct_t[name_t] = type_t
            struct_ts[struct_t_name] = struct_t
    
    #返回提取到的header和struct
    return header_ts,struct_ts

#解析header，把树返回出来
def aggregate_parse_header(aggregate_parameter):
    parser = Lark(grammar_header)
    with open(aggregate_parameter["input_path"] + '//include//header.pne','r') as file:
        code = file.read()
        tree = parser.parse(code)
        return tree

#这是构建define列表
#我其实没想到这里也要用到这个东西，所以其实预编译确实应该扔出去做
def construct_type_dict_global(aggregate_parameter):
    global type_dict_global,const_dict_global
    type_dict_global = {}
    parser = Lark(grammar_define)
    with open(aggregate_parameter["input_path"] + '//include//define.pne','r') as file:
        code = file.read()
        tree = parser.parse(code)
        for define_t in tree.children:
            if define_t.data == "type_define":
                type_dict_global[define_t.children[1].value] = define_t.children[0].value
            elif define_t.data == "const_define":
                name = define_t.children[1]
                value = define_t.children[2]
                const_dict_global[name.children[0].children[0].value] = value.children[0].children[0].value
            else:
                print("666565",define_t.data)
                exit()
            type_dict_global['bool'] = 'bit<1>'
    return type_dict_global