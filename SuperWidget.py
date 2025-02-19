from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QVBoxLayout, QTextEdit, QDialog, QDialogButtonBox, QVBoxLayout, QLineEdit, QLabel
from PyQt5.QtCore import Qt, QPoint

def is_in_center_area(widget, point, edge_margin=10):
    # 获取 widget 的矩形区域
    widget_rect = widget.rect()
    
    # 计算中心区域的边界
    center_rect = widget_rect.adjusted(edge_margin, edge_margin, -edge_margin, -edge_margin)
    
    # 判断点是否在中心区域内
    if center_rect.contains(point):
        return True, None  # 点在中心区域内，返回 True 和 None (表示没有在边缘上)
    
    # 如果点不在中心区域内，检查点在哪个边缘
    if point.x() < widget_rect.left() + edge_margin:  # 左边缘
        return False, 'Left'
    elif point.x() > widget_rect.right() - edge_margin:  # 右边缘
        return False, 'Right'
    elif point.y() < widget_rect.top() + edge_margin:  # 上边缘
        return False, 'Top'
    elif point.y() > widget_rect.bottom() - edge_margin:  # 下边缘
        return False, 'Bottom'
    
    return False, None  # 默认返回，防止遗漏

class SuperButton(QPushButton):
    def __init__(self,Text, Owner, parent_widget=None):
        super().__init__(Text, parent_widget)
        self.drag_start_position = QPoint()
        self.owner = Owner
        self.dragging = False
        self.first_dragging = True
        self.is_resizing = False
        self.resize_cursor = Qt.SizeFDiagCursor
        self.drag_threshold = 5  # 拖动触发阈值（像素）
        self.resize_threshold = 5  # 缩放触发阈值（像素）
        self.drag_threshold = 5  # 拖动触发阈值（像素）

    def get_geometry(self):
        # 获取窗口的几何信息并返回元组 (x, y, width, height)
        geometry = self.geometry()
        return (geometry.x(), geometry.y(), geometry.width(), geometry.height())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.dragging:
            # 判断是否在右下角区域
                if event.pos().x() >= self.width() - 10 and event.pos().y() >= self.height() - 10:
                    self.is_resizing = True
                    self.setCursor(self.resize_cursor)
                else:
                    self.drag_start_position = event.pos()
                    self.dragging = False
                    super().mousePressEvent(event)  # 保持父类点击事件处理

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            # 计算新的宽度和高度
            new_width = event.pos().x()
            new_height = event.pos().y()
            self.setFixedSize(new_width, new_height)
        else:
            if event.buttons() & Qt.LeftButton:
                # 计算移动距离
                move_distance = (event.pos() - self.drag_start_position).manhattanLength()
                
                if not self.dragging and move_distance > self.drag_threshold:
                    self.dragging = True
                    self.setCursor(Qt.ClosedHandCursor)
                
                if self.dragging:
                    # 转换为父部件坐标系
                    parent_pos = self.parent().mapFromGlobal(event.globalPos())
                    # 计算新位置（保持按钮中心跟随鼠标）
                    new_x = parent_pos.x() - self.width()/2
                    new_y = parent_pos.y() - self.height()/2
                    self.move(int(new_x), int(new_y))
            elif self.dragging:
                    # 转换为父部件坐标系
                    parent_pos = self.parent().mapFromGlobal(event.globalPos())
                    # 计算新位置（保持按钮中心跟随鼠标）
                    new_x = parent_pos.x() - self.width()/2
                    new_y = parent_pos.y() - self.height()/2
                    self.move(int(new_x), int(new_y))
            else:
                super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ArrowCursor)
            if self.dragging:
                # 如果正在拖动，则忽略点击事件
                event.ignore()
                self.dragging = False
                self.setMouseTracking(False)
                if self.first_dragging:
                    self.first_drag_end()
                    self.first_dragging = False
            else:
                # 点击事件处理
                if not self.is_resizing:
                    flag, edge = is_in_center_area(self, event.pos())
                    if flag:
                        self.clicked_center()
                    else:
                        self.clicked_edge(edge)

        self.is_resizing = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)  # 正常处理点击事件

            
    def contextMenuEvent(self, event):
        # 创建右键菜单
        menu = QMenu(self)
        action1 = QAction("编辑", self)
        menu.addAction(action1)
        action2 = QAction("删除", self)
        menu.addAction(action2)
        
        # 连接菜单项的信号槽
        action1.triggered.connect(self.on_action1)
        action2.triggered.connect(self.on_action2)
        
        # 在鼠标点击位置显示菜单
        menu.exec_(event.globalPos())

    def on_action1(self):
        self.edit()

    def on_action2(self):
        self.delete()

    def edit(self):
        print("Please override function 'edit'")

    def delete(self):
        print("Please override function 'delete'")

    def clicked_center(self):
        print("Please override function 'clicked_center'")

    def clicked_edge(self, edge):
        print("Please override function 'clicked_edge'")

    def first_drag_end(self):
        print("Please override function 'first_drag_end'")


class SuperDialog(QDialog):
    def __init__(self, Name, Text, Code):
        super().__init__()
        
        # 设置对话框标题和大小
        self.setWindowTitle("编辑")
        self.setFixedSize(400, 300)

        # 创建控件
        self.single_line_input1 = QLineEdit(self)
        self.single_line_input1.setText(Name)

        self.single_line_input2 = QLineEdit(self)
        self.single_line_input2.setText(Text)

        self.multi_line_input = QTextEdit(self)
        self.multi_line_input.setText(Code)

        self.submit_button = QPushButton("提交", self)
        self.submit_button.clicked.connect(self.submit)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.single_line_input1)
        layout.addWidget(QLabel("Text:"))
        layout.addWidget(self.single_line_input2)

        layout.addWidget(QLabel("多行输入:"))
        layout.addWidget(self.multi_line_input)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

        # Store original text
        self.original_name = Name
        self.original_text = Text
        self.original_code = Code

    def submit(self):
        # 获取用户输入的文本，如果没有输入则返回原来的文本
        self.single_line_text1 = self.single_line_input1.text() or self.original_name
        self.single_line_text2 = self.single_line_input2.text() or self.original_text
        self.multi_line_text = self.multi_line_input.toPlainText() or self.original_code

        self.accept()

    def getText(self):
        return self.single_line_text1, self.single_line_text2, self.multi_line_text

    def setText(self, text1, text2, text3):
        self.single_line_input1.setText(text1)
        self.single_line_input2.setText(text2)  
        self.multi_line_input.setText(text3)
