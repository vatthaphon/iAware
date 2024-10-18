from PyQt5 import QtWidgets as pqtQtWidgets

from signup import Signup

class Login(pqtQtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)

        self.__label_username = pqtQtWidgets.QLabel("Email Address")

        self.__label_password = pqtQtWidgets.QLabel("Password")

        self.__textName = pqtQtWidgets.QLineEdit(self)
        self.__textPass = pqtQtWidgets.QLineEdit(self)
        self.__textPass.setEchoMode(pqtQtWidgets.QLineEdit.Password)

        self.__buttonLogin = pqtQtWidgets.QPushButton('Login', self)
        self.__buttonLogin.clicked.connect(self.handleLogin)

        self.__buttonSignup = pqtQtWidgets.QPushButton('Sign up', self)
        self.__buttonSignup.clicked.connect(self.handleSignup)

        layout1 = pqtQtWidgets.QVBoxLayout(self)
        layout1.addWidget(self.__label_username)
        layout1.addWidget(self.__textName)
        layout1.addWidget(self.__label_password)
        layout1.addWidget(self.__textPass)

        layout2 = pqtQtWidgets.QHBoxLayout(self)
        layout1.addLayout(layout2)

        layout2.addWidget(self.__buttonLogin)
        layout2.addWidget(self.__buttonSignup)

    def handleLogin(self):
        if (self.__textName.text() == 'foo' and
            self.__textPass.text() == 'bar'):
            self.accept()
        else:
            pqtQtWidgets.QMessageBox.warning(self, 'Error', 'Bad user or password')

    def handleSignup(self):
        # pqtQtWidgets.QMessageBox.warning(self, 'Error', 'Signup')

        self.close()
        self.__Signup = Signup()
        self.__Signup.show()
        self.__Signup.exec_()
