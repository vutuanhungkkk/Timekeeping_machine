import os
from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
import queue
import sqlite3
import serial
import socket
import torch
import adafruit_fingerprint
import threading
from contextlib import closing

def init_app(self,root,ort_session,face_detector,anti_spoof_detector,test_transform,device,vid):
    self.root = root
    #self.root.attributes("-fullscreen", True)
    #self.root.overrideredirect(True)
    self.root.bind('a', lambda event: self.allow_comfirm(event))
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
    self.resolution_height = 600
    self.resolution_width = 1024
    self.root.geometry(f"{self.resolution_width}x{self.resolution_height}")
    self.choose_check_inout_background_image = self.convert_image_for_tkinter("icon_images/theme2.jpg",(int(self.resolution_width / 2), self.resolution_height))
    self.insert_card_image = self.convert_image_for_tkinter("icon_images/fingerprint.jpg",(self.resolution_width, 6 * int(self.resolution_height / 7)))
    self.register_face_image = self.convert_image_for_tkinter("icon_images/face.jpg",(int(self.resolution_width / 4), int(self.resolution_height / 4)))
    self.register_id_image = self.convert_image_for_tkinter("icon_images/fingerprint.jpg",(int(self.resolution_width / 4),int(self.resolution_height / 4)))
    self.register_image = self.convert_image_for_tkinter("icon_images/register.jpg", (self.resolution_width//2, (self.resolution_height -50)//3))
    self.system_image = self.convert_image_for_tkinter("icon_images/system.jpg", (self.resolution_width//2, (self.resolution_height -50)//3))
    #camera
    self.vid =  vid
    ## database ##
    with closing(sqlite3.connect('database/web.db',timeout=1)) as web_conn:
        web_conn.execute('PRAGMA journal_mode=WAL;')
        with closing(web_conn.cursor()) as web_cursor:
            web_cursor.execute('SELECT Username, Password FROM web LIMIT 1')
            web_info = web_cursor.fetchone()
            if web_info:
                self.username = web_info[0]
                self.password = web_info[1]
            else:
                print("Error: No username and password in database")
                self.username = "error"
                self.password = "error"
    with closing(sqlite3.connect('database/department.db',timeout=1)) as department_conn:
        department_conn.execute('PRAGMA journal_mode=WAL;')
        with closing(department_conn.cursor()) as department_cursor:
            department_cursor.execute('SELECT department FROM departments')
            self.user_departments = [row[0] for row in department_cursor.fetchall()]
            if not self.user_departments:
                self.user_departments = ["No department"]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "Unable to get IP"
    finally:
        s.close()
    self.ip_address = "http://" + ip_address + ":5000"

    ##fingerprint
    try:
        uart = serial.Serial('/dev/ttyTHS1', 57200, timeout=5)
        self.finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
        self.finger.empty_library()
        self.finger.set_sysparam(5, 1)
        self.finger.count_templates()
        print(f"Number of stored fingerprints: {self.finger.template_count}")
        self.finger.get_image()
        self.fingerprint_buffer = 0
        self.fingerprint_mismatch = False
        self.fingerprint_already_exist = False
    except:
        print("Fingerprint sensor not connected")
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
    self.thread_lock = threading.Lock()
    self.open_camera_allow = False
    self.check_user_allow = False
    self.get_data_user_allow = False
    self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    self.face_detector = face_detector
    self.anti_spoof_detector = anti_spoof_detector
    self.ort_session = ort_session
    self.test_transform = test_transform
    self.number_of_face_to_train = 12
    self.check_confirm_add_user = False
    self.face_already_exist = False
    self.user_info = None
    create_widgets(self)
    self.update_web_info()
    self.running_camera()
    
    

def create_widgets(self):
    #choose_check_inout_frame
    self.choose_check_inout_frame = Frame(self.root,height=self.resolution_height,width= self.resolution_width,bg='gray')
    self.choose_check_inout_background_label = Label(self.choose_check_inout_frame, image = self.choose_check_inout_background_image)
    self.please_choose_check_inout_label = Label(self.choose_check_inout_frame,text = "PLEASE  CHOOSE",font=('Arial',40),bg='gray',fg='white')
    self.check_in_button = Button(self.choose_check_inout_frame,text = "CHECK IN",font=('Arial',40),bg='white',fg='black',command=lambda:self.switch_frame(self.choose_face_or_card_frame,self.choose_check_inout_frame,"check in"))
    self.check_out_button = Button(self.choose_check_inout_frame, text="CHECK OUT", font=('Arial', 40), bg='white', fg='black',command=lambda:self.switch_frame(self.choose_face_or_card_frame,self.choose_check_inout_frame,"check out"))
    self.go_to_insert_admin_ID_button = Button(self.choose_check_inout_frame, text=" → To Admin page ", font=('Arial', 30), bg='white', fg='black',relief='flat',command=lambda:self.switch_frame(self.choose_face_or_card_frame,self.choose_check_inout_frame,"check admin authority"))
    #self.go_to_insert_admin_ID_button = Button(self.choose_check_inout_frame, text=" → To Administration ", font=('Arial', 30), bg='white', fg='black',relief='flat',command= self.go_to_database_frame)
    self.destroy_gui_button = Button(self.choose_check_inout_frame, text="DESTROY", font=('Arial', 20), bg='white', fg='black',command=self.destroy_gui)
    self.destroy_gui_button.place(x=self.resolution_width - self.destroy_gui_button.winfo_reqwidth(),y=0)
    self.bypass_button = Button(self.choose_check_inout_frame, text="BYPASS", font=('Arial', 20), bg='white', fg='black',command=self.go_to_database_frame_bypass)
    self.bypass_button.place(x=self.resolution_width - self.destroy_gui_button.winfo_reqwidth(),y=self.resolution_height - self.bypass_button.winfo_reqheight())
    #authentication_frame
    self.authentication_frame = Frame(self.root,height=self.resolution_height,width= self.resolution_width,bg='gray')
    self.back_to_check_inout_button = Button(self.authentication_frame, text="CANCEL", font=('Arial', 30),bg='white', fg='black', command=lambda: self.switch_frame(self.choose_face_or_card_frame,self.authentication_frame,"None"))
    self.check_inout_confirmation_button = Button(self.authentication_frame, text="CONFIRM", font=('Arial', 30),bg='white', fg='black',command=lambda: self.update_timekeeping_db(self.task_category))
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
    self.cancel_choose_face_or_card_button = Button(self.choose_face_or_card_frame, text="CANCEL", font=('Arial', 30), bg='white', fg='black',command=lambda: self.switch_frame(self.choose_check_inout_frame,self.choose_face_or_card_frame,"None"))
    self.face_button.place(x=0, y=self.cancel_choose_face_or_card_button.winfo_reqheight(), width=self.resolution_width // 2, height=self.resolution_height)
    self.card_button.place(x=self.resolution_width // 2,  y=self.cancel_choose_face_or_card_button.winfo_reqheight(), width=self.resolution_width // 2, height=self.resolution_height)
    self.cancel_choose_face_or_card_button.place(x=0, y=0)

    #### register_frame
    self.current_entry = None
    self.register_user_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray25')
    self.register_title_label = Label(self.register_user_frame, text=' ID :  ', font=('Arial', 40), bg='gray25',fg='white')
    self.register_name_label = Label(self.register_user_frame, text='Name:', font=('Arial', 35), bg='grey25', fg='white')
    self.register_department_label = Label(self.register_user_frame, text='Department:', font=('Arial', 35), bg='grey25', fg='white')
    self.register_department_combobox = Button(self.register_user_frame,text="Select Department",bg="white",font=('Arial', 20) , command=lambda : self.show_combbobox_value_frame(values=self.user_departments,frame = self.register_user_frame,task="department"))
    self.register_name_entry = Button(self.register_user_frame, font=('Arial', 20), bg='white',command=lambda: self.keyboard(self.register_name_entry,self.register_user_frame))
    self.register_face_button = Button(self.register_user_frame, text=" Register Face ",bg="white", font=('Arial', 30),image=self.register_face_image, compound=LEFT, command=lambda:self.face_activities("register", "None",self.task_category))
    self.register_card_button = Button(self.register_user_frame, text=" Register Finger ",bg="white" ,font=('Arial', 30),image=self.register_id_image, compound=LEFT, command=lambda:self.card_activities("register", "None",self.task_category))
    self.cancel_register_button = Button(self.register_user_frame, text="CANCEL", font=('Arial', 30), bg='white', fg='black',command=lambda: self.ask_to_confirm_action("None", self.register_user_frame,self.register_content_frame))
    self.confirm_register_button = Button(self.register_user_frame, text="CONFIRM", font=('Arial', 30), bg='white',fg='black',command=lambda: self.update_database_db(self.task_category),state=DISABLED)
    self.create_department_button = Button(self.register_user_frame, text="Create department", font=('Arial', 20), bg='white', fg='black',command=lambda: self.keyboard(self.create_department_button,self.register_user_frame))
    self.create_department_button.place(x=0,y=40 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight())

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
    self.insert_card_guidline_label = Label(self.card_activities_frame,font=('Arial', 30), bg='gray', fg='white')
    self.cancel_card_activities_button = Button(self.card_activities_frame, text='CANCEL', font=('Arial', 30), bg='white',fg='black', command=lambda:self.cancel_card_activities("None","None"))

    ###face_activities_frame
    self.face_activities_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.register_face_guidline_label = Label(self.face_activities_frame, text='Finding face....',font=('Arial', 30), bg='gray', fg='white')
    self.camera_frame = Frame(self.face_activities_frame, width=self.resolution_width, height=6 * (self.resolution_height // 7),bg='black')
    self.camera_label = Label(self.camera_frame, bg='black', width=self.resolution_width, height=6 * (self.resolution_height // 7))
    self.cancel_face_activities_button = Button(self.face_activities_frame, text='CANCEL', font=('Arial', 30), bg='white',fg='black', command = lambda:self.cancel_face_activities("None","None"))
    self.take_face_confirmation_button = Button(self.face_activities_frame, text='TAKE', font=('Arial', 30), bg='white',fg='black', command= lambda:self.check_user("check"))
    self.retake_face_confirmation_button = Button(self.face_activities_frame, text="RETAKE", font=('Arial', 30),bg='white', fg='black',command=lambda: self.face_activities("check","None","None"))
    self.start_get_data_user_button = Button(self.face_activities_frame, text='START', font=('Arial', 30), bg='white',fg='black', command= lambda:self.check_user("register"))
    self.restart_get_data_user_button = Button(self.face_activities_frame, text="RESTART", font=('Arial', 30),bg='white', fg='black',command=lambda: self.face_activities("register","None","None"))

    #setting_frame
    self.setting_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='grey')
    ###database_frame
    self.register_content_select_button = Button(self.setting_frame,image = self.register_image,compound='top', text='REGISTER', font=('Arial', 18),bg='gray', fg='white', state=NORMAL,command=lambda:self.switch_frame(self.register_user_frame, self.setting_frame,"register user"),borderwidth=0)
    self.info_content_select_button = Button(self.setting_frame,image = self.system_image,compound='top', text='WEBSITE', font=('Arial', 18),bg='gray', fg='white', state=NORMAL, borderwidth=0,command= lambda:self.switch_frame(self.info_content_frame, self.setting_frame,"None"))
    self.back_to_check_inout_from_database_button = Button(self.setting_frame, text='  BACK  ', font=('Arial', 30),bg='white', fg='black',command= lambda: self.switch_frame(self.choose_check_inout_frame,self.setting_frame,"None"))
    self.register_content_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height,bg='gray25')
    self.info_content_frame = Frame(self.root, width=self.resolution_width, height=self.resolution_height,bg='gray25')

    ####### database_content_frame and register_content_frame
    self.register_user_or_admin_label = Label(self.register_content_frame, text='REGISTER AS', font=('Arial', 60),bg='gray25', fg='white')
    self.register_user_button = Button(self.register_content_frame, text=' USER ', font=('Arial', 50), fg='black',command=lambda: self.switch_frame(self.register_user_frame,self.register_content_frame,"register user"))
    self.register_admin_button = Button(self.register_content_frame, text='ADMIN', font=('Arial', 50), fg='black',command=lambda: self.switch_frame(self.register_user_frame,self.register_content_frame,"register admin"))

    ### info_content_frame
    self.username_label = Label(self.info_content_frame, text='Username', font=('Arial', 30), bg='grey25', fg='white')
    self.username_entry = Button(self.info_content_frame, font=('Arial', 20), bg='white', text=self.username)
    self.password_label = Label(self.info_content_frame, text='Password', font=('Arial', 30), bg='grey25', fg='white')
    self.password_entry = Button(self.info_content_frame, font=('Arial', 20), bg='white', text=self.password)
    self.ip_adress_label = Label(self.info_content_frame, text='Website Address', font=('Arial', 30), bg='grey25', fg='white')
    self.ip_adress_entry = Button(self.info_content_frame, text=self.ip_address, font=('Arial', 20), bg='white')
    self.change_username_button = Button(self.info_content_frame, text='Change', font=('Arial', 20, 'italic'), bg='white',fg='black', relief=RAISED, borderwidth=3,command=lambda: self.keyboard(self.username_entry,self.info_content_frame))
    self.change_password_button = Button(self.info_content_frame, text='Change', font=('Arial', 20, 'italic'), bg='white',fg='black', relief=RAISED, borderwidth=3,command=lambda: self.keyboard(self.password_entry,self.info_content_frame))
    self.quit_info_content_button  = Button(self.info_content_frame, text='  BACK  ', font=('Arial', 30), bg='white', fg='black',command=lambda: self.switch_frame(self.setting_frame,self.info_content_frame,"None"))
    self.quit_info_content_button.place(x=0, y=0)
    self.username_label.place(x=self.info_content_frame.winfo_reqwidth() // 4,y=self.quit_info_content_button.winfo_reqheight())
    self.username_entry.place(x=self.info_content_frame.winfo_reqwidth() // 2 ,y=self.quit_info_content_button.winfo_reqheight(),width=self.info_content_frame.winfo_reqwidth() // 2)
    self.password_label.place(x=self.info_content_frame.winfo_reqwidth() // 4,y=3*self.quit_info_content_button.winfo_reqheight())
    self.password_entry.place(x=self.info_content_frame.winfo_reqwidth() // 2,y=3*self.quit_info_content_button.winfo_reqheight(),width=self.info_content_frame.winfo_reqwidth() // 2)
    self.change_username_button.place(x=self.info_content_frame.winfo_reqwidth() // 4 -20 - self.change_username_button.winfo_reqwidth(),y=self.quit_info_content_button.winfo_reqheight()+5)
    self.change_password_button.place(x=self.info_content_frame.winfo_reqwidth() // 4 -20 - self.change_username_button.winfo_reqwidth(),y=3*self.quit_info_content_button.winfo_reqheight()+5)
    self.ip_adress_label.place(x=0,y=5*self.quit_info_content_button.winfo_reqheight(),width=self.info_content_frame.winfo_reqwidth() // 2)
    self.ip_adress_entry.place(x=self.info_content_frame.winfo_reqwidth() // 2, y=5 * self.quit_info_content_button.winfo_reqheight(),width=self.info_content_frame.winfo_reqwidth() // 2)

    #######user_log_content_frame
    self.quit_register_content_button = Button(self.register_content_frame, text='  BACK  ', font=('Arial', 30), bg='white', fg='black',command=lambda: self.switch_frame(self.setting_frame,self.register_content_frame,"None"))
    self.quit_register_content_button.place(x=0, y=0)
    self.back_to_check_inout_from_database_button.place(x=0, y=0)

    ####confirm_action_frame
    self.confirm_action_frane = Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.confirm_action_title_label = Label(self.confirm_action_frane, text=' CONFIRM ACTION ', font=('Arial', 60),bg='gray', fg='white')
    self.confirm_yes_action_button = Button(self.confirm_action_frane, text='YES', font=('Arial', 50), bg='white', fg='black',relief=RAISED, borderwidth=5)
    self.confirm_no_action_button = Button(self.confirm_action_frane, text=' NO ', font=('Arial', 50), bg='white', fg='black',relief=RAISED, borderwidth=5)
    self.confirm_action_title_label.place(x=self.resolution_width // 2 - self.confirm_action_title_label.winfo_reqwidth() // 2,y=self.resolution_height // 3)
    self.confirm_yes_action_button.place(x=self.resolution_width // 2 - 20 - self.confirm_yes_action_button.winfo_reqwidth(), y=self.resolution_height // 3+ self.confirm_action_title_label.winfo_reqheight())
    self.confirm_no_action_button.place(x=self.resolution_width // 2 + 20, y=self.resolution_height // 3+ self.confirm_action_title_label.winfo_reqheight())

    #####please_wait_frame
    self.please_wait_frame= Frame(self.root, width=self.resolution_width, height=self.resolution_height, bg='gray')
    self.please_wait_label = Label(self.please_wait_frame, text="Please wait......", font=("Helvetica", 80),bg='gray',fg = 'white')
    self.please_wait_label.place(x=self.resolution_width // 2 - self.please_wait_label.winfo_reqwidth() // 2+10,y=self.resolution_height // 2-30)

    #### value_frame
    self.value_frame = Frame(self.root,width=self.resolution_width, height=self.resolution_height, bg='gray')
    ###################################################################################################################################################################################################################
    ###################################################################################################################################################################################################################
    ##################################################################################################### PACKING #####################################################################################################
    # choose_check_inout_frame
    self.choose_check_inout_frame.place(x=0, y=0)
    self.choose_check_inout_background_label.place(x=int(self.resolution_width/2),y=0)
    self.please_choose_check_inout_label.place(x=(self.resolution_width//2 - self.please_choose_check_inout_label.winfo_reqwidth())//2,y=(self.resolution_height//6))
    self.check_in_button.place(width=self.resolution_width//2 - 40,height=self.resolution_height//6,x=20,y=(self.resolution_height//6)+ self.please_choose_check_inout_label.winfo_reqheight())
    self.check_out_button.place(width=self.resolution_width//2 - 40,height=self.resolution_height//6,x=20,y=(self.resolution_height//4)+ self.please_choose_check_inout_label.winfo_reqheight()+self.check_in_button.winfo_reqheight())
    self.go_to_insert_admin_ID_button.place(x=0,y=int(5.3*(self.resolution_height//6)))
    #authentication_frame
    self.back_to_check_inout_button.place(x=0, y=0)
    self.check_inout_confirmation_button.place(x=self.resolution_width - self.back_to_check_inout_button.winfo_reqwidth()-10, y=0)
    self.face_detected_authentication_frame.place(x=0,y=int(self.resolution_height/7),height=int((6 / 7) * self.resolution_height))
    self.information_authentication_frame.place(x=int(self.resolution_width / 2),y=int(self.resolution_height/7), width=int(self.resolution_width/2),height=int((6/7)*self.resolution_height))
    self.name_authentication_label.grid(row=1, column=0, sticky="W")
    self.department_authentication_label.grid(row=2, column=0, sticky="W")
    self.id_authentication_label.grid(row=0, column=0, sticky="W")
    self.time_authentication_label.grid(row=3, column=0, sticky="W")

    ### setting_frame
    self.register_content_select_button.place(x=self.resolution_width // 4,y=self.back_to_check_inout_button.winfo_reqheight() + 20,width=self.resolution_width // 2 - 20)
    self.info_content_select_button.place(x=self.resolution_width // 4,y=self.back_to_check_inout_button.winfo_reqheight() + 20 + self.register_content_select_button.winfo_reqheight(),width=self.resolution_width // 2 - 20)
    self.register_user_or_admin_label.place(x=self.resolution_width // 2 - self.register_user_or_admin_label.winfo_reqwidth() // 2,y=self.resolution_height // 3)
    self.register_user_button.place(x=self.resolution_width // 2  -  self.register_user_button.winfo_reqwidth()-20,y=self.resolution_height // 3 +  self.register_user_or_admin_label.winfo_reqheight() )
    self.register_admin_button.place(x=self.resolution_width // 2  +  20,y=self.resolution_height // 3 +  self.register_user_or_admin_label.winfo_reqheight() )
   ##register_user_frame
    self.register_title_label.place(x=self.resolution_width // 2 - self.register_title_label.winfo_reqwidth() // 2, y=0)
    self.register_name_label.place(x=self.resolution_width // 4 + int((20/1024)*self.resolution_width), y=40 + self.register_title_label.winfo_reqheight(),width=self.register_face_button.winfo_reqwidth()//4)
    self.register_name_entry.place(x=self.resolution_width // 4 +  int((20/1024)*self.resolution_width) + 10 + self.register_name_label.winfo_reqwidth(),y=40 + self.register_title_label.winfo_reqheight(),height=self.register_name_label.winfo_reqheight(),width=self.register_face_button.winfo_reqwidth() - self.register_name_label.winfo_reqwidth())
    self.cancel_register_button.place(x=0, y=0)
    self.register_department_label.place(x=self.resolution_width // 4+ int((20/1024)*self.resolution_width), y=40 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight())
    self.register_department_combobox.place(x=self.resolution_width // 4+ int((20/1024)*self.resolution_width) + 10 + self.register_department_label.winfo_reqwidth(),y=40 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight(),height=self.register_name_label.winfo_reqheight(),width=self.register_face_button.winfo_reqwidth() - self.register_department_label.winfo_reqwidth())
    self.confirm_register_button.place(x=self.resolution_width - self.cancel_register_button.winfo_reqwidth()-20, y=0)
    self.register_face_button.place(x=self.resolution_width // 4-5, y=60 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight() + self.register_department_label.winfo_reqheight(),width = self.resolution_width//3 + self.resolution_width//5)
    self.register_card_button.place(x=self.resolution_width // 4-5, y=80 + self.register_title_label.winfo_reqheight() + self.register_name_label.winfo_reqheight() + self.register_face_button.winfo_reqheight()+ self.register_department_label.winfo_reqheight(),width = self.resolution_width//3 + self.resolution_width//5)

    ##insert_card_frame
    self.insert_card_background_label.place(x=0, y=self.resolution_height // 7)
    self.insert_card_guidline_label.place(x=self.resolution_width // 4, y=0)
    self.cancel_card_activities_button.place(x=0, y=0)

    ###face_activities_frame
    self.register_face_guidline_label.place(x=self.resolution_width // 2 - self.register_face_guidline_label.winfo_reqwidth() // 2,y=0)
    self.camera_frame.place(x=0, y=self.resolution_height // 7)
    self.camera_label.place(x=0, y=0)
    self.cancel_face_activities_button.place(x=0, y=0)


