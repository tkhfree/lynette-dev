class LYNETTE_PIPELINE():
    def __init__(self):
        self.name = '666'
        self.modules = []
        self.parser = ''
        self.deparser = ''

    def show_self(self):
        print('name:',self.name)

class LYNETTE_SERVICE():
    def __init__(self):
        self.name = '666'
        self.application = []

class LYNETTE_APP():
    def __init__(self):
        self.name = '666'
        self.var = {} #变量
        self.tuple = {}
        self.mapl = {}
        self.setl = {} 
        self.reg = {}
        self.ins = []

class LYNETTE_MODULE():
    def __init__(self):
        self.name = '666'
        self.call_type = []
        self.call_par = []
        self.call_par_type = []
        self.var = {} #变量
        self.tuple = {}
        self.mapl = {}
        self.setl = {} 
        self.reg = {}
        self.ins = []
        self.func = {}

class LYNETTE_MAP():
    def __init__(self):
        self.name = '666'
        self.key = []
        self.value = []
        self.size = 50
        self.entry = {}

class LYNETTE_SET():
    def __init__(self):
        self.name = '666'
        self.key = []
        self.size = 50
        self.entry = {}

class LYNETTE_INS():
    def __init__(self):
        self.type = ''

        self.left = []
        self.right1 = ''
        self.right2 = ''
        self.op = ''

        self.call_name = ''
        self.call_par = []
        self.call_par_type = []

        self.condition = []
        self.condition_block = []
        self.else_ins_t = 0
        self.else_ins : LYNETTE_INS
        self.default = 0
        self.default_bolck : LYNETTE_BLOCK

        self.key = []
        self.case = []
        self.func = []

        self.primitive_type = ''
        self.primitive_par = []

class LYNETTE_FRAG_RELATION():
    def __init__(self):
        self.name = ''
        self.input = []
        self.output = []
        self.varfile = []
        self.module = {}
        self.table_num = 0

class LYNETTE_BLOCK():
    def __init__(self):
        self.ins = []

class LYNETTE_CONDITION():
    def __init__(self):
        self.no = 0
        self.type = ''
        self.left = []
        self.right = []

class LYNETTE_REG():
    def __init__(self):
        self.name = ''
        self.type = ''
        self.size = 50

class LYNETTE_PARSER_NODE():
    def __init__(self):
        self.name = ''
        self.exact = ''
        self.select = ''
        self.protocol = [] #这是后置协议
        self.rely = [] #前驱节点
        self.next = {} #后续节点
        self.ins = [] #注意在node中用的ins和前面是完全不一样的东西，是个很原始的子树

class LYNETTE_TABLE():
    def __init__(self):
        self.name = ''
        self.keys = []

