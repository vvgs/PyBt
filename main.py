import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QWidget, QInputDialog
from PyQt5.QtCore import QPoint
import Core as core
import  SuperWidget as sw
import json

import importlib
import re

def import_libs(text):
    # 按行处理每一行
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue  # 跳过空行

        # 处理形如 "numpy as np" 的情况
        match = re.match(r"(\S+)\s+as\s+(\S+)", line)
        if match:
            lib = match.group(1)
            # 动态导入库
            try:
                globals()[match.group(2)] = importlib.import_module(lib)
                print(f"Successfully imported {lib} as {match.group(2)}")
            except ImportError:
                print(f"Failed to import {lib} as {match.group(2)}")
            continue
        
        # 处理形如 "PyQt5.QtCore: Qt, QPoint" 的情况
        match = re.match(r"(\S+):\s*(\S+)(.*)", line)
        if match:
            lib = match.group(1)
            # 动态导入主模块
            try:
                module = importlib.import_module(lib)
                print(f"Successfully imported {lib}")
            except ImportError:
                print(f"Failed to import {lib}")
                
            # 处理指定的类或子模块
            items = match.group(2).split(',')
            for item in items:
                item = item.strip()
                try:
                    getattr(module, item)  # 检查该类或子模块是否存在
                    print(f"Successfully imported {item} from {lib}")
                except AttributeError:
                    print(f"Failed to import {item} from {lib}")
            continue

        # 处理没有别名和模块限定的简单库名称
        libraries = line.split(",")
        for lib in libraries:
            lib = lib.strip()
            if lib:
                try:
                    importlib.import_module(lib)
                    print(f"Successfully imported {lib}")
                except ImportError:
                    print(f"Failed to import {lib}")

class Code_button(sw.SuperButton):
    def __init__(self, Text, Owner):
        super().__init__(Text, Owner, Owner.owner.widget)

    def edit(self):
        dialog = sw.SuperDialog(self.owner.name, self.owner.text, self.owner.code)
        if dialog.exec_() == QDialog.Accepted:
            text1, text2, text3 = dialog.getText()
            self.owner.name = text1
            self.owner.text = text1 if text2 == 'Unnamed' else text2
            self.owner.code = text3
            self.owner.make_func()
            self.owner.widget.setText(self.owner.text)

    def delete(self):
        return self.owner.delete()

    def clicked_center(self):
        self.owner.execute()
    
    def clicked_edge(self, edge):
        if self.owner.owner.is_linking:
            text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter name:')
            if ok:
                b1 = self.owner.owner.start_block.new_buffer(text)
                b2 = self.owner.new_buffer(text)
                self.owner.owner.link(b1, b2, text)
                print("link success")
            else:
                print("link canceled")
            self.owner.owner.is_linking = False
            self.owner.owner.start_block = None
        else:
            self.owner.owner.is_linking = True
            self.owner.owner.start_block = self.owner
            print("start link")

    def first_drag_end(self):
        print('first_drag_end')
        self.edit()

class Vbuffer(core.Buffer):
    def __init__(self, Owner, Name='Unnamed', Angle=0):
        super().__init__(Owner, Name)
        self.angle = Angle
        self.widget = QWidget()
        self.widget.hide()

    def to_dict(self):
        return {
            'name': self.name,
            'angle': self.angle
        }
    
    def delete(self):
        self.owner.buffers.remove(self)
        self.owner.buffer_dic.pop(self.name)
        for connection in self.owner.connections_in[::-1]:
            if connection.target_buffer == self:
                connection.delete()
        for connection in self.owner.connections_out[::-1]:
            if connection.origin_buffer == self:
                connection.delete()
        self.widget.deleteLater()
        self.widget.deleteLater()
    
class Vconnection(core.Connection):
    def __init__(self, Owner, Origin_buffer, Target_buffer, Name='Unnamed'):
        super().__init__(Owner, Origin_buffer, Target_buffer, Name)\
        
        self.widget = QWidget()
        self.widget.hide()

    def to_dict(self):
        return {            
            'name': self.name,
            'origin_block': self.origin_buffer.owner.name,
            'origin_buffer': self.origin_buffer.name,
            'target_block': self.target_buffer.owner.name,
            'target_buffer': self.target_buffer.name,
        }
    
    def delete(self):
        self.owner.sub_connections.remove(self)
        self.origin_buffer.owner.connections_out.remove(self)
        self.target_buffer.owner.connections_in.remove(self)
        self.widget.deleteLater()
    
class Code_vblock(core.Code_block):
    def __init__(self, Owner, Name='Unnamed', Geometry=(0,0,40,40), Code=None, Text = 'Unnamed', Visible=True, Buffers=[]):
        super().__init__(Code)
        self.owner = Owner
        self.visible = Visible
        self.explicit = False
        self.name = Name
        self.text = Name if Text == 'Unnamed' else Text
        self.sub_blocks = []
        self.widget = Code_button(self.text, self)
        self.widget.setGeometry(Geometry[0], Geometry[1], Geometry[2], Geometry[3])
        self.widget.show()
        for buffer in Buffers:
            self.new_buffer(buffer['name'], 0, buffer['angle'])

        self.dragging = False
        self.offset = QPoint()

    def __del__(self): # test delete
        print("Code_vblock deleted")

    def to_dict(self):
        # 递归将嵌套的对象转换为字典
        return {
            'name': self.name,
            'type': 'Code_vblock',
            'text': self.text,
            'geometry': self.widget.get_geometry(),
            'visible': self.visible,
            'code': self.code,
            'buffers': [item.to_dict() for item in self.buffers]
        }
    
    def from_dict(self,data):
        return Code_vblock(None, data['name'], data['geometry'], data['code'], data['text'], data['visible'], data['buffers'])
    
    def new_buffer(self, Name, Data = 0, Angle = 0):
        self.buffer_dic[Name] = Data
        self.buffers.append(Vbuffer(self, Name, Angle))
        return self.buffers[-1]
    
    def delete(self):
        for connection in self.connections_in[::-1]:
            connection.delete()
        for connection in self.connections_out[::-1]:
            connection.delete()
        self.owner.sub_blocks.remove(self)
        self.widget.deleteLater()

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

class Uni_vblock(core.Uni_block):
    def __init__(self, Owner, Name='Unnamed', Geometry=(0,0,40,40), Text = 'Unnamed', Visible=True, Buffers=[], Sub_connections=[], Sub_blocks=[]):
        super().__init__()
        self.owner = Owner
        self.name = Name
        self.text = Name if Text == 'Unnamed' else Text
        self.visible = Visible
        self.widget = None # make_widget()方法未实现
        self.widget.setGeometry(Geometry[0], Geometry[1], Geometry[2], Geometry[3])
        self.widget.show()
        self.run_block = Code_vblock(self)
        self.run_block.make_func("parent.owner.execute()")
        for buffer in Buffers:
            self.new_buffer(buffer['name'], 0, buffer['angle'])
        self.sub_blocks = Sub_blocks
        for block in Sub_blocks:
            block.owner = self
        for connection in Sub_connections:
            if connection['origin_block'] == self.name:
                block1 = self
            else:
                for block in self.owner.sub_blocks:
                    if block.name == connection['origin_block']:
                        block1 = block
                        break
            if connection['target_block'] == self.name:
                block2 = self
            else:
                for block in self.owner.sub_blocks:
                    if block.name == connection['target_block']:
                        block2 = block
                        break
            self.link(block1.get_buffer(connection['origin_buffer']), block2.get_buffer(connection['target_buffer']), connection['name'])

        self.is_linking = False
        self.start_block = None
    
    def to_dict(self):
        # 递归将嵌套的对象转换为字典
        return {
            'name': self.name,
            'type': 'Uni_vblock',
            'text': self.text,
            'geometry': self.widget.get_geometry(),
            'visible': self.visible,
            'sub_blocks': [item.to_dict() if isinstance(item, (Uni_vblock, Code_vblock)) else item for item in self.sub_blocks],
            'buffers': [item.to_dict() for item in self.buffers],
            'connections': [item.to_dict() for item in self.sub_connections]
        }
    
    def from_dict(data):
        if data['type'] == 'Uni_vblock':
            blocks = [Uni_vblock.from_dict(item) if item['type'] == 'Uni_vblock' else Code_vblock.from_dict(item) for item in data['sub_blocks']]
            return Uni_vblock(None, data['name'], data['geometry'], data['text'], data['visible'], data['buffers'], data['connections'], blocks)
        elif data['type'] == 'Code_vblock':
            return Code_vblock(None, data['name'], data['geometry'], data['code'], data['text'], data['visible'], data['buffers'])
    
    def new_buffer(self, Name, Data = 0, Angle = 0):
        self.buffer_dic[Name] = Data
        self.buffers.append(Vbuffer(self, Name, Angle))
        return self.buffers[-1]
    
    def new_block(self, Type, Name='Unnamed', Geometry=(0,0,100,60), Text = 'Unnamed'):
        if Type == 'Code_vblock':
            block = Code_vblock(self, Name, Geometry, None, Text)
            self.sub_blocks.append(block)
        elif Type == 'Uni_vblock':
            block = Uni_vblock(self, Name, Geometry, Text)
            self.sub_blocks.append(block)
        return block
    
    def link(self, Origin_buffer = None, Target_buffer = None, Name = "Unnamed"):
        self.sub_connections.append(Vconnection(self, Origin_buffer, Target_buffer, Name))
        return self.sub_connections[-1]
    
    def delete(self):
        for connection in self.connections_in[::-1]:
            connection.delete()
        for connection in self.connections_out[::-1]:
            connection.delete()
        self.owner.sub_blocks.remove(self)
        self.widget.deleteLater()

class Main_vblock(core.Uni_block):
    def __init__(self):
        super().__init__()
        self.main_window = MainWindow()
        self.widget = QWidget()
        self.main_window.setCentralWidget(self.widget)
        self.name = 'MainBlock'
        self.is_con_execute = True

        self.run_block = Code_vblock(self, 'run', (1500, 0, 100,60))
        self.sub_blocks.append(self.run_block)
        self.run_block.make_func('''parent.owner.init_connection.updata()
parent.owner.execute()''')
        
        self.open_file_block = Code_vblock(self, 'open_file', (0, 0, 100,60))
        self.sub_blocks.append(self.open_file_block)
        self.open_file_block.make_func('''parent.owner.load('pure.txt')''') # 测试
        
        self.init_block = Code_vblock(self, 'init', (0, 470, 100,60))
        self.sub_blocks.append(self.init_block)
        self.init_block.make_func('''parent.owner.is_activated = True''') # 测试
        b1 = self.new_buffer('start', 0)
        b2 = self.init_block.new_buffer('start', 0)
        self.init_connection = self.link(b1,b2,'init_connection')

        self.is_linking = False
        self.start_block = None
        
        self.main_window.show()
        

    def new_buffer(self, Name, Data = 0, Angle = 0):
        self.buffer_dic[Name] = Data
        self.buffers.append(Vbuffer(self, Name, Angle))
        return self.buffers[-1]
    
    def new_block(self, Type, Name='Unnamed', Geometry=(0,0,100,60), Text = 'Unnamed'):
        if Type == 'Code_vblock':
            block = Code_vblock(self, Name, Geometry, None, Text)
            self.sub_blocks.append(block)
        elif Type == 'Uni_vblock':
            block = Uni_vblock(self, Name, Geometry, Text)
            self.sub_blocks.append(block)
        return block
    
    def link(self, Origin_buffer = None, Target_buffer = None, Name = "Unnamed"):
        self.sub_connections.append(Vconnection(self, Origin_buffer, Target_buffer, Name))
        return self.sub_connections[-1]

    def save(self, file_path): # 将block数据加入到txt文件
        with open(file_path, "w", encoding="utf-8") as file:
            dic = {
                'name': self.name,
                'type': 'Main_vblock',
                'buffers': [item.to_dict() for item in self.buffers],
                'connections': [item.to_dict() for item in self.sub_connections],
               'sub_blocks': [item.to_dict() if isinstance(item, (Uni_vblock, Code_vblock)) else item for item in self.sub_blocks]
            }
            json.dump(dic, file, ensure_ascii=False, indent=4)

    def load(self, file_path): # 从txt文件读取block数据
        for block in self.sub_blocks[::-1]:
            block.delete()
        for connection in self.sub_connections[::-1]:
            connection.delete()
        for buffer in self.buffers[::-1]:
            buffer.delete()
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if data['type'] == 'Main_vblock':
                self.name = data['name']
                self.buffers = []
                for buffer in data['buffers']:
                    self.new_buffer(buffer['name'], 0, buffer['angle'])

                self.sub_blocks = []
                for block in data['sub_blocks']:
                    if block['type'] == 'Uni_vblock':
                        blocks = [Uni_vblock.from_dict(item) if item['type'] == 'Uni_vblock' else Code_vblock.from_dict(item) for item in block['sub_blocks']]
                        self.sub_blocks.append(Uni_vblock(self, block['name'], block['geometry'], block['text'], block['visible'], block['buffers'], block['connections'], blocks))
                    elif block['type'] == 'Code_vblock':
                        self.sub_blocks.append(Code_vblock(self, block['name'], block['geometry'], block['code'], block['text'], block['visible'], block['buffers']))
                for block in self.sub_blocks:
                    block.owner = self

                self.sub_connections = []
                for connection in data['connections']:
                    if connection['origin_block'] == self.name:
                        block1 = self
                    else:
                        for block in self.sub_blocks:
                            if block.name == connection['origin_block']:
                                block1 = block
                                break
                    if connection['target_block'] == self.name:
                        block2 = self
                    else:
                        for block in self.sub_blocks:
                            if block.name == connection['target_block']:
                                block2 = block
                                break
                    self.link(block1.get_buffer(connection['origin_buffer']), block2.get_buffer(connection['target_buffer']), connection['name'])
        for connection in self.sub_connections:
            if connection.name == 'init_connection':
                self.init_connection = connection
        self.main_window.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口标题
        self.setWindowTitle("简单的 PyQt 主窗口")

        # 设置窗口大小
        self.setGeometry(100, 100, 1600, 1000)

if __name__ == "__main__":
    # 创建应用程序对象
    app = QApplication(sys.argv)

    # 创建主窗口对象
    #window = MainWindow()
    main_vblock = Main_vblock()

    # 进入应用程序的主循环
    sys.exit(app.exec_())