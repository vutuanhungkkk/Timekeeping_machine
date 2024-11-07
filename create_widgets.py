import numpy as np
from tkinter import *
import multiprocessing
import serial
from tkcalendar import Calendar
import os
import datetime
import queue
import time
from yolov8 import YOLOv8_face
from FaceAntiSpoofing import AntiSpoof
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from yolov8 import increased_crop
import os
import cv2
import torch
import threading
from torchvision import transforms as trans
from face_model import MobileFaceNet, l2_norm
import adafruit_fingerprint
import socket
# for jetson_use
# import nanocamera as nano


def init_app(self,root,detect_model,face_detector,anti_spoof_detector,test_transform,device,vid):
    self.root = root
    #self.root.attributes("-fullscreen", True)
    #self.root.overrideredirect(True)
    self.task_category = "None"
    self.allow_training = False
    self.user_image_dir = None
    self.card_input =0
    self.train_model()
    self.edit_mode_var = tk.BooleanVar(value=False)
    self.select_all_var = tk.BooleanVar(value=False)
    self.root.bind('p', self.go_to_database_frame)
    self.dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    print(screen_width)
    print(screen_height)
    self.resolution_height = 600
    self.resolution_width = 1024
    self.root.geometry(f"{self.resolution_width}x{self.resolution_height}")
    self.choose_check_inout_background_image = self.convert_image_for_tkinter("icon_images/theme2.jpg",(int(self.resolution_width / 2), self.resolution_height))
    self.insert_card_image = self.convert_image_for_tkinter("icon_images/fingerprint.jpg",(self.resolution_width, 6 * int(self.resolution_height / 7)))
    self.database_icon_image = self.convert_image_for_tkinter("icon_images/database.png", (int((self.resolution_width / 5) * (4 / 3)), int(self.resolution_height / 4)))
    self.register_face_image = self.convert_image_for_tkinter("icon_images/face.jpg",(int(self.resolution_width / 4), int(self.resolution_height / 4)))
    self.register_id_image = self.convert_image_for_tkinter("icon_images/fingerprint.jpg",(int(self.resolution_width / 4),int(self.resolution_height / 4)))
    self.dataset_image = self.convert_image_for_tkinter("icon_images/dataset.jpg", (self.resolution_width//2, (self.resolution_height -50)//3))
    self.register_image = self.convert_image_for_tkinter("icon_images/register.jpg", (self.resolution_width//2, (self.resolution_height -50)//3))
    self.user_log_image = self.convert_image_for_tkinter("icon_images/user_log.jpg", (self.resolution_width//2, (self.resolution_height -50)//3))
    self.system_image = self.convert_image_for_tkinter("icon_images/system.jpg", (self.resolution_width//2, (self.resolution_height -50)//3))
    #camera
    self.vid =  vid
    ## database ##
    self.dataset_conn = sqlite3.connect('database/dataset.db')
    self.dataset_cursor = self.dataset_conn.cursor()
    self.timekeeping_conn = sqlite3.connect('database/timekeeping.db')
    self.timekeeping_cursor = self.timekeeping_conn.cursor()
    self.web_conn = sqlite3.connect('database/web.db')
    self.web_cursor = self.web_conn.cursor()
    self.web_cursor.execute('SELECT Username, Password FROM web LIMIT 1')
    web_info = self.web_cursor.fetchone()
    self.username = web_info[0]
    self.password = web_info[1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "Unable to get IP"
    finally:
        s.close()
    self.ip_address = "http://" + ip_address + ":5000"
    self.department_conn = sqlite3.connect('database/department.db')
    self.department_cursor = self.department_conn.cursor()
    self.department_cursor.execute('SELECT department FROM departments')
    self.user_departments = [row[0] for row in self.department_cursor.fetchall()]
    ##fingerprint
    uart = serial.Serial('/dev/ttyTHS1', 57200, timeout=2)  # for jetson_use
    self.finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
    self.finger.empty_library()
    self.fingerprint_buffer = 0
    self.fingerprint_mismatch = False
    self.fingerprint_already_exist = False
    self.get_card_allow = False
    ###face_recognition
    self.left_face_count = 0
    self.right_face_count = 0
    self.left_captures = []
    self.right_captures = []
    self.frame_capture = []
    self.boxes_capture = []
    self.prediction_queue = queue.Queue()
    self.prediction_thread = None
    self.get_face_allow = False
    self.check_user_allow = False
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.face_detector = face_detector
    self.anti_spoof_detector = anti_spoof_detector
    self.detect_model = detect_model
    self.test_transform = test_transform
    self.load_models_allow = True
    self.check_confirm_add_user = False
    self.open_camera("None","None","None")

def create_widgets(self):
    #choose_check_inout_frame
    self.choose_check_inout_frame = Frame(self.root,height=self.resolution_height,width= self.resolution_width,bg='gray')
    self.choose_check_inout_background_label = Label(self.choose_check_inout_frame, image = self.choose_check_inout_background_image)
    self.please_choose_check_inout_label = Label(self.choose_check_inout_frame,text = "PLEASE  CHOOSE",font=('Arial',40),bg='gray',fg='white')
    self.check_in_button = Button(self.choose_check_inout_frame,text = "CHECK IN",font=('Arial',40),bg='white',fg='black',command=lambda:self.switch_frame(self.choose_face_or_card_frame,self.choose_check_inout_frame,"check in"))
    self.check_out_button = Button(self.choose_check_inout_frame, text="CHECK OUT", font=('Arial', 40), bg='white', fg='black',command=lambda:self.switch_frame(self.choose_face_or_card_frame,self.choose_check_inout_frame,"check out"))
    #self.go_to_insert_admin_ID_button = Button(self.choose_check_inout_frame, text=" → Go to setting ", font=('Arial', 25), bg='white', fg='black',relief='flat',command= lambda: self.card_activities("check", "admin","None"))
    self.go_to_insert_admin_ID_button = Button(self.choose_check_inout_frame, text=" → Go to setting ", font=('Arial', 25), bg='white', fg='black',relief='flat',command= self.go_to_database_frame)
    #authentication_frame
    self.authentication_frame = Frame(self.root,height=self.resolution_height,width= self.resolution_width,bg='gray')
    self.back_to_check_inout_button = Button(self.authentication_frame, text="CANCEL", font=('Arial', 20),bg='white', fg='black', command=lambda: self.switch_frame(self.choose_check_inout_frame,self.authentication_frame,"None"))
    self.check_inout_confirmation_button = Button(self.authentication_frame, text="CONFIRM CHECK", font=('Arial', 20),bg='white', fg='black',command=lambda: self.update_timekeeping_db(self.task_category))
    self.authentication_guidline_label = Label(self.authentication_frame, text="Please authenticate", font=('Arial', 30), bg='gray', fg='white')
    self.authentication_guidline_label.place(x=self.resolution_width // 2 - self.authentication_guidline_label.winfo_reqwidth() // 2, y=0)
    self.face_detected_authentication_frame = LabelFrame(self.authentication_frame,width=int(self.resolution_width/2),height=int((6/7)*self.resolution_height),text="USER FACE",relief='ridge',font=('Arial', 20),bd=10,labelanchor="n")
    self.face_detected_authentication_label = Label(self.face_detected_authentication_frame, font=('Arial', 30),fg='black')
    self.information_authentication_frame = LabelFrame(self.authentication_frame, width=int(self.resolution_width/2),height=int((6/7)*self.resolution_height),text="USER INFORMATION",relief='ridge',font=('Arial', 20),bd=10,labelanchor="n")
    self.name_authentication_label = Label(self.information_authentication_frame, text="Name:", font=('Arial', 30),fg='black')
    self.id_authentication_label = Label(self.information_authentication_frame, text="ID:", font=('Arial', 30),fg='black')
    self.time_authentication_label = Label(self.information_authentication_frame, text="Time:", font=('Arial', 30),fg='black')
    self.department_authentication_label = Label(self.information_authentication_frame, text="Department:", font=('Arial', 30),fg='black')

    # choose_face_or_card_frame
    self.choose_face_or_card_frame = Frame(self.root, height=self.resolution_height, width=self.resolution_width, bg='gray')
    self.face_button = Button(self.choose_face_or_card_frame, text="  FACE  ", font=('Arial', 40), image=self.register_face_image, compound=LEFT,command=lambda:self.face_activities("check", "user","None"))
    self.card_button = Button(self.choose_face_or_card_frame, text=" FINGER ", font=('Arial', 40), image=self.register_id_image, compound=LEFT,command=lambda:self.card_activities("check", "user","None"))
    self.cancel_choose_face_or_card_button = Button(self.choose_face_or_card_frame, text="CANCEL", font=('Arial', 20), bg='white', fg='black',command=lambda: self.switch_frame(self.choose_check_inout_frame,self.choose_face_or_card_frame,"None"))
    self.face_button.place(x=0, y=self.cancel_choose_face_or_card_button.winfo_reqheight(), width=self.resolution_width // 2, height=self.resolution_height)
    self.card_button.place(x=self.resolution_width // 2,  y=self.cancel_choose_face_or_card_button.winfo_reqheight(), width=self.resolution_width // 2, height=self.resolution_height)
    self.cancel_choose_face_or_card_button.place(x=0, y=0)

    #### register_frame
    self.current_entry = None
    self.register_user_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray25')
    self.register_title_label = Label(self.register_user_frame, text=' ID :  ', font=('Arial', 35), bg='gray25',fg='white')
    self.register_name_label = Label(self.register_user_frame, text='Name:', font=('Arial', 35), bg='grey25', fg='white')
    self.register_department_label = Label(self.register_user_frame, text='Department:', font=('Arial', 35), bg='grey25', fg='white')
    self.register_department_combobox = Button(self.register_user_frame,text="Select Department",bg="white",font=('Arial', 20) , command=lambda : self.show_combbobox_value_frame(values=self.user_departments,frame = self.register_user_frame,task="department"))
    self.register_name_entry = Button(self.register_user_frame, font=('Arial', 15), bg='white',command=lambda: self.keyboard(self.register_name_entry,self.register_user_frame))
    self.register_face_button = Button(self.register_user_frame, text=" Register Face ",bg="white", font=('Arial', 30),image=self.register_face_image, compound=LEFT, command=lambda:self.face_activities("register", "None",self.task_category))
    self.register_card_button = Button(self.register_user_frame, text=" Register Card ",bg="white" ,font=('Arial', 30),image=self.register_id_image, compound=LEFT, command=lambda:self.card_activities("register", "None",self.task_category))
    self.cancel_register_button = Button(self.register_user_frame, text="CANCEL", font=('Arial', 30), bg='white', fg='black',command=lambda: self.ask_to_confirm_action("None", self.register_user_frame,self.register_content_frame))
    self.confirm_register_button = Button(self.register_user_frame, text="CONFIRM", font=('Arial', 30), bg='white',fg='black',command=lambda: self.update_database_db(self.task_category),state=DISABLED)
    self.create_department_button = Button(self.register_user_frame, text="Create department", font=('Arial', 15), bg='white', fg='black',command=lambda: self.keyboard(self.create_department_button,self.register_user_frame))
    self.create_department_button.place(x=self.resolution_width - self.create_department_button.winfo_reqwidth() - 10,y=40 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight())

    #### keyboard_frame
    self.caps_lock_on = False
    self.buttons = {}
    self.keyboard_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='grey')
    self.keyboard_box = Button(self.keyboard_frame, width=150, border=7, font=("Courier", 20))
    self.keyboard_box.place(x=10, y=0, width=self.resolution_width - 20, height=self.resolution_height // 10)
    keyboard_buttons = [('0', 1, 0), ('1', 1, 1), ('2', 1, 2), ('3', 1, 3), ('4', 1, 4), ('5', 1, 5), ('6', 1, 6),('7', 1, 7), ('8', 1, 8), ('9', 1, 9), ('h', 2, 0), ('w', 2, 1), ('e', 2, 2), ('r', 2, 3),('t', 2, 4), ('y', 2, 5), ('u', 2, 6), ('i', 2, 7), ('o', 2, 8), ('p', 2, 9),
                        ('a', 3, 0), ('s', 3, 1), ('d', 3, 2), ('f', 3, 3), ('g', 3, 4), ('h', 3, 5), ('j', 3, 6),('k', 3, 7), ('l', 3, 8), ('z', 4, 0), ('x', 4, 1), ('c', 4, 2), ('v', 4, 3), ('b', 4, 4),
                        ('n', 4, 5), ('m', 4, 6),('Space', 5, 2, lambda: self.handle_button_click(' ')), ('Capslock', 4, 7, self.toggle_caps_lock),('Del', 3, 9, lambda: self.handle_button_click('Del')), ('.', 5, 0), ('@', 5, 1),('Done', 5, 8, self.confirm_keyboard)]
    for btn in keyboard_buttons:
        text, row, col = btn[:3]
        cmd = btn[3] if len(btn) > 3 else lambda t=text.strip(): self.handle_button_click(t)
        button = Button(self.keyboard_frame, text=text, font=("Courier", 22), command=cmd, background='grey25',foreground='white')
        if text in ['Capslock', 'Space', 'Del', 'Done']:
            button.place(x=col * (self.resolution_width // 10), y=row * self.resolution_height // 6, width=(self.resolution_width // 10) * (3 if text == 'Capslock' else 6 if text == 'Space' else 2 if text == 'Done' else 1),height=self.resolution_height // 6)
        else:
            button.place(x=col * (self.resolution_width // 10), y=row * self.resolution_height // 6,width=(self.resolution_width // 10), height=self.resolution_height // 6)
            self.buttons[text] = button

    #### card_activities_frame
    self.card_activities_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.insert_card_background_label = Label(self.card_activities_frame, image=self.insert_card_image)
    self.insert_card_guidline_label = Label(self.card_activities_frame, text='Please insert your card to the reader',font=('Arial', 30), bg='gray', fg='white')
    self.cancel_card_activities_button = Button(self.card_activities_frame, text='CANCEL', font=('Arial', 25), bg='white',fg='black', command=lambda:self.cancel_card_activities("None","None"))

    ###face_activities_frame
    self.face_activities_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.register_face_guidline_label = Label(self.face_activities_frame, text='Finding face....',font=('Arial', 30), bg='gray', fg='white')
    self.camera_frame = Frame(self.face_activities_frame, width=self.resolution_width, height=6 * (self.resolution_height // 7),bg='black')
    self.camera_label = Label(self.camera_frame, bg='black', width=self.resolution_width, height=6 * (self.resolution_height // 7))
    self.cancel_face_activities_button = Button(self.face_activities_frame, text='CANCEL', font=('Arial', 25), bg='white',fg='black', command = lambda:self.cancel_face_activities("None","None"))
    self.take_face_confirmation_button = Button(self.face_activities_frame, text='TAKE', font=('Arial', 30), bg='white',fg='black', command=lambda: self.check_user("check","user",self.task_category))
    self.retake_face_confirmation_button = Button(self.face_activities_frame, text="RETAKE", font=('Arial', 30),bg='white', fg='black',command=lambda: self.face_activities("check","user",self.task_category))
    #for jetson_use

    #setting_frame
    self.setting_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='grey')

    ###database_frame
    self.database_content_select_button = Button(self.setting_frame,image = self.dataset_image,compound='top', text='DATABASE', font=('Arial', 18),bg='gray', fg='black', state=NORMAL,command=lambda:self.switch_frame(self.database_content_frame, self.setting_frame,"None"), borderwidth=0)
    self.register_content_select_button = Button(self.setting_frame,image = self.register_image,compound='top', text='REGISTER', font=('Arial', 18),bg='gray', fg='black', state=NORMAL,command=lambda:self.switch_frame(self.register_content_frame, self.setting_frame,"None"),borderwidth=0)
    self.user_log_content_select_button = Button(self.setting_frame,image = self.user_log_image,compound='top', text="USERS LOG", font=('Arial', 18),bg='gray', fg='black', state=NORMAL,command = lambda:self.switch_frame(self.user_log_content_frame, self.setting_frame,"None"),borderwidth=0)
    self.info_content_select_button = Button(self.setting_frame,image = self.system_image,compound='top', text='SYSTEM INFO', font=('Arial', 18),bg='gray', fg='black', state=NORMAL, borderwidth=0,command= lambda:self.switch_frame(self.info_content_frame, self.setting_frame,"None"))
    self.back_to_check_inout_from_database_button = Button(self.setting_frame, text='  BACK  ', font=('Arial', 20),bg='white', fg='black',command= lambda: self.switch_frame(self.choose_check_inout_frame,self.setting_frame,"None"))
    self.database_content_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height,bg='gray25')
    self.register_content_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height,bg='gray25')
    self.user_log_content_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height,bg='gray25')
    self.info_content_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height,bg='gray25')

    ####### database_content_frame and register_content_frame
    self.user_list_frame = Frame(self.database_content_frame, width=int(self.resolution_width / 5) * 4, height=self.resolution_height,bg='gray25')
    self.database_icon_label = Label(self.database_content_frame, image=self.database_icon_image)
    self.remove_user_database_button = Button(self.database_content_frame, text='Remove', font=('Arial', 15), bg='red4',fg='black', relief=RAISED, borderwidth=3,command=lambda: self.ask_to_confirm_action("None",current_frame=self.database_content_frame,next_frame=self.database_content_frame))
    self.user_list_frame_scroll = ttk.Scrollbar(self.user_list_frame)
    style = ttk.Style()
    style.theme_use('default')
    style.configure("Treeview", font=("Calibri", 13))
    style.configure("Treeview.Heading", font=("Calibri", 15), background="grey", foreground="white")
    self.user_list = ttk.Treeview(self.user_list_frame, columns=("ID", "Name", "Authority","Department"), show='headings',yscrollcommand=self.user_list_frame_scroll.set, height=15)
    user_columns = [("ID", 60, tk.CENTER), ("Name", 200, tk.CENTER), ("Authority", 120, tk.CENTER),("Department", 140, tk.CENTER)]
    for col, width, anchor in user_columns:
        self.user_list.heading(col, text=col)
        self.user_list.column(col, width=width, anchor=anchor)
    self.user_list.bind("<<TreeviewSelect>>", self.on_treeview_select)
    self.user_image_label = Label(self.database_content_frame, bg='gray25', text="Choose user to continue",font=('Arial', 20), fg="white")
    self.user_list_frame_scroll.config(command=self.user_list.yview)
    self.register_user_or_admin_label = Label(self.register_content_frame, text='REGISTER AS', font=('Arial', 40),bg='gray25', fg='white')
    self.register_user_button = Button(self.register_content_frame, text=' USER ', font=('Arial', 35), fg='black',command=lambda: self.switch_frame(self.register_user_frame,self.register_content_frame,"register user"))
    self.register_admin_button = Button(self.register_content_frame, text='ADMIN', font=('Arial', 35), fg='black',command=lambda: self.switch_frame(self.register_user_frame,self.register_content_frame,"register admin"))
    self.select_entry = Button(self.database_content_frame,text = "Sort by: ID/Name",font=('Arial', 12),width=15, command = lambda: self.show_combbobox_value_frame(values=["ID", "Name"],frame=self.database_content_frame,task="ID/Name"))
    self.select_department = Button(self.database_content_frame,text = "Sort by: Department",font=('Arial', 12),width=30, command = lambda: self.show_combbobox_value_frame(values=self.user_departments,frame=self.database_content_frame,task="department"))
    self.search_entry = Button(self.database_content_frame, font=('Arial', 12),width=30,bg="white")
    self.search_entry.bind("<Button-1>", lambda event: self.keyboard(self.search_entry,self.database_content_frame))
    self.search_button = Button(self.database_content_frame, text="Search", font=('Arial', 15),command=lambda: self.search(self.user_list, "dataset", self.select_entry, self.search_entry, self.dataset_cursor,None,None,self.select_department))
    self.cancel_search_button = Button(self.database_content_frame, text="Show all", font=('Arial', 15),command=lambda: self.show_all(self.user_list, "dataset", self.dataset_cursor, self.search_entry, self.from_button,self.to_button))

    ### info_content_frame
    self.username_label = Label(self.info_content_frame, text='Username', font=('Arial', 30), bg='grey25', fg='white')
    self.username_entry = Button(self.info_content_frame, font=('Arial', 20), bg='white', text=self.username)
    self.password_label = Label(self.info_content_frame, text='Password', font=('Arial', 30), bg='grey25', fg='white')
    self.password_entry = Button(self.info_content_frame, font=('Arial', 20), bg='white', text=self.password)
    self.ip_adress_label = Label(self.info_content_frame, text='Website Address', font=('Arial', 30), bg='grey25', fg='white')
    self.ip_adress_entry = Button(self.info_content_frame, text=self.ip_address, font=('Arial', 20), bg='white', state=DISABLED)
    self.change_username_button = Button(self.info_content_frame, text='Change', font=('Arial', 15, 'italic'), bg='white',fg='black', relief=RAISED, borderwidth=3,command=lambda: self.keyboard(self.username_entry,self.info_content_frame))
    self.change_password_button = Button(self.info_content_frame, text='Change', font=('Arial', 15, 'italic'), bg='white',fg='black', relief=RAISED, borderwidth=3,command=lambda: self.keyboard(self.password_entry,self.info_content_frame))
    self.username_label.place(x=self.info_content_frame.winfo_reqwidth() // 4,y=self.resolution_height // 10)
    self.username_entry.place(x=self.info_content_frame.winfo_reqwidth() // 2 ,y=self.resolution_height // 10,width=self.info_content_frame.winfo_reqwidth() // 2)
    self.password_label.place(x=self.info_content_frame.winfo_reqwidth() // 4,y=3*self.resolution_height // 10)
    self.password_entry.place(x=self.info_content_frame.winfo_reqwidth() // 2,y=3*self.resolution_height // 10,width=self.info_content_frame.winfo_reqwidth() // 2)
    self.change_username_button.place(x=self.info_content_frame.winfo_reqwidth() // 4 -20 - self.change_username_button.winfo_reqwidth(),y=self.resolution_height // 10+5)
    self.change_password_button.place(x=self.info_content_frame.winfo_reqwidth() // 4 -20 - self.change_username_button.winfo_reqwidth(),y=3*self.resolution_height // 10+5)
    self.ip_adress_label.place(x=self.info_content_frame.winfo_reqwidth() // 4 -100 - self.change_username_button.winfo_reqwidth(),y=5*self.resolution_height // 10,width=self.info_content_frame.winfo_reqwidth() // 2)
    self.ip_adress_entry.place(x=self.info_content_frame.winfo_reqwidth() // 2, y=5 * self.resolution_height // 10,width=self.info_content_frame.winfo_reqwidth() // 2)

    #######user_log_content_frame
    self.user_log_list_frame = Frame(self.user_log_content_frame, bg='gray25')
    self.user_log_list_frame_scroll = ttk.Scrollbar(self.user_log_list_frame)
    self.user_log_list = ttk.Treeview(self.user_log_list_frame, yscrollcommand=self.user_log_list_frame_scroll.set, height=15,columns=("Date","Department", "ID", "Name", "In", "Out"), show="headings")
    self.user_log_columns = [("Date", 160, tk.CENTER),("Department", 160, tk.CENTER), ("ID", 70, tk.CENTER), ("Name", 230, tk.CENTER),("In", 150, tk.CENTER), ("Out", 150, tk.CENTER)]
    for col, width, anchor in self.user_log_columns:
        self.user_log_list.heading(col, text=col)
        self.user_log_list.column(col, width=width, anchor=anchor)
    self.user_log_list_frame_scroll.config(command=self.user_log_list.yview)
    self.calendar_frame = Frame(self.root, height=self.resolution_height,width=self.resolution_width, bg='gray25')
    self.cal = Calendar(self.calendar_frame, selectmode='day', year=2024, month=5, day=22, font=('Arial', 35),background='darkblue', foreground='white', selectbackground='red', selectforeground='white')
    self.get_date_button = Button(self.calendar_frame, text="Get Date", command=self.grad_date, font=('Arial', 25))
    self.from_date_label = Label(self.user_log_content_frame, text="From", font=('Arial', 28), bg="grey25", fg="white")
    self.from_button = Button(self.user_log_content_frame, text="Select date", font=('Arial', 17),command=lambda: self.open_calendar(self.from_button))
    self.to_date_label = Label(self.user_log_content_frame, text="To", font=('Arial', 28), bg="grey25", fg="white")
    self.to_button = Button(self.user_log_content_frame, text="Select date", font=('Arial', 17),command=lambda: self.open_calendar(self.to_button))
    self.select_entry_log = Button(self.user_log_content_frame,text="Sort by: ID/Name",font=('Arial', 12),width=15, command=lambda : self.show_combbobox_value_frame(values=["ID", "Name"],frame = self.user_log_content_frame,task="ID/Name"))
    self.select_department_log = Button(self.user_log_content_frame,font=('Arial', 12),width=30,text="Sort by: Department", command=lambda : self.show_combbobox_value_frame(values=self.user_departments,frame = self.user_log_content_frame,task="department"))
    self.search_entry_log = Button(self.user_log_content_frame, font=('Arial', 15),width=30,bg="white")
    self.search_entry_log.bind("<Button-1>", lambda event: self.keyboard(self.search_entry_log,self.user_log_content_frame))
    self.search_button_log = Button(self.user_log_content_frame, text="Search", font=('Arial', 15),command=lambda: self.search(self.user_log_list, "timekeeping", self.select_entry_log,self.search_entry_log, self.timekeeping_cursor, self.from_button, self.to_button,self.select_department_log))
    self.cancel_search_button_log = Button(self.user_log_content_frame, text="Show all", font=('Arial', 15),command=lambda: self.show_all(self.user_log_list, "timekeeping", self.timekeeping_cursor,self.search_entry_log, self.from_button, self.to_button))
    self.show_all(self.user_list, "dataset", self.dataset_cursor, self.search_entry, self.from_button, self.to_button)
    self.show_all(self.user_log_list, "timekeeping", self.timekeeping_cursor, self.search_entry_log, self.from_button, self.to_button)
    #self.date_warning_label = Label(self.user_log_content_frame, text="Please select date", font=('Arial', 20), bg='gray25',fg='red')
    self.edit_mode_database_checkbutton = tk.Checkbutton(self.user_log_content_frame, text="Edit", font=('Arial', 15), variable=self.edit_mode_var,command=self.toggle_edit_mode)
    self.selectall_mode_database_checkbutton = tk.Checkbutton(self.user_log_content_frame, text="Select all",font=('Arial', 15),variable=self.select_all_var, command= self.toggle_select_all)
    self.remove_log_button = Button(self.user_log_content_frame, text='Remove log', font=('Arial', 15), bg='red4', fg='black',relief=RAISED, borderwidth=3,command=lambda: self.ask_to_confirm_action("None", current_frame=self.user_log_content_frame,next_frame=self.user_log_content_frame))
    self.quit_user_log_content_button = Button(self.user_log_content_frame, text='  BACK  ', font=('Arial', 20), bg='white', fg='black',command=lambda: self.switch_frame(self.setting_frame,self.user_log_content_frame,"None"))
    self.quit_database_content_button = Button(self.database_content_frame, text='  BACK  ', font=('Arial', 20), bg='white', fg='black',command=lambda: self.switch_frame(self.setting_frame,self.database_content_frame,"None"))
    self.quit_register_content_button = Button(self.register_content_frame, text='  BACK  ', font=('Arial', 20), bg='white', fg='black',command=lambda: self.switch_frame(self.setting_frame,self.register_content_frame,"None"))
    self.quit_info_content_button  = Button(self.info_content_frame, text='  BACK  ', font=('Arial', 20), bg='white', fg='black',command=lambda: self.switch_frame(self.setting_frame,self.info_content_frame,"None"))
    self.quit_user_log_content_button.place(x=0, y=0)
    self.quit_database_content_button.place(x=0, y=0)
    self.quit_register_content_button.place(x=0, y=0)
    self.quit_info_content_button.place(x=0, y=0)
    self.back_to_check_inout_from_database_button.place(x=0, y=0)
    self.toggle_edit_mode()

    ####confirm_action_frame
    self.confirm_action_frane = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.confirm_action_title_label = Label(self.confirm_action_frane, text=' Confirm action? ', font=('Arial', 50),bg='gray', fg='white')
    self.confirm_yes_action_button = Button(self.confirm_action_frane, text='YES', font=('Arial', 40), bg='white', fg='black',relief=RAISED, borderwidth=5)
    self.confirm_no_action_button = Button(self.confirm_action_frane, text=' NO ', font=('Arial', 40), bg='white', fg='black',relief=RAISED, borderwidth=5)
    self.confirm_action_title_label.place(x=self.resolution_width // 2 - self.confirm_action_title_label.winfo_reqwidth() // 2,y=self.resolution_height // 5)
    self.confirm_yes_action_button.place(x=self.resolution_width // 2 - 20 - self.confirm_yes_action_button.winfo_reqwidth(), y=self.resolution_height // 2)
    self.confirm_no_action_button.place(x=self.resolution_width // 2 + 20, y=self.resolution_height // 2)

    #####please_wait_frame
    self.please_wait_frame= Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.please_wait_label = Label(self.please_wait_frame, text="Please wait", font=("Helvetica", 40))
    self.please_wait_label.place(x=self.resolution_width // 2 - self.please_wait_label.winfo_reqwidth() // 2,y=self.resolution_height // 2)

    #### value_frame
    self.value_frame = Frame(self.root,width=self.resolution_width, height=self.resolution_height, bg='gray')
    ###################################################################################################################################################################################################################
    ###################################################################################################################################################################################################################
    ##################################################################################################### PACKING #####################################################################################################
    # choose_check_inout_frame
    self.choose_check_inout_frame.place(x=0, y=0)
    self.choose_check_inout_background_label.place(x=int(self.resolution_width/2),y=0)
    self.please_choose_check_inout_label.place(x=(self.resolution_width//2 - self.please_choose_check_inout_label.winfo_reqwidth())//2,y=(self.resolution_height//6))
    self.check_in_button.place(width=self.resolution_width//2 - 40,height=self.resolution_height//6,x=20,y=20+(self.resolution_height//6)+ self.please_choose_check_inout_label.winfo_reqheight())
    self.check_out_button.place(width=self.resolution_width//2 - 40,height=self.resolution_height//6,x=20,y=40+(self.resolution_height//6)+ self.please_choose_check_inout_label.winfo_reqheight()+self.check_in_button.winfo_reqheight())
    self.go_to_insert_admin_ID_button.place(x=0,y=int(5.3*(self.resolution_height//6)))
    #authentication_frame
    self.back_to_check_inout_button.place(x=0, y=0)
    self.check_inout_confirmation_button.place(x=self.resolution_width - self.back_to_check_inout_button.winfo_reqwidth(), y=0)
    self.face_detected_authentication_frame.place(x=0,y=int(self.resolution_height/7),height=int((6 / 7) * self.resolution_height))
    self.information_authentication_frame.place(x=int(self.resolution_width / 2),y=int(self.resolution_height/7), width=int(self.resolution_width/2),height=int((6/7)*self.resolution_height))
    self.name_authentication_label.grid(row=1, column=0, sticky="W")
    self.department_authentication_label.grid(row=2, column=0, sticky="W")
    self.id_authentication_label.grid(row=0, column=0, sticky="W")
    self.time_authentication_label.grid(row=3, column=0, sticky="W")

    ### database_frame
    self.database_content_select_button.place(x=0, y=50, width=self.resolution_width // 2 - 20)
    self.register_content_select_button.place(x=self.database_content_select_button.winfo_reqwidth(), y=50,width=self.resolution_width // 2 - 20)
    self.user_log_content_select_button.place(x=0, y=50+self.database_content_select_button.winfo_reqheight(),width=self.resolution_width // 2 - 20)
    self.info_content_select_button.place(x=self.user_log_content_select_button.winfo_reqwidth(), y=50+self.user_log_content_select_button.winfo_reqheight(),width=self.resolution_width // 2 - 20)
    self.database_icon_label.place(x=self.database_content_frame.winfo_reqwidth() // 2 - self.database_icon_label.winfo_reqwidth() // 2, y=0)
    self.user_list_frame.place(x=40, y=self.database_icon_label.winfo_reqheight() + 24 + 3 * self.select_entry.winfo_reqheight())
    self.user_list_frame_scroll.pack(side="right", fill="both")
    self.user_list.pack()
    self.user_image_label.place(x=self.database_content_frame.winfo_reqwidth() // 2 + 100,y=self.database_icon_label.winfo_reqheight() + 20 + 3 * self.select_entry.winfo_reqheight())
    self.register_user_or_admin_label.place(x=self.database_content_frame.winfo_reqwidth() // 2 - self.register_user_or_admin_label.winfo_reqwidth() // 2 + 20,y=self.resolution_height // 4)
    self.register_user_button.place(x=self.resolution_width // 3,y=self.resolution_height // 4 + self.register_user_or_admin_label.winfo_reqheight() + 40)
    self.register_admin_button.place(x=self.resolution_width// 3 + self.register_user_button.winfo_reqwidth() + 10,y=self.resolution_height // 4 +self.register_user_or_admin_label.winfo_reqheight() + 40)
    self.select_entry.place(x=40, y=self.database_icon_label.winfo_reqheight() + 18)
    self.search_entry.place(x=60 + self.select_entry.winfo_reqwidth(), y=self.database_icon_label.winfo_reqheight() + 18)
    self.select_department.place(x=40, y=self.database_icon_label.winfo_reqheight() + 25 + self.select_entry.winfo_reqheight())
    self.search_button.place(x=self.database_content_frame.winfo_reqwidth() // 3+50, y=self.database_icon_label.winfo_reqheight() + 20 + self.select_entry.winfo_reqheight())
    self.cancel_search_button.place(x=self.database_content_frame.winfo_reqwidth() // 3 + self.search_button.winfo_reqwidth()+50,y=self.database_icon_label.winfo_reqheight() + 20 + self.select_entry.winfo_reqheight())

    ##user_log_content_frame
    self.user_log_list_frame.place(x=50, y=self.resolution_height // 3)
    self.user_log_list_frame_scroll.pack(side="right", fill="both")
    self.user_log_list.pack()
    self.from_date_label.place(x=50, y=self.resolution_height // 10 + 20)
    self.from_button.place(x=self.from_date_label.winfo_reqwidth() + 100, y=self.resolution_height // 10 + 30)
    self.to_date_label.place(x=50, y=self.resolution_height // 10 + self.from_date_label.winfo_reqheight() + 20)
    self.to_button.place(x=self.from_date_label.winfo_reqwidth() + 100, y=self.resolution_height // 10 + self.from_date_label.winfo_reqheight() + 30)
    self.select_entry_log.place(x=self.user_log_content_frame.winfo_reqwidth() // 2 - 10, y=self.resolution_height // 3 - 3 * self.search_entry_log.winfo_reqheight())
    self.select_department_log.place(x=self.user_log_content_frame.winfo_reqwidth() // 2 - 10,y=self.resolution_height // 3 - 2 * self.search_entry_log.winfo_reqheight()+10)
    self.search_entry_log.place(x=self.select_entry_log.winfo_reqwidth()+self.user_log_content_frame.winfo_reqwidth() // 2 ,y=self.resolution_height // 3 - 3 * self.search_entry_log.winfo_reqheight())
    self.search_button_log.place(x=self.user_log_content_frame.winfo_reqwidth() // 2 + self.search_entry_log.winfo_reqwidth() - 35,y=self.resolution_height // 3 - 2 * self.search_entry_log.winfo_reqheight()+10)
    self.cancel_search_button_log.place(x=self.user_log_content_frame.winfo_reqwidth() // 2 + self.search_entry_log.winfo_reqwidth() + self.search_button_log.winfo_reqwidth() - 25,y=self.resolution_height // 3 - 2 * self.search_entry_log.winfo_reqheight()+10)
    self.edit_mode_database_checkbutton.place(x=50, y=self.resolution_height - 2 * self.edit_mode_database_checkbutton.winfo_reqheight())
    self.selectall_mode_database_checkbutton.place(x=60 + self.edit_mode_database_checkbutton.winfo_reqwidth(),y=self.resolution_height - 2 * self.edit_mode_database_checkbutton.winfo_reqheight())
    self.cal.place(x=90, y=30)
    self.get_date_button.place(x=self.calendar_frame.winfo_reqwidth() // 2 - self.get_date_button.winfo_reqwidth() // 2,y=self.resolution_height - 30 - self.get_date_button.winfo_reqheight())
    self.remove_log_button.place(x=80 + self.edit_mode_database_checkbutton.winfo_reqwidth() + self.selectall_mode_database_checkbutton.winfo_reqwidth(), y=self.resolution_height - 2 * self.edit_mode_database_checkbutton.winfo_reqheight())
    #self.date_warning_label.place(x=self.calendar_frame.winfo_reqwidth() // 2 - self.date_warning_label.winfo_reqwidth() // 2, y=0)

    ##register_user_frame
    self.register_title_label.place(x=self.resolution_width // 2 - self.register_title_label.winfo_reqwidth() // 2, y=0)
    self.register_name_label.place(x=self.resolution_width // 4, y=40 + self.register_title_label.winfo_reqheight())
    self.register_name_entry.place(x=self.resolution_width // 4 + 10 + self.register_name_label.winfo_reqwidth(),y=40 + self.register_title_label.winfo_reqheight(),height=self.register_name_label.winfo_reqheight(),width=self.register_face_button.winfo_reqwidth() - 10 - self.register_name_label.winfo_reqwidth())
    self.cancel_register_button.place(x=0, y=0)
    self.register_department_label.place(x=self.resolution_width // 4, y=40 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight())
    self.register_department_combobox.place(x=self.resolution_width // 4 + 10 + self.register_department_label.winfo_reqwidth(),y=40 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight(),height=self.register_name_label.winfo_reqheight(),width=self.register_face_button.winfo_reqwidth() - 10 - self.register_department_label.winfo_reqwidth())
    self.confirm_register_button.place(x=self.resolution_width - self.cancel_register_button.winfo_reqwidth(), y=0)
    self.register_face_button.place(x=self.resolution_width // 4-5, y=60 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight() + self.register_department_label.winfo_reqheight(),width = self.resolution_width//3 + self.resolution_width//5)
    self.register_card_button.place(x=self.resolution_width // 4-5, y=80 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight() + self.register_face_button.winfo_reqheight()+ self.register_department_label.winfo_reqheight(),width = self.resolution_width//3 + self.resolution_width//5)

    ##insert_card_frame
    self.insert_card_background_label.place(x=0, y=self.resolution_height // 7)
    self.insert_card_guidline_label.place(x=self.resolution_width // 2 - self.insert_card_guidline_label.winfo_reqwidth() // 2, y=0)
    self.cancel_card_activities_button.place(x=0, y=0)

    ###face_activities_frame
    self.register_face_guidline_label.place(x=self.resolution_width // 2 - self.register_face_guidline_label.winfo_reqwidth() // 2,y=0)
    self.camera_frame.place(x=0, y=self.resolution_height // 7)
    self.camera_label.place(x=0, y=0)
    self.cancel_face_activities_button.place(x=0, y=0)


