from lark import Lark, Tree, Token
import os,json
from lynette.lynette_lib import data_structure
from lynette.lynette_lib.grammar.grammar_define import grammar_define

class Generator():
    def __init__(self, **args):
        self.component_dir = args["sys_path"] + '//component//'

        self.type_dict = {}
        self.entry_v1mod = 'no'
        self.tables = {}
        self.const_dict = {}
        self.var_dict = {}
        self.reg_dict = {}
        self.frag_relation_dict = {}
        self.table_name = {}
        self.action_name = {}
        self.sys_data_dict_global = {'_FALSE':"0",'_TRUE':"1", '_Next':'Next'}
        self.compare_type = {"compare_b":" > ","compare_be":" >= ","compare_e":" == ","compare_s":" < ","compare_se":" <= ","compare_ne":" != "}
        self.table_id = 0
        self.action_id = 0

    #这个东西是用来第一次进app或者进module的时候，把里面的变量生成一遍,并记录对应关系
    #生成的时候会覆盖掉原来已有的映射
    #注意module是上下文切换，所以不会集成之前的全部var
    #但是在实际聚合的时候，其实是个树形聚合
    #参数：要生成的变量列表，要用来记录的表，前缀
    def generate_var(self, var_to_generate:dict, var_list:dict, prefix:str):
        #把数据类型洗一遍
        for var_name_i in var_to_generate:
            if var_to_generate[var_name_i] in self.type_dict:
                var_to_generate[var_name_i] = self.type_dict[var_to_generate[var_name_i]]
        #开始生成
        #看看这是不是个新的命名域，有可能不是新的
        if prefix not in self.var_dict:
            self.var_dict[prefix] = {}
        else:
            return
        with open(self.component_dir + "//" + prefix + '_var.pne','a') as file:
            for var_name_i in var_to_generate:
                var_name = prefix + "_" + var_name_i
                file.write(var_to_generate[var_name_i])
                file.write(" ")
                file.write(var_name)
                file.write(";\n")
                #要记录一下程序里面的名字和生成出来的名字的对应关系
                var_list[var_name_i] = var_name

    #生成赋值语句。这个情况可以是赋值也可以是table，还可以是寄存器。它要返回是什么情况。
    def generate_ins_assign(self, 
                            ins:data_structure.LYNETTE_INS,
                            var_list_o:dict,#当前可用变量列表
                            prefix:str,#当前所需前缀
                            level_o:int,#当前缩进等级
                            tuple_o:dict,#当前可用元组
                            mapl_o:dict,#当前可用map
                            setl_o:dict,#当前可用set
                            reg_o:dict,#当前可用reg
                            file_write_o = '//component//trash.pne', #往啥片段放
                            if_generate = "yes", #是否实际生成
                            available_key = [], #用于key判断，判断if和switch在table取值的时候key是不是合法
                            if_action = "no" #是完整的table生成还是作为action的一部分生成
                            ):
        if if_action == "yes":
            file_write = self.component_dir + file_write_o + "_action.pne"
        else:
            file_write = self.component_dir + file_write_o + "_control.pne"
        if if_generate == "yes":
            with open(file_write,'a') as file:
                for i in range(level_o):
                    file.write("    ")
        assign_type = ''
        if ins.left[0].children[0].data == "array":
            #这个情况一定是给寄存器赋值
            print("generate-ins-assign error function 2")
            exit()
        elif ins.right1.children[0].data == "array":
            #这个情况一定是从寄存器取值或者是从table里面取值
            #看一下这个是不是map
            map_name = ins.right1.children[0].children[0].children[0].children[0].value
            if map_name in mapl_o:
                #所以这东西是个map
                if if_generate == "no":
                    #不生成，所以这是if和switch在检查
                    assign_type = 'table_assign_yes'
                    if ins.right1.children[0].children[1].data == "index_null":
                        print("error-generate-ins-assign map[_]")
                        exit()
                    else:
                        #检查用的key的数量
                        if len(ins.right1.children[0].children[1].children) > len(available_key):
                            assign_type = 'table_assign_no'
                        else:
                            #检查用的key能不能用，其实还应该检查一下table是不是对的
                            for data in ins.right1.children[0].children[1].children:
                                data_name,data_type = self.generate_data(data.children[0],var_list_o,if_generate="no")
                                if data_name not in available_key:
                                    assign_type = 'table_assign_no'
                elif if_generate == "yes":
                    if if_action == "yes":
                        int_i = 0
                        for data_i in ins.left:
                            if int_i != 0:
                                for i in range(level_o):
                                    with open(file_write,"a") as file:
                                        file.write("    ")
                            data_name,_ = self.generate_data(data_i,var_list_o,file_write_o=file_write)
                            self.frag_relation_dict[file_write_o].output.append(data_name)
                            with open(file_write,"a") as file:
                                file.write(" = value_" + str(int_i) + ";\n")
                            int_i = int_i + 1
                    else:
                        #实际生成一个map的取值table
                        self.frag_relation_dict[file_write_o].table_num = self.frag_relation_dict[file_write_o].table_num + 1
                        #构造table名字和key列表
                        """table_name = prefix + "_" + map_name + "_" + str(self.table_id)
                        self.table_id = self.table_id + 1 """
                        table_name = prefix + "_" + map_name
                        if table_name not in self.table_name:
                            self.table_name[table_name] = 0
                        else:
                            self.table_name[table_name] = self.table_name[table_name] + 1
                            table_name = table_name + "_" + str(self.table_name[table_name])
                        keys = []
                        if ins.right1.children[0].children[1].data == "index_null":
                            print("error-generate-ins-assign map[_]")
                            exit()
                        else:
                            for key in ins.right1.children[0].children[1].children:
                                key = key.children[0]
                                key,key_type = self.generate_data(key,var_list_o,if_generate="no")
                                if key_type != "hdr" and key_type != "var" and key_type != "pkt":
                                    print("error-generate-ins-assign what key",key_type)
                                    exit()
                                keys.append(key)

                        #key列表应该是每个frag的input
                        for key in keys:
                            self.frag_relation_dict[file_write_o].input.append(key)
                        
                        #生成一下table名字和key列表
                        file_write_table  = file_write_o + "_table.pne"
                        with open(self.component_dir + file_write_table,"a") as file:
                            file.write("table " + table_name + "{\n")
                        with open(self.component_dir + file_write_table,'a') as file:
                            file.write("    key = {\n")
                        for key in keys:
                            with open(self.component_dir + file_write_table,'a') as file:
                                file.write("        ")
                                file.write(key)
                                file.write(" : exact;\n")
                                file.write("    }\n")

                        #构造一个目标动作
                        file_write_action = file_write_o + "_action.pne"
                        values = []
                        with open(self.component_dir + file_write_action,'a') as file:
                            file.write("action ")
                            """ action_name = table_name + "_action_" + str(self.action_id)
                            self.action_id = self.action_id + 1  """
                            action_name = table_name + "_action"
                            if action_name not in self.action_name:
                                self.action_name[action_name] = 0
                            else:
                                self.action_name[action_name] = self.action_name[action_name] + 1
                                action_name = action_name + "_" + str(self.action_name[action_name])
                            file.write(action_name)
                            file.write("(")
                            value_i = 0
                            for value_type in mapl_o[map_name].value:
                                if value_i != 0:
                                    file.write(", ")
                                value_type = value_type.value
                                if value_type in self.type_dict:
                                    value_type = self.type_dict[value_type]
                                file.write(value_type+" ")
                                value_name = "value_" + str(value_i)
                                value_i = value_i + 1
                                values.append(value_name)
                                file.write(value_name)
                            file.write(")\n")
                            file.write("{\n")
                            value_i = 0
                            #所有被赋值的left应该是frag的output
                            for left in ins.left:
                                left,_ = self.generate_data(left,var_list_o,if_generate="no")
                                self.frag_relation_dict[file_write_o].output.append(left)
                                file.write("    " + left)
                                file.write(" = value_" + str(value_i) + ";\n")
                                value_i = value_i + 1
                            file.write("}\n")

                        #关联table和action
                        with open(self.component_dir + file_write_table,'a') as file:
                            file.write("    actions = {\n")
                            file.write("        " + action_name + ";\n")
                            file.write("    }\n")
                            file.write("}\n")

                        #构造entry
                        file_write_entry = file_write_o + "_entry.pne"
                        with open(self.component_dir + file_write_entry,'a') as file:
                            entry = mapl_o[map_name].entry
                            if len(entry) != 0:
                                if len(keys) + len(values) != len(entry[0]):
                                    print("error-generate_if_single_table key value entry")
                                    print(keys)
                                    print(values)
                                    print(entry)
                                    exit()
                                for e in entry:
                                    ae = {}
                                    ae['table'] = table_name
                                    matchs = {}
                                    k_i = 0
                                    while k_i < len(keys):
                                        matchs[keys[k_i]] = [entry[e][k_i]]
                                        k_i = k_i + 1
                                    ae['match'] = matchs
                                    ae['action_name'] = action_name
                                    pa = {}
                                    zero = k_i
                                    while k_i < len(entry[e]):
                                        pa["value_" + str(k_i - zero)] = [entry[e][k_i]]
                                        k_i = k_i + 1
                                    ae['action_params'] = pa
                                    json.dump(ae,file)
                                    file.write("\n")


                        #在control中调用
                        file_write_control = file_write_o + "_control.pne"
                        with open(self.component_dir + file_write_control,'a') as file:
                            file.write(table_name + ".apply();\n")
                else:
                    print("error-generate-ins-assign what generate?")
                    exit()
            else:
                #进else意味着应该是个寄存器
                print("generate-ins-assign error function 3")
                exit()
        else:
            #所以现在只会是简单赋值了
            assign_type = 'simple_assign'
            if if_generate == "yes":
                #先生成一下左边
                data_name,data_type = self.generate_data(ins.left[0],var_list_o,file_write_o=file_write)
                if data_type == "var" or data_type == "hdr" or data_type == "meta":
                    self.frag_relation_dict[file_write_o].output.append(data_name)
                #然后是中间这个等于号
                with open(file_write,"a") as file:
                    file.write(" = ")
                #然后是右边
                data_name,data_type = self.generate_data(ins.right1,var_list_o,file_write_o=file_write)
                if data_type == "var" or data_type == "hdr" or data_type == "meta":
                    self.frag_relation_dict[file_write_o].input.append(data_name)
                #然后换行
                with open(file_write,"a") as file:
                    file.write(";\n")
        return assign_type
    
    #生成data，输入一个data为根的树，返回生成出来的这个str串，顺便写到文件里面去
    def generate_data(self, data_o:Tree, 
                    var_list_o:dict,
                    file_write_o = 'need to be full path', #往啥片段放
                    if_generate = 'yes' #是否实际生成，如果为no则只是转换成字符串
                    ):
        data = data_o.children[0]
        data_name = ''
        data_type = ''
        if data.data == "name":
            data_name = data.children[0].value
            if data_name not in var_list_o:
                print("error-generate_data no find this data")
                print(data_name)
                exit()
            else:
                data_name = var_list_o[data_name]
                data_type = "var"
        elif data.data == "name_field":
            data_len = len(data.children)
            data_name = data.children[0].value
            for i in range(data_len-1):
                data_name = data_name + "." + data.children[i+1].value
            if data.children[0].value == "hdr":
                data_type = "hdr"
            elif data.children[0].value == "pkt":
                if data_len != 2:
                    print("error-generate_data pkt small than 2")
                    exit()
                data_type = "pkt"
                data_name = "LynettePKT"
                if data.children[1].value == 'out_port':
                    data_name = data_name + ".LynetteOutPort"
                elif data.children[1].value == 'in_port':
                    data_name = data_name + ".LynetteInPort"
                else:
                    print("error-generate_data pkt what")
                    exit()
            elif data.children[0].value == "gmeta":
                if data_len != 2:
                    print("error-generate_data pkt small than 2")
                    exit()
                data_type = "gmeta"
                data_name = "gmeta."
                data_name = data_name + data.children[1].value
            else:
                print("generate_data what type? error function 2")
                print(data.children[0].value)
                exit()
        elif data.data == "sys_data":
            data_name = data.children[0].value
            if data_name in self.sys_data_dict_global:
                data_name = self.sys_data_dict_global[data_name]
                data_type = "sys_data"
            else:
                print("error-generate_data what sys data")
                exit()
        elif data.data == "int":
            data_type = "int"
            data_name = str(data.children[0].value)
        elif data.data == "ip_data":
            ip = data.children[0].value
            ip = ip.split(".")
            data_name = (int(ip[0])<<24) + (int(ip[1])<<16) + (int(ip[2])<<8) + int(ip[3])
            data_name = str(data_name)
            data_type = "ip_data"
        else:
            print("generate_data what type? error function 1")
            print(data.data)
            exit()
        if if_generate == "yes":
            with open(file_write_o,"a") as file:
                file.write(data_name)
        return data_name,data_type

    #检查if单表的可能性，返回yes/no
    def generate_if_can_single_table(self, ins:data_structure.LYNETTE_INS,
                                modules:dict,#当前可调起module
                                var_list_o:dict,#当前可用变量列表
                                prefix:str,#当前所需前缀
                                level_o:int,#当前缩进等级
                                tuple_o:dict,#当前可用元组
                                mapl_o:dict,#当前可用map
                                setl_o:dict,#当前可用set
                                func_o:dict,#当前可用func
                                reg_o:dict,#当前可用reg
                                file_write_o = 'app' #往啥片段放
                                ):
        return_answer = "yes"

        #检查是不是整个if都是check条件
        ins_i = ins
        if ins_i.condition[0].type != "check":
            return_answer = "no"
        while ins_i.else_ins_t == 1:
            ins_i = ins_i.else_ins
            if ins_i.condition[0].type != "check":
                return_answer = "no"

        #检查是不是整个if的check条件的key是否被首项包含
        ins_i = ins
        key_list = []
        for key in ins_i.condition[0].left:
            data_name,data_type = self.generate_data(key,var_list_o,if_generate="no")
            if data_type == "var" or data_type == "hdr" or data_type == "gmeta" or data_type == "pkt":
                key_list.append(data_name)
            else:
                print(data_type)
                return_answer = "no"
        while ins_i.else_ins_t == 1:
            ins_i = ins_i.else_ins
            for key in ins_i.condition[0].left:
                data_name,data_type = self.generate_data(key,var_list_o,if_generate="no")
                if data_type == "var" or data_type == "hdr" or data_type == "gmeta" or data_type == "pkt":
                    if data_name not in key_list:
                        return_answer = "no"
                else:
                    return_answer = "no"
            if len(ins_i.condition[0].left) != len(key_list):
                return_answer = "no"

        #检查是不是整个if的动作都是简单动作，这个东西可能有判断上的问题
        ins_i = ins
        for ins_ac in ins_i.condition_block[0].ins:
            if ins_ac.type == "ins_assign":
                assign_type = self.generate_ins_assign(ins_ac,var_list_o,prefix,level_o,tuple_o,mapl_o,setl_o,reg_o,if_generate="no",available_key=key_list)
                if assign_type != "simple_assign" and assign_type != "table_assign_yes":
                    return_answer = "no"
            elif ins_ac.type == "ins_cul":
                pass
            elif ins_ac.type == "primitive":
                pass
            else:
                #print(ins_ac.type,"5454545")
                #print(prefix)
                return_answer = "no"
        while ins_i.else_ins_t == 1:
            ins_i = ins_i.else_ins
            for ins_ac in ins_i.condition_block[0].ins:
                if ins_ac.type == "ins_assign":
                    assign_type = self.generate_ins_assign(ins_ac,var_list_o,prefix,level_o,tuple_o,mapl_o,setl_o,reg_o,if_generate="no",available_key=key_list)
                    if assign_type != "simple_assign" and assign_type != "table_assign_yes":
                        return_answer = "no"
                elif ins_ac.type == "ins_cul":
                    pass
                elif ins_ac.type == "primitive":
                    pass
                else:
                    print(ins_ac.type,"5454545")
                    return_answer = "no"
        if ins_i.default == 1:
            ins_i = ins_i.default_bolck
            for ins_ac in ins_i.ins:
                if ins_ac.type == "ins_assign":
                    assign_type = self.generate_ins_assign(ins_ac,var_list_o,prefix,level_o,tuple_o,mapl_o,setl_o,reg_o,if_generate="no",available_key=key_list)
                    if assign_type != "simple_assign":
                        return_answer = "no"
                elif ins_ac.type == "ins_cul":
                    pass
                elif ins_ac.type == "primitive":
                    pass
                else:
                    print(ins_ac.type,"5454545")
                    return_answer = "no"

        return return_answer

    #展开整个代码块的指令序列
    def generate_ins_all(self, 
                        all_ins:list,
                        modules:dict,#当前可调起module
                        var_list_o:dict,#当前可用变量列表
                        prefix:str,#当前所需前缀
                        level_o:int,#当前缩进等级
                        tuple_o:dict,#当前可用元组
                        mapl_o:dict,#当前可用map
                        setl_o:dict,#当前可用set
                        func_o:dict,#当前可用func
                        reg_o:dict,#当前可用reg
                        can_cut = 'yes',#这个代码块可以切割不
                        file_write_o = 'app', #往啥片段放
                        if_action = "no" #是不是在往action写
                        ):
        level = level_o
        tuple = tuple_o
        mapl = mapl_o
        setl = setl_o
        func = func_o
        reg = reg_o
        assert_num = 0
        fragment_num = 0
        for ins in all_ins:
            if can_cut == 'yes':
                file_write = prefix + "_" + str(fragment_num)
                self.frag_relation_dict[prefix] = fragment_num
                fragment_num = fragment_num + 1
                self.frag_relation_dict[file_write] = data_structure.LYNETTE_FRAG_RELATION()
                self.frag_relation_dict[file_write].name = file_write
                self.frag_relation_dict[file_write].varfile.append(prefix + "_var.pne")
                file_write_control = file_write + "_control.pne"
                file_write_reg     = file_write + "_reg.pne"
                file_write_action  = file_write + "_action.pne"
                file_write_table   = file_write + "_table.pne"
                file_write_tem     = file_write + "_tem.pne"
                file_write_entry   = file_write + "_entry.pne"
                with open(self.component_dir + file_write_control,"a") as file:
                    file.write("")
                with open(self.component_dir + file_write_reg,"a") as file:
                    file.write("")
                with open(self.component_dir + file_write_action,"a") as file:
                    file.write("")
                with open(self.component_dir + file_write_table,"a") as file:
                    file.write("")
                with open(self.component_dir + file_write_tem,"a") as file:
                    file.write("")
                with open(self.component_dir + file_write_entry,"a") as file:
                    file.write("")
            else:
                file_write = file_write_o
            ins : data_structure.LYNETTE_INS
            var_list = self.copy_dict_for_no_struct(var_list_o)
            if ins.type == "ins_assign":
                #赋值指令
                self.generate_ins_assign(ins,var_list,prefix,level,tuple,mapl,setl,reg,file_write_o=file_write,if_action=if_action)
            elif ins.type == "ins_call":
                #调用module了
                self.generate_module(ins,modules,prefix,var_list,level,file_write)
            elif ins.type == "if":
                #if指令，先尝试能不能单表，然后展开
                if_single_table = self.generate_if_can_single_table(ins,modules,var_list,prefix,level,tuple,mapl,setl,func,reg,file_write_o=file_write)
                if if_single_table == "yes":
                    #是单表，那么按照单表展开
                    self.generate_if_single_table(ins,modules,var_list,prefix,level,tuple,mapl,setl,func,reg,file_write_o=file_write)
                else:
                    #不是单表，按照大if展开
                    self.generate_if_big_if(ins,modules,var_list,prefix,level,tuple,mapl,setl,func,reg,file_write_o=file_write)
            elif ins.type == "ins_cul":
                #计算指令
                self.generate_ins_cul(ins,var_list,level,file_write,if_action=if_action)
            elif ins.type == "switch":
                #swich，先试试能不能单表展开
                if_single_table = self.generate_switch_can_single_table(ins,modules,var_list,prefix,level,tuple,mapl,setl,func,reg,file_write_o=file_write)
                if if_single_table == "yes":
                    #是单表，那么按照单表展开
                    self.generate_switch_single_table(ins,modules,var_list,prefix,level,tuple,mapl,setl,func,reg,file_write_o=file_write)
                else:
                    print("error here 7894")
                    exit()
            elif ins.type == "assert":
                self.generate_condition(ins.condition[0],modules,var_list,prefix,level,tuple,mapl,setl,func,reg,file_write_o=file_write_o)
                assert_num = assert_num + 1
                with open(self.component_dir+file_write_o+"_control.pne",'a') as file:
                    for i in range(level):
                        file.write("    ")
                    file.write("{\n")
                level = level + 1
            elif ins.type == "primitive":
                #展开源语
                self.generate_primitive(ins,var_list,level,file_write,if_action=if_action)
            else:
                print("?-generate.py-generate_ins what ins",ins.type)
                exit()
        while assert_num > 0:
            assert_num = assert_num - 1
            level = level - 1
            with open(self.component_dir+file_write_o+"_control.pne",'a') as file:
                for i in range(level):
                    file.write("    ")
                file.write("}\n")

    #展开源语
    def generate_primitive(self, 
                        ins:data_structure.LYNETTE_INS,
                        var_list_o:dict,#当前可用变量列表
                        level_o:int,#当前缩进等级
                        file_write_o = 'app', #往啥片段放
                        if_action = "no" #是不是在往action写
                        ):
        if if_action == "yes":
            file_write = self.component_dir + file_write_o + "_action.pne"
        else:
            file_write = self.component_dir + file_write_o + "_control.pne"
        
        with open(file_write,'a') as file:
            for i in range(level_o):
                file.write("    ")

        if ins.primitive_type == "drop":
            with open(file_write,'a') as file:
                file.write("LynetteDrop;\n")
        elif ins.primitive_type == "headercompress":
            with open(file_write,'a') as file:
                file.write("LynetteHeaderCompress(")
            self.generate_data(ins.primitive_par[0],var_list_o,file_write)
            with open(file_write,'a') as file:
                file.write(");\n")
        elif ins.primitive_type == "nop":
            with open(file_write,'a') as file:
                file.write(";\n")
        else:
            print("error-generate_primitive what primitive",ins.primitive_type)
            exit()
        
    #把switch按照单表展开
    def generate_switch_single_table(self, 
                                    ins:data_structure.LYNETTE_INS,
                                    modules:dict,#当前可调起module
                                    var_list_o:dict,#当前可用变量列表
                                    prefix:str,#当前所需前缀
                                    level_o:int,#当前缩进等级
                                    tuple_o:dict,#当前可用元组
                                    mapl_o:dict,#当前可用map
                                    setl_o:dict,#当前可用set
                                    func_o:dict,#当前可用func
                                    reg_o:dict,#当前可用reg
                                    file_write_o = 'app' #往啥片段放
                                ):
        file_write         = file_write_o
        file_write_control = file_write_o + "_control.pne"
        file_write_reg     = file_write_o + "_reg.pne"
        file_write_table   = file_write_o + "_table.pne"
        file_write_action  = file_write_o + "_action.pne"
        self.frag_relation_dict[file_write_o].table_num = self.frag_relation_dict[file_write_o].table_num + 1

        #生成table名字和key信息
        """ table_name = prefix + "_" + ins.case[0].children[0].children[0].value + "_" + str(self.table_id)
        self.table_id = self.table_id + 1 """
        table_name = prefix + "_" + ins.case[0].children[0].children[0].value
        if table_name not in self.table_name:
            self.table_name[table_name] = 0
        else:
            self.table_name[table_name] = self.table_name[table_name] + 1
            table_name = table_name + "_" + str(self.table_name[table_name])
        keys = []
        for key in ins.key:
            key_name,_ = self.generate_data(key,var_list_o,if_generate="no")
            keys.append(key_name)
            self.frag_relation_dict[file_write_o].input.append(key_name)
        with open(self.component_dir + file_write_table,"a") as file:
            file.write("table " + table_name + "{\n")
            file.write("    key = {\n")
            for key in keys:
                file.write("        " + key + " : exact;\n")
            file.write("    }\n")

        #开始逐个生成action
        with open(self.component_dir + file_write_table,"a") as file:
            file.write("    actions = {\n")
        default_action = ''
        int_ic = 0
        while int_ic < len(ins.case):
            #如果涉及下表项的话，说不定可以从action_name考虑考虑
            """ action_name = table_name + "_action_" + str(self.action_id)
            self.action_id = self.action_id + 1 """
            action_name = table_name + "_action"
            if action_name not in self.action_name:
                self.action_name[action_name] = 0
            else:
                self.action_name[action_name] = self.action_name[action_name] + 1
                action_name = action_name + "_" + str(self.action_name[action_name])
            action_par = []
            condition_case = ins.case[int_ic].children[0].children[0].value
            with open(self.component_dir + file_write_table,"a") as file:
                file.write("        " + action_name + ";\n")
            
            if condition_case != "default":
                #如果不是默认，则正常构造action的par
                if condition_case in mapl_o:
                    for par_i in mapl_o[condition_case].value:
                        par_i = par_i.value
                        if par_i in self.type_dict:
                            par_i = self.type_dict[par_i]
                        action_par.append(par_i)
            else:
                #如果是默认，则构造default action，其实只是记录一下谁是default
                default_action = action_name
            #向action里边构造内容
            #先打变量
            with open(self.component_dir + file_write_action,"a") as file:
                file.write("action " + action_name + "(")
                par_num = 0
                for par_i in action_par:
                    if par_num != 0:
                        file.write(", ")
                    file.write(par_i + " value_" + str(par_num))
                    par_num = par_num + 1
                file.write(")\n{\n")
            #然后打指令
            if ins.func[int_ic].call_name in func_o:
                self.generate_ins_all(func_o[ins.func[int_ic].call_name].ins,modules,var_list_o,prefix,1,tuple_o,mapl_o,setl_o,func_o,reg_o,can_cut="no",file_write_o=file_write,if_action="yes")
            elif ins.func[int_ic].call_name == "nop":
                with open(self.component_dir + file_write_action,"a") as file:
                    file.write("    ;\n")
            elif ins.func[int_ic].call_name == "drop":
                with open(self.component_dir + file_write_action,"a") as file:
                    file.write("    mark_to_drop(im);\n")
            else:
                print("error-generate_switch_single_table what call",ins.func[int_ic].call_name)
                exit()
            with open(self.component_dir + file_write_action,"a") as file:
                file.write("}\n")
        
            int_ic = int_ic + 1

            values = action_par
            file_write_entry = file_write_o + "_entry.pne"
            if condition_case != "default" and condition_case in mapl_o:
                with open(self.component_dir + file_write_entry,'a') as file:
                    entry = mapl_o[condition_case].entry
                    if len(entry) != 0:
                        if len(keys) + len(values) != len(entry[0]):
                            print("error-generate_if_single_table key value entry")
                            print(keys)
                            print(values)
                            print(entry)
                            exit()
                        for e in entry:
                            ae = {}
                            ae['table'] = table_name
                            matchs = {}
                            k_i = 0
                            while k_i < len(keys):
                                matchs[keys[k_i]] = [entry[e][k_i]]
                                k_i = k_i + 1
                            ae['match'] = matchs
                            ae['action_name'] = action_name
                            pa = {}
                            zero = k_i
                            while k_i < len(entry[e]):
                                pa["value_" + str(k_i - zero)] = [entry[e][k_i]]
                                k_i = k_i + 1
                            ae['action_params'] = pa
                            json.dump(ae,file)
                            file.write("\n")

        
        with open(self.component_dir + file_write_table,"a") as file:
            file.write("    }\n")
            if default_action != '':
                file.write("    default_action = " + default_action + "();\n")
            file.write("}\n")

        #在control中实际调用一下
        with open(self.component_dir + file_write_control,"a") as file:
            file.write(table_name)
            file.write(".apply();\n")

    #检查switch单表的可能性，返回yes/no
    def generate_switch_can_single_table(self, ins:data_structure.LYNETTE_INS,
                                        modules:dict,#当前可调起module
                                        var_list_o:dict,#当前可用变量列表
                                        prefix:str,#当前所需前缀
                                        level_o:int,#当前缩进等级
                                        tuple_o:dict,#当前可用元组
                                        mapl_o:dict,#当前可用map
                                        setl_o:dict,#当前可用set
                                        func_o:dict,#当前可用func
                                        reg_o:dict,#当前可用reg
                                        file_write_o = 'app' #往啥片段放
                                        ):
        return_answer = "yes"

        key_list = []
        for key in ins.key:
            key,_ = self.generate_data(key,var_list_o,if_generate="no")
            key_list.append(key)

        #检查一下匹配key的数量是否全部符合，顺便检查一下这些table什么的是不是全部合法,其实这一步应该是语法检查的事情
        key_num = len(ins.key)
        for case in ins.case:
            case = case.children[0].children[0].value
            if case == "default":
                continue
            if case in mapl_o:
                case = mapl_o[case]
            elif case in setl_o:
                case = setl_o[case]
            else:
                print("error-generate_switch_can_single_table what case")
                exit()
            if key_num != len(case.key):
                print("error-generate_switch_can_single_table what key num")
                exit()
        
        #检查是不是整个switch的动作都是简单动作，这个东西可能有判断上的问题
        int_i = 0
        for func in ins.func:
            if func.call_name == "nop" or func.call_name == "drop":
                pass
            elif func.call_name not in func_o:
                print("error-generate_switch_can_single_table what func")
                exit()
            else:
                func_ins = func_o[func.call_name].ins
                for ins_i in func_ins:
                    if ins_i.type == "ins_assign":
                        #其实我一直觉得func的这个判断不是太对
                        assign_type = self.generate_ins_assign(ins_i,var_list_o,prefix,level_o,tuple_o,mapl_o,setl_o,reg_o,if_generate="no",available_key=key_list)
                        if assign_type != "simple_assign" and assign_type != "table_assign_yes":
                            return_answer = "no"
                    elif ins_i.type == "primitive":
                        pass
                    elif ins_i.type == "ins_cul":
                        pass
                    else:
                        print(ins_i.type,"323232323")
                        return_answer = "no"
            int_i = int_i + 1

        return return_answer

    #展开condition，会把if写出来，但是不会把双括号写出来
    def generate_condition(self, 
                            condition:data_structure.LYNETTE_CONDITION,
                            modules:dict,#当前可调起module
                            var_list_o:dict,#当前可用变量列表
                            prefix:str,#当前所需前缀
                            level_o:int,#当前缩进等级
                            tuple_o:dict,#当前可用元组
                            mapl_o:dict,#当前可用map
                            setl_o:dict,#当前可用set
                            func_o:dict,#当前可用func
                            reg_o:dict,#当前可用reg
                            file_write_o = 'app' #往啥片段放
                            ):


        #check型的condition
        if condition.type == "check":
            #table_data绝对有用，但是在版本迭代中失去了引用，应该是某个优化想法//3.22推测是生成entry
            #3.23发现确实是entry
            if condition.right[0].children[0].children[0].value in mapl_o:
                table_data = mapl_o[condition.right[0].children[0].children[0].value]
            elif condition.right[0].children[0].children[0].value in setl_o:
                table_data = setl_o[condition.right[0].children[0].children[0].value]
            else:
                print("error-generate_condition check what")
                exit()
            file_write_control = file_write_o + "_control.pne"
            file_write_table   = file_write_o + "_table.pne"
            file_write_action  = file_write_o + "_action.pne"
            file_write_tem     = file_write_o + "_tem.pne"
            file_write_entry   = file_write_o + "_entry.pne"

            #先构造一下table的名字
            """ table_name = prefix + "_" + condition.right[0].children[0].children[0].value + "_hit_table_" + str(self.table_id)
            self.table_id = self.table_id + 1 """
            table_name = prefix + "_" + condition.right[0].children[0].children[0].value
            if table_name not in self.table_name:
                self.table_name[table_name] = 0
            else:
                self.table_name[table_name] = self.table_name[table_name] + 1
                table_name = table_name + "_" + str(self.table_name[table_name])
            
            self.frag_relation_dict[file_write_o].table_num = self.frag_relation_dict[file_write_o].table_num + 1

            #构造一下目标变量，有hit到就是1，没有是0.这里采用变量方案而不是meta方案
            tem_name = table_name + "_data"
            with open(self.component_dir + file_write_tem,'a') as file:
                file.write("bit<1> " + tem_name + ";\n")

            #然后构造两个目标动作
            action_names = []
            with open(self.component_dir + file_write_action,'a') as file:
                file.write("action ")
                """ action_name = table_name + "_action_" + str(self.action_id)
                self.action_id = self.action_id + 1  """
                action_name = table_name + "_action"
                if action_name not in self.action_name:
                    self.action_name[action_name] = 0
                else:
                    self.action_name[action_name] = self.action_name[action_name] + 1
                    action_name = action_name + "_" + str(self.action_name[action_name])
                file.write(action_name)
                file.write("()\n")
                file.write("{\n")
                file.write("    ")
                file.write(tem_name)
                file.write(" = 1;\n}\n")
                action_names.append(action_name)
            with open(self.component_dir + file_write_action,'a') as file:
                file.write("action ")
                """ action_name = table_name + "_action_" + str(self.action_id)
                self.action_id = self.action_id + 1  """
                action_name = table_name + "_action"
                if action_name not in self.action_name:
                    self.action_name[action_name] = 0
                else:
                    self.action_name[action_name] = self.action_name[action_name] + 1
                    action_name = action_name + "_" + str(self.action_name[action_name])
                file.write(action_name)
                file.write("()\n")
                file.write("{\n")
                file.write("    ")
                file.write(tem_name)
                file.write(" = 0;\n}\n")
                action_names.append(action_name)

            #然后构造表
            with open(self.component_dir + file_write_table,'a') as file:
                file.write("table ")
                file.write(table_name) 
                file.write("{\n")
            #构造表的key
            with open(self.component_dir + file_write_table,'a') as file:
                file.write("    key = {\n")
            keys = []
            for key in condition.left:
                with open(self.component_dir + file_write_table,'a') as file:
                    file.write("        ")
                data_name,_ = self.generate_data(key,var_list_o, self.component_dir + file_write_table)
                self.frag_relation_dict[file_write_o].input.append(data_name)
                keys.append(data_name)
                with open(self.component_dir + file_write_table,'a') as file:
                    file.write(" : exact;\n")
            with open(self.component_dir + file_write_table,'a') as file:
                file.write("    }\n")

            #构造表的action
            with open(self.component_dir + file_write_table,'a') as file:
                file.write("    actions = {\n")
            for action_name in action_names:
                with open(self.component_dir + file_write_table,'a') as file:
                    file.write("        " + action_name + ";\n")
            with open(self.component_dir + file_write_table,'a') as file:
                file.write("    }\n")
            #构造表的default
            with open(self.component_dir + file_write_table,'a') as file:
                file.write("    default_action = " + action_names[-1] + "();\n}\n")
            
            #构造entry，hit到了为1
            with open(self.component_dir + file_write_entry,'a') as file:
                entry = table_data.entry
                if len(entry) != 0:
                    for e in entry:
                        ae = {}
                        ae['table'] = table_name
                        matchs = {}
                        k_i = 0
                        while k_i < len(keys):
                            matchs[keys[k_i]] = [entry[e][k_i]]
                            k_i = k_i + 1
                        ae['match'] = matchs
                        ae['action_name'] = action_name
                        pa = {}
                        ae['action_params'] = pa
                        json.dump(ae,file)
                        file.write("\n")

            #在control中调用这个table
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write(table_name + ".apply();\n")

            #写入if
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("if(" + tem_name + " == 1)\n")
        elif condition.type in self.compare_type:
            #比较型的condition
            file_write_control = file_write_o + "_control.pne"
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("if(")
            data_name,data_type = self.generate_data(condition.left[0],var_list_o,file_write_o=self.component_dir+file_write_control)
            if data_type == "hdr" or data_type == "pkt" or data_type == "var":
                self.frag_relation_dict[file_write_o].input.append(data_name)
            with open(self.component_dir + file_write_control,'a') as file:
                file.write(self.compare_type[condition.type])
            data_name,data_type = self.generate_data(condition.right[0],var_list_o,file_write_o=self.component_dir+file_write_control)
            if data_type == "hdr" or data_type == "pkt" or data_type == "var":
                self.frag_relation_dict[file_write_o].input.append(data_name)
            with open(self.component_dir + file_write_control,'a') as file:
                file.write(")\n")
        elif condition.type == "isvalid":
            #isvalid型的condition
            file_write_control = file_write_o + "_control.pne"
            with open(self.component_dir + file_write_control,'a') as file:
                file.write("if(")
            #这里需要一个语义检查来保障
            hdr  = condition.left[0].children[0].children[0].value
            hdrr = condition.left[0].children[0].children[1].value
            self.frag_relation_dict[file_write_o].input.append(hdr+"."+hdrr)
            with open(self.component_dir + file_write_control,'a') as file:
                file.write(hdr+"."+hdrr)
            with open(self.component_dir + file_write_control,'a') as file:
                file.write(".isValid())\n")
        else:
            print("generate_condition error function 1")
            print(condition.type)
            exit()

    #把if按照大if展开
    def generate_if_big_if(self, ins:data_structure.LYNETTE_INS,
                        modules:dict,#当前可调起module
                        var_list_o:dict,#当前可用变量列表
                        prefix:str,#当前所需前缀
                        level_o:int,#当前缩进等级
                        tuple_o:dict,#当前可用元组
                        mapl_o:dict,#当前可用map
                        setl_o:dict,#当前可用set
                        func_o:dict,#当前可用func
                        reg_o:dict,#当前可用reg
                        file_write_o = 'app' #往啥片段放
                        ):
        file_write_control = file_write_o + "_control.pne"
        condition = ins.condition[0]
        #展开条件
        self.generate_condition(condition,modules,var_list_o,prefix,level_o,tuple_o,mapl_o,setl_o,func_o,reg_o,file_write_o=file_write_o)
        #展开代码块
        with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("{\n")
        self.generate_ins_all(ins.condition_block[0].ins,modules,var_list_o,prefix,level_o + 1,tuple_o,mapl_o,setl_o,func_o,reg_o,can_cut="no",file_write_o=file_write_o)
        with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("}\n")

        #展开else if
        if ins.else_ins_t == 1:
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("else\n")
                for i in range(level_o):
                    file.write("    ")
                file.write("{\n")
            self.generate_if_big_if(ins.else_ins,modules,var_list_o,prefix,level_o + 1,tuple_o,mapl_o,setl_o,func_o,reg_o,file_write_o=file_write_o)
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("}\n")

        #展开else
        if ins.default == 1:
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("else\n")
                for i in range(level_o):
                    file.write("    ")
                file.write("{\n")
            self.generate_ins_all(ins.default_bolck.ins,modules,var_list_o,prefix,level_o + 1,tuple_o,mapl_o,setl_o,func_o,reg_o,can_cut="no",file_write_o=file_write_o)
            with open(self.component_dir + file_write_control,'a') as file:
                for i in range(level_o):
                    file.write("    ")
                file.write("}\n")

    #展开计算式
    def generate_ins_cul(self, ins:data_structure.LYNETTE_INS,
                        var_list_o:dict,#当前可用变量列表
                        level_o:int,#当前缩进等级
                        file_write_o = 'app', #往啥片段放
                        if_action = "no" #是不是在往action写
                        ):
        if if_action == "yes":
            file_write = self.component_dir + file_write_o + "_action.pne"
        else:
            file_write = self.component_dir + file_write_o + "_control.pne"
        
        with open(file_write,'a') as file:
            for i in range(level_o):
                file.write("    ")

        #先生成左值
        data_name,_ = self.generate_data(ins.left[0],var_list_o,file_write)
        self.frag_relation_dict[file_write_o].output.append(data_name)
        #然后是赋值
        with open(file_write,"a") as file:
            file.write(" = ")
        #然后右边
        data_name,data_type = self.generate_data(ins.right1,var_list_o,file_write)
        if data_type == "hdr" or data_type == "var":
            self.frag_relation_dict[file_write_o].input.append(data_name)
        with open(file_write,"a") as file:
            file.write(" " + ins.op + " ")
        data_name,data_type = self.generate_data(ins.right2,var_list_o,file_write)
        if data_type == "hdr" or data_type == "var":
            self.frag_relation_dict[file_write_o].input.append(data_name)
        #换行
        with open(file_write,"a") as file:
            file.write(";\n")

    #把if按照单表展开
    def generate_if_single_table(self, ins:data_structure.LYNETTE_INS,
                                modules:dict,#当前可调起module
                                var_list_o:dict,#当前可用变量列表
                                prefix:str,#当前所需前缀
                                level_o:int,#当前缩进等级
                                tuple_o:dict,#当前可用元组
                                mapl_o:dict,#当前可用map
                                setl_o:dict,#当前可用set
                                func_o:dict,#当前可用func
                                reg_o:dict,#当前可用reg
                                file_write_o = 'app' #往啥片段放
                                ):
        file_write         = file_write_o
        file_write_control = file_write_o + "_control.pne"
        file_write_reg     = file_write_o + "_reg.pne"
        file_write_table   = file_write_o + "_table.pne"
        file_write_action  = file_write_o + "_action.pne"
        self.frag_relation_dict[file_write_o].table_num = self.frag_relation_dict[file_write_o].table_num + 1

        #生成table名字和key信息
        first_condition = ins.condition[0]
        """ table_name = prefix + "_" + first_condition.right[0].children[0].children[0].value + "_" + str(self.table_id)
        self.table_id = self.table_id + 1 """
        table_name = prefix + "_" + first_condition.right[0].children[0].children[0].value
        if table_name not in self.table_name:
            self.table_name[table_name] = 0
        else:
            self.table_name[table_name] = self.table_name[table_name] + 1
            table_name = table_name + "_" + str(self.table_name[table_name])
        keys = []
        for key in first_condition.left:
            #这里key在生成的时候会有隐性bug，因为变量的链式提取，到了根部可能会是个常量
            key_name,_ = self.generate_data(key,var_list_o,if_generate="no")
            keys.append(key_name)
        with open(self.component_dir + file_write_table,"a") as file:
            file.write("table " + table_name + "{\n")
            file.write("    key = {\n")
            for key in keys:
                file.write("        " + key + " : exact;\n")
            file.write("    }\n")

        #key列表应该是每个frag的input
        for key in keys:
            self.frag_relation_dict[file_write_o].input.append(key)

        #开始逐个生成action
        with open(self.component_dir + file_write_table,"a") as file:
            file.write("    actions = {\n")
        action_till = 1
        ins_i = ins
        while action_till == 1:
            """ action_name = table_name + "_action_" + str(self.action_id)
            self.action_id = self.action_id + 1 """
            action_name = table_name + "_action"
            if action_name not in self.action_name:
                self.action_name[action_name] = 0
            else:
                self.action_name[action_name] = self.action_name[action_name] + 1
                action_name = action_name + "_" + str(self.action_name[action_name])
            with open(self.component_dir + file_write_table,"a") as file:
                file.write("        " + action_name + ";\n")
            #向action里边构造内容
            #先打变量
            with open(self.component_dir + file_write_action,"a") as file:
                file.write("action " + action_name + "(")
                #action的参数，直接取用条件里面这个map的参数，但是其实有可能是set
                map_name = ins_i.condition[0].right[0].children[0].children[0].value
                if map_name in mapl_o:
                    map_value = mapl_o[map_name].value
                    par_num = 0
                    for par in map_value:
                        par = par.value
                        if par in self.type_dict:
                            par = self.type_dict[par]
                        if par_num != 0:
                            file.write(", ")
                        file.write(par + " value_" + str(par_num))
                        par_num = par_num + 1
                else:
                    map_value = {}
                file.write(")\n{\n")
            #然后打指令
            self.generate_ins_all(ins_i.condition_block[0].ins,modules,var_list_o,prefix,1,tuple_o,mapl_o,setl_o,func_o,reg_o,can_cut="no",file_write_o=file_write,if_action="yes")
            with open(self.component_dir + file_write_action,"a") as file:
                file.write("}\n")

            #构造entry
            values = map_value
            file_write_entry = file_write_o + "_entry.pne"
            with open(self.component_dir + file_write_entry,'a') as file:
                if map_name in mapl_o:
                    entry = mapl_o[map_name].entry
                else:
                    entry = setl_o[map_name].entry
                if len(entry) != 0:
                    if len(keys) + len(values) != len(entry[0]):
                        print("error-generate_if_single_table key value entry")
                        print(keys)
                        print(values)
                        print(entry)
                        exit()
                    for e in entry:
                        ae = {}
                        ae['table'] = table_name
                        matchs = {}
                        k_i = 0
                        while k_i < len(keys):
                            matchs[keys[k_i]] = [entry[e][k_i]]
                            k_i = k_i + 1
                        ae['match'] = matchs
                        ae['action_name'] = action_name
                        pa = {}
                        zero = k_i
                        while k_i < len(entry[e]):
                            pa["value_" + str(k_i - zero)] = [entry[e][k_i]]
                            k_i = k_i + 1
                        ae['action_params'] = pa
                        json.dump(ae,file)
                        file.write("\n")


            #循环终止条件，其实这是写了个do while 5555555555555
            if ins_i.else_ins_t != 1:
                action_till = 0
            else:
                ins_i = ins_i.else_ins

        #这个是default action
        if ins_i.default == 1:
            """ action_name = table_name + "_action_" + str(self.action_id)
            self.action_id = self.action_id + 1 """
            action_name = table_name + "_action"
            if action_name not in self.action_name:
                self.action_name[action_name] = 0
            else:
                self.action_name[action_name] = self.action_name[action_name] + 1
                action_name = action_name + "_" + str(self.action_name[action_name])
            with open(self.component_dir + file_write_table,"a") as file:
                file.write("        " + action_name + ";\n")
            #向action里边构造内容
            #先打变量
            with open(self.component_dir + file_write_action,"a") as file:
                file.write("action " + action_name + "(")
                #default action不会有参数
                file.write(")\n{\n")
            #然后打指令
            self.generate_ins_all(ins_i.default_bolck.ins,modules,var_list_o,prefix,1,tuple_o,mapl_o,setl_o,func_o,reg_o,can_cut="no",file_write_o=file_write,if_action="yes")
            with open(self.component_dir + file_write_action,"a") as file:
                file.write("}\n")

        with open(self.component_dir + file_write_table,"a") as file:
            file.write("    }\n")
            if ins_i.default == 1:
                file.write("    default_action = " + action_name + "();\n")
            file.write("}\n")
        
        #在control调用table
        with open(self.component_dir + file_write_control,"a") as file:
            for i in range(level_o):
                file.write("    ")
            file.write(table_name + ".apply();\n")
            
    #展开module，输入是调用的ins
    def generate_module(self, ins:data_structure.LYNETTE_INS,
                        modules:dict,
                        prefix_o:str,
                        var_list_o:dict,#上层可用变量列表
                        level_o:int,#当前缩进等级
                        file_write_o = 'app' #往啥片段放
                        ):
        if ins.call_name not in modules:
            print("error-generate_module what module")
            print(ins.call_name,prefix_o)
            exit()
        else:
            module = modules[ins.call_name]
            module:data_structure.LYNETTE_MODULE
        self.frag_relation_dict[file_write_o].module[module.name] = 1
        if len(module.call_par) != len(module.call_par_type) or len(module.call_par) != len(module.call_type):
            print("error-generate_module error par")
            exit()
        if  len(module.call_par) != len(ins.call_par):
            print("error-generate_module error call")
            exit()
        prefix = prefix_o + "_" + ins.call_name
        #处理一下参数的问题
        par_len = len(module.call_par)
        var_list = {}
        for par_i in range(par_len):
            if module.call_type[par_i] == "out" or module.call_type[par_i] == "inout":
                #这意味着是引用调用
                if module.call_par[par_i] in module.var:
                    print("error-generate_module error par and var")
                    exit()
                data_name,_ = self.generate_data(ins.call_par[par_i],var_list_o,if_generate='no')
                var_list[module.call_par[par_i]] = data_name
            elif module.call_type[par_i] == "in":
                #传值调用
                data_name,_ = self.generate_data(ins.call_par[par_i],var_list_o,if_generate='no')

                #新建一个变量出来
                var_name = prefix + "_" + module.call_par[par_i]
                var_type = module.call_par_type[par_i]
                if var_type in self.type_dict:
                    var_type = self.type_dict[var_type]

                #在var文件中注册一个
                with open(self.component_dir + prefix + "_var.pne","a") as file:
                    file.write(var_type + " " + var_name + ";\n")

                #在control中赋值
                with open(self.component_dir + file_write_o + "_control.pne","a") as file:
                    for i in range(level_o):
                        file.write("    ")
                        file.write(var_name)
                        file.write(" = ")
                        file.write(data_name)
                        file.write(";\n")

                var_list[module.call_par[par_i]] = var_name
            else:
                print("error-generate_module error call par type")
                exit()

        #别管干啥先把变量生成出来。注意是变量，不是meta
        self.generate_var(module.var,var_list,prefix)
        self.frag_relation_dict[file_write_o].varfile.append(prefix + "_var.pne")
        #然后根据指令序列开始生成构造
        self.generate_ins_all(module.ins,modules,var_list,prefix,level_o,module.tuple,module.mapl,module.setl,module.func,module.reg,can_cut="no",file_write_o=file_write_o)

    #展开app
    def generate_app(self, app:data_structure.LYNETTE_APP,modules:dict,prefix:str):
        var_list = {}
        #别管干啥先把变量生成出来。注意是变量，不是meta
        self.generate_var(app.var,var_list,prefix)
        #然后根据指令序列开始生成构造
        self.generate_ins_all(app.ins,modules,var_list,prefix,0,{},{},{},{},{})


    #执行入口
    def execute(self, services:dict, applications:dict, modules:dict, path):
        print('generate...')
        with open(path + "//log_out//log.txt","a") as file:
            file.write('generate...\n')
        self.generate_all_clear()
        self.type_dict = self.construct_type_dict_global()
        for service_name_i in services:
            service = services[service_name_i]
            for app_name_i in service.application:
                if app_name_i[:4] == "host":
                    service.application.pop(service.application.index(app_name_i))
                    continue
                self.generate_app(applications[app_name_i],modules,service_name_i + "_" + app_name_i)
        return self.frag_relation_dict
    

    #重置一下组件
    def generate_all_clear(self):
        pass
        """ # 指定要删除的文件夹路径
        folder_path = "Lynette_file//component"
        # 获取该文件夹下的所有文件名列表
        file_list = os.listdir(folder_path) 
        # 遍历文件列表并删除每个文件
        for file in file_list:
            # 构建完整的文件路径
            file_path = os.path.join(folder_path, file)      
            if os.path.isfile(file_path):
                # 如果是文件则直接删除
                os.remove(file_path) """

    #这是构建define列表
    #其实预编译应该扔出去做
    def construct_type_dict_global(self):
        self.type_dict = {}
        parser = Lark(grammar_define)
        with open('include//define.pne','r') as file:
            code = file.read()
            tree = parser.parse(code)
            for define_t in tree.children:
                if define_t.data == "type_define":
                    self.type_dict[define_t.children[1].value] = define_t.children[0].value
                elif define_t.data == "const_define":
                    name = define_t.children[1]
                    value = define_t.children[2]
                    self.const_dict[name.children[0].children[0].value] = value.children[0].children[0].value
                else:
                    print("666565",define_t.data)
                    exit()
                self.type_dict['bool'] = 'bit<1>'
        return self.type_dict

    #这函数把dict复制一遍
    #别跟我扯有库函数，我更信任我自己写的
    def copy_dict_for_no_struct(self, dict_o:dict):
        dict = {}
        for name in dict_o:
            dict[name] = dict_o[name]
        return dict