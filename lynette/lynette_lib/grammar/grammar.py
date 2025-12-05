"""
PNE (Programmable Network Element) 语言语法规则定义

PNE语言是一个面向网络拓扑的特定领域语言，用于将基于整个网络拓扑的程序编译生成
面向单个设备的P4程序。本文件使用EBNF语法定义PNE语言的核心语法规则，使用Lark库进行解析。

语法规则说明：
- 每个规则定义了PNE语言的一个语法结构
- 规则名称使用小写字母和下划线，对应PNE源代码中的语法元素
- 大写规则名称表示词法单元（token），如NAME、INT等
- 注释说明了每个语法规则的作用和对应的P4语言特性
"""

grammar = """
    // ============================================================================
    // 顶层结构：PNE程序的基本结构
    // ============================================================================
    
    // 程序入口：可选的include、usingparser和code部分
    // 对应P4的顶层结构，支持文件包含、解析器声明和代码定义
    start: include? usingparser? code?

    // ============================================================================
    // 文件包含机制：支持系统文件和用户文件的包含
    // ============================================================================
    
    // include部分：支持多种包含方式
    // - include_sys_file: 系统文件包含，使用尖括号 <>
    // - include_sys_domain: 系统域文件包含，用于批量包含
    // - include_user_file: 用户文件包含，使用特殊标记 >-<
    // - include_user_domain: 用户域文件包含
    // - annotation: 注释块，可包含被注释的代码
    include: (include_sys_file|include_sys_domain|include_user_file|include_user_domain|annotation)*

    // 系统文件包含：格式 #include <path/to/file.pne>
    // 用于包含系统库文件，路径使用斜杠分隔
    include_sys_file: ("#include" "<" NAME("/"NAME)*".pne" ">")
    
    // 系统域文件包含：格式 #include <domain.domain>
    // 域文件包含多个文件的列表，用于批量导入
    include_sys_domain: "#include" "<" NAME ".domain" ">"
    
    // 用户文件包含：格式 #include ">-<path/to/file.pne>-<"
    // 用于包含用户自定义文件，使用特殊标记避免与字符串冲突
    include_user_file: ("#include" ">-<" NAME("/"NAME)* ".pne" ">-<")
    
    // 用户域文件包含：格式 #include ">-<path/to/domain.domain>-<"
    include_user_domain: "#include" ">-<" NAME("/"NAME)* ".domain" ">-<"

    // ============================================================================
    // 解析器声明：指定使用的解析器
    // ============================================================================
    
    // 解析器声明：格式 using ParserName;
    // 对应P4的parser声明，指定应用使用的解析器
    usingparser: "using" NAME ";"

    // ============================================================================
    // 代码结构：服务、应用和模块定义
    // ============================================================================
    
    // 代码部分：包含服务、应用和模块定义
    // 这些是PNE语言的核心抽象，用于描述网络功能
    code: (service|application|module)*

    // 服务定义：格式 service[ServiceName] { app1 -> app2 -> ... }
    // 服务定义了应用的调用链，描述数据包在网络中的处理流程
    // 对应P4中多个control块的组合调用
    service: "service[" NAME "]" "{" ser_app "}"
    
    // 服务应用链：定义应用的顺序调用关系
    // 使用 -> 表示数据流方向，如 app1 -> app2 表示先执行app1再执行app2
    ser_app: NAME ("->" NAME)*

    // 应用定义：格式 application AppName [using ParserName] { ... }
    // 应用是网络功能的逻辑单元，可以包含多个模块的调用
    // using子句指定使用的解析器，对应P4的package声明
    application: "application" NAME ("using" NAME)?  "{" code_body "}"

    // 模块定义：格式 module ModuleName([params]) [using Parser] { parser {...} control {...} }
    // 模块是可复用的网络功能组件，包含parser和control两部分
    // 对应P4的control块，可以接收参数，支持参数化设计
    module: "module" module_name "(" module_pars? ")" module_parser? "{" parser? control "}"
    
    // 模块名称：标识符
    module_name : NAME
    
    // 模块解析器声明：格式 using ParserName
    // 指定模块使用的解析器
    module_parser: ("using" NAME)
    
    // 模块参数列表：多个参数用逗号分隔
    // 支持参数化模块，提高代码复用性
    module_pars : module_par ("," module_par)*
    
    // 模块参数：格式 paramName DATA_TYPE defaultValue
    // 参数包含名称、类型和默认值，用于模块实例化
    module_par : (NAME) (DATA_TYPE data)
    
    // ============================================================================
    // Parser和Control：对应P4的解析器和控制平面
    // ============================================================================
    
    // Parser定义：格式 parser { header1; header2; ... }
    // 声明需要解析的头部字段，对应P4 parser中的extract操作
    // 简化了P4 parser的复杂状态机定义
    parser: "parser" "{" (data ";")* "}"

    // Control定义：格式 control { ... }
    // 包含控制平面的逻辑，对应P4的control块
    // 可以包含表操作、条件判断、数据包处理等
    control: "control" "{" code_body "}"

    // ============================================================================
    // 代码体：指令序列
    // ============================================================================
    
    // 代码体：由多个指令组成
    // 指令按顺序执行，对应P4 control中的语句序列
    code_body: (instruction)*

    // ============================================================================
    // 指令类型：支持多种控制流和数据操作指令
    // ============================================================================
    
    // 指令：支持多种类型的指令
    // - ins_assign: 赋值指令
    // - ins_call: 表/模块调用
    // - if: 条件判断
    // - assert: 断言检查
    // - define: 定义（表、变量、函数等）
    // - switch: 多路选择
    // - primitive: 原语操作（drop、nop等）
    // - ins_cul: 算术运算
    // - annotation: 注释
    // - ins_null: 空语句
    instruction: ins_assign|ins_call|if|assert|define|switch|primitive|ins_cul|annotation|ins_null|for_loop|while_loop
    
    // 注释：格式 /* ... */
    // 支持多行注释，可以包含被注释的代码
    annotation: "/*" (instruction|include_sys_file|include_sys_domain|include_user_file|include_user_domain)* "*/"
    
    // 单行注释：格式 // ...
    // 对应P4的单行注释
    line_comment: "//" /[^\\n]*/
    
    // 变量定义：格式 DATA_TYPE varName;
    // 定义局部变量，对应P4 control中的变量声明
    ins_define_var: DATA_TYPE NAME ";"
    
    // 赋值指令：格式 left = right;
    // 支持多值赋值，对应P4的赋值语句
    // 可以同时给多个变量赋值，如 (a, b) = (1, 2);
    ins_assign: ins_assign_left "=" ins_assign_right ";"
    
    // 赋值左侧：可以是单个变量或多个变量的元组
    ins_assign_left : data ("," data)*
    
    // 赋值右侧：表达式或值
    ins_assign_right : expression
    
    // 表/模块调用：格式 TableName.apply([params]);
    // 调用P4表或模块，对应P4的table.apply()或control.apply()
    // 可以传递参数，用于表查找或模块执行
    ins_call: NAME ".apply" "("  ins_call_par? ")" ";"
    
    // 调用参数：多个参数用逗号分隔
    ins_call_par:((data) (","(data))*)
    
    // 算术运算：格式 result = left OP right;
    // 支持加法和减法运算，对应P4的算术表达式
    // 注意：P4不支持运行时除法，所以只支持+和-
    ins_cul: data "=" data INS_CUL_TYPE data ";"
    
    // 算术运算符：加号或减号
    INS_CUL_TYPE: "+"|"-"
    
    // 空语句：单独的分号
    // 用于占位或空操作
    ins_null: ";"

    // ============================================================================
    // 函数定义：可复用的代码块
    // ============================================================================
    
    // 函数定义：格式 func FunctionName() { ... }
    // 定义可复用的代码块，对应P4的action或function
    // 注意：当前版本不支持参数，未来可扩展
    func : "func" NAME "(" func_params? ")" "{" code_body "}"
    
    // 函数参数：格式 param1, param2, ...
    func_params: func_param ("," func_param)*
    
    // 函数参数定义：格式 DATA_TYPE paramName
    func_param: DATA_TYPE NAME
    
    // ============================================================================
    // 原语操作：P4提供的基础数据包操作
    // ============================================================================
    
    // 原语：P4提供的基础操作
    // 这些操作直接映射到P4的原语，用于数据包处理
    primitive: sendtocpu|nop|drop|removeheader|addheader|return|updatechecksum|headercompress
    
    // 发送到CPU：格式 sendToCPU();
    // 将数据包发送到控制平面处理，对应P4的packet_in
    sendtocpu: "sendToCPU" "(" ")" ";"
    
    // 空操作：格式 nop();
    // 不执行任何操作，用于占位
    nop: "nop" "(" ")" ";"
    
    // 丢弃数据包：格式 drop();
    // 丢弃当前数据包，对应P4的mark_to_drop()
    drop: "drop" "(" ")" ";"
    
    // 移除头部：格式 removeHeader(headerName);
    // 移除数据包中的指定头部，对应P4的header.setInvalid()
    removeheader: "removeHeader" "(" data ")" ";"
    
    // 头部压缩：格式 HeaderCompress(headerName);
    // 压缩头部字段，用于节省带宽
    headercompress: "HeaderCompress" "(" data ")" ";"
    
    // 添加头部：格式 addHeader(headerName);
    // 添加新的头部到数据包，对应P4的header.setValid()
    addheader: "addHeader" "(" data ")" ";"
    
    // 返回：格式 return();
    // 提前退出当前控制块，对应P4的return语句
    return: "return" "(" ")" ";"
    
    // 更新校验和：格式 updateChecksum(header, ...);
    // 更新头部的校验和字段，对应P4的verify_checksum/update_checksum
    updatechecksum: "updateChecksum" "(" data ("," data)* ")" ";"

    // ============================================================================
    // Switch语句：多路选择
    // ============================================================================
    
    // Switch语句：格式 switch(key) { case1: action1; case2: action2; }
    // 根据键值选择执行不同的操作，对应P4的switch语句
    // 用于实现多路分支逻辑
    switch: "switch" "(" switch_key ")" "{" switch_item* "}"
    
    // Switch键：可以是单个值或多个值的元组
    switch_key : data ("," data)*
    
    // Switch项：格式 value: action;
    // 定义每个case的值和对应的操作
    switch_item: data ":" (func_call|ins_call)
    
    // 函数调用：格式 FunctionName([params]);
    // 调用定义的函数
    func_call: NAME "(" func_call_par? ")" ";"
    
    // 函数调用参数：多个参数用逗号分隔
    func_call_par: ((data) (","(data))*)

    // ============================================================================
    // 定义语句：表、变量、函数、寄存器等
    // ============================================================================
    
    // 定义：支持多种类型的定义
    // - tuple: 元组定义
    // - set: 集合定义（对应P4的set）
    // - map: 映射表定义（对应P4的table）
    // - ins_define_var: 变量定义
    // - func: 函数定义
    // - reg: 寄存器定义（对应P4的register）
    define: tuple|set|map|ins_define_var|func|reg

    // 寄存器定义：格式 static DATA_TYPE regName[size];
    // 定义状态寄存器，对应P4的register
    // 用于存储状态信息，支持数组形式的寄存器
    reg: "static" DATA_TYPE NAME ( "[" INT "]" )? ";"

    // 元组定义：格式 tuple TupleName { field1, field2, ... }
    // 定义元组类型，用于多值返回或传递
    tuple: "tuple" NAME "{" tuple_data "}"
    
    // 元组数据：多个字段用逗号分隔
    tuple_data: data ("," data)*
    
    // 集合定义：格式 set<keyType> setName [entries];
    // 定义集合，对应P4的set，用于成员关系检查
    set: "set" "<" set_key ">" set_name entry?";"
    
    // 集合键类型：可以是位类型或类型名，支持复合键
    set_key: (BIT_TYPE|NAME) ("," (BIT_TYPE|NAME))*
    
    // 集合名称：标识符
    set_name: NAME
    
    // 映射表定义：格式 map<keyType, valueType>[size] tableName [entries];
    // 定义映射表，对应P4的table，用于查找和匹配
    // 支持固定大小的表（通过[size]指定），可以预定义表项
    map: "map" "<" map_key "," map_value ">" ("[" map_len "]")? map_name entry?";"
    
    // 表项定义：格式 { entry1; entry2; ... }
    // 定义表的初始表项，对应P4的table entries
    entry: "{" (single_entry (single_entry)*)? "}"
    
    // 单个表项：格式 (key1, key2, ...);
    // 定义表的一个条目，键值用逗号分隔
    single_entry: "(" (data ("," data)*)? ")" ";"
    
    // 映射表名称：标识符
    map_name: NAME
    
    // 映射表键类型：支持简单类型或复合类型（元组）
    map_key: (BIT_TYPE|NAME) | ("<" (BIT_TYPE|NAME) ("," (BIT_TYPE|NAME))* ">")
    
    // 映射表值类型：支持简单类型或复合类型（元组）
    map_value: (BIT_TYPE|NAME) | ("<" (BIT_TYPE|NAME) ("," (BIT_TYPE|NAME))* ">")
    
    // 映射表长度：整数，指定表的最大容量
    map_len: int

    // ============================================================================
    // 断言：运行时检查
    // ============================================================================
    
    // 断言：格式 assert(condition);
    // 运行时断言检查，用于调试和验证
    // 对应P4的assert语句（如果目标架构支持）
    assert: "assert" "(" condition ")" ";"

    // ============================================================================
    // 条件语句：if-else结构
    // ============================================================================
    
    // If语句：格式 if(condition) { ... } [else if ...] [else ...]
    // 条件分支语句，对应P4的if-else
    // 支持嵌套和else if链
    if: "if" "(" if_block "}" else_block?
    
    // If块：条件表达式和代码体
    if_block: condition ")" "{" code_body
    
    // Elif块列表：多个else if
    elif_blocks : elif_block+
    
    // Elif块：格式 else if(condition) { ... }
    elif_block : ("else" "if" "(" if_block "}")
    
    // Else块：格式 else { ... } 或 else if ...
    else_block: "else" (if|else)
    
    // Else子句：代码体
    else: "{" code_body "}"
    
    // ============================================================================
    // 循环语句：for和while循环
    // ============================================================================
    
    // For循环：格式 for(init; condition; update) { ... }
    // 支持C风格的for循环，用于迭代处理
    // 注意：P4对循环有严格限制（必须是编译时确定次数）
    for_loop: "for" "(" for_init? ";" for_condition? ";" for_update? ")" "{" code_body "}"
    
    // For循环初始化：变量定义或赋值
    for_init: ins_define_var | ins_assign
    
    // For循环条件：条件表达式
    for_condition: condition
    
    // For循环更新：赋值或函数调用
    for_update: ins_assign | ins_call
    
    // While循环：格式 while(condition) { ... }
    // 条件循环，注意P4对while循环有严格限制
    while_loop: "while" "(" condition ")" "{" code_body "}"
    
    // ============================================================================
    // 条件表达式：逻辑和比较操作
    // ============================================================================
    
    // 逻辑非：格式 !expression
    not: "!"
    
    // 条件：支持逻辑非、比较、成员检查和有效性检查
    // - compare: 比较操作（==, !=, >, >=, <, <=）
    // - check: 成员关系检查（in操作）
    // - isvalid: 头部有效性检查
    // - logical: 逻辑运算（&&, ||）
    condition: (not)? (compare | check | isvalid | logical)
    
    // 比较操作：支持多种比较运算符
    compare: compare_e | compare_ne | compare_b | compare_be | compare_s | compare_se
    
    // 等于：格式 left == right
    compare_e: (data) "==" (data)
    
    // 不等于：格式 left != right
    compare_ne: (data) "!=" (data)
    
    // 大于：格式 left > right
    compare_b: (data) ">" (data)
    
    // 大于等于：格式 left >= right
    compare_be: (data) ">=" (data)
    
    // 小于：格式 left < right
    compare_s: (data) "<" (data)
    
    // 小于等于：格式 left <= right
    compare_se: (data) "<=" (data)
    
    // 成员检查：格式 (key1, key2, ...) in table
    // 检查键是否在表中，对应P4的table.apply().hit
    check: check_left "in" check_right
    
    // 检查左侧：可以是单个值或多个值的元组
    check_left: data ("," data)*
    
    // 检查右侧：表或集合名称
    check_right: data
    
    // 有效性检查：格式 header.isValid() 或 isValid(header, ...)
    // 检查头部是否有效，对应P4的header.isValid()
    isvalid: (data ".isValid()")|("isValid(" data ("," data)* ")")
    
    // 逻辑运算：格式 left && right 或 left || right
    // 支持逻辑与和逻辑或，用于组合多个条件
    logical: logical_and | logical_or
    
    // 逻辑与：格式 left && right
    logical_and: condition "&&" condition
    
    // 逻辑或：格式 left || right
    logical_or: condition "||" condition
    
    // ============================================================================
    // 表达式：支持更复杂的表达式计算
    // ============================================================================
    
    // 表达式：支持算术、位运算、括号等
    // 对应P4的表达式，支持多种运算符
    expression: term (("+"|"-") term)*
    
    // 项：乘除运算的优先级高于加减
    term: factor (("*"|"/"|"%") factor)*
    
    // 因子：基本数据或括号表达式
    factor: data | "(" expression ")" | unary_op factor
    
    // 一元运算符：正负号、位取反、逻辑非
    unary_op: "+" | "-" | "~" | "!"
    
    // 位运算表达式：格式 left OP right
    // 支持位与、位或、位异或、左移、右移
    bitwise_expr: data (BITWISE_OP data)+
    
    // 位运算符：&, |, ^, <<, >>
    BITWISE_OP: "&" | "|" | "^" | "<<" | ">>"

    // ============================================================================
    // 数据：支持多种数据类型和访问方式
    // ============================================================================
    
    // 数据：支持多种数据形式
    // - name_field: 字段访问（如 hdr.ethernet.dmac）
    // - int: 整数常量
    // - name: 变量名
    // - array: 数组访问
    // - sys_data: 系统数据（以下划线开头）
    // - ip_data: IP地址（IPv4或IPv6）
    // - ox_num: 十六进制数
    // - expression: 表达式结果
    data: name_field | int | name | array | sys_data | ip_data | ox_num | "(" expression ")"
    
    // IP地址数据：IPv4或IPv6格式
    ip_data : IP | IPS
    
    // IPv4地址：格式 192.168.1.1
    IP : INT"."INT"."INT"."INT
    
    // IPv6地址：格式 2001:db8::1:2:3:4:5:6:7:8
    IPS: INT":"INT":"INT":"INT":"INT":"INT":"INT":"INT
    
    // 字段访问：格式 object.field 或 object.field.subfield
    // 用于访问头部字段或结构体成员，对应P4的字段访问
    name_field: NAME "." NAME ("." NAME)?
    
    // 整数：十进制整数
    int : INT
    
    // 系统数据：以下划线开头的标识符
    // 用于访问系统提供的元数据，如 _standard_metadata
    sys_data : SYS_DATA
    
    // 系统数据格式：_identifier
    SYS_DATA : "_" (LCASE_LETTER|UCASE_LETTER|DIGIT)*
    
    // 名称：标识符
    name: NAME
    
    // 索引：用于数组访问
    index: data
    
    // 索引列表：多个索引用逗号分隔，用于多维数组
    indexs : index ("," index)*
    
    // 空索引：下划线，表示忽略该维度
    index_null : "_"
    
    // 数组访问：格式 array[index] 或 array[index1, index2]
    // 支持一维和多维数组访问，对应P4的数组索引
    array: data "[" (indexs | index_null) "]"
    
    // 十六进制数：格式 0x1234 或 0xABCD
    ox_num: OX_NUM
    
    // 十六进制数格式：0x后跟十六进制数字
    OX_NUM :  "0x" (INT|UCASE_LETTER)+
    
    // ============================================================================
    // 词法定义：标识符、类型等
    // ============================================================================
    
    // 标识符：以字母开头，可包含字母、数字和下划线
    // 对应P4的标识符规则
    NAME: (LCASE_LETTER|UCASE_LETTER)(("_")?(LCASE_LETTER|UCASE_LETTER|DIGIT))*
    
    // 数据类型：可以是类型名或位类型
    // 对应P4的类型系统
    DATA_TYPE: NAME | BIT_TYPE
    
    // 位类型：格式 bit<width>
    // 定义固定宽度的位字段，对应P4的bit<W>类型
    // 这是P4中最基本的数据类型
    BIT_TYPE : "bit" "<" INT ">"
    
    // ============================================================================
    // Lark库导入：使用Lark提供的公共定义
    // ============================================================================

    // 导入Lark的公共定义
    // - LETTER: 所有字母
    // - LCASE_LETTER: 小写字母
    // - UCASE_LETTER: 大写字母
    // - DIGIT: 数字
    // - INT: 整数
    // - WS: 空白符
    // - _STRING_INNER: 字符串内容
    // - QUATE: 引号
    %import common.LETTER
    %import common.LCASE_LETTER
    %import common.UCASE_LETTER
    %import common.DIGIT
    %import common.INT
    %import common.WS
    %import common._STRING_INNER
    %import common.QUATE
    
    // 忽略空白符：自动跳过空格、制表符、换行符等
    // 这使得语法定义更加清晰，不需要显式处理空白
    %ignore WS
"""