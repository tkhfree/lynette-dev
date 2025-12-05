grammar_define = """
    start: (type_define|const_define|null)*

    type_define: "typedef" BIT_TYPE NAME ";"

    const_define: "const" BIT_TYPE data "=" data ";"

    null : ";"


    data: int | name | ox_num
    int : INT
    name : NAME
    NAME: (LCASE_LETTER|UCASE_LETTER)(("_")?(LCASE_LETTER|UCASE_LETTER|DIGIT))*
    DATA_TYPE: NAME | BIT_TYPE
    BIT_TYPE : "bit" "<" INT ">"
    ox_num: OX_NUM
    OX_NUM : "0x" (INT|UCASE_LETTER)*
    
    ANNOTATION: "/*" _STRING_INNER "*/"

    %import common.LETTER
    %import common.LCASE_LETTER
    %import common.UCASE_LETTER
    %import common.DIGIT
    %import common.INT
    %import common.WS
    %import common._STRING_INNER
    %import common.QUATE
    %ignore WS
"""
#底部 %import 引入 Lark 的公共定义（字母、数字、空白等），%ignore WS 表示忽略所有空白符。
#grammar_define 只支持三种句子：类型别名、常量定义和空语句。
# 类型/常量需要用 bit<宽度> 标注，常量左右都是 data 表达式，用来在 define.pne 中写全局类型/常量，供后续编译阶段引用。