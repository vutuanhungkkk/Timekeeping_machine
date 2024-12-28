import sqlite3
from yolov8 import YOLOv8_face, make_prediction,increased_crop
from FaceAntiSpoofing import AntiSpoof
import adafruit_fingerprint
from tkinter import *
from PIL import Image, ImageTk
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
import cv2
import torch
import threading
from torchvision import transforms as trans
from create_widgets import init_app
import shutil
import time
import datetime
from datetime import datetime as dt
from collections import Counter
import pickle
import numpy as np
import onnxruntime as ort
from contextlib import closing
root = Tk()

class App:

    def destroy_gui(self):
        self.vid.release()
        self.root.destroy()

    def convert_image_for_tkinter(self, image_path, target_size):
        if image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            image = cv2.imread(image_path)
            image = cv2.resize(image, target_size)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
        else:
            image = Image.open(image_path)
            image = image.resize(target_size)
        image_tk = ImageTk.PhotoImage(image)
        return image_tk

    def __init__(self, root,ort_session,face_detector,anti_spoof_detector,test_transform,device,vid):
        init_app(self, root,ort_session,face_detector,anti_spoof_detector,test_transform,device,vid)

    def go_to_database_frame_bypass(self):
        self.card_activities_frame.place_forget()
        self.setting_frame.place(x=0, y=0)

    def go_to_database_frame(self):
        self.setting_frame.place(x=0, y=0)
        
        
    def allow_comfirm(self,event):
        self.check_confirm_add_user = False
        print("allow add data imediatly")
        self.confirm_register_button.config(state=NORMAL)

    def get_value_behind_colon_combobbox(self,button):
        button_text = button.cget("text")
        parts = button_text.split(":")
        if len(parts) > 1:
            return parts[1].strip()
        return None

    def show_combbobox_value_frame(self, values,frame,task):
        for widget in self.value_frame.winfo_children():
            widget.destroy()
        canvas = Canvas(self.value_frame, height=self.resolution_height, width=self.resolution_width,background="grey")  # Fixed height and width for the canvas
        scrollbar = Scrollbar(self.value_frame, orient="vertical", command=canvas.yview,width=30)
        scrollable_frame = Frame(canvas,bg="grey")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.place(x=0, y=0)
        scrollbar.pack(side="right", fill="y")
        for i, value in enumerate(values):
            button = Button(scrollable_frame, text=value, font=('Arial', int((35/1024)*self.resolution_width)), command=lambda d=value:self.on_combbobox_value_select(value=d,frame=frame,task=task),width=int((15/1024)*self.resolution_width))
            button.grid(row=i, column=0,columnspan=3, padx=340, pady=5)
        frame.place_forget()
        self.value_frame.pack(fill=BOTH, expand=True)
        
    def on_combbobox_value_select(self,value,frame,task):
        if frame == self.register_user_frame:
            self.register_department_combobox.config(text=value)
        self.value_frame.pack_forget()
        frame.place(x=0,y=0)

    def l2_norm(self, inp, axis=1):
        norm = torch.norm(inp,2,axis,True)
        output = torch.div(inp, norm)
        return output
        
    def running_camera(self):
        if self.open_camera_allow == False and self.vid is not None:
            try:
                ret, frame = self.vid.read()
                if ret and frame is not None:
                    opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    self.update_camera_frame(opencv_image)
             
            except:
                self.vid.release()
                time.sleep(1)
                vid = self.find_available_camera()
        if self.get_card_allow == False:
            try:
                check_press = self.finger.get_image()
                print("reading sensor")
            except:
                print("Error in reading sensor")
        self.root.after(1000, self.running_camera)

    def update_web_info(self):
        with closing(sqlite3.connect('database/web.db', timeout=1)) as web_conn:
            web_conn.execute('PRAGMA journal_mode=WAL;')
            with closing(web_conn.cursor()) as web_cursor:
                web_cursor.execute('SELECT Username, Password FROM web LIMIT 1')
                web_info = web_cursor.fetchone()
                if web_info:
                    self.username = web_info[0]
                    self.password = web_info[1]
                    self.username_entry.config(text=self.username)
                    self.password_entry.config(text=self.password)

        if self.user_info is not None:
            user_ID = self.user_info[0]
            with closing(sqlite3.connect('database/dataset.db', timeout=1)) as dataset_conn:
                dataset_conn.execute('PRAGMA journal_mode=WAL;')
                with closing(dataset_conn.cursor()) as dataset_cursor:
                    dataset_cursor.execute('SELECT * FROM dataset WHERE ID=?', (user_ID,))
                    user_information = dataset_cursor.fetchone()
                    if user_information:
                        self.check_inout_confirmation_button.config(state=NORMAL)
                        self.name_authentication_label.config(text=f"Name: {user_information[1]}")
                        self.department_authentication_label.config(text=f"Department: {user_information[3]}")
                    else:
                        self.check_inout_confirmation_button.config(state=DISABLED)
        self.root.after(1500, self.update_web_info)



    def card_activities(self, task, authority, task_category):
        #self.card_activities_frame.place(x=0, y=0)#delay
        self.update_guideline_message("No finger detected, place finger", "red")
        self.root.after(50, lambda: self.card_activities_frame.place(x=0, y=0))
        if task == "check":
            self.choose_face_or_card_frame.place_forget()
        elif task == "register":
            self.register_user_frame.place_forget()
            if self.register_card_button.cget("bg") == "green":
                try:
                    self.finger.delete_model(self.new_id)
                    print("delete finger")
                except:
                    print("Error in delete finger")
        self.cancel_card_activities_button.config(command=lambda: self.cancel_card_activities(task, authority))
        self.get_card_allow = True
        #self.get_card_input(task, authority, task_category) #delay
        self.root.after(100, self.get_card_input, task, authority, task_category)

    def cancel_card_activities(self, task, authority):
        self.card_activities_frame.place_forget()
        time.sleep(0.1)
        self.get_card_allow = False
        self.fingerprint_buffer = 0
        if task == "check":
            #self.choose_face_or_card_frame.place(x=0, y=0) #delay
            self.root.after(50, lambda: self.choose_face_or_card_frame.place(x=0, y=0))
        elif task == "register":
            #self.register_user_frame.place(x=0, y=0) #delay
            self.root.after(50, lambda: self.register_user_frame.place(x=0, y=0))
            try:
                self.finger.delete_model(self.new_id)
                print("delete finger")
            except:
                print("Error in delete finger")
        time.sleep(0.2)
        self.register_card_button.config(fg="black", text=" Register Finger ", bg="white", state=NORMAL,command=lambda: self.card_activities("register", "None", "None"))
        self.confirm_add_user()
        
    def face_activities(self, task, authority, task_category):
        self.face_activities_frame.place(x=0, y=0)
        if task_category in ["check in", "check out"]:
            authority = "user"
        elif task_category in ["check admin authority"]:
            authority = "admin"
        if task == "check":
            self.choose_face_or_card_frame.place_forget()
            self.start_get_data_user_button.place_forget()
            self.restart_get_data_user_button.place_forget()
            self.take_face_confirmation_button.place(x=self.resolution_width - self.take_face_confirmation_button.winfo_reqwidth(), y=0)
            self.retake_face_confirmation_button.place_forget()
        elif task == "register":
            self.register_user_frame.place_forget()
            self.retake_face_confirmation_button.place_forget()
            self.take_face_confirmation_button.place_forget()
            self.start_get_data_user_button.place(x=self.resolution_width - self.take_face_confirmation_button.winfo_reqwidth()-10, y=0)
            self.restart_get_data_user_button.place_forget()
            self.prediction_thread = None
        self.open_camera_allow = True
        self.check_user_allow = False
        self.get_data_user_allow = False
        self.register_face_guidline_label.configure(text="Put face in the box",fg ="white",bg="gray")
        self.frame_capture = []
        self.boxes_capture = []
        self.left_captures = []
        self.right_captures = []
        self.left_face_count = 0
        self.right_face_count = 0
        self.cancel_face_activities_button.config(command=lambda: self.cancel_face_activities(task, authority))
        #self.open_camera(task, authority, task_category)#delay
        self.root.after(10, lambda: self.open_camera(task, authority, task_category))
        

    def cancel_face_activities(self, task, authority):
        self.open_camera_allow = False
        self.frame_capture = []
        self.boxes_capture = []
        self.left_captures = []
        self.right_captures = []
        self.left_face_count = 0
        self.right_face_count = 0
        self.face_activities_frame.place_forget()
        if task == "check":
            #self.choose_face_or_card_frame.place(x=0, y=0) #delay
            self.root.after(50, lambda: self.choose_face_or_card_frame.place(x=0, y=0))
        elif task == "register":
            #self.register_user_frame.place(x=0, y=0) #delay
            self.root.after(50, lambda: self.register_user_frame.place(x=0, y=0))
        self.register_face_button.config(fg="black", text=" Register Face ", bg="white", state=NORMAL,command=lambda: self.face_activities("register", "None", "None"))


    def switch_frame(self, frame_to_place, frame_to_forget, task_category):
        if frame_to_place != self.choose_check_inout_frame:
            self.choose_check_inout_frame.place_forget()
        if frame_to_place == self.choose_face_or_card_frame and frame_to_forget == self.choose_check_inout_frame:
            if task_category in ["check in", "check out"]:
                self.face_button.config(command=lambda: self.face_activities("check", "user", task_category))
                self.card_button.config(command=lambda: self.card_activities("check", "user", task_category))
                self.retake_face_confirmation_button.config(command=lambda: self.face_activities("check", "user", task_category))
            elif task_category in ["check admin authority"]:
                self.face_button.config(command=lambda: self.face_activities("check", "admin", task_category))
                self.card_button.config(command=lambda: self.card_activities("check", "admin", task_category))
                self.retake_face_confirmation_button.config(command=lambda: self.face_activities("check", "admin", task_category))
        if frame_to_place == self.register_user_frame and frame_to_forget == self.setting_frame:
            if task_category == "register user":
                self.register_face_button.config(command=lambda: self.face_activities("register", "user", task_category))
                self.restart_get_data_user_button.config(command=lambda: self.face_activities("register", "user", task_category))
            elif task_category == "register admin":
                self.register_face_button.config(command=lambda: self.face_activities("register", "admin", task_category))
                self.restart_get_data_user_button.config(command=lambda: self.face_activities("register", "admin", task_category))
            self.task_category = task_category
            with closing(sqlite3.connect('database/dataset.db', timeout=1)) as dataset_conn:
                dataset_conn.execute('PRAGMA journal_mode=WAL;')
                with closing(dataset_conn.cursor()) as dataset_cursor:
                    dataset_cursor.execute('SELECT ID FROM dataset ORDER BY ID')
                    existing_ids = [row[0] for row in dataset_cursor.fetchall()]
                    self.new_id = next((i for i in range(1, 1001) if i not in existing_ids), max(existing_ids, default=0) + 1)
                    self.register_title_label.config(text=f"ID: {self.new_id}")
                    self.check_confirm_add_user = True
                    self.register_department_combobox.config(text ="Select Department")
                    self.register_name_entry.config(state=NORMAL)
                    self.register_department_combobox.config(state=NORMAL)
                    self.create_department_button.config(state=NORMAL)
                    self.confirm_add_user()
        elif frame_to_place == self.setting_frame and frame_to_forget == self.register_user_frame:
            self.register_name_entry.config(text="")
            self.register_face_button.config(fg="black", text=" Register Face ", bg="white", state=NORMAL,command=lambda: self.face_activities("register", "None", "None"))
            self.register_card_button.config(fg="black", text=" Register Finger ", bg="white", state=NORMAL,command=lambda: self.card_activities("register", "None", "None"))
            self.register_department_combobox.config(text="")
            self.register_name_entry.config(state=NORMAL)
            self.register_department_combobox.config(state=NORMAL)
            self.create_department_button.config(state=NORMAL)
            self.current_entry = None
            self.frame_capture = []
            self.boxes_capture = []
            self.check_confirm_add_user = False
            self.get_card_allow = False
        frame_to_forget.place_forget()
        self.root.after(10, lambda: frame_to_place.place(x=0, y=0))
        
 
        
    def keyboard(self, entry, current_frame):
        self.current_entry = entry
        self.keyboard_box.config(text="")
        if self.current_entry in [self.register_name_entry, self.username_entry, self.password_entry]:
            self.keyboard_box.config(text=self.current_entry.cget('text'))
        elif self.current_entry == self.create_department_button:
            pass
        else:
            self.keyboard_box.config(text=self.current_entry.cget("text"))
        self.keyboard_frame.place(x=0, y=0)
        current_frame.place_forget()

    def confirm_keyboard(self):
        self.keyboard_frame.place_forget()
        if self.current_entry and self.current_entry not in [self.register_name_entry, self.username_entry,self.password_entry, self.create_department_button]:
            self.current_entry.config(text="")
            self.current_entry.config(text=self.keyboard_box.cget("text"))
        if self.current_entry == self.create_department_button:
            self.register_department_combobox.config(text=self.keyboard_box.cget("text"))
            self.register_user_frame.place(x=0, y=0)
        if self.current_entry == self.register_name_entry:
            self.register_name_entry.config(text=self.keyboard_box.cget("text"))
            self.register_user_frame.place(x=0, y=0)
        elif self.current_entry in [self.username_entry, self.password_entry]:
            self.info_content_frame.place(x=0, y=0)
        if self.keyboard_box.cget("text") != "":
            if self.current_entry == self.username_entry:
                self.username = self.keyboard_box.cget("text")
                self.username_entry.config(text=self.username)
            if self.current_entry == self.password_entry:
                self.password = self.keyboard_box.cget("text")
                self.password_entry.config(text=self.password)
            if self.current_entry == self.username_entry or self.current_entry == self.password_entry:
                with closing(sqlite3.connect('database/web.db', timeout=1)) as web_conn:
                    web_conn.execute('PRAGMA journal_mode=WAL;')
                    with closing(web_conn.cursor()) as web_cursor:
                        web_cursor.execute('DELETE FROM web')
                        web_cursor.execute('INSERT INTO web (Username, Password) VALUES (?, ?)',(self.username, self.password))
                        web_conn.commit()

    def toggle_caps_lock(self):
        self.caps_lock_on = not self.caps_lock_on
        for key, btn in self.buttons.items():
            if key.isalpha():
                new_text = key.upper() if self.caps_lock_on else key.lower()
                btn.config(text=new_text)

    def handle_button_click(self, alfabet):
        current = self.keyboard_box.cget("text")
        if alfabet == 'Del':
            self.keyboard_box.config(text="")
            self.keyboard_box.config(text=current[:-1])
        else:
            if self.caps_lock_on and alfabet.isalpha():
                alfabet = alfabet.upper() if alfabet.islower() else alfabet.lower()
            self.keyboard_box.config(text="")
            self.keyboard_box.config(text=str(current) + str(alfabet))


    def ask_to_confirm_action(self, action, current_frame, next_frame):
        if action == "None":
            if current_frame == self.register_user_frame:
                current_frame.place_forget()
                self.confirm_yes_action_button.configure(command=lambda: self.ask_to_confirm_action("Yes", self.register_user_frame,self.setting_frame))
                self.confirm_no_action_button.configure(command=lambda: self.ask_to_confirm_action("No", self.register_user_frame,self.setting_frame))
            self.confirm_action_frane.place(x=0, y=0)
        elif action == "Yes":
            next_frame.place(x=0, y=0)
            self.confirm_action_frane.place_forget()
            if current_frame == self.register_user_frame:
                try:
                    self.finger.delete_model(self.new_id)
                except:
                    print("Error in delete finger")
                #self.switch_frame(self.setting_frame, self.register_user_frame, self.task_category) #delay
                self.root.after(50, self.switch_frame, self.setting_frame, self.register_user_frame, self.task_category)
        elif action == "No":
            if current_frame == self.register_user_frame:
                current_frame.place(x=0, y=0)
            self.confirm_action_frane.place_forget()
        time.sleep(0.2)

    def update_timekeeping_db(self, task_category):
        update_not_successful = False
        name = self.name_authentication_label.cget("text").split(": ")[1]
        department = self.department_authentication_label.cget("text").split(": ")[1]
        user_id = self.id_authentication_label.cget("text").split(": ")[1]
        datetime_str = self.time_authentication_label.cget("text").split(": ")[1]
        date_str, time_str = datetime_str.split(" ")
        with closing(sqlite3.connect('database/timekeeping.db', timeout=1)) as timekeeping_conn:
            timekeeping_conn.execute('PRAGMA journal_mode=WAL;')
            with closing(timekeeping_conn.cursor()) as timekeeping_cursor:
                timekeeping_cursor.execute('SELECT * FROM timekeeping WHERE "Date"=? AND "Department"=? AND "ID"=? AND "Name"=? ORDER BY rowid DESC',(date_str, department, user_id, name))
                latest_entry = timekeeping_cursor.fetchone()
                if latest_entry:
                    if task_category == "check in":
                        if latest_entry[4] != "-" and latest_entry[5] != "-":
                            timekeeping_cursor.execute('INSERT INTO timekeeping ("Date", "Department", "ID", "Name", "In", "Out") VALUES (?, ?, ?, ?, ?, ?)',(date_str, department, user_id, name, time_str, "-"))
                        elif latest_entry[4] != "-" and latest_entry[5] == "-":
                            self.authentication_guidline_label.config(text="You've already checked in!",fg="red")
                            update_not_successful = True
                            return
                    elif task_category == "check out":
                        if latest_entry[4] != "-" and latest_entry[5] == "-":
                            timekeeping_cursor.execute('UPDATE timekeeping SET "Out"=? WHERE "Date"=? AND "ID"=? AND "Name"=? AND "Out"=?',(time_str, date_str, user_id, name, "-"))
                        else:
                            if latest_entry[4] == "-":
                                self.authentication_guidline_label.config(text="You can't check out before checking in!",fg="red")
                            else:
                                self.authentication_guidline_label.config(text="You've already checked out!",fg="red")
                            update_not_successful = True
                            return
                else:
                    if task_category == "check out":
                        self.authentication_guidline_label.config(text="You haven't checked in yet!",fg="red")
                        update_not_successful = True
                        return
                    elif task_category == "check in":
                        timekeeping_cursor.execute('INSERT INTO timekeeping ("Date", "Department", "ID", "Name", "In", "Out") VALUES (?, ?, ?, ?, ?, ?)',(date_str, department, user_id, name, time_str, "-"))
            timekeeping_conn.commit()
        if not update_not_successful:
            self.authentication_guidline_label.config(text="Please authenticate",fg="white")
            #self.switch_frame(self.choose_check_inout_frame, self.authentication_frame, task_category) #delay
            self.root.after(50, self.switch_frame, self.choose_check_inout_frame, self.authentication_frame, task_category)

    def to_numpy(self,tensor):
        return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

    def run_onnx_model(self,face):
        ort_inputs = {self.ort_session.get_inputs()[0].name: self.to_numpy(face)}
        ort_outs = self.ort_session.run(None, ort_inputs)
        return torch.tensor(ort_outs[0])

    def Face_alignment(self, img, bbox):
        try:
            x1, y1, x2, y2 = map(int, bbox[:4])
            h, w, _ = img.shape
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
            face = img[y1:y2, x1:x2]
            face = cv2.resize(face, (112, 112))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            return face
        except Exception as e:
            print(f"Error in Face_alignment: {e}")
            return None


    def train_model(self):
        def prepare_facebank(model, tta=True):
            embeddings, names = [], ['']
            embs = []
            def process_frame_bbox(frame, bbox):
                x1, y1, x2, y2 = bbox
                aligned_face = self.Face_alignment(frame, (x1, y1, x2, y2))
                if aligned_face is None:
                    print(f"[ERROR] Face alignment failed ")
                    return
                with torch.no_grad():
                    if tta:
                        mirror = cv2.flip(aligned_face, 1)
                        emb = model(self.test_transform(aligned_face).unsqueeze(0).to(self.device))
                        emb_mirror = model(self.test_transform(mirror).unsqueeze(0).to(self.device))
                        embs.append(self.l2_norm(emb + emb_mirror))
                    else:
                        embs.append(model(self.test_transform(aligned_face).unsqueeze(0).to(self.device)))
                if len(embs) == 0:
                    return

            threads = []
            for frame, bbox in zip(self.frame_capture, self.boxes_capture):
                #process_frame_bbox (frame,bbox)
                #time.sleep(0.1)
                thread = threading.Thread(target=process_frame_bbox, args=(frame, bbox))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            if len(embs) > 0:
                embedding = torch.cat(embs).mean(0, keepdim=True)
                embeddings.append(embedding)
                names.append(self.user_image_dir)
            if len(embeddings) > 0:
                embeddings = torch.cat(embeddings)
            else:
                embeddings = torch.empty(0, 512)
            names = np.array(names)
            return embeddings, names


        ##########train##########
        if self.allow_training:
            time.sleep(0.2)
            with open('facebank/data.pickle', 'rb') as f:
                data = pickle.load(f)
                existing_embeddings = data['embeddings'].to(self.device)
                existing_names = data['names']
            print(f" all names before training data:{existing_names}")
            new_embeddings, new_names = prepare_facebank(self.run_onnx_model, tta=True)
            if new_embeddings.size(0) == 0:
                return
            for i, name in enumerate(new_names[1:]):
                if name not in existing_names:
                    if i < len(new_embeddings):
                        existing_names = np.append(existing_names, name)
                        existing_embeddings = torch.cat((existing_embeddings, new_embeddings[i].unsqueeze(0).to(self.device)), dim=0)
            with open('facebank/data.pickle', "wb") as data_file:
                pickle.dump({'embeddings': existing_embeddings, 'names': existing_names}, data_file)
            print(f" all names after training data:{existing_names}")
            self.root.after(50, self.switch_frame, self.setting_frame, self.please_wait_frame,self.task_category)
            self.frame_capture = []
            self.boxes_capture = []
            self.allow_training = False
        self.root.after(1000, self.train_model)

    def confirm_add_user(self):
        both_face_and_finger = False
        if self.check_confirm_add_user == True and both_face_and_finger == True:
            if self.register_name_entry.cget("text") != "" and self.register_department_combobox.cget('text') != "" and self.register_department_combobox.cget('text') != "Select Department":
                self.register_face_button.config(state=NORMAL)
            else:
                self.register_face_button.config(state=DISABLED)
                self.register_card_button.config(state=DISABLED)
                self.confirm_register_button.config(state=DISABLED)
            if self.register_face_button.cget("bg") == "green":
                self.register_card_button.config(state=NORMAL)
                self.register_face_button.config(state=DISABLED)
                self.register_name_entry.config(state=DISABLED)
                self.register_department_combobox.config(state=DISABLED)
                self.create_department_button.config(state=DISABLED)
            if self.register_card_button.cget("bg") == "green" and self.register_face_button.cget("bg") == "green":
                self.register_card_button.config(state=DISABLED)
                self.confirm_register_button.config(state=NORMAL)
            self.root.after(100, self.confirm_add_user)
        elif self.check_confirm_add_user == True and both_face_and_finger == False:
            if self.register_name_entry.cget("text") != "" and self.register_department_combobox.cget('text') != "" and self.register_department_combobox.cget('text') != "Select Department":
                self.register_face_button.config(state=NORMAL)
            else:
                self.register_face_button.config(state=DISABLED)
                self.register_card_button.config(state=DISABLED)
                self.confirm_register_button.config(state=DISABLED)
            if self.register_face_button.cget("bg") == "green":
                self.register_card_button.config(state=NORMAL)
                self.register_face_button.config(state=DISABLED)
                self.register_name_entry.config(state=DISABLED)
                self.register_department_combobox.config(state=DISABLED)
                self.create_department_button.config(state=DISABLED)
                self.confirm_register_button.config(state=NORMAL)
            self.root.after(100, self.confirm_add_user)


    def update_database_db(self, task_category):
        self.root.after(0, self.switch_frame, self.please_wait_frame, self.register_user_frame,self.task_category)
        task_category = self.task_category
        user_id = self.register_title_label.cget("text").split(": ")[1]
        user_name = self.register_name_entry.cget("text")
        user_authority = task_category.split(" ")[1]
        user_department = self.register_department_combobox.cget('text')
        self.register_name_entry.config(text="")
        self.register_face_button.config(fg="black", text=" Register Face ", bg="white", state=NORMAL,command=lambda: self.face_activities("register", "None", "None"))
        self.register_card_button.config(fg="black", text=" Register Finger ", bg="white", state=NORMAL,command=lambda: self.card_activities("register", "None", "None"))
        self.register_department_combobox.config(text="")
        self.user_path_dir = os.path.join('dataset',f"{user_id}-{user_name}-{user_authority}-{user_department}")
        self.user_image_dir = f"{user_id}-{user_name}-{user_authority}-{user_department}"
        user_path_dir = self.user_path_dir
        if not os.path.exists(user_path_dir):
            os.makedirs(user_path_dir)
        for i, (frame, bbox) in enumerate(zip(self.frame_capture, self.boxes_capture)):
            x1, y1, x2, y2 = bbox
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(frame.shape[1], x2), min(frame.shape[0], y2)
            face_area = frame[y1:y2, x1:x2]
            cv2.imwrite(f"{user_path_dir}/{i}.jpg", face_area)
        with closing(sqlite3.connect('database/dataset.db', timeout=1)) as dataset_conn:
            dataset_conn.execute('PRAGMA journal_mode=WAL;')
            with closing(dataset_conn.cursor()) as dataset_cursor:
                dataset_cursor.execute('SELECT * FROM dataset WHERE ID=?', (user_id,))
                dataset_entry = dataset_cursor.fetchone()
                if not dataset_entry:
                    dataset_cursor.execute('INSERT INTO dataset (ID, Name, Authority, Department) VALUES (?, ?, ?, ?)',(user_id, user_name, user_authority, user_department))
                    dataset_conn.commit()
        with closing(sqlite3.connect('database/department.db', timeout=1)) as department_conn:
            department_conn.execute('PRAGMA journal_mode=WAL;')
            with closing(department_conn.cursor()) as department_cursor:
                department_cursor.execute('SELECT * FROM departments WHERE department=?', (user_department,))
                department_entry = department_cursor.fetchone()
                if not department_entry:
                    department_cursor.execute('INSERT INTO departments (department) VALUES (?)', (user_department,))
                    department_conn.commit()
                    department_cursor.execute('SELECT department FROM departments')
                    self.user_departments = [row[0] for row in department_cursor.fetchall()]
        self.allow_training = True
        self.confirm_register_button.config(state=DISABLED)


    def authentication(self, method, user_recognized, task_category):
        self.task_category = task_category
        if method == "face":
            self.face_activities_frame.place_forget()
        elif method == "finger":
            self.get_card_allow = False
            self.card_activities_frame.place_forget()
        #self.authentication_frame.place(x=0, y=0) #delay
        if user_recognized != "unknown":
            user_info = user_recognized.split('-')
            self.user_info = user_info
            user_id = user_info[0]
            user_name = user_info[1]
            user_department = user_info[3]
            user_image_dir = os.path.join('dataset', user_recognized)
            image_files = [f for f in os.listdir(user_image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                image_files.sort()
                middle_index = len(image_files) // 2
                user_image_path = os.path.join(user_image_dir, image_files[middle_index])
            else:
                user_image_path = None
            self.authentication_guidline_label.config(text = "Please authenticate",fg="white")
            user_image = self.convert_image_for_tkinter(user_image_path,(self.resolution_width // 2, self.resolution_height // 2))
            self.face_detected_authentication_label.config(image=user_image)
            self.face_detected_authentication_label.image = user_image
            self.face_detected_authentication_label.pack()
            self.name_authentication_label.config(text=f"Name: {user_name}")
            self.department_authentication_label.config(text=f"Department: {user_department}")
            self.id_authentication_label.config(text=f"ID: {user_id}")
            current_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_authentication_label.config(text=f"Time: {current_time}")
            self.root.after(50, lambda: self.authentication_frame.place(x=0, y=0))
      


    def get_card_input(self, task, authority, task_category):
        if self.get_card_allow == True:
            print("scanning")
            check_press = self.finger.get_image()
            #time.sleep(0.2)
            if check_press != adafruit_fingerprint.NOFINGER:
                get_print = self.finger.get_image()
                #time.sleep(0.3)
                if get_print == adafruit_fingerprint.OK:
                    print(task)
                    if task == "check":
                        print("checking")
                        self.handle_fingerprint_check(task, authority, task_category)
                    elif task == "register":
                        if self.fingerprint_buffer == 0 and self.fingerprint_already_exist == True:
                            self.update_guideline_message("Remove finger. Finger already exist", "red")
                            self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                        elif (self.fingerprint_buffer == 0 and self.fingerprint_already_exist == False) or self.fingerprint_buffer == 2:
                            self.handle_fingerprint_registration(task, authority, task_category)
                        elif self.fingerprint_buffer == 1: # different finger
                            self.update_guideline_message("            Remove finger", "green")
                            self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                else:
                    self.update_guideline_message("  Take image failed, retrying", "red")
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
            else:
                self.fingerprint_already_exist = False
                if task == "register" and (self.fingerprint_buffer == 1 or self.fingerprint_buffer == 2):
                    self.update_guideline_message("     Place the same finger again", "green") # different finger
                    self.fingerprint_buffer = 2 # different finger
                    #self.update_guideline_message("Do not remove finger, try again", "red")
                    #self.fingerprint_buffer = 0 
                    self.root.after(100, lambda: self.get_card_input(task, authority, task_category))
                else:
                    self.update_guideline_message("No finger detected, place finger", "red")
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))

    def handle_fingerprint_check(self, task, authority, task_category):
        template_buffer_1 = self.finger.image_2_tz(1)
        time.sleep(0.3)
        if template_buffer_1 == adafruit_fingerprint.OK:
            self.card_recogintion_operation(task, authority, task_category)
        else:
            self.update_guideline_message("  Template failed, retrying..", "red")
            self.root.after(10, lambda: self.get_card_input(task, authority, task_category))

    def handle_fingerprint_registration(self, task, authority, task_category):
        if self.fingerprint_buffer == 0:
            template_buffer_1 = self.finger.image_2_tz(1)
            time.sleep(0.2)
            if  template_buffer_1 == adafruit_fingerprint.OK:
                self.update_guideline_message("             Keep pressing", "green")
                self.card_recogintion_operation(task, authority, task_category)
            else:
                self.update_guideline_message("  Template failed, retrying..", "red")
                self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
        elif self.fingerprint_buffer == 2:
            template_buffer_2 = self.finger.image_2_tz(2)
            time.sleep(0.2)
            if template_buffer_2 == adafruit_fingerprint.OK:
                self.update_guideline_message("             Keep pressing", "green")
                self.card_recogintion_operation(task, authority, task_category)
            else:
                self.update_guideline_message("  Template failed, retrying..", "red")
                self.fingerprint_buffer = 0
                self.root.after(50, lambda: self.get_card_input(task, authority, task_category))

    def update_guideline_message(self, message, color):
        self.insert_card_guidline_label.config(text=message, fg=color)

    def card_recogintion_operation(self, task, authority, task_category):
        if task == "check":
            recognize_finger_time = time.time()
            search_user = self.finger.finger_fast_search()
            time.sleep(0.5)
            print(f"recognize_finger_time: {time.time() - recognize_finger_time}")
            if search_user != adafruit_fingerprint.OK:
                self.insert_card_guidline_label.config(text="     No permission, please retry", fg='red')
                self.root.after(1000, lambda: self.get_card_input(task, authority, task_category))
            else:
                print("Detected #", self.finger.finger_id, "with confidence", self.finger.confidence)
                with closing(sqlite3.connect('database/dataset.db', timeout=1)) as dataset_conn:
                    dataset_conn.execute('PRAGMA journal_mode=WAL;')
                    with closing(dataset_conn.cursor()) as dataset_cursor:
                        dataset_cursor.execute('SELECT * FROM dataset WHERE ID=?', (self.finger.finger_id,))
                        user_entry = dataset_cursor.fetchone()
                        if user_entry[2] == authority or (user_entry[2] != authority and user_entry[2] == "admin"):
                            if task_category in ["check in", "check out"]:
                                user_info = f'{user_entry[0]}-{user_entry[1]}-{user_entry[2]}-{user_entry[3]}'
                                self.authentication("finger", user_info, task_category)
                            elif task_category == "check admin authority":
                                #self.switch_frame(self.setting_frame, self.card_activities_frame, task_category)# delay
                                self.root.after(50, self.switch_frame, self.setting_frame, self.card_activities_frame, task_category)
                        else:
                            self.insert_card_guidline_label.config(text=f"     No {authority} permission", fg='red')
                            self.root.after(100, lambda: self.get_card_input(task, authority, task_category))

        elif task == "register":
            if self.fingerprint_buffer == 0:
                search_user = self.finger.finger_fast_search()
                time.sleep(0.5)
                if search_user == adafruit_fingerprint.OK:
                    self.insert_card_guidline_label.config(text="     Finger already exists", fg='red')
                    self.fingerprint_already_exist = True
                    self.root.after(50, lambda: self.get_card_input(task, authority, task_category))
                else:
                    self.fingerprint_buffer = 1 #different finger
                    #self.fingerprint_buffer = 2
                    self.fingerprint_already_exist = False
                    self.root.after(1000, lambda: self.get_card_input(task, authority, task_category))
            elif self.fingerprint_buffer == 2:
                i = self.finger.create_model()
                time.sleep(0.1)
                if i == adafruit_fingerprint.OK:
                    a = self.finger.store_model(self.new_id)
                    if a == adafruit_fingerprint.OK:
                        self.fingerprint_buffer = 0
                        #self.switch_frame(self.register_user_frame, self.card_activities_frame, task_category)#delay
                        self.get_card_allow = False
                        self.root.after(50, self.switch_frame, self.register_user_frame, self.card_activities_frame,task_category)
                        self.register_card_button.config(text="", bg="green", state=DISABLED,width=self.resolution_width // 3 + self.resolution_width // 5)
                    else:
                        if a == adafruit_fingerprint.BADLOCATION:
                            print("Bad storage location")
                        elif a == adafruit_fingerprint.FLASHERR:
                            print("Flash storage error")
                        else:
                            print("Other error")
                else:
                    if i == adafruit_fingerprint.ENROLLMISMATCH:
                        self.insert_card_guidline_label.config(text="        Not the same finger", fg='red')
                        #self.fingerprint_buffer = 0 # different finger
                        self.root.after(100, lambda: self.get_card_input(task, authority, task_category))
                    else:
                        self.insert_card_guidline_label.config(text="      Other error", fg='red')
                        self.root.after(50, lambda: self.get_card_input(task, authority, task_category))
        

    def face_recogintion_operation(self, task, authority, task_category):
        def process_frame_bbox(frame, bbox, existing_names,existing_embeddings, recognized_names, device, run_onnx_model, test_transform):
            embs = []
            face = self.Face_alignment(frame, bbox)
            face = test_transform(face).to(device).unsqueeze(0)
            with torch.no_grad():
                emb = run_onnx_model(face)
            embs.append(emb)
            if embs:
                source_embs = torch.cat(embs).to(device)
            else:
                source_embs = torch.empty(0, 512).to(device)
            if source_embs.size(0) == 0:
                return
            if len(existing_embeddings) == 0:
                recognized_names.append("Unknown")
                return
            results = [-1] * len(source_embs)
            if len(source_embs) > 0:
                diff = source_embs.unsqueeze(-1) - existing_embeddings.transpose(1, 0).unsqueeze(0).to(device)
                dist = torch.sum(torch.pow(diff, 2), dim=1).to(device)
                minimum, min_idx = torch.min(dist, dim=1)
                min_idx[minimum > 1.2] = -1
                results = min_idx
            for i in range(len(results)):
                if i < len(results) and i < len(existing_names):
                    if results[i] != -1 and results[i] < len(existing_names):
                        name = existing_names[results[i]]
                    else:
                        name = "Unknown"
                else:
                    name = "Unknown"
                recognized_names.append(name)
        if task == "check":
            regconize_face_time = time.time()
            recognized_names = []
            with open('facebank/data.pickle', 'rb') as f:
                data = pickle.load(f)
            existing_names = data['names']
            existing_embeddings = data['embeddings']
            print(f"Existing names in data before recognize to check:{existing_names}")
            user_recognized = "Unknown"
            for frame, bbox in zip(self.frame_capture, self.boxes_capture):
                process_frame_bbox(frame, bbox, existing_names,existing_embeddings, recognized_names, self.device, self.run_onnx_model,self.test_transform)
            print(f"recognized_names: {recognized_names}")
            most_common_name = Counter(recognized_names).most_common(1)[0][0]
            print(f"recognize time: {time.time() - regconize_face_time}")
            if user_recognized != most_common_name:
                user_recognized = most_common_name
                self.frame_capture = []
                self.boxes_capture = []
                user_info = user_recognized.split('-')
                if user_info[2] == authority or (user_info[2] != authority and user_info[2]=="admin"):
                    if task_category in ["check in", "check out"]:
                        self.open_camera_allow = False
                        self.authentication("face", user_recognized, task_category)
                    elif task_category == "check admin authority":
                        self.open_camera_allow = False
                        #self.switch_frame(self.setting_frame, self.face_activities_frame, task_category)#delay
                        self.root.after(50, self.switch_frame, self.setting_frame, self.face_activities_frame,task_category)
                        
                else:
                    self.frame_capture = []
                    self.boxes_capture = []
                    self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                    self.register_face_guidline_label.configure(text=f"No {authority} permission", fg="red")
            else:
                self.frame_capture = []
                self.boxes_capture = []
                self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                self.register_face_guidline_label.configure(text="No permission", fg="red")

        elif task == "register":
            recognized_names = []
            with open('facebank/data.pickle', 'rb') as f:
                data = pickle.load(f)
            existing_names = data['names']
            existing_embeddings = data['embeddings']
            print(f"Existing names in data before recognize to register:{existing_names}")
            user_recognized = "Unknown"
            i=0
            for frame, bbox in zip(self.frame_capture, self.boxes_capture):
                if i in [3,self.number_of_face_to_train//2,self.number_of_face_to_train-1]:
                    process_frame_bbox(frame, bbox, existing_names,existing_embeddings, recognized_names, self.device, self.run_onnx_model,self.test_transform)
                i+=1
            print(f"names already exists: {recognized_names}")
            most_common_name = Counter(recognized_names).most_common(1)[0][0]
            if most_common_name != user_recognized:
                self.register_face_guidline_label.config(text=f"User already exists", fg="red")
                self.restart_get_data_user_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth()-10, y=0)
                self.get_data_user_allow = False
                self.frame_capture =[]
                self.boxes_capture = []
            else:
                #self.switch_frame(self.register_user_frame, self.face_activities_frame, task_category)
                self.open_camera_allow = False
                self.root.after(50, self.switch_frame, self.register_user_frame, self.face_activities_frame, task_category)
                self.register_face_button.config(text="", bg="green", state=DISABLED,width = self.resolution_width//3 + self.resolution_width//5)

    def check_user(self,task):
        if task == "check":
            self.check_user_allow = True
            self.take_face_confirmation_button.place_forget()
        elif task == "register":
            self.get_data_user_allow = True
            self.start_get_data_user_button.place_forget()

    def update_camera_frame(self, opencv_image = None):
        display_frame = cv2.resize(opencv_image,(self.resolution_width, 6 * (self.resolution_height // 7)))
        captured_image = Image.fromarray(display_frame)
        photo_image = ImageTk.PhotoImage(image=captured_image)
        self.camera_label.photo_image = photo_image
        self.camera_label.configure(image=photo_image, width=self.resolution_width, height=6 * (self.resolution_height // 7))

    def make_prediction_thread(self, frame_to_predict):        
        if frame_to_predict is not None and self.prediction_queue.empty():
            bboxes, landmarks, predictions = self.make_prediction(frame_to_predict, self.face_detector, self.anti_spoof_detector, allow_predict_spoof=True)
            self.prediction_queue.put((bboxes, landmarks, predictions))
    
    def make_prediction(self,img, face_detector, anti_spoof, allow_predict_spoof):
        n = 10
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        frame_area = img.shape[0] * img.shape[1]
        min_face_area = frame_area / n
        boxes, scores, classids, kpts = face_detector.detect(img)
        predictions = []
        bboxes = []
        lanmarks = kpts
        for box, kpt, score in zip(boxes, kpts, scores):
            x, y, w, h = box.astype(int)
            face_area = w * h
            # if face_area >= min_face_area:## bo khuon mat qua nho ( nho hon n lan so voi khung hinh)
            #print(f' face score {score}')
            if score>0.6:
                bbox = np.array([x, y, x + w, y + h])
                bboxes.append(bbox)
                if allow_predict_spoof == True:
                    s= time.time()
                    pred = anti_spoof([increased_crop(img, bbox, bbox_inc=1.5)])[0]
                    score_pred = pred[0][0]
                    #print(f' face pred score {score_pred}')
                    label = np.argmax(pred)

                    predictions.append((bbox, label, score_pred, kpt))
        bboxes = np.array(bboxes)
        return bboxes, lanmarks, predictions
       
       
    def find_available_camera(self):
        device_paths = ["/dev/video0", "/dev/video1"]
        for device_path in device_paths:
            cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
            if cap.isOpened():
                print(f"Camera available at {device_path}")
                return cap
            else:
                cap.release()
        print("No available cameras found.")
        return None

    def open_camera(self, task, authority, task_category):
        if self.open_camera_allow == True:
            try:
                ret, frame = self.vid.read()
                if ret and frame is not None:
                    opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    height, width = opencv_image.shape[:2]
                    face_area_to_detect = (width // 5, height // 5, 3 * width // 5, 3 * height // 5)
                    overlay = np.zeros_like(opencv_image)
                    overlay[:] = (0, 0, 0, 128)
                    x, y, w, h = face_area_to_detect
                    overlay[y:y + h, x:x + w] = opencv_image[y:y + h, x:x + w]
                    cv2.addWeighted(overlay, 0.5, opencv_image, 0.5, 0, opencv_image)
                    frame_to_predict = np.zeros_like(opencv_image)
                    frame_to_predict[y:y + h, x:x + w] = opencv_image[y:y + h, x:x + w]
                    frame_to_predict = cv2.cvtColor(frame_to_predict, cv2.COLOR_RGBA2BGR)
                    self.update_camera_frame(opencv_image)
                    if task == "check" and self.check_user_allow == True:
                        bboxes, landmarks, predictions = self.make_prediction(frame_to_predict, self.face_detector,self.anti_spoof_detector,allow_predict_spoof=True)
                        if len(bboxes) == 1:
                            (x1, y1, x2, y2), label, score, kpt = predictions[0]
                            color_bgr = (0, 255, 0)
                            color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                            cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                            self.update_camera_frame(opencv_image)
                            if label in [1, 2, 3, 7, 8, 9] and score < 0.8:
                                self.register_face_guidline_label.configure(text="Spoofing detected", fg="red")
                                self.update_camera_frame(opencv_image)
                                self.frame_capture = []
                                self.boxes_capture = []
                                self.take_face_confirmation_button.place_forget()
                                self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(),y=0)
                            else:
                                self.frame_capture.append(frame_to_predict)
                                self.boxes_capture.append(bboxes[0])
                                self.face_recogintion_operation(task, authority, task_category)
                        elif len(bboxes) >= 2:
                            self.register_face_guidline_label.configure(text="Only one face is allowed", fg="red")
                            for bbox in bboxes:
                                (x1, y1, x2, y2) = bbox
                                color_bgr = (0, 0, 255)
                                color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                                cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                            self.update_camera_frame(opencv_image)
                            self.frame_capture = []
                            self.boxes_capture = []
                            self.take_face_confirmation_button.place_forget()
                            self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                        elif len(bboxes) == 0:
                            self.frame_capture = []
                            self.register_face_guidline_label.configure(text="Face not found", fg="red")
                            self.take_face_confirmation_button.place_forget()
                            self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                    elif task == "check" and self.check_user_allow == False:
                        self.root.after(10, lambda: self.open_camera(task, authority, task_category))
                    elif task == "register" and self.get_data_user_allow == False:
                        self.root.after(10, lambda: self.open_camera(task, authority, task_category))
                    elif task == "register" and self.get_data_user_allow == True:
                        no_direction = True
                        with self.thread_lock:
                            if (self.prediction_thread is None or not self.prediction_thread.is_alive()) and self.prediction_queue.empty():
                                self.prediction_thread = threading.Thread(target=self.make_prediction_thread,args=(frame_to_predict,))
                                self.prediction_thread.start()
                        if not self.prediction_queue.empty():
                            bboxes, landmarks, predictions = self.prediction_queue.get()
                            self.prediction_queue.queue.clear()
                            if len(bboxes) == 1:
                                (x1, y1, x2, y2), label, score, kpt = predictions[0]
                                color_bgr = (0, 255, 0)
                                color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                                cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                                self.update_camera_frame(opencv_image)
                                if label in [1, 2, 3, 7, 8, 9]:
                                    # if 0:
                                    self.register_face_guidline_label.configure(text="Spoofing detected", fg="red")
                                    self.update_camera_frame(opencv_image)
                                    self.start_get_data_user_button.place_forget()
                                    self.restart_get_data_user_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(),y=0)
                                    self.get_data_user_allow = False
                                else:
                                    def calculate_distance(landmark1, landmark2):
                                        return np.sqrt(np.sum((landmark1 - landmark2) ** 2))
                                    def save_user(frame_to_predict, bboxes, x1, y1, x2, y2):
                                        self.frame_capture.append(frame_to_predict)
                                        self.boxes_capture.append(bboxes[0])
                                        frame_to_predict_flip = cv2.flip(frame_to_predict, 1)
                                        self.frame_capture.append(frame_to_predict_flip)
                                        flipped_x1 = frame_to_predict.shape[1] - x2
                                        flipped_x2 = frame_to_predict.shape[1] - x1
                                        flipped_bbox = np.array([flipped_x1, y1, flipped_x2, y2])
                                        self.boxes_capture.append(flipped_bbox)
                                    bbox = bboxes[0]
                                    p = landmarks[0]
                                    left_eye_x = p[0]
                                    right_eye_x = p[3]
                                    left_edge_dist = left_eye_x - bbox[0]
                                    right_edge_dist = bbox[2] - right_eye_x
                                    face_direction = "left" if left_edge_dist < right_edge_dist else "right"
                                    threshold_face_direction = 3
                                    if len(self.frame_capture) == 0 and abs(left_edge_dist - right_edge_dist) <= 20 and no_direction == False:
                                        print("look strange")
                                        save_user(frame_to_predict, bboxes, x1, y1, x2, y2)
                                    if self.left_face_count < self.number_of_face_to_train // 4 and no_direction == False:
                                        self.register_face_guidline_label.configure(text=f"Turn face to the left: {100 * self.left_face_count // (self.number_of_face_to_train // 4)}%",fg="white")
                                        if face_direction == "left":
                                            if not self.left_captures or calculate_distance(self.left_captures[-1],np.array([left_eye_x,right_eye_x])) > threshold_face_direction:
                                                save_user(frame_to_predict, bboxes, x1, y1, x2, y2)
                                                self.left_face_count += 1
                                                self.left_captures.append(np.array([left_eye_x, right_eye_x]))
                                    elif self.left_face_count == self.number_of_face_to_train // 4 and no_direction == False:
                                        self.register_face_guidline_label.configure(
                                            text=f"Turn face to the right: {100 * self.right_face_count // (self.number_of_face_to_train // 4)}%",
                                            fg="white")
                                        if face_direction == "right" and self.right_face_count <= self.number_of_face_to_train // 4:
                                            if not self.right_captures or calculate_distance(self.right_captures[-1],np.array([left_eye_x,right_eye_x])) > threshold_face_direction:
                                                save_user(frame_to_predict, bboxes, x1, y1, x2, y2)
                                                self.right_face_count += 1
                                                self.right_captures.append(np.array([left_eye_x, right_eye_x]))
                                                self.register_face_guidline_label.configure(text=f"Turn face to the right: {100 * self.right_face_count // (self.number_of_face_to_train // 4)}%",fg="white")

                                    if no_direction == True:
                                        save_user(frame_to_predict, bboxes, x1, y1, x2, y2)
                            if len(bboxes) >= 2:
                                self.register_face_guidline_label.configure(text="Only one face is allowed", fg="red")
                                for bbox in bboxes:
                                    (x1, y1, x2, y2) = bbox
                                    color_bgr = (0, 0, 255)
                                    color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                                    cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                                self.update_camera_frame(opencv_image)
                                self.start_get_data_user_button.place_forget()
                                self.restart_get_data_user_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth() - 10,y=0)
                                self.open_camera_allow = False
                                self.get_data_user_allow = False
                            if len(bboxes) == 0:
                                self.register_face_guidline_label.configure(text="Face not found", fg="red")
                            if (self.left_face_count >= self.number_of_face_to_train // 4) and (self.right_face_count >= self.number_of_face_to_train // 4) and len(self.frame_capture) >= self.number_of_face_to_train + 2 and no_direction == False:
                                self.left_face_count = 0
                                self.right_face_count = 0
                                self.left_captures = []
                                self.right_captures = []
                                self.face_recogintion_operation(task, authority, task_category)
                            elif len(self.frame_capture) >= 5 and no_direction == True:
                                self.left_face_count = 0
                                self.right_face_count = 0
                                self.left_captures = []
                                self.right_captures = []
                                self.face_recogintion_operation(task, authority, task_category)
                            else:
                                self.root.after(10, lambda: self.open_camera(task, authority, task_category))
                        else:
                            self.root.after(10, lambda: self.open_camera(task, authority, task_category))
                else:
                    print(f"Error reading from camera: Retrying in 1 second...")
                    self.vid.release()
                    time.sleep(1)
                    self.vid = self.find_available_camera()
                    if self.vid is not None:
                        self.root.after(1000, lambda: self.open_camera(task, authority, task_category))
                    else:
                        print("Failed to reconnect to the camera.")
            except Exception as e:
                print(f"Error reading from camera: {e}. Retrying in 1 second...")
                self.vid.release()
                time.sleep(1)
                self.vid = self.find_available_camera()
                if self.vid is not None:
                    self.root.after(1000, lambda: self.open_camera(task, authority, task_category))
                else:
                    print("Failed to reconnect to the camera.")

def find_available_camera():
    device_paths = ["/dev/video0", "/dev/video1"] 
    for device_path in device_paths:
        cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"Camera available and working at {device_path}")
                return cap
            else:
                print(f"Camera at {device_path} is not returning frames. Retrying...")
                cap.release()
                return None
        else:
            print(f"Camera at {device_path} could not be opened. Retrying...")
            cap.release()
            return None

def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()
    
def run_onnx_model(face,ort_session):
    ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(face)}
    ort_outs = ort_session.run(None, ort_inputs)
    return torch.tensor(ort_outs[0])

def main():
    vid = find_available_camera()
    if vid is None:
        print("Error in open camera")
        return
    vid.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
    #vid.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    #vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    #vid.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    start = time.time()
    s= time.time()
    path_face = os.path.abspath("Weights/face.onnx")
    face_detector = YOLOv8_face(path_face, conf_thres=0.7, iou_thres=0.2)
    test_image = cv2.imread("test_system.jpg")
    _ = make_prediction(test_image,face_detector)
    print(f"face_detector_load :{time.time()-s}")
    #onnx_model_path = 'Weights/MobileFaceNet.onnx'
    test_image = cv2.imread("test_system.jpg")
    anti_spoof_detector = AntiSpoof("Weights/spoof.onnx")
    _, _, _ = make_prediction(test_image, face_detector, anti_spoof_detector,allow_predict_spoof=True)
    onnx_model_path = os.path.abspath("Weights/MobileFaceNet.onnx")
    try:
        ort_session = ort.InferenceSession(onnx_model_path,providers=['TensorrtExecutionProvider'])
    except:
        ort_session = ort.InferenceSession(onnx_model_path,providers=['CUDAExecutionProvider'])
    test_transform = trans.Compose([trans.ToTensor(), trans.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])])
    s= time.time()
    dummy_input = torch.randn(1, 3, 112, 112).to(device)
    _ = run_onnx_model(dummy_input, ort_session)
    print(f"embedding extractor :{time.time()-s}")
    print("Models not use threading loading time: ", time.time() - start)
    app = App(root, ort_session, face_detector, test_transform, device, vid)
    running = True

    def on_close():
        nonlocal running
        running = False
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    while running:
        try:
            root.update_idletasks()
            root.update()
        except KeyboardInterrupt:
            vid.release()
            on_close()
if __name__ == '__main__':
    main()


