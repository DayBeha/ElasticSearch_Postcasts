import sys
# from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QToolTip, QMessageBox
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from timeit import default_timer as timer


class MyWidget(QWidget):
    def __init__(self, search_engine):
        super().__init__()
        self.search_engine = search_engine
        self.initUI()
        self.center()  # 调用center方法
        self.show()

        self.doc_list = []

    def center(self):
        # 获取窗口的矩形
        qtRectangle = self.frameGeometry()
        # 获取屏幕的中心点
        centerPoint = self.screen().availableGeometry().center()
        # 移动窗口的中心点到屏幕的中心点
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def initUI(self):
        # QToolTip.setFont(QFont('SansSerif', 10))
        # self.setToolTip('This is a <b>QWidget</b> widget')

        ############
        ## 搜索设置
        self.layout2 = QVBoxLayout()
        # 显示文本
        self.label2 = QLabel(self)
        self.label2.setText("Time Limit:")
        self.label2.setFont(QFont('Time', 10, QFont.Weight.Bold))    # 设置字体字号
        # 创建单行输入框并设置回车键响应, 接收时间限制
        self.input_box_time = QLineEdit(self)
        self.input_box_time.editingFinished.connect(self.get_time_limit)
        self.input_box_time.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号
        self.layout2.addWidget(self.label2)
        self.layout2.addWidget(self.input_box_time)
        
        
        self.layout1 = QVBoxLayout()
        # 显示文本
        self.label = QLabel(self)
        self.label.setText("Query:")
        self.label.setFont(QFont('Time', 10, QFont.Weight.Bold))    # 设置字体字号
        # 创建单行输入框并设置回车键响应，接收查询语句
        self.input_box_query = QLineEdit(self)
        self.input_box_query.returnPressed.connect(self.process_input)
        self.input_box_query.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.input_box_query)


        # 创建水平布局，将两个垂直布局放入其中
        self.layout_H = QHBoxLayout()
        self.layout_H.addLayout(self.layout2)
        self.layout_H.addLayout(self.layout1)


        ############
        ## 搜索结果
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.layout_H)
        # 显示文本
        self.label3 = QLabel(self)
        self.label3.setText("Results:")
        self.label3.setFont(QFont('Time', 10, QFont.Weight.Bold))    # 设置字体字号
        # 创建列表部件，用以显示搜索结果
        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("listWidget_docs")
        self.list_widget.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked) # 设置双击项目时触发的槽函数
        self.list_widget.itemClicked.connect(self.on_item_clicked) # 设置鼠标进入项目时触发的槽函数
        self.layout.addWidget(self.label3)
        self.layout.addWidget(self.list_widget)

        # 显示文本
        self.label4 = QLabel(self)
        self.label4.setText("Content:")
        self.label4.setFont(QFont('Time', 10, QFont.Weight.Bold))    # 设置字体字号
        # 创建文本框，显示更详细内容
        self.text_box = QTextEdit(self)
        self.text_box.setObjectName("textEdit")
        self.text_box.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号
        self.text_box.setReadOnly(True) # 设置为只读
        self.layout.addWidget(self.label4)
        self.layout.addWidget(self.text_box)

        # 状态栏
        self.label5 = QLabel(self)
        self.label5.setText("Ready") # 当状态栏用（左下角）
        self.label5.setFont(QFont("KaiTi", 10, QFont.Weight.Normal))    # 设置字体字号

        self.layout.addWidget(self.label5)
        self.layout.addWidget(self.label5)
        # 设置中央窗口部件的布局管理器
        self.setLayout(self.layout)

        self.setGeometry(300, 600, 600, 700) # x, y, width, height
        self.setWindowTitle('Search Engine')
        self.setWindowIcon(QIcon('icon.png'))


    # def closeEvent(self, event):
    #     reply = QMessageBox.question(self, 'Message', 'Are you sure to quit?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
    #     if reply == QMessageBox.StandardButton.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()

    def reset(self):
        self.list_widget.clear()
        self.text_box.clear()
        # self.statusBar().setStyleSheet("QStatusBar {color: black;}")
        self.label5.setStyleSheet("color: black")

    def get_time_limit(self):
        """获取用户输入的时间限制 """
        self.reset()
        input_text = self.input_box_time.text()
        try:
            integer_value = float(input_text)
            print(f"用户输入了: {integer_value}")
            if integer_value > 5:   # 设置最大时间限制为5min
                integer_value = 5
            self.search_engine.set_time_limit(integer_value)
            self.label5.setText(f"set time limit:{integer_value} min")   # 状态栏（左下角）
            return integer_value
        except ValueError:
            self.label5.setText('Error! Please input valid number!')   # 状态栏（左下角）
            # self.statusBar().setStyleSheet("QStatusBar {color: red;}")
            # 设置self.label5的字体颜色为红色
            self.label5.setStyleSheet("color: red")

    def get_input(self):
        """
        获取用户输入的文本
        """
        input_text = self.input_box_query.text()
        # print(f"用户输入了: {input_text}")
        # words = input_text.split()
        # query = {
        #         "bool": {
        #             "should": [{"match": {"transcript": f"{word}"}} for word in words],
        #             }
        #         }
        query = {
                    "bool": {
                        "must": {
                            "match": {
                                "transcript": {
                                    "query": input_text,
                                    "minimum_should_match": "50%"
                                }
                            }
                        },
                        "should": {
                            "match_phrase": {
                                "transcript": {
                                    "query": input_text,
                                    "slop": 20
                                }
                            }
                        }
                    }
                }
        return query, input_text


    def show_result(self):
        """
        搜索结果显示到list_view上
        :param doc_list: 搜索结果列表
        """
        self.list_widget.clear()
        for i, clip in enumerate(self.doc_list):
            str = f"{i+1}. " + clip.show_info.get('show_filename_prefix') 
            str += " (" + " ".join(clip.text.split()[:3]) + "...)"
            str += f":  {clip.score:.5f}"

                
            # for trans in item:
            #     str += trans.to_str()
            self.list_widget.addItem(str)

    def process_input(self):
        """
        处理用户输入
        """
        self.reset()
        """获取输入文本"""
        query, input_text = self.get_input()

        """进行搜索"""
        self.label5.setText('Searching...')   # 状态栏（左下角）
        t0 = timer()
        self.doc_list = self.search_engine.search(query, input_text)
        self.label5.setText('Search Finished')   # 状态栏（左下角）
        t1 = timer()

        """展示搜索结果"""
        self.show_result()
        self.label5.setText(f"OK, search use time: {t1-t0} s")   # 状态栏（左下角）

    # 设置双击项目时触发的槽函数
    def on_item_double_clicked(self, item):
        index = self.list_widget.row(item)
        # text = ""
        # for trans in self.doc_list[index]:
        #     text += trans.to_str()
        text = self.doc_list[index].text

        # 在文本框中显示详细内容
        # text = item.text()
        # text = self.search_engine.get_trans(text, self.min_limit)   # TODO 获取对应的transcript 片段
        self.text_box.setText(text)

    def on_item_clicked(self, item):
        index = self.list_widget.row(item)
        text = self.doc_list[index].show_info.get('episode_name')   # 显示 episode_name
        item.setToolTip(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    search_engine = None    # TODO 这里要创建SeacherEngine对象
    w = MyWidget(search_engine)
    sys.exit(app.exec())