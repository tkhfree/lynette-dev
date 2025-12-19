from lark import Lark
from lynette.lynette_lib.grammar.grammar import grammar

#执行一下文件的符号替换, " -> >-<
def change_1(file):
    """将domain文件中的双引号替换为内部使用的占位符\">-<\"。

    Lark语法中include_user_domain/include_sys_domain规则使用\">-<\"来代表字符串，
    因此在解析domain文件前需要把所有\"替换成\">-<\"，解析完成后再替换回去。

    Args:
        file (str): 待转换的domain文件绝对路径。
    """
    pre_code = ''
    with open(file,"r") as f:
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
    with open(file,"w") as f:
        f.write(code)

#执行一下文件的符号替换, >-< -> "
def change_2(file):
    """把change_1生成的\">-<\"占位符恢复成标准的双引号。

    Args:
        file (str): 需要还原的domain文件绝对路径。
    """
    pre_code = ''
    with open(file,"r") as f:
        pre_code = f.read()
    pre_code = pre_code.split('>-<')
    code = ''
    if len(pre_code) > 1:
        len_c = len(pre_code)
        code = pre_code[0] + "\"" + pre_code[1] + "\"" + pre_code[2]
        i = 3
        while i < len_c:
            code = code + "\"" + pre_code[i] + "\"" + pre_code[i+1]
            i = i + 2
    else:
        code = pre_code[0]
    with open(file,"w") as f:
        f.write(code)

#整个提取树的逻辑有大问题
#和预编译一起重构一下
def execute(parser_tree_paremeter):
    """解析入口文件及其include形成的语法森林。

    1. 读取component/main目录下的入口PNE文件并生成语法树；
    2. 扫描include语句，递归解析普通PNE文件和domain文件；
    3. domain文件会列出额外需要解析的PNE文件，因此需要先进行双引号替换；
    4. 所有解析结果存放到forest字典中，key为文件标识，value为Lark语法树。

    Args:
        parser_tree_paremeter (dict): 执行参数集合。
            - main_file_name (str): 入口PNE文件名，例如 Alice_main.pne。
            - input_path (str): 用户工程输入目录，用于定位include文件。
            - sys_path (str): lynette包目录，用于定位component/main路径。

    Returns:
        dict: {文件名: Lark Tree} 的语法森林，供后续collect阶段使用。
    """
    print('parser_tree...')
    with open(parser_tree_paremeter["input_path"] + "//log_out//log.txt","a") as file:
        file.write('parser_tree...\n')
    parser = Lark(grammar)
    forest = {}
    with open(parser_tree_paremeter["sys_path"] + "//component//main//" + parser_tree_paremeter["main_file_name"],'r') as file:
        code = file.read()
        tree = parser.parse(code)
        forest['main'] = tree
        for node_main in tree.children:
            if node_main.data == "include":
                for include in node_main.children:
                    if include.data == "include_user_file":
                        file_path = ''
                        for i in range(len(include.children)-1):
                            file_path = file_path + '//' + include.children[i]
                        file_name = file_path + '//' + include.children[-1]
                        tree_name = file_name
                        file_name = parser_tree_paremeter["input_path"] + file_name + '.pne'
                        with open(file_name,'r') as file:
                            code = file.read()
                            tree = parser.parse(code)
                            forest[tree_name] = tree
                    elif include.data == "include_user_domain":
                        file_path = ''
                        for i in range(len(include.children)-1):
                            file_path = file_path + '//' + include.children[i]
                        file_name = parser_tree_paremeter["input_path"][:-2] + file_path + "//" + include.children[-1] + '.domain'
                        domain_file_name = file_name
                        #print("parser - 44",domain_file_name)
                        change_1(domain_file_name)
                        with open(domain_file_name,"r") as domain_file:
                            domain_code = domain_file.read()
                            domain_tree = parser.parse(domain_code)
                        change_2(domain_file_name)
                        domain_tree_include = domain_tree.children[0]
                        for file_i_t in domain_tree_include.children:
                            if file_i_t.data == "include_user_file":
                                file_name_t = file_i_t.children[0].value
                                if file_name_t == "parser":
                                    continue
                                file_name = parser_tree_paremeter["input_path"][:-2] + file_path + "//" + file_name_t + ".pne"
                                #print("parser - 45",file_name)
                                with open(file_name,'r') as file:
                                    code = file.read()
                                    tree = parser.parse(code)
                                    forest[file_name_t] = tree
                    elif include.data == "include_sys_domain":
                        file_path = "//include"
                        file_name = parser_tree_paremeter["input_path"] + file_path + "//" + include.children[-1] + '.domain'
                        domain_file_name = file_name
                        #print("parser - 44",domain_file_name)
                        change_1(domain_file_name)
                        with open(domain_file_name,"r") as domain_file:
                            domain_code = domain_file.read()
                            domain_tree = parser.parse(domain_code)
                        change_2(domain_file_name)
                        domain_tree_include = domain_tree.children[0]
                        for file_i_t in domain_tree_include.children:
                            if file_i_t.data == "include_sys_file":
                                file_name_t = file_i_t.children[0].value
                                if file_name_t == "parser":
                                    continue
                                file_name = parser_tree_paremeter["input_path"] + file_path + "//" + file_name_t + ".pne"
                                #print("parser - 45",file_name)
                                with open(file_name,'r') as file:
                                    code = file.read()
                                    tree = parser.parse(code)
                                    forest[file_name_t] = tree

    return forest