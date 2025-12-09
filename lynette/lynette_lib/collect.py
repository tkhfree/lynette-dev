"""collect.py - 语法树收集模块

功能说明：
    将 Lark 语法树（Tree）转换为内部数据结构（data_structure），
    这是编译流程的第二阶段：源代码 → 语法树 → [collect] → 数据结构 → P4代码

模块结构：
    1. 指令收集函数：收集各种指令类型
       - collect_ins_assign()    : 赋值指令（a = b）
       - collect_ins_cul()       : 计算指令（a = b + c）
       - collect_ins_call()      : 调用指令
       - collect_func_call()     : 函数调用
       - collect_primitive()     : 原语操作（drop, return, addheader等）
    
    2. 控制流收集函数：收集控制结构
       - collect_if()            : if-else条件分支
       - collect_switch()        : switch语句
       - collect_condition()     : 条件表达式（比较、isvalid、check）
       - collect_assert()        : 断言语句
    
    3. 代码块收集函数：
       - collect_code_body()     : 代码块（指令序列）
    
    4. 顶层组件收集函数：
       - collect_service()       : 服务定义
       - collect_app()           : 应用定义
       - collect_module()        : 模块定义
    
    5. 主入口函数：
       - execute()               : 遍历语法森林，调度所有收集函数

Application 组件结构：
    collect_app() 处理的子组件：
    ├─ define
    │  └─ ins_define_var        : 变量定义
    ├─ ins_assign               : 赋值指令 → collect_ins_assign()
    ├─ ins_call                 : 调用指令 → collect_ins_call()
    ├─ if                       : 条件语句 → collect_if()
    └─ primitive                : 原语操作 → collect_primitive()

Module 组件结构：
    collect_module() 处理的子组件：
    ├─ module_name              : 模块名称
    ├─ module_pars              : 模块参数
    ├─ module_parser            : 模块parser（跳过）
    ├─ parser                   : parser定义（跳过）
    └─ control                  : control块
       ├─ assert                : 断言 → collect_assert()
       ├─ define                : 定义块
       │  ├─ tuple              : 元组定义
       │  ├─ set                : 集合定义
       │  ├─ map                : 映射定义
       │  ├─ func               : 函数定义 → collect_code_body()
       │  ├─ ins_define_var     : 变量定义
       │  └─ reg                : 寄存器定义
       ├─ switch                : switch语句 → collect_switch()
       ├─ if                    : 条件语句 → collect_if()
       ├─ ins_assign            : 赋值指令 → collect_ins_assign()
       ├─ ins_call              : 调用指令 → collect_ins_call()
       ├─ ins_cul               : 计算指令 → collect_ins_cul()
       ├─ primitive             : 原语操作 → collect_primitive()
       ├─ annotation            : 注解（跳过）
       └─ ins_null              : 空指令（跳过）

注意事项：
    - 所有 collect_xxx 函数遵循相同模式：输入Tree → 提取数据 → 输出data_structure对象
    - Module 比 Application 支持更多的特性（如 assert、switch、func、reg等）
    - 遇到未识别的节点类型时，程序会打印错误信息并退出
"""

from lark import Lark, Tree, Token
from lynette_lib import data_structure

def collect_ins_assign(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "ins_assign"
    ins_left_tem = ins.children[0]
    for data_tem in ins_left_tem.children:
        ins_data.left.append(data_tem)
    ins_data.right1 = ins.children[1].children[0]
    return ins_data

def collect_ins_cul(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "ins_cul"
    ins_data.left.append(ins.children[0])
    ins_data.right1 = ins.children[1]
    ins_data.op = ins.children[2].value
    ins_data.right2 = ins.children[3]
    return ins_data

def collect_ins_call(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "ins_call"
    ins_call_name = ins.children[0].value
    ins_data.call_name = ins_call_name
    if len(ins.children) > 1:
        ins_call_par_list = ins.children[1]
        for par in ins_call_par_list.children:
            ins_data.call_par.append(par)
    return ins_data

def collect_func_call(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "func_call"
    ins_call_name = ins.children[0].value
    ins_data.call_name = ins_call_name
    if len(ins.children) > 1:
        ins_call_par_list = ins.children[1]
        for par in ins_call_par_list.children:
            ins_data.call_par.append(par)
    return ins_data

def collect_primitive(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "primitive"
    ins_data.primitive_type = ins.children[0].data
    if ins_data.primitive_type == "addheader":
        ins_data.primitive_par.append(ins.children[0].children[0])
    elif ins_data.primitive_type == "removeheader":
        ins_data.primitive_par.append(ins.children[0].children[0])
    elif ins_data.primitive_type == "headercompress":
        ins_data.primitive_par.append(ins.children[0].children[0])
    elif ins_data.primitive_type == "updatechecksum":
        for data_tem in ins.children[0].children:
            ins_data.primitive_par.append(data_tem)
    elif ins_data.primitive_type == "drop":
        pass
    elif ins_data.primitive_type == "return":
        pass
    elif ins_data.primitive_type == "nop":
        pass
    else:
        print("?-collect.py-collect_primitive",ins_data.primitive_type)
    return ins_data

def collect_code_body(body:Tree):
    code_body = data_structure.LYNETTE_BLOCK()
    for ins_p in body.children:
        if ins_p.data == "instruction":
            ins = ins_p.children[0]
            if ins.data == "ins_assign":
                ins_data = collect_ins_assign(ins)
                code_body.ins.append(ins_data)
            elif ins.data == "ins_call":
                ins_data = collect_ins_call(ins)
                code_body.ins.append(ins_data)
            elif ins.data == "if":
                ins_data = collect_if(ins)
                code_body.ins.append(ins_data)
            elif ins.data == "primitive":
                ins_data = collect_primitive(ins)
                code_body.ins.append(ins_data)
            elif ins.data == "ins_cul":
                ins_data = collect_ins_cul(ins)
                code_body.ins.append(ins_data)
            else:
                print("?-collect.py-collect_code_body-ins_type",ins.data)
                exit()
    return code_body

def collect_condition(condition_define:Tree):
    condition = data_structure.LYNETTE_CONDITION()
    for i in condition_define.children:
        if i.data == 'compare':
            condition.type = i.children[0].data
            condition.left.append(i.children[0].children[0])
            condition.right.append(i.children[0].children[1])
        elif i.data == 'isvalid':
            condition.type = 'isvalid'
            condition.left.append(i.children[0])
        elif i.data == 'check':
            condition.type = 'check'
            for left_i in i.children[0].children:
                condition.left.append(left_i)
            condition.right.append(i.children[1].children[0])
        else:
            print("?-collect.py-collect_condition",i.data)
            exit()
    return condition

def collect_assert(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "assert"
    condition = data_structure.LYNETTE_CONDITION()
    for node in ins.children:
        condition = collect_condition(node)
        ins_data.condition.append(condition)
    return ins_data

def collect_if(ins:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "if"
    for block_tem in ins.children:
        if block_tem.data == "if_block":
            condition = data_structure.LYNETTE_CONDITION()
            condition = collect_condition(block_tem.children[0])
            block = data_structure.LYNETTE_BLOCK()
            block = collect_code_body(block_tem.children[1])
            ins_data.condition.append(condition)
            ins_data.condition_block.append(block)
        elif block_tem.data == "else_block":
            block_tem_t = block_tem.children[0]
            if block_tem_t.data == "else":
                ins_data.default = 1
                block_i = data_structure.LYNETTE_BLOCK()
                block_i = collect_code_body(block_tem.children[0].children[0])
                ins_data.default_bolck = block_i
            else:
                ins_data_t = collect_if(block_tem_t)
                ins_data.else_ins = ins_data_t
                ins_data.else_ins_t = 1
        else:
            print("?-collect.py-collect_if",block_tem.data)
            exit()
    return ins_data

def collect_app(tree:Tree):
    app_name = ''
    app = data_structure.LYNETTE_APP()
    app_name = tree.children[0].value
    app.name = app_name
    if len(tree.children) > 2:
        code_body = tree.children[2]
    else:
        code_body = tree.children[1]
    for node in code_body.children:
        ins = node.children[0]
        if ins.data == "define":
            ins = ins.children[0]
            if ins.data == "ins_define_var":
                define_type = ins.children[0].value
                define_name = ins.children[1].value
                if define_name not in app.var:
                    app.var[define_name] = define_type
            else:
                print("?-collect.py-collect_app-define_type",ins.data)
                exit()
        elif ins.data == "ins_assign":
            ins_data = collect_ins_assign(ins)
            app.ins.append(ins_data)
        elif ins.data == "ins_call":
            ins_data = collect_ins_call(ins)
            app.ins.append(ins_data)
        elif ins.data == "if":
            ins_data = collect_if(ins)
            app.ins.append(ins_data)
        elif ins.data == "primitive":
            ins_data = collect_primitive(ins)
            app.ins.append(ins_data)
        else:
            print("?-collect.py-collect_app-ins_type",ins.data)
            exit()
    return app_name, app

def collect_service(tree:Tree):
    service_name = ''
    service = data_structure.LYNETTE_SERVICE()
    service_name = tree.children[0].value
    service.name = service_name
    for app in tree.children[1].children:
        service.application.append(app.value)
    return service_name , service

def collect_switch(tree:Tree):
    ins_data = data_structure.LYNETTE_INS()
    ins_data.type = "switch"
    for node in tree.children:
        if node.data == "switch_key":
            for key in node.children:
                ins_data.key.append(key)
        elif node.data == "switch_item":
            ins_data.case.append(node.children[0])
            func_data = node.children[1]
            if func_data.data == "func_call":
                ins_data.func.append(collect_func_call(func_data))
            elif func_data.data == "ins_call":
                ins_data.func.append(collect_ins_call(func_data))
            else:
                print("?-collect.py-collect_switch call what?")
                exit()
        else:
            print("?-collect.py-collect_switch",node.data)
            exit()
    return ins_data

def collect_module(tree:Tree):
    module_name = tree.children[0].children[0].value
    module = data_structure.LYNETTE_MODULE()
    module.name = module_name
    for node in tree.children:
        if node.data == "module_name":
            pass
        elif node.data == "parser":
            pass
        elif node.data == "control":
            for inss in node.children[0].children:
                ins = inss.children[0]
                if ins.data == "assert":
                    ins_data = collect_assert(ins)
                    module.ins.append(ins_data)
                elif ins.data == "define":
                    ins = ins.children[0]
                    if ins.data == "tuple":
                        tuple_name = ins.children[0].value
                        tuple_data = []
                        for data in ins.children[1].children:
                            tuple_data.append(data)
                        module.tuple[tuple_name] = tuple_data
                    elif ins.data == "set":
                        setl = data_structure.LYNETTE_SET()
                        for i in ins.children:
                            if i.data == "set_name":
                                setl.name = i.children[0].value
                            elif i.data == "set_key":
                                for j in i.children:
                                   setl.key.append(j) 
                            elif i.data == "entry":
                                int_i = 0
                                for entry_i in i.children:
                                    entry = []
                                    for entry_data in entry_i.children:
                                        entry_data = entry_data.children[0].children[0].value
                                        entry.append(entry_data)
                                    setl.entry[int_i] = entry
                                    int_i = int_i + 1
                            else:
                                print("?-collect.py-collect_module-define-set",i.data)
                                exit()
                        module.setl[setl.name] = setl
                    elif ins.data == "map":
                        mapl = data_structure.LYNETTE_MAP()
                        for i in ins.children:
                            if i.data == "map_name":
                                mapl.name = i.children[0].value
                            elif i.data == "map_key":
                                for j in i.children:
                                   mapl.key.append(j) 
                            elif i.data == "map_value":
                                for j in i.children:
                                   mapl.value.append(j) 
                            elif i.data == "map_len":
                                mapl.size = int(i.children[0].children[0].value)
                            elif i.data == "entry":
                                int_i = 0
                                for entry_i in i.children:
                                    entry = []
                                    for entry_data in entry_i.children:
                                        entry_data = entry_data.children[0].children[0].value
                                        entry.append(entry_data)
                                    mapl.entry[int_i] = entry
                                    int_i = int_i + 1
                            else:
                                print("?-collect.py-collect_module-define-map",i.data)
                                exit()
                        module.mapl[mapl.name] = mapl
                    elif ins.data == "func":
                        block = data_structure.LYNETTE_BLOCK()
                        block = collect_code_body(ins.children[1])
                        module.func[ins.children[0].value] = block
                    elif ins.data == "ins_define_var":
                        define_type = ins.children[0].value
                        define_name = ins.children[1].value
                        if define_name not in module.var:
                            module.var[define_name] = define_type
                    elif ins.data == "reg":
                        reg_type = ins.children[0].value
                        reg_name = ins.children[1].value
                        if len(ins.children) > 2:
                            reg_size = int(ins.children[2].value)
                        else:
                            reg_size = 50
                        register = data_structure.LYNETTE_REG()
                        register.size = reg_size
                        register.name = reg_name
                        register.type = reg_type
                        module.reg[reg_name] = register
                    else:
                        print("?-collect.py-collect_module-define",ins.data)
                        exit()
                elif ins.data == "switch":
                    ins_data = collect_switch(ins)
                    module.ins.append(ins_data)
                elif ins.data == "if":
                    ins_data = collect_if(ins)
                    module.ins.append(ins_data)
                elif ins.data == "ins_assign":
                    ins_data = collect_ins_assign(ins)
                    module.ins.append(ins_data)
                elif ins.data == "ins_call":
                    ins_data = collect_ins_call(ins)
                    module.ins.append(ins_data)
                elif ins.data == "ins_cul":
                    ins_data = collect_ins_cul(ins)
                    module.ins.append(ins_data)
                elif ins.data == "primitive":
                    ins_data = collect_primitive(ins)
                    module.ins.append(ins_data)
                elif ins.data == "annotation":
                    pass
                elif ins.data == "ins_null":
                    pass
                else:
                    print("?-collect.py-collect_module-control",ins.data)
                    exit()
        elif node.data == "module_pars":
            for par in node.children:
                call_type = par.children[0].value
                type_par = par.children[1].value
                name_par = par.children[2].children[0].children[0].value
                module.call_type.append(call_type)
                module.call_par.append(name_par)
                module.call_par_type.append(type_par)
        elif node.data == "module_parser":
            pass
        else:
            print("?-collect.py-collect_module",node.data)
            exit()
    return module_name, module

def execute(forest:dict, path):
    """从语法森林中提取并收集所有程序组件（service、application、module）。
    
    这是编译流程中的"收集"阶段，将Lark语法树转换为中间数据结构。
    遍历语法森林中的所有语法树，识别并提取三种类型的组件：
    1. service: 服务定义，描述应用之间的调用关系
    2. application: 应用定义，包含变量定义和指令序列
    3. module: 模块定义，包含parser、control块、元组、集合、映射等
    
    Args:
        forest (dict): 语法森林字典，key为文件名标识，value为Lark语法树对象。
                       由parser_tree.execute()生成，包含入口文件及其所有include文件的语法树。
        path (str): 工程输入路径，用于写入日志文件。
    
    Returns:
        tuple: 包含三个字典的元组：
            - services (dict): {服务名: LYNETTE_SERVICE对象}，存储所有服务定义
            - applications (dict): {应用名: LYNETTE_APP对象}，存储所有应用定义
            - modules (dict): {模块名: LYNETTE_MODULE对象}，存储所有模块定义
    
    处理流程:
        1. 遍历语法森林中的每个文件语法树
        2. 在每个语法树中查找'code'节点（包含实际的程序组件）
        3. 根据节点类型（service/application/module）调用对应的collect函数
        4. 将提取的数据结构对象存入对应的字典中
        5. 如果遇到未知的节点类型，报错退出
    """
    print('collect...')
    with open(path + "//log_out//log.txt","a") as file:
        file.write('collect...\n')
    #一次扫描：遍历所有语法树，提取三种类型的组件
    services = {}      # 存储所有服务定义
    applications = {}  # 存储所有应用定义
    modules = {}       # 存储所有模块定义
    
    # 遍历语法森林中的每个文件语法树
    for tree_name in forest:
        tree = forest[tree_name]
        tree : Tree
        # 遍历语法树的直接子节点，查找'code'节点（包含实际的程序组件）
        for code in tree.children:
            if code.data == 'code':
                # 遍历code节点下的所有组件节点
                for node in code.children:
                    # 处理service组件：服务定义，描述应用调用关系
                    if node.data == 'service':
                        service_name,service = collect_service(node)
                        if service_name not in services:
                            services[service_name] = service
                    # 处理application组件：应用定义，包含变量和指令
                    elif node.data == 'application':
                        app_name, app = collect_app(node)
                        if app_name not in applications:
                            applications[app_name] = app
                    # 处理module组件：模块定义，包含parser和control块
                    elif node.data == 'module':
                        module_name, module = collect_module(node)
                        if module_name not in modules:
                            modules[module_name] = module
                    # 遇到未知节点类型，报错退出
                    else:
                        print("?-collect.py-execute",node.data)
                        exit()
    return services, applications, modules
        