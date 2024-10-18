from PyQt5 import QtWidgets as pqtQtWidgets

from login import Login

class Signup(pqtQtWidgets.QDialog):

    def __init__(self, parent_p=None):

        super(Signup, self).__init__(parent_p)

        ########## Set the layouts
        layoutMain = pqtQtWidgets.QVBoxLayout(self)
        layoutFirstLastName = pqtQtWidgets.QHBoxLayout(self)
        layoutFirstName = pqtQtWidgets.QVBoxLayout(self)
        layoutLastName  = pqtQtWidgets.QVBoxLayout(self)
        layoutEmail = pqtQtWidgets.QVBoxLayout(self)
        layoutPassword = pqtQtWidgets.QVBoxLayout(self)
        layoutConfirmPwd = pqtQtWidgets.QVBoxLayout(self)
        layoutButtons = pqtQtWidgets.QHBoxLayout(self)

        layoutMain.addLayout(layoutFirstLastName)
        layoutFirstLastName.addLayout(layoutFirstName)
        layoutFirstLastName.addLayout(layoutLastName)

        layoutMain.addLayout(layoutEmail)
        layoutMain.addLayout(layoutPassword)
        layoutMain.addLayout(layoutConfirmPwd)
        layoutMain.addLayout(layoutButtons)

        ########## Create items

        self.__labelFirstName = pqtQtWidgets.QLabel("First Name")
        self.__labelLastName = pqtQtWidgets.QLabel("Last Name")

        self.__textFirstName = pqtQtWidgets.QLineEdit(self)
        self.__textLastName = pqtQtWidgets.QLineEdit(self)

        self.__labelEmail = pqtQtWidgets.QLabel("Last Name")
        self.__textEmail = pqtQtWidgets.QLineEdit(self)

        self.__labelPassword = pqtQtWidgets.QLabel("Password")
        self.__textPassword = pqtQtWidgets.QLineEdit(self)
        self.__textPassword.setEchoMode(pqtQtWidgets.QLineEdit.Password)

        self.__labelConfirmPwd = pqtQtWidgets.QLabel("Confirmed Password")
        self.__textConfirmPwd = pqtQtWidgets.QLineEdit(self)
        self.__textConfirmPwd.setEchoMode(pqtQtWidgets.QLineEdit.Password)

        self.__buttonSubmit = pqtQtWidgets.QPushButton("Submit", self)

        ########## Assign items to the layouts
        layoutFirstName.addWidget(self.__labelFirstName)
        layoutFirstName.addWidget(self.__textFirstName)

        layoutLastName.addWidget(self.__labelLastName)
        layoutLastName.addWidget(self.__textLastName)

        layoutEmail.addWidget(self.__labelEmail)
        layoutEmail.addWidget(self.__textEmail)

        layoutPassword.addWidget(self.__labelPassword)
        layoutPassword.addWidget(self.__textPassword)

        layoutConfirmPwd.addWidget(self.__labelConfirmPwd)
        layoutConfirmPwd.addWidget(self.__textConfirmPwd)

        layoutButtons.addWidget(self.__buttonSubmit)

    def closeEvent(self, event):
    # Clean up before exiting.
        # event.accept() # let the window close

        # self.__login.exec_()


        self.close()
        self.__Login = Login()
        self.__Login.show()
        self.__Login.exec_()        


    def handleSubmit(self):
        pass