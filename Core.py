class Buffer:
    def __init__(self, Owner = None, Name = "Unnamed") -> None:
        self.owner = Owner
        self.name = Name
        self.changed = False
        self.type = None # "in" or "out" or None
    
    def data(self):
        return self.owner.buffer_dic[self.name]
    
    def updata(self, New_data):
        self.owner.buffer_dic[self.name] = New_data

class Connection:
    def __init__(self, Owner = None, Origin_buffer = None, Target_buffer = None, Name = "Unnamed") -> None:
        self.owner = Owner
        self.origin_buffer = Origin_buffer
        self.target_buffer = Target_buffer
        self.delay = -1
        self.initial_delay = 0
        self.name = Name
        if (Origin_buffer != None) and (Target_buffer != None):
            Origin_buffer.owner.connections_out.append(self)
            Target_buffer.owner.connections_in.append(self)

    def updata(self, Is_activate = True):
        self.target_buffer.updata(self.origin_buffer.data())
        if Is_activate:
            if self.target_buffer.owner.is_activated == False:
                self.activate()

    def activate(self):
        self.owner.controller.active_blocks.append(self.target_buffer.owner)
        self.target_buffer.owner.is_activated = True

    def time_reset(self):
        self.delay = self.initial_delay

class Block:
    def __init__(self) -> None:
        self.buffer_dic = {}
        self.buffer_dic["parent"] = self
        self.buffers = []
        self.connections_in = []
        self.connections_out = []
        self.name = 'unnamed'
        self.is_activated = False

    def activate(self):
        for c in self.connections_in:
            c.activate()
    
    def new_buffer(self, Name, Data = 0):
        self.buffer_dic[Name] = Data
        self.buffers.append(Buffer(self, Name))
        return self.buffers[-1]

    def get_buffer(self, Name):
        for b in self.buffers:
            if b.name == Name:
                return b

    def buffer_data(self, Name):
        return self.buffer_dic[Name]

    def buffer_updata(self, Name, Data):
        self.buffer_dic[Name] = Data

class Uni_block(Block):
    def __init__(self, Sub_blocks = [], Sub_connections = []) -> None:
        super().__init__()
        self.sub_blocks = Sub_blocks
        self.sub_connections =Sub_connections
        self.controller = Controller(self)
        self.is_con_execute = True
        self.is_finish = False

    def link(self, Origin_buffer = None, Target_buffer = None, Name = "Unnamed"):
        self.sub_connections.append(Connection(self, Origin_buffer, Target_buffer, Name))
        return self.sub_connections[-1]
    
    def execute(self, Is_con_execute = None):
        if Is_con_execute == None:
            Is_con_execute = self.is_con_execute
        if Is_con_execute:
            while(1):
                self.controller.execute()
                self.is_finish = True
                for c in self.sub_connections:
                    if c.delay >= 0:
                        self.is_finish = False
                if self.is_finish:
                    break
        else:
            self.controller.execute()

class Code_block(Block):
    def __init__(self, Code = None) -> None:
        super().__init__()
        self.code = Code
        self.func = None
        self.make_func()
    
    def execute(self, _=None):
        self.func(self.buffer_dic)
    
    def make_func(self, Code = None):
        # 创建一个新的函数实例
        if Code == None:
            code = self.code
        else:
            code = Code
        if code != None:
            self.code = code
            def func(buffer_dic):
                exec(code, globals(), buffer_dic)  # 执行给定的代码
            self.func = func

# 定义控制器
# uni_block 拥有控制器
class Controller:
    def __init__(self, Owner) -> None:
        self.owner = Owner
        self.active_blocks = []

    def execute(self):
        for connection in self.owner.sub_connections:
            if connection.delay == 0:
                connection.updata(Is_activate = True)
            if connection.delay >= 0:
                connection.delay -= 1

        for block in self.active_blocks:
            block.execute(False)
            for c in block.connections_out:
                c.time_reset()
            block.is_activated = False

        self.active_blocks = []
    
    
if __name__ == '__main__':
    cblock1 = Code_block(
"""        
b = a+1
print("cblock1 is executed.")
"""
    )
    cblock1.name = 'cblock1'
    cblock1.new_buffer("a", 0)
    cblock1.new_buffer("b", 0)

    cblock2 = Code_block(
"""        
c = b+1
print("cblock2 is executed.")
"""
    )
    cblock2.name = 'cblock2'
    cblock2.new_buffer("b", 0)
    cblock2.new_buffer("c", 0)

    ublock1 = Uni_block([cblock1, cblock2])
    ublock1.name = 'ubllock1'
    ublock1.new_buffer("a", 1)
    ublock1.new_buffer("c", 0)
    ublock1.link(cblock1.get_buffer('b'), cblock2.get_buffer('b'))
    c1 = ublock1.link(ublock1.get_buffer('a'), cblock1.get_buffer('a'))
    ublock1.link(cblock2.get_buffer('c'), ublock1.get_buffer('c'))

    ublock1.is_activated = 'True'
    c1.updata()
    ublock1.execute()
    print(ublock1.buffer_data('c'))

    #while(1):
    #    contr.execute()