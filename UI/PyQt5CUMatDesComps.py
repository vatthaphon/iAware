import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class Test(QtWidgets.QDialog):
    def __init__(self):

        super(Test, self).__init__()

        ########## Set the layouts
        layout1 = QtWidgets.QVBoxLayout(self)

        self.__buttonLogin = CUMatDesQLineEdit()
        # self.__buttonLogin.clicked.connect(self.handleLogin)

        # self.__buttonFaceLogin = pqtQtWidgets.QPushButton('Face Login', self)
        # self.__buttonFaceLogin.clicked.connect(self.handleFaceLogin)

        # self.__buttonSignup = pqtQtWidgets.QPushButton('Sign up', self)
        # self.__buttonSignup.clicked.connect(self.handleSignup)

        ########## Assign items to the layouts
        layout1.addWidget(self.__buttonLogin)

        self.setLayout(layout1)


        
class CUMatDesQMainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):

        super(CUMatDesQMainWindow, self).__init__(*args, **kwargs)

        self.center()

        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        # self.setStyleSheet('CUMatDesQMainWindow{background:rgb(0,242,246);}')
        self.setStyleSheet('CUMatDesQMainWindow{background:rgb(59, 175, 218);}')

    def center(self):
        # geometry of the main window
        qr_l = self.frameGeometry()

        # center point of screen
        cp_l = QtWidgets.QDesktopWidget().availableGeometry().center()

        # move rectangle's center point to screen's center point
        qr_l.moveCenter(cp_l)



class CUMatDesQDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        super(CUMatDesQDialog, self).__init__(*args, **kwargs)

        self.center()

        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet('CUMatDesQDialog{background:rgb(59, 175, 218);}')

    def center(self):
        # geometry of the main window
        qr_l = self.frameGeometry()

        # center point of screen
        cp_l = QtWidgets.QDesktopWidget().availableGeometry().center()

        # move rectangle's center point to screen's center point
        qr_l.moveCenter(cp_l)

        # # top left of rectangle becomes top left of window centering it
        # self.move(qr_l.topLeft())


# class fd(CUMatDesQDialog):

#     def __init__(self, *args, **kwargs):
#         super(fd, self).__init__(*args, **kwargs)


class CUMatDesQLineEdit(QtWidgets.QLineEdit):
    
    def __init__(self, *args, **kwargs):
        super(CUMatDesQLineEdit, self).__init__(*args, **kwargs)

        self.setStyleSheet("""
QLineEdit {
    height: 30px;
    font-size: 30px;
    font-family: Helvetica Neue, Helvetica, Arial, sans-serif;
    background: transparent;
    padding: 4px 22px;
    background: white;
    border: 1px solid;
    border-radius: 8px;    
    color: #000000;
}
    """)

class CUMatDesQLabel(QtWidgets.QLabel):
    
    def __init__(self, *args, **kwargs):
        super(CUMatDesQLabel, self).__init__(*args, **kwargs)

        self.setStyleSheet("""
QLabel {
    font-size: 20px;
    font-family: Helvetica Neue, Helvetica, Arial, sans-serif;
    background: transparent;
    padding: 4px 22px;
    color: #FFFFFF;             /* Not sure about this one */
}
    """)


#         QLabel {
#     background: transparent;
#     color: #000000;             /* Not sure about this one */
# }
#     """)


class CUMatDesQPushButton(QtWidgets.QPushButton):
    
    def __init__(self, *args, **kwargs):
        super(CUMatDesQPushButton, self).__init__(*args, **kwargs)

        self.setStyleSheet("""
QPushButton {
    background-color: #FFFFFF;
    color: #000000;
    width: 220px;
    height: 50px;
    font-size: 40px;
    font-family: Helvetica Neue, Helvetica, Arial, sans-serif;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 4px 22px;
}

QPushButton:hover {
    width: 220px;
    height: 50px;
}

QPushButton:pressed {
    background-color: #4A89DC;
    color: #FFFFFF;
}
    """)

    # color: #4A89DC;

#         self.setStyleSheet("""
# QPushButton {
#     background-color: #EC87C0;
#     color: #000000;
#     border: 1px solid transparent;
#     padding: 4px 22px;
# }

# QPushButton:hover {
#     color: #AFBDC4;
# }

# QPushButton:pressed {
#     background-color: #D770AD;
#     color: #FFFFFF;
# }
#     """)

if __name__ == '__main__':

    app_l = QtWidgets.QApplication(sys.argv)

    login_l         = Test()
    # login_l         = fd()
    

    login_l.show()

    sys.exit(app_l.exec_())




# QPushButton {
#     width: 90px;
#     height: 30px;
#     border: {{ _borderWidth }}px solid rgba({{ _borderColor }});
#     border-radius: {{ _borderRadius }}px;
#     color: rgba({{ _textColor }});
#     background-color: rgba({{ _backgroundColor }});
# }
# QPushButton:hover {
#     border: {{ _borderWidth }}px solid rgba({{ _borderColorHover }});
#     border-radius: {{ _borderRadius }}px;
#     color: rgba({{ _textColorHover }});
#     background-color: rgba({{ _backgroundColorHover }});
# }
# QPushButton:pressed {
#     border: {{ _borderWidth + 5 }}px solid rgba({{ _borderColorPressed }});
#     border-radius: {{ _borderRadius }}px;
#     color: rgba({{ _textColorPressed }});
#     background-color: rgba({{ _backgroundColorPressed }});
# }





#     # -*- coding: utf-8 -*-

# # Form implementation generated from reading ui file 'untitled.ui'
# #
# # Created by: PyQt5 UI code generator 5.5.1
# #
# # WARNING! All changes made in this file will be lost!

# from PyQt5 import QtCore, QtGui, QtWidgets

# class Ui_Form(object):
#     def setupUi(self, Form):
#         Form.setObjectName("Form")
#         Form.resize(400, 300)
#         self.Button = Button(Form)
#         self.Button.setGeometry(QtCore.QRect(130, 60, 90, 30))
#         self.Button.setObjectName("Button")

#         self.retranslateUi(Form)
#         QtCore.QMetaObject.connectSlotsByName(Form)

#     def retranslateUi(self, Form):
#         _translate = QtCore.QCoreApplication.translate
#         Form.setWindowTitle(_translate("Form", "Form"))
#         self.Button.setStyleSheet(_translate("Form", "/*QFlat Button Style*/\n"
# "QPushButton {\n"
# "    width: 90px;\n"
# "    height: 30px;\n"
# "    border: 0px solid rgba(255, 255, 255, 0);\n"
# "    border-radius: 4px;\n"
# "    color: rgba(255, 255, 255, 255);\n"
# "    background-color: rgba(150, 122, 220, 255);\n"
# "}\n"
# "QPushButton:hover {\n"
# "    border: 0px solid rgba(255, 255, 255, 0);\n"
# "    border-radius: 4px;\n"
# "    color: rgba(255, 255, 255, 255);\n"
# "    background-color: rgba(172, 146, 236, 255);\n"
# "}\n"
# "QPushButton:pressed {\n"
# "    border: 5px solid rgba(150, 122, 220, 255);\n"
# "    border-radius: 4px;\n"
# "    color: rgba(255, 255, 255, 255);\n"
# "    background-color: rgba(150, 122, 220, 255);\n"
# "}\n"
# "    "))

# import os
# import sys

# ROOTPATH_g = (os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")).split("/Data")[0]
# sys.path.append(ROOTPATH_g + "/Data/Work/UtilSrcCode/QFlat-master")


# from Widgets.Button import Button

# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     Form = QtWidgets.QWidget()
#     ui = Ui_Form()
#     ui.setupUi(Form)
#     Form.show()
#     sys.exit(app.exec_())

