grammar_parser = """
    start: "parser" name "(" par_pkt "," par_hdr "," par_gmeta ")" "{" nodes deparser "}"

    par_pkt: ("in"|"inout"|"out")? name name

    par_hdr: ("in"|"inout"|"out")? name name

    par_gmeta: ("in"|"inout"|"out")? name name

    nodes : node+

    node : "state" name "{" (ins|exact)* trans "}"

    trans : (transition_select|transition)
    transition : "transition" name ";"
    transition_select : "transition" "select" "(" data ")" "{" (transition_entry)+ "}"
    transition_entry : data ":" name ";"

    ins : tmp_def|lookahead|advance|assign
    tmp_def : name name ";"
    lookahead : data "=" "pkt.lookahead<" name ">();"
    exact : "pkt.extract(" name_field ");"
    advance : "pkt.advance(" (data|data_plus) ");"
    data_plus : data ("*" int)
    assign : data "=" data ";"

    deparser : "deparser" name "{" deparser_hdr* "}"
    deparser_hdr : "pkt.emit(" name_field ");"

    data: int | name | name_field | aheaddata
    aheaddata : "pkt.lookahead<" BIT_TYPE ">()"
    name_field: NAME "." NAME ("." NAME)?
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