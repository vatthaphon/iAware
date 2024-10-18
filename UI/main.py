import sys

from mainUIMin import run as mainUIRun
from pathlib import Path
from PyQt5 import QtWidgets as pqtQtWidgets
from PyQt5.QtCore import Qt
from uis import LoginFaceID, Login, Signup, SignupFaceID


class Window(pqtQtWidgets.QMainWindow):

    def __init__(self, parent=None):

        super(Window, self).__init__(parent)

        self.__app = None

        self.__loginFaceID = None
        self.__login = None
        self.__signup = None
        self.__mainUI = None
        self.__signupFaceID = None

    def setChilds(self, loginFaceID_p, login_p, signup_p, mainUI_p, signupFaceID_p):
        self.__loginFaceID = loginFaceID_p
        self.__login = login_p
        self.__signup = signup_p
        self.__mainUI = mainUI_p
        self.__signupFaceID = signupFaceID_p

    def setParent(self, app_p):
        self.__app = app_p

    # Login UI
    def showLogin(self):
        self.__login.show()
    def hideLogin(self):
        self.__login.hide()
    def signout(self):
        operation_code_l, msg_l = self.__login.signout()

        return operation_code_l, msg_l
    def closeLogin(self):
        self.__login.exit()

    # LoginFaceID UI
    def showLoginFaceID(self):
        # self.__signupFaceID.setcallback_FaceLogin(callback_FaceLogin_p=callback_FaceLogin_p)
        self.__loginFaceID.start_streaming()
        self.__loginFaceID.show()
    def hideLoginFaceID(self):
        self.__loginFaceID.stop_streaming()
        self.__loginFaceID.hide()
    def closeLoginFaceID(self):
        self.__loginFaceID.exit()        

    # Signup UI
    def showSignup(self):
        self.__signup.show()
    def hideSignup(self):
        self.__signup.hide()
    def closeSignup(self):
        self.__signup.exit()

    # SignupFaceID UI
    def showSignupFaceID(self, identity_p=None):
        self.__signupFaceID.start_streaming()
        self.__signupFaceID.setIdentity(identity_p=identity_p)        
        self.__signupFaceID.show()
    def hideSignupFaceID(self):
        self.__signupFaceID.stop_streaming()
        self.__signupFaceID.hide()
    def closeSignupFaceID(self):
        self.__signupFaceID.exit()


    # EEG UI
    def showMainUI(self):
        self.__mainUI.run()
        self.__mainUI.show()
    def hideMainUI(self):
        self.__mainUI.stop()
        self.__mainUI.hide()
    def closeMainUI(self):
        self.__mainUI.exit()


    def get_abs_path_all_faces(self):
        return str(Path("/Volumes/Data/Work/FIRST/EEG/UI/iAwareUI/all_faces.dat").resolve())


    def exit(self):
        self.closeSignup()
        self.closeLogin()
        self.closeMainUI()
        self.closeSignupFaceID()
        self.__app.quit()
        sys.exit()

if __name__ == '__main__':    
    app_l = pqtQtWidgets.QApplication(sys.argv)

    # Main window
    window_l    = Window()

    # Child windows
    login_l         = Login(main_p=window_l)
    loginFaceID_l   = LoginFaceID(main_p=window_l)
    signup_l        = Signup(main_p=window_l)
    mainUI_l        = mainUIRun(main_p=window_l)
    signupFaceID_l  = SignupFaceID(main_p=window_l)

    window_l.setChilds(loginFaceID_p=loginFaceID_l, login_p=login_l, signup_p=signup_l, mainUI_p=mainUI_l, signupFaceID_p=signupFaceID_l)

    window_l.setParent(app_p=app_l)

    window_l.hideLoginFaceID()
    window_l.hideSignup()
    window_l.hideMainUI()
    window_l.hideSignupFaceID()
    window_l.showLogin()    
    # login_l.exec_()
    # signup_l.exec_()
    # if login_l.exec_() == pqtQtWidgets.QDialog.Accepted:
    #     # signup_l.exec_()
    #     window_l.showSignup()
        # window_l.show()
    sys.exit(app_l.exec_())