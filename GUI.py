import sys
# from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QToolTip, QMessageBox
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QPalette, QColor
from timeit import default_timer as timer


class MyWidget(QMainWindow):
    def __init__(self, search_engine):
        super().__init__()
        self.search_engine = search_engine
        self.initUI()
        self.center()  # 调用center方法
        self.show()

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

        self.setToolTip('This is a <b>QWidget</b> widget')

        # btn = QPushButton('Button', self)
        # # btn.setToolTip('This is a <b>QPushButton</b> widget')
        # btn.setStatusTip('This is a <b>QPushButton</b> widget')
        # btn.clicked.connect(QApplication.instance().quit)   # quit the application
        # btn.resize(btn.sizeHint())
        # btn.move(50, 50)

        # 显示文本
        self.label = QLabel(self)
        self.label.setText("Query:")
        self.label.setGeometry(5, 5, 50, 10)
        self.label.setFont(QFont('Time', 10, QFont.Weight.Bold))    # 设置字体字号

        self.label2 = QLabel(self)
        self.label2.setText("Time Limit:")
        self.label2.setGeometry(520, 5, 80, 10)
        self.label2.setFont(QFont('Time', 10, QFont.Weight.Bold))    # 设置字体字号


        height = 20
        # 创建单行输入框并设置回车键响应，接收查询语句
        self.input_box_query = QLineEdit(self)
        self.input_box_query.returnPressed.connect(self.process_input)
        self.input_box_query.setGeometry(5, height, 500, 50)
        self.input_box_query.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号
        # 创建单行输入框并设置回车键响应, 接收时间限制
        self.input_box_time = QLineEdit(self)
        self.input_box_time.returnPressed.connect(self.get_time_limit)
        self.input_box_time.setGeometry(520, height, 75, 50)
        self.input_box_time.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号

        height += 60
        # 创建列表部件，用以显示搜索结果
        self.list_widget = QListWidget(self)
        self.list_widget.setGeometry(0, height, 600, 300)
        self.list_widget.setObjectName("listWidget_docs")
        self.list_widget.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked) # 设置双击项目时触发的槽函数

        height += 310
        # 创建文本框，显示更详细内容
        self.text_box = QTextEdit(self)
        self.text_box.setGeometry(0, height, 600, 200)
        self.text_box.setObjectName("textEdit")
        self.text_box.setFont(QFont('Time', 20, QFont.Weight.Bold))    # 设置字体字号



        self.statusBar().showMessage('Ready')   # 状态栏（左下角）
        height += 210
        self.setGeometry(300, height, 600, height+10) # x, y, width, height
        self.setWindowTitle('Search Engine')


    # def closeEvent(self, event):
    #     reply = QMessageBox.question(self, 'Message', 'Are you sure to quit?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
    #     if reply == QMessageBox.StandardButton.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()

    def reset(self):
        self.list_widget.clear()
        self.text_box.clear()
        self.statusBar().setStyleSheet("QStatusBar {color: black;}")

    def get_time_limit(self):
        """获取用户输入的时间限制 """
        input_text = self.input_box_time.text()
        try:
            integer_value = float(input_text)
            print(f"用户输入了: {integer_value}")
            if integer_value > 5:   # 设置最大时间限制为5min  TODO 阈值有待推敲
                integer_value = 5
            self.statusBar().showMessage(f"set time limit:{integer_value} min")   # 状态栏（左下角）
            return integer_value
        except ValueError:
            self.statusBar().showMessage('Error! Please input valid number!')   # 状态栏（左下角）
            self.statusBar().setStyleSheet("QStatusBar {color: red;}")


    def get_input(self):
        """
        获取用户输入的文本
        """
        input_text = self.input_box_query.text()
        words = input_text.split()
        query = {
                "bool": {
                    "should": [{"match": {"transcript": f"{word}"}} for word in words],
                    }
                }

        # print(f"用户输入了: {input_text}")
        return query


    def show_result(self, doc_list):
        """
        搜索结果显示到list_view上
        :param doc_list: 搜索结果列表
        """
        self.list_widget.clear()
        for i, item in enumerate(doc_list):
            str = f"{i+1}. {item[0].get_episode_filename_prefix()}"
            for trans in item:
                str += trans.to_str()
            self.list_widget.addItem(str)

    def process_input(self):
        """
        处理用户输入
        """
        self.reset()
        """获取输入文本"""
        query = self.get_input()

        """进行搜索"""
        self.statusBar().showMessage('Searching...')   # 状态栏（左下角）
        t0 = timer()
        # doc_list = ["doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8", "doc9", "dco10"]
        # TODO 这里要调用search_engine的search方法，并将结果保存到doc_list中
        doc_list = self.search_engine.search(query)

        print('search finish')
        t1 = timer()

        """展示搜索结果"""
        self.show_result(doc_list)
        self.statusBar().showMessage(f"OK, search use time: {t1-t0} s")   # 状态栏（左下角）

    # 设置双击项目时触发的槽函数
    def on_item_double_clicked(self, item):
        # 在文本框中显示详细内容
        text = item.text()
        # text = self.search_engine.get_trans(text, self.min_limit)   # TODO 获取对应的transcript 片段
        self.text_box.setText(text)



if __name__ == '__main__':
    app = QApplication(sys.argv)

    search_engine = None    # TODO 这里要创建SeacherEngine对象
    w = MyWidget(search_engine)
    sys.exit(app.exec())