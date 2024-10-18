import cv2
import numpy as np
import os
import pickle
import sys

from pathlib import Path
from PyQt5 import QtGui as pqtQtGui
from PyQt5 import QtWidgets as pqtQtWidgets
from PyQt5 import QtCore as pqtQtCore
from PyQt5.QtCore import Qt

ROOTPATH_g = (os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")).split("/Data")[0]

sys.path.append(ROOTPATH_g + "/Data/Work/UtilSrcCode/Python_JSON")
from webservice import record, signout, signup, signin

sys.path.append(ROOTPATH_g + "/Data/Work/UtilSrcCode/python-FaceRecog")
from AV_facerecog import AV_cmp_FacesVsFace, AV_Webcam, AV_WebCamFaceDetectionWidget, AV_get_face_embeddings_from_image, AV_draw_face_rectangles

from PyQt5CUMatDesComps import *

token_g = None

class Login(CUMatDesQDialog):
    def __init__(self, main_p):

        super(Login, self).__init__()

        self.__main = main_p

        ########## Set the layouts
        layout1 = pqtQtWidgets.QVBoxLayout(self)
        layout2 = pqtQtWidgets.QHBoxLayout(self)        

        ########## Create items
        self.__label_username = CUMatDesQLabel("Email Address")
        self.__label_password = CUMatDesQLabel("Password")

        self.__textName = CUMatDesQLineEdit(self)
        self.__textPass = CUMatDesQLineEdit(self)
        self.__textPass.setEchoMode(pqtQtWidgets.QLineEdit.Password)

        self.__buttonLogin = CUMatDesQPushButton('Login', self)
        self.__buttonLogin.clicked.connect(self.handleLogin)

        self.__buttonFaceLogin = CUMatDesQPushButton('Face Login', self)
        self.__buttonFaceLogin.clicked.connect(self.handleFaceLogin)

        self.__buttonSignup = CUMatDesQPushButton('Sign up', self)
        self.__buttonSignup.clicked.connect(self.handleSignup)

        ########## Assign items to the layouts
        layout1.addWidget(self.__label_username)
        layout1.addWidget(self.__textName)
        layout1.addWidget(self.__label_password)
        layout1.addWidget(self.__textPass)

        layout1.addLayout(layout2)

        layout2.addWidget(self.__buttonLogin)
        layout2.addWidget(self.__buttonFaceLogin)        
        layout2.addWidget(self.__buttonSignup)

        self.setLayout(layout1)


    def handleLogin(self):
        global token_g
        
        operation_code_l, token_g = signin(email=self.__textName.text(), password=self.__textPass.text())

        if operation_code_l:
            self.__main.hideLogin()
            self.__main.showMainUI()
        else:
            pqtQtWidgets.QMessageBox.warning(self, 'Error', token_g)

    def handleFaceLogin(self):
        self.__main.hideLogin()
        self.__main.showLoginFaceID()

    def callback_FaceLogin(self):
        print("FinishFaceLogin")

    def handleSignup(self):
        self.__main.hideLogin()
        self.__main.showSignup()

    def signout(self):
        global token_g

        operation_code_l, msg_l = signout(token=token_g)

        if operation_code_l:
            token_g = None

        return operation_code_l, msg_l

    def exit(self):
        self.close()     

    def closeEvent(self, event):
    # Clean up before exiting.
        event.ignore() # let the window close

        self.__main.exit()

class Signup(CUMatDesQDialog):

    def __init__(self, main_p):

        super(Signup, self).__init__()

        self.__main = main_p

        ########## Set the layouts
        layoutMain = pqtQtWidgets.QVBoxLayout(self)
        layoutFirstLastName = pqtQtWidgets.QHBoxLayout(self)
        layoutFirstName = pqtQtWidgets.QVBoxLayout(self)
        layoutLastName  = pqtQtWidgets.QVBoxLayout(self)
        layoutEmail = pqtQtWidgets.QVBoxLayout(self)
        layoutPhoneNo = pqtQtWidgets.QVBoxLayout(self)
        layoutPassword = pqtQtWidgets.QVBoxLayout(self)
        layoutConfirmPwd = pqtQtWidgets.QVBoxLayout(self)
        layoutButtons = pqtQtWidgets.QHBoxLayout(self)

        layoutMain.addLayout(layoutFirstLastName)
        layoutFirstLastName.addLayout(layoutFirstName)
        layoutFirstLastName.addLayout(layoutLastName)

        layoutMain.addLayout(layoutEmail)
        layoutMain.addLayout(layoutPhoneNo)
        layoutMain.addLayout(layoutPassword)
        layoutMain.addLayout(layoutConfirmPwd)
        layoutMain.addLayout(layoutButtons)

        ########## Create items
        self.__labelFirstName = pqtQtWidgets.QLabel("First Name")
        self.__textFirstName = pqtQtWidgets.QLineEdit(self)
        
        self.__labelLastName = pqtQtWidgets.QLabel("Last Name")
        self.__textLastName = pqtQtWidgets.QLineEdit(self)

        self.__labelEmail = pqtQtWidgets.QLabel("Email")
        self.__textEmail = pqtQtWidgets.QLineEdit(self)

        self.__labelPhoneNo = pqtQtWidgets.QLabel("Phone No.")
        self.__textPhoneNo = pqtQtWidgets.QLineEdit(self)

        self.__labelPassword = pqtQtWidgets.QLabel("Password")
        self.__textPassword = pqtQtWidgets.QLineEdit(self)
        self.__textPassword.setEchoMode(pqtQtWidgets.QLineEdit.Password)

        self.__labelConfirmPwd = pqtQtWidgets.QLabel("Confirmed Password")
        self.__textConfirmPwd = pqtQtWidgets.QLineEdit(self)
        self.__textConfirmPwd.setEchoMode(pqtQtWidgets.QLineEdit.Password)

        self.__buttonSubmit = pqtQtWidgets.QPushButton("Submit", self)
        self.__buttonSubmit.clicked.connect(self.handleSubmit)

        # self.__buttonFace = pqtQtWidgets.QPushButton("Face", self)
        # self.__buttonFace.clicked.connect(self.handleFace)


        ########## Assign items to the layouts
        layoutFirstName.addWidget(self.__labelFirstName)
        layoutFirstName.addWidget(self.__textFirstName)

        layoutLastName.addWidget(self.__labelLastName)
        layoutLastName.addWidget(self.__textLastName)

        layoutEmail.addWidget(self.__labelEmail)
        layoutEmail.addWidget(self.__textEmail)

        layoutPhoneNo.addWidget(self.__labelPhoneNo)
        layoutPhoneNo.addWidget(self.__textPhoneNo)

        layoutPassword.addWidget(self.__labelPassword)
        layoutPassword.addWidget(self.__textPassword)

        layoutConfirmPwd.addWidget(self.__labelConfirmPwd)
        layoutConfirmPwd.addWidget(self.__textConfirmPwd)

        layoutButtons.addWidget(self.__buttonSubmit)
        # layoutButtons.addWidget(self.__buttonFace)

        self.setLayout(layoutMain)

    # def handleFace(self):
    #     self.__main.hideSignup()
    #     self.__main.showSignupFaceID()

    def handleSubmit(self):

        if not (self.__textPassword.text() == self.__textConfirmPwd.text()):
            pqtQtWidgets.QMessageBox.warning(self, 'Error', "Mismatched confirmed password.")            
        else:
            full_name_l = self.__textFirstName.text() + " " + self.__textLastName.text()
            operation_code_l, msg_l = signup(full_name=full_name_l, email=self.__textEmail.text(), password=self.__textPassword.text(), phone_no=self.__textPhoneNo.text())

            # operation_code_l = True
            if operation_code_l:                
                # pqtQtWidgets.QMessageBox.information(self, 'Success', "Signup Success.")

                identity_l = dict()
                identity_l["full_name"] = full_name_l
                identity_l["email"] = self.__textEmail.text()
                identity_l["password"] = self.__textPassword.text()

                self.__main.hideSignup()
                self.__main.showSignupFaceID(identity_p=identity_l)
            else:
                pqtQtWidgets.QMessageBox.warning(self, 'Error', msg_l)

    def exit(self):
        self.close()

    def closeEvent(self, event):
    # Clean up before exiting.

        event.ignore() # let the window close

        # self.setVisible(False)
        # self.__login.exec_()

        # self.__main.exit()

        # self.close()
        # self.__Login = Login()
        # self.__Login.setVisible(True)
        # self.__Login.exec_()        

        self.__main.showLogin()
        self.__main.hideSignup()

class LoginFaceID(CUMatDesQDialog):

    def __init__(self, main_p):

        super(LoginFaceID, self).__init__()

        self.__main = main_p
        self.__N_features = 128
        self.__FaceIDsManager = FaceIDsManager(self.__main.get_abs_path_all_faces())

        self.init()

        ########## Set the layouts
        layoutMain_l = pqtQtWidgets.QVBoxLayout(self)

        ########## Create items
        self.__face_detection = AV_WebCamFaceDetectionWidget(where2sendFace_p=self.processFaces)

        layoutMain_l.addWidget(self.__face_detection)

        self.setLayout(layoutMain_l)

        self.resize(1280, 720) # the width and height is obtained from width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.center()        
    
    def init(self):
        self.__N_faces = 2
        self.__identity = None
        self.__isStartRecording = False        
        self.__faces_features = []
        self.__MaxFrameTested = 10

    def start_streaming(self):
        self.init()
        self.__face_detection.start_streaming()        

    def stop_streaming(self):
        self.__isStartRecording = False
        self.__face_detection.stop_streaming()        

    def processFaces(self, face_encodings_p :list):

        if len(face_encodings_p) == 0:
            #TODO: What to do if no face detected.
            print("LoginFaceID: No face detected")
            pass
        elif len(face_encodings_p) > 1:
            #TODO: What to do if there are more than one faces.
            print("LoginFaceID: Too many detected faces = " + str(len(face_encodings_p)))
            pass
        else:
            ids_ListOfDicts_l = self.__FaceIDsManager.authen_FaceIDs(face_encodings_p[0])

            print(ids_ListOfDicts_l)

            if len(ids_ListOfDicts_l) > 0:
                self.__main.hideLoginFaceID()
                pqtQtWidgets.QMessageBox.information(self, 'Success', "Hi!!! " + ids_ListOfDicts_l[0]["email"] + ". How are you today?")
                self.__main.showMainUI()
            else:
                if self.__MaxFrameTested <= 0:

                    self.__main.hideLoginFaceID()
                    pqtQtWidgets.QMessageBox.warning(self, 'Error', "Not detected face.")
                    self.__main.showLogin()
                    
                else:
                    self.__MaxFrameTested = self.__MaxFrameTested - 1

    def exit(self):

        self.stop_streaming()        
        self.close()

    def closeEvent(self, event):

        event.ignore() # do not let the window close

        self.stop_streaming()        
        self.__main.hideLoginFaceID()
        self.__main.showLogin()

class SignupFaceID(CUMatDesQDialog):

    def __init__(self, main_p):

        super(SignupFaceID, self).__init__()

        self.__main = main_p
        self.__N_features = 128
        self.__FaceIDsManager = FaceIDsManager(self.__main.get_abs_path_all_faces())

        self.init()

        ########## Set the layouts
        layoutMain_l = pqtQtWidgets.QVBoxLayout(self)

        ########## Create items
        self.__face_detection = AV_WebCamFaceDetectionWidget(where2sendFace_p=self.processFaces)
        self.__buttonStart = pqtQtWidgets.QPushButton("Start Recording")
        self.__buttonStart.clicked.connect(self.handleStart)

        layoutMain_l.addWidget(self.__face_detection)
        layoutMain_l.addWidget(self.__buttonStart)

        self.setLayout(layoutMain_l)

        self.resize(1280, 720) # the width and height is obtained from width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.center()
    
    def init(self):
        self.__N_faces = 2
        self.__identity = None
        self.__isStartRecording = False        
        # self.__faces_features = np.ndarray(shape=(self.__N_faces, self.__N_features), dtype=float)
        self.__faces_features = []

    def start_streaming(self):
        self.init()
        self.__face_detection.start_streaming()        

    def stop_streaming(self):
        self.__isStartRecording = False
        self.__face_detection.stop_streaming()        

    def processFaces(self, face_encodings_p :list):
        if self.__isStartRecording:

            if len(face_encodings_p) == 0:
                #TODO: What to do if no face detected.
                print("SignupFaceID: No face detected")
                pass
            elif len(face_encodings_p) > 1:
                #TODO: What to do if there are more than one faces.
                print("SignupFaceID: Too many detected faces = " + str(len(face_encodings_p)))
                pass
            else:
                print("Recording: " + str(self.__Cnt_N_faces))

                self.__Cnt_N_faces = self.__Cnt_N_faces - 1

                # self.__faces_features[self.__Cnt_N_faces] = face_encodings_p[0]

                self.__faces_features.append(face_encodings_p[0])

                if self.__Cnt_N_faces == 0:
                    self.__isStartRecording = False

                    self.__FaceIDsManager.append_FaceIDs(identity_p=self.__identity, faces_features_p=self.__faces_features)
                    # faces_features_l = np.copy(self.__faces_features)
                    # self.__callback_face_features(faces_features_p=faces_features_l)                

                    self.__main.hideSignupFaceID()
                    self.__main.showLogin()

    def setIdentity(self, identity_p):
        """
        Params:
            identity_p :    It is a Dictionary.
        """
        self.__identity = identity_p

    def handleStart(self):

        print("SignupFaceID: Start recording.")

        self.__Cnt_N_faces = self.__N_faces
        self.__isStartRecording = True

    def exit(self):

        self.stop_streaming()        
        self.close()

    def closeEvent(self, event):

        event.ignore() # do not let the window close

        self.stop_streaming()        
        self.__main.hideSignupFaceID()
        self.__main.showSignup()


class FaceIDsManager():

    def __init__(self, abs_path_FaceIDs_dat_p):

        self.abs_path_FaceIDs_dat = abs_path_FaceIDs_dat_p

    def append_FaceIDs(self, identity_p, faces_features_p):
        """
        If the identity specified by email is already stored. It will update the corresponding information. Beware, one FaceID could be linked to
        multiple identities due to multiple emails.

        Params:
            identity_p          : it has a datatype of dict().
            faces_features_p    : it has a datatype of np.ndarray[the number of faces per one identity, 128 facial features]
        """

        if os.path.isfile(self.abs_path_FaceIDs_dat):

            with open(self.abs_path_FaceIDs_dat, "rb") as fp:
                all_faces_features_l, all_faces_identity_l = pickle.load(fp)
                fp.close()
        else:

            all_faces_features_l = dict()
            all_faces_identity_l = dict()

        id_l = identity_p["email"]

        if id_l in all_faces_identity_l:
            print("FaceIDsManager: Update info. of " + id_l)

        all_faces_features_l[id_l] = faces_features_p
        all_faces_identity_l[id_l] = identity_p

        with open(self.abs_path_FaceIDs_dat, "wb+") as fp:
            pickle.dump([all_faces_features_l, all_faces_identity_l], fp)
            fp.close()

        return True, None

    def authen_FaceIDs(self, face_features_p):

        if os.path.isfile(self.abs_path_FaceIDs_dat):

            with open(self.abs_path_FaceIDs_dat, "rb") as fp:
                all_faces_features_l, all_faces_identity_l = pickle.load(fp)
                fp.close()

            matching_list_l = [False]*len(all_faces_identity_l)

            ids_ListOfDicts_l = []
            for id_l in all_faces_identity_l.keys():
                
                if len(all_faces_features_l[id_l]) == np.sum(AV_cmp_FacesVsFace(all_faces_features_l[id_l], face_features_p)):
                    ids_ListOfDicts_l.append(all_faces_identity_l[id_l])

            return ids_ListOfDicts_l
        else:
            return []
