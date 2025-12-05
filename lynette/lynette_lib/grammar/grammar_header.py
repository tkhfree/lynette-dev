grammar_header = """
    start: (header|struct)*

    header : "header" header_name "{" header_def* "}"
    header_def : (BIT_TYPE|NAME) NAME ";"
    header_name : NAME

    struct : "struct" struct_name "{" struct_def* "}"
    struct_def : (BIT_TYPE|NAME) NAME ";"
    struct_name : NAME

    data: int | name
    int : INT
    name : NAME
    NAME: ("_")?(LCASE_LETTER|UCASE_LETTER)(("_")?(LCASE_LETTER|UCASE_LETTER|DIGIT))*
    DATA_TYPE: NAME | BIT_TYPE
    BIT_TYPE : "bit" "<" INT ">"
    
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