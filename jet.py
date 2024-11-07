from yolov8 import YOLOv8_face
from FaceAntiSpoofing import AntiSpoof
import adafruit_fingerprint
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
from tkinter import *
import queue
from PIL import Image, ImageTk
import serial
from yolov8 import increased_crop
import shutil
import time
import datetime
from datetime import datetime as dt
from imutils import paths
from collections import Counter
from PIL import Image, ImageEnhance
import random
import os
import cv2
import torch
import pickle
import numpy as np
import threading
from collections import Counter
from face_model import MobileFaceNet, l2_norm
from create_widgets import init_app,create_widgets
import threading
from annoy import AnnoyIndex  # Import Annoy
root = Tk()

class App:
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

    def __init__(self, root,detect_model,face_detector,anti_spoof_detector,test_transform,device,vid):
        init_app(self, root,detect_model,face_detector,anti_spoof_detector,test_transform,device,vid)

    #def go_to_database_frame(self, event):
        #self.card_activities_frame.place_forget()
        #self.setting_frame.place(x=0, y=0)

    def go_to_database_frame(self):
        self.setting_frame.place(x=0, y=0)

    def get_value_behind_colon_combobbox(self,button):
        button_text = button.cget("text")
        parts = button_text.split(":")
        if len(parts) > 1:
            return parts[1].strip()
        return None


    def show_combbobox_value_frame(self, values,frame,task):
        frame.place_forget()
        self.value_frame.pack(fill=BOTH, expand=True)
        for widget in self.value_frame.winfo_children():
            widget.destroy()
        canvas = Canvas(self.value_frame, height=self.resolution_height, width=self.resolution_width,background="grey")  # Fixed height and width for the canvas
        scrollbar = Scrollbar(self.value_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas,bg="grey")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.place(x=0, y=0)
        scrollbar.pack(side="right", fill="y")
        for i, value in enumerate(values):
            button = Button(scrollable_frame, text=value, font=('Arial', 35), command=lambda d=value:self.on_combbobox_value_select(value=d,frame=frame,task=task),width=15)
            button.grid(row=i, column=0,columnspan=3, padx=340, pady=5)

    def on_combbobox_value_select(self,value,frame,task):
        print(value)
        if frame == self.database_content_frame:
            if task == "ID/Name":
                self.select_entry.config(text=f"Category: {value}")
            else:
                self.select_department.config(text=f"Department: {value}")
        elif frame == self.user_log_content_frame:
            if task == "ID/Name":
                self.select_entry_log.config(text=f"Category: {value}")
            else:
                self.select_department_log.config(text=f"Department: {value}")
        elif frame == self.register_user_frame:
            self.register_department_combobox.config(text=value)
        self.value_frame.pack_forget()
        frame.place(x=0,y=0)


    def card_activities(self, task, authority, task_category):
        self.card_activities_frame.place(x=0, y=0)
        print("Number of templates found: ", self.finger.template_count)
        if task == "check":
            self.choose_face_or_card_frame.place_forget()
        elif task == "register":
            self.register_user_frame.place_forget()
        self.cancel_card_activities_button.config(command=lambda: self.cancel_card_activities(task, authority))
        self.get_card_allow = True
        self.get_card_input(task, authority, task_category)

    def cancel_card_activities(self, task, authority):
        self.card_activities_frame.place_forget()
        self.get_card_allow = False
        self.fingerprint_buffer = 0
        #self.insert_card_guidline_label.config(text='Please insert your card to the reader', font=('Arial', 30),bg='gray', fg='white')
        
        if task == "check":
            if authority == "user":
                self.choose_face_or_card_frame.place(x=0, y=0)
            elif authority == "admin":
                self.choose_check_inout_frame.place(x=0, y=0)
        elif task == "register":
            print(f"Number of templates after delete {self.new_id}: {self.finger.template_count}" )
            self.register_user_frame.place(x=0, y=0)

    def face_activities(self, task, authority, task_category):
        self.face_activities_frame.place(x=0, y=0)
        if task == "check":
            self.choose_face_or_card_frame.place_forget()
        elif task == "register":
            self.register_user_frame.place_forget()
            self.retake_face_confirmation_button.place_forget()
            self.take_face_confirmation_button.place_forget()
        self.get_face_allow = True
        self.check_user_allow = False
        self.register_face_guidline_label.configure(text="Put face in the box",fg ="white",bg="gray")
        self.open_camera(task, authority, task_category)
        self.cancel_face_activities_button.config(command=lambda: self.cancel_face_activities(task, authority))

    def cancel_face_activities(self, task, authority):
        self.get_face_allow = False
        self.frame_capture = []
        self.boxes_capture = []
        self.face_activities_frame.place_forget()
        if task == "check":

            if authority == "user":
                self.choose_face_or_card_frame.place(x=0, y=0)
            elif authority == "admin":
                self.choose_check_inout_frame.place(x=0, y=0)
        elif task == "register":
            self.register_user_frame.place(x=0, y=0)

    def reset_sort_buttons(self):
        self.select_entry.config(text="Sort by: ID/Name")
        self.select_department.config(text="Sort by: Department")
        self.search_entry.config(text="")
        self.select_entry_log.config(text="Sort by: ID/Name")
        self.select_department_log.config(text="Sort by: Department")
        self.search_entry_log.config(text="")
        self.from_button.config(text="Select date")
        self.to_button.config(text="Select date")

    def switch_frame(self, frame_to_place, frame_to_forget, task_category):
        if frame_to_place == self.choose_face_or_card_frame and frame_to_forget == self.choose_check_inout_frame:
            self.face_button.config(command=lambda: self.face_activities("check", "user", task_category))
            self.card_button.config(command=lambda: self.card_activities("check", "user", task_category))
        if frame_to_place == self.setting_frame and (frame_to_forget == self.database_content_frame or frame_to_forget == self.user_log_content_frame):
            self.show_all(self.user_list, "dataset", self.dataset_cursor, self.search_entry, self.from_button, self.to_button)
            self.show_all(self.user_log_list, "timekeeping", self.timekeeping_cursor, self.search_entry_log, self.from_button, self.to_button)
        elif frame_to_place == self.register_user_frame and frame_to_forget == self.register_content_frame:
            if task_category == "register user":
                self.register_face_button.config(command=lambda: self.face_activities("register", "user", task_category))
            elif task_category == "register admin":
                self.register_face_button.config(command=lambda: self.face_activities("register", "admin", task_category))
            self.task_category = task_category
            self.dataset_cursor.execute("SELECT ID FROM dataset ORDER BY ID")
            existing_ids = [row[0] for row in self.dataset_cursor.fetchall()]
            self.new_id = next((i for i in range(1, 1001) if i not in existing_ids), max(existing_ids, default=0) + 1)
            self.register_title_label.config(text=f"ID: {self.new_id}")
            self.check_confirm_add_user = True
            self.confirm_add_user()
        elif frame_to_place == self.register_content_frame and frame_to_forget == self.register_user_frame:
            self.register_name_entry.config(text="")
            self.register_face_button.config(fg="black", text=" Register Face ", bg="white", state=NORMAL,command=lambda: self.face_activities("register", "None", "None"))
            self.register_card_button.config(fg="black", text=" Register Card ", bg="white", state=NORMAL,command=lambda: self.card_activities("register", "None", "None"))
            self.register_department_combobox.set("")
            self.current_entry = None
            self.frame_capture = []
            self.boxes_capture = []
            self.check_confirm_add_user = False
            self.get_card_allow = False
        frame_to_forget.place_forget()
        frame_to_place.place(x=0, y=0)

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
        elif self.current_entry == self.search_entry:
            self.database_content_frame.place(x=0, y=0)
        elif self.current_entry == self.search_entry_log:
            self.user_log_content_frame.place(x=0, y=0)
        if self.keyboard_box.cget("text") != "":
            if self.current_entry == self.username_entry:
                self.username = self.keyboard_box.cget("text")
                self.username_entry.config(text=self.username)
            if self.current_entry == self.password_entry:
                self.password = self.keyboard_box.cget("text")
                self.password_entry.config(text=self.password)
            if self.current_entry == self.username_entry or self.current_entry == self.password_entry:
                self.web_cursor.execute('DELETE FROM web')
                self.web_cursor.execute('INSERT INTO web (Username, Password) VALUES (?, ?)',(self.username, self.password))
                self.web_conn.commit()

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

    def toggle_edit_mode(self):
        self.user_log_list.unbind("<Button-1>")
        if self.edit_mode_var.get():
            self.user_log_list.bind("<Button-1>", self.toggle_selection)
        else:
            self.user_log_list.bind("<Button-1>", self.block_selection)
            self.user_log_list.selection_remove(self.user_log_list.selection())

    def toggle_selection(self, event):
        item = self.user_log_list.identify_row(event.y)
        if item:
            if item in self.user_log_list.selection():
                self.user_log_list.selection_remove(item)
            else:
                self.user_log_list.selection_add(item)
        return "break"

    def block_selection(self, event):
        return "break"

    def toggle_select_all(self):
        if self.select_all_var.get():
            self.user_log_list.selection_set(self.user_log_list.get_children())
        else:
            self.user_log_list.selection_remove(self.user_log_list.get_children())

    def on_treeview_select(self, event):
        self.user_image_label.place(x=self.database_content_frame.winfo_reqwidth() // 2 + 100,y=self.database_icon_label.winfo_reqheight() + 20 + 3 * self.select_entry.winfo_reqheight())
        self.remove_user_database_button.place(x=self.database_content_frame.winfo_reqwidth() // 2 + 100, y=self.database_icon_label.winfo_reqheight() + 40 + self.database_content_frame.winfo_reqheight() // 2 - 60 + self.select_entry.winfo_reqheight() * 3)
        selected_item = self.user_list.selection()
        if selected_item:
            selected_item = self.user_list.selection()[0]
            item_values = self.user_list.item(selected_item, "values")
            user_id = item_values[0]
            user_image_dir = None
            for folder_name in os.listdir(self.dataset_path):
                if folder_name.startswith(user_id):
                    user_image_dir = os.path.join(self.dataset_path, folder_name)
                    break
            if user_image_dir and os.path.isdir(user_image_dir):
                images = [f for f in os.listdir(user_image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
                if images:
                    random_image = random.choice(images)
                    image_path = os.path.join(user_image_dir, random_image)
                    img = Image.open(image_path)
                    img = img.resize((self.database_content_frame.winfo_reqwidth() // 2 - 100, self.database_content_frame.winfo_reqheight() // 2 - 60))
                    photo_img = ImageTk.PhotoImage(img)
                    self.user_image_label.config(image=photo_img)
                    self.user_image_label.image = photo_img
        else:
            self.user_image_label.place_forget()
            self.remove_user_database_button.place_forget()

    def open_calendar(self, button):
        self.current_button = button
        self.calendar_frame.place(x=0, y=0,width =self.resolution_width, height = self.resolution_height)

    def grad_date(self):
        selected_date = self.cal.get_date()
        date_obj = datetime.datetime.strptime(selected_date, "%m/%d/%y")
        formatted_date = date_obj.strftime("%d-%m-%Y")
        self.current_button.config(text=formatted_date)
        self.calendar_frame.place_forget()

    def ask_to_confirm_action(self, action, current_frame, next_frame):
        if action == "None":
            if current_frame == self.database_content_frame:
                if len(self.user_list.get_children()) == 0:
                    return
                current_frame.place_forget()
                self.confirm_yes_action_button.configure(command=lambda: self.ask_to_confirm_action("Yes", self.database_content_frame,self.database_content_frame))
                self.confirm_no_action_button.configure(command=lambda: self.ask_to_confirm_action("No", self.database_content_frame,self.database_content_frame))
            elif current_frame == self.user_log_content_frame:
                if len(self.user_log_list.get_children()) == 0:
                    return
                current_frame.place_forget()
                self.confirm_yes_action_button.configure(command=lambda: self.ask_to_confirm_action("Yes", self.user_log_content_frame,self.user_log_content_frame))
                self.confirm_no_action_button.configure(command=lambda: self.ask_to_confirm_action("No", self.user_log_content_frame,self.user_log_content_frame))
            elif current_frame == self.register_user_frame:
                current_frame.place_forget()
                self.confirm_yes_action_button.configure(command=lambda: self.ask_to_confirm_action("Yes", self.register_user_frame,self.register_content_frame))
                self.confirm_no_action_button.configure(command=lambda: self.ask_to_confirm_action("No", self.register_user_frame,self.register_content_frame))
            self.confirm_action_frane.place(x=0, y=0)
        elif action == "Yes":
            next_frame.place(x=0, y=0)
            self.confirm_action_frane.place_forget()
            if current_frame == self.database_content_frame:
                self.remove_row(self.user_list, "dataset", self.dataset_cursor)
                for child in [self.user_image_label, self.remove_user_database_button]:
                    child.place_forget()
            if current_frame == self.user_log_content_frame:
                self.remove_row(self.user_log_list, "timekeeping", self.timekeeping_cursor)
            if current_frame == self.register_user_frame:
                self.finger.delete_model(self.new_id)
                self.switch_frame(self.register_content_frame, self.register_user_frame, self.task_category)
        elif action == "No":
            if current_frame == self.database_content_frame:
                self.database_content_frame.place(x=0, y=0)
            elif current_frame == self.user_log_content_frame:
                self.user_log_content_frame.place(x=0, y=0)
            elif current_frame == self.register_user_frame:
                current_frame.place(x=0, y=0)
            self.confirm_action_frane.place_forget()

    def search(self, treeview, table_name, search_type_combobox, search_entry, cursor_treeview, from_button=None, to_button=None, department_combobox=None):
        search_value = search_entry.cget("text").lower()
        print(search_value)
        selected_column = self.get_value_behind_colon_combobbox(search_type_combobox)
        from_date_str = from_button.cget('text') if from_button else ""
        to_date_str = to_button.cget('text') if to_button else ""
        department = self.get_value_behind_colon_combobbox(department_combobox)
        from_date_valid = from_date_str != "" and from_date_str != "Select date"
        to_date_valid = to_date_str != "" and to_date_str != "Select date"
        department_valid = department != "None" and department != "Department"
        valid_date_range = False
        if from_date_valid and to_date_valid:
            try:
                from_date = dt.strptime(from_date_str, "%d-%m-%Y").date()
                to_date = dt.strptime(to_date_str, "%d-%m-%Y").date()
                valid_date_range = from_date <= to_date
            except ValueError:
                print("Invalid date format. Please use 'DD-MM-YYYY'.")

        # Clear the treeview before populating search results
        for row in treeview.get_children():
            treeview.delete(row)
        # SQL Query Builder
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []
        # If there's a search value and a selected column, add it to the query
        if search_value and selected_column:
            query += f" AND LOWER({selected_column}) LIKE ?"
            params.append(f"%{search_value}%")
        # If the date range is valid, add it to the query
        if valid_date_range:
            query += " AND DATE(date) BETWEEN ? AND ?"
            params.append(from_date)
            params.append(to_date)
        # If a department is selected, add it to the query
        if department_valid:
            query += " AND department = ?"
            params.append(department)
        print(query)
        print(tuple(params))
        try:
            cursor_treeview.execute(query, tuple(params))
            rows = cursor_treeview.fetchall()
            # Insert the matching rows into the treeview
            for row in rows:
                treeview.insert("", "end", values=row)
            print(f"Found {len(rows)} matching records.")
        except Exception as e:
            print(f"Error during search: {e}")

    def show_all(self, treeview, table_name, cursor_treeview, search_entry, from_button, to_button):
        self.reset_sort_buttons()
        for row in treeview.get_children():
            treeview.delete(row)
        cursor_treeview.execute(f"SELECT * FROM {table_name}")
        rows = cursor_treeview.fetchall()
        for row in rows:
            treeview.insert('', 'end', values=row)

    def remove_row(self, treeview, table_name, cursor_treeview):
        selected_items = treeview.selection()
        if selected_items:
            for selected_item in selected_items:
                item = treeview.item(selected_item)
                if treeview == self.user_list:
                    item_id = item['values'][0]
                    cursor_treeview.execute(f'DELETE FROM {table_name} WHERE ID=?', (item_id,))
                    self.dataset_conn.commit()
                    with open('facebank/data.pickle', 'rb') as f:
                        data = pickle.load(f)
                        existing_names = data['names']
                        existing_names_list = data['names'].tolist()
                        existing_embeddings = data['embeddings']
                    person_to_remove = f"{item['values'][0]}-{item['values'][1]}-{item['values'][2]}-{item['values'][3]}"
                    if person_to_remove in existing_names:
                        user_index = existing_names_list.index(person_to_remove)
                        existing_names_list.pop(user_index)
                        existing_embeddings = torch.cat([existing_embeddings[:user_index], existing_embeddings[user_index + 1:]])
                        index = AnnoyIndex(512, 'angular')
                        for i in range(existing_embeddings.size(0)):
                            index.add_item(i, existing_embeddings[i].cpu().numpy())
                        index.build(10)
                        index.save('facebank/annoy_index.ann')
                    with open('facebank/data.pickle', 'wb') as f:
                        pickle.dump({'embeddings': existing_embeddings, 'names': existing_names}, f)
                    print(f'person_to_remove is {person_to_remove}')
                    self.user_image_label.place_forget()
                    self.remove_user_database_button.place_forget()
                    self.finger.delete_model(item['values'][0])
                    folder_to_remove_path = os.path.join(self.dataset_path, person_to_remove)
                    shutil.rmtree(folder_to_remove_path)
                else:
                    item_date = item['values'][0]
                    item_department = item['values'][1]
                    item_id = item['values'][2]
                    item_name = item['values'][3]
                    item_in = item['values'][4]
                    item_out = item['values'][5]
                    cursor_treeview.execute(f'DELETE FROM {table_name} WHERE "Date"=? AND "Department"=? AND "ID"=? AND "Name"=? AND "In"=? AND "Out"=?',(item_date, item_department, item_id, item_name, item_in, item_out))
                    self.timekeeping_conn.commit()
                treeview.delete(selected_item)


    def update_timekeeping_db(self, task_category):
        update_not_successful = False
        name = self.name_authentication_label.cget("text").split(": ")[1]
        department = self.department_authentication_label.cget("text").split(": ")[1]
        user_id = self.id_authentication_label.cget("text").split(": ")[1]
        datetime_str = self.time_authentication_label.cget("text").split(": ")[1]
        date_str, time_str = datetime_str.split(" ")
        self.timekeeping_cursor.execute('SELECT * FROM timekeeping WHERE "Date"=? AND "Department"=? AND "ID"=? AND "Name"=?',(date_str, department, user_id, name))
        entry = self.timekeeping_cursor.fetchone()

        if entry:
            if task_category == "check in":
                if entry[5] == "-":
                    self.timekeeping_cursor.execute('UPDATE timekeeping SET "In"=? WHERE "Date"=? AND "ID"=? AND "Name"=?',(time_str, date_str, user_id, name))
                else:
                    self.timekeeping_cursor.execute('INSERT INTO timekeeping ("Date", "Department", "ID", "Name", "In", "Out") VALUES (?, ?, ?, ?, ?, ?)',(date_str, department, user_id, name, time_str, "-"))
            elif task_category == "check out":
                if entry[5] == "-":  # "Out" field is "-"
                    self.timekeeping_cursor.execute('UPDATE timekeeping SET "Out"=? WHERE "Date"=? AND "ID"=? AND "Name"=?',(time_str, date_str, user_id, name))
                else:  # "Out" field is not "-"
                    self.timekeeping_cursor.execute('UPDATE timekeeping SET "Out"=? WHERE "Date"=? AND "ID"=? AND "Name"=?',(time_str, date_str, user_id, name))
        else:
            if task_category == "check in":
                self.timekeeping_cursor.execute('INSERT INTO timekeeping ("Date", "Department", "ID", "Name", "In", "Out") VALUES (?, ?, ?, ?, ?, ?)',(date_str, department, user_id, name, time_str, "-"))
            elif task_category == "check out":
                self.authentication_guidline_label.config(text="You haven't checked in")
                update_not_successful = True
                return

        self.timekeeping_conn.commit()
        self.show_all(self.user_log_list, "timekeeping", self.timekeeping_cursor, self.search_entry_log, self.from_button, self.to_button)
        if not update_not_successful:
            self.authentication_guidline_label.config(text="Please authenticate")
            self.switch_frame(self.choose_check_inout_frame, self.authentication_frame, task_category)

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


    # trainmodel with threading
    def train_model(self):
        def prepare_facebank(model, tta=True):
            model.eval()
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
                        emb = model(self.test_transform(aligned_face).to(self.device).unsqueeze(0))
                        emb_mirror = model(self.test_transform(mirror).to(self.device).unsqueeze(0))
                        embs.append(l2_norm(emb + emb_mirror))
                    else:
                        embs.append(model(self.test_transform(aligned_face).to(self.device).unsqueeze(0)))
                if len(embs) == 0:
                    return

            threads = []
            print("traning")
            print(len(self.frame_capture), len(self.boxes_capture))
            for frame, bbox in zip(self.frame_capture, self.boxes_capture):
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
            with open('facebank/data.pickle', 'rb') as f:
                data = pickle.load(f)
                existing_embeddings = data['embeddings'].to(self.device)
                existing_names = data['names']
            if self.user_image_dir in data["names"]:
                print(f"[INFO] {self.user_image_dir} already exists in the dataset. Skipping...")
            new_embeddings, new_names = prepare_facebank(self.detect_model, tta=True)
            if new_embeddings.size(0) == 0:
                return
            print(f"new_embeddings.size(0) is {new_embeddings.size(0)}")
            for i, name in enumerate(new_names[1:]):
                print(f"Train more user {i}{name}...")
                if name not in existing_names:
                    if i < len(new_embeddings):
                        existing_names = np.append(existing_names, name)
                        existing_embeddings = torch.cat((existing_embeddings, new_embeddings[i].unsqueeze(0).to(self.device)), dim=0)  # Ensure new embeddings are on the same device
            with open('facebank/data.pickle', "wb") as data_file:
                pickle.dump({'embeddings': existing_embeddings, 'names': existing_names}, data_file)
            index = AnnoyIndex(512, 'angular')
            for i in range(existing_embeddings.size(0)):
                index.add_item(i, existing_embeddings[i].cpu().numpy())
            index.build(10)
            index.save('facebank/annoy_index.ann')
            self.root.after(0, self.show_all, self.user_list, "dataset", self.dataset_cursor, self.search_entry,self.from_button, self.to_button)
            self.root.after(0, self.switch_frame, self.register_content_frame, self.please_wait_frame,self.task_category)
            self.frame_capture = []
            self.boxes_capture = []
            self.allow_training = False
        self.root.after(2000, self.train_model)

    def confirm_add_user(self):
        if self.check_confirm_add_user == True:
            if self.register_name_entry.cget("text") != "" and self.register_department_combobox.cget('text') != "":
                self.register_face_button.config(state=NORMAL)
            else:
                self.register_face_button.config(state=DISABLED)
                self.register_card_button.config(state=DISABLED)
                self.confirm_register_button.config(state=DISABLED)
            if self.register_face_button.cget("bg") == "green":
                self.register_card_button.config(state=NORMAL)
            if self.register_card_button.cget("bg") == "green":
                self.confirm_register_button.config(state=NORMAL)
            self.root.after(100, self.confirm_add_user)

    def update_database_db(self, task_category):
        self.switch_frame(self.please_wait_frame, self.register_user_frame, task_category)
        task_category = self.task_category
        user_id = self.register_title_label.cget("text").split(": ")[1]
        user_name = self.register_name_entry.cget("text")
        user_authority = task_category.split(" ")[1]
        user_department = self.register_department_combobox.cget('text')
        self.register_name_entry.config(text="")
        self.register_face_button.config(fg="black", text=" Register Face ", bg="white", state=NORMAL,command=lambda: self.face_activities("register", "None", "None"))
        self.register_card_button.config(fg="black", text=" Register Fingerprint ", bg="white", state=NORMAL,command=lambda: self.card_activities("register", "None", "None"))
        self.register_department_combobox.config(text="")
        self.user_path_dir = os.path.join('dataset',f"{user_id}-{user_name}-{user_authority}-{user_department}")
        self.user_image_dir = f"{user_id}-{user_name}-{user_authority}-{user_department}"
        user_path_dir = self.user_path_dir
        if not os.path.exists(user_path_dir):
            os.makedirs(user_path_dir)
        for i, frame in enumerate(self.frame_capture):
            cv2.imwrite(f"{user_path_dir}/{i}.jpg", frame)
        self.dataset_cursor.execute('SELECT * FROM dataset WHERE ID=?', (user_id,))
        dataset_entry = self.dataset_cursor.fetchone()
        if not dataset_entry:
            self.dataset_cursor.execute('INSERT INTO dataset (ID, Name, Authority, Department) VALUES (?, ?, ?, ?)',(user_id, user_name, user_authority, user_department))
        self.department_cursor.execute('SELECT * FROM departments WHERE department=?', (user_department,))
        department_entry = self.department_cursor.fetchone()
        if not department_entry:
            self.department_cursor.execute('INSERT INTO departments (department) VALUES (?)', (user_department,))
        self.dataset_conn.commit()
        self.allow_training = True
        self.confirm_register_button.config(state=DISABLED)

    def authentication(self, method, user_recognized, task_category):
        self.task_category = task_category
        if method == "face":
            self.face_activities_frame.place_forget()
        elif method == "finger":
            self.card_activities_frame.place_forget()
        self.authentication_frame.place(x=0, y=0)
        if user_recognized != "unknown":
            user_info = user_recognized.split('-')
            user_id = user_info[0]
            user_name = user_info[1]
            user_authority = user_info[2]
            user_department = user_info[3]
            user_image_dir = os.path.join('dataset', user_recognized)
            print(f'in def authentication user_info is {user_recognized}')
            image_files = [f for f in os.listdir(user_image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                user_image_path = os.path.join(user_image_dir, image_files[0])
            else:
                user_image_path = None
            user_image = self.convert_image_for_tkinter(user_image_path,(self.resolution_width // 2, self.resolution_height // 2))
            self.face_detected_authentication_label.config(image=user_image)
            self.face_detected_authentication_label.image = user_image
            self.face_detected_authentication_label.pack()
            self.name_authentication_label.config(text=f"Name: {user_name}")
            self.department_authentication_label.config(text=f"Department: {user_department}")
            self.id_authentication_label.config(text=f"ID: {user_id}")
            current_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_authentication_label.config(text=f"Time: {current_time}")

    def get_card_input(self, task, authority, task_category):
        if self.get_card_allow == True:
        # Check if finger is detected
            time.sleep(1.5)
            get_print = self.finger.get_image()
            if get_print != adafruit_fingerprint.NOFINGER:
                if self.finger.get_image() == adafruit_fingerprint.OK:
                    if task == "check":
                        self.handle_fingerprint_check(task, authority, task_category)
                    elif task == "register":
                        if self.fingerprint_buffer == 1:
                            self.update_guideline_message("Remove finger", "red")
                            self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                        elif self.fingerprint_buffer == 0 and self.fingerprint_already_exist == True:
                            self.update_guideline_message("Remove finger. Finger is already exist", "red")
                            self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                        elif (self.fingerprint_buffer == 0 and self.fingerprint_already_exist == False) or self.fingerprint_buffer == 2:
                            self.handle_fingerprint_registration(task, authority, task_category)
                else:
                    self.update_guideline_message("Failed to capture image", "red")
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
            else:
                self.fingerprint_already_exist = False
                if task == "register" and (self.fingerprint_buffer == 1 or self.fingerprint_buffer == 2):
                    self.update_guideline_message("Place the same finger again", "red")
                    self.fingerprint_buffer = 2
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                else:
                    self.update_guideline_message("No finger detected, place finger", "red")
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))

    def handle_fingerprint_check(self, task, authority, task_category):
        if self.finger.image_2_tz(1) == adafruit_fingerprint.OK:
            self.card_recogintion_operation(task, authority, task_category)
        else:
            self.update_guideline_message("Template failed", "red")
            self.root.after(10, lambda: self.get_card_input(task, authority, task_category))

    def handle_fingerprint_registration(self, task, authority, task_category):
        if self.fingerprint_buffer == 0 :
            if self.finger.image_2_tz(1) == adafruit_fingerprint.OK:
                self.update_guideline_message("Image buffer1  taken", "green")
                self.card_recogintion_operation(task, authority, task_category)
            else:
                self.update_guideline_message("Template buffer1 failed", "red")
                self.root.after(10, lambda: self.get_card_input(task, authority, task_category))

        elif self.fingerprint_buffer == 2:
            if self.finger.image_2_tz(2) == adafruit_fingerprint.OK:
                self.update_guideline_message("Image buffer2 taken", "green")
                self.card_recogintion_operation(task, authority, task_category)
            else:
                self.update_guideline_message("Template buffer2 failed", "red")
                self.root.after(10, lambda: self.get_card_input(task, authority, task_category))


    def update_guideline_message(self, message, color):
        self.insert_card_guidline_label.config(text=message, fg=color)

    def card_recogintion_operation(self, task, authority, task_category):
        if task == "check":
            if self.finger.finger_search() != adafruit_fingerprint.OK:
                self.insert_card_guidline_label.config(text="     No user or admin permission", fg='red')
                self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
            else:
                # print("Detected #", self.finger.finger_id, "with confidence", self.finger.confidence)
                self.dataset_cursor.execute('SELECT * FROM dataset WHERE ID=?', (self.finger.finger_id,))
                user_entry = self.dataset_cursor.fetchone()
                if user_entry[2] == authority:
                    user_info = f'{user_entry[0]}-{user_entry[1]}-{user_entry[2]}-{user_entry[3]}'
                    self.authentication("finger", user_info, task_category)
                else:
                    self.insert_card_guidline_label.config(text=f"     No {authority} permission", fg='red')                                                       
                
        elif task == "register":
            if self.fingerprint_buffer == 0:
                if self.finger.finger_search() == adafruit_fingerprint.OK:
                    # print("Finger already exists")
                    self.insert_card_guidline_label.config(text="Finger already exists", fg='red')
                    print("already exist")
                    self.fingerprint_already_exist = True
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                else:
                    self.fingerprint_buffer = 1
                    print("not in dataset")
                    self.fingerprint_already_exist = False
                    self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
            elif self.fingerprint_buffer == 2:
                i = self.finger.create_model()
                if i == adafruit_fingerprint.OK:
                    print("Created")
                    a = self.finger.store_model(self.new_id)
                    if a == adafruit_fingerprint.OK:
                        print("Stored")
                        self.fingerprint_buffer = 0
                        self.switch_frame(self.register_user_frame, self.card_activities_frame, task_category)             
                        self.register_card_button.config(text="", bg="green", state=DISABLED,width = self.resolution_width//3 + self.resolution_width//5)
                    else:
                        if a == adafruit_fingerprint.BADLOCATION:
                            print("Bad storage location")
                        elif a == adafruit_fingerprint.FLASHERR:
                            print("Flash storage error")
                        else:
                            print("Other error")
                else:
                    if i == adafruit_fingerprint.ENROLLMISMATCH:
                        self.insert_card_guidline_label.config(text="      Not the same finger", fg='red')
                        self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
                    else:
                        print("Other error")
                        self.insert_card_guidline_label.config(text="      Other error", fg='red')
                        self.root.after(10, lambda: self.get_card_input(task, authority, task_category))
        
        
    # #recognition not use threading
    def face_recogintion_operation(self, task, authority, task_category):
        def process_frame_bbox(index,frame, bbox, existing_names, recognized_names, device, detect_model, test_transform):
            embs = []
            face = self.Face_alignment(frame, bbox)
            face = test_transform(face).to(device).unsqueeze(0)
            with torch.no_grad():
                emb = detect_model(face)
            embs.append(emb)
            if embs:
                source_embs = torch.cat(embs).to(device)
            else:
                source_embs = torch.empty(0, 512).to(device)
            if source_embs.size(0) == 0:
                return
            results = [-1] * len(source_embs)
            if len(source_embs) > 0:
                for i, emb in enumerate(source_embs):
                    idx = index.get_nns_by_vector(emb, 1, include_distances=True)
                    dist = idx[1][0] if idx[1] else float('inf')
                    if dist > 1.2:
                        results[i] = -1
                    else:
                        results[i] = idx[0][0]
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
            recognized_names = []
            with open('facebank/data.pickle', 'rb') as f:
                data = pickle.load(f)
            index_file = 'facebank/annoy_index.ann'
            index = AnnoyIndex(512, 'angular')
            index.load(index_file)
            existing_names = data['names']
            # existing_embeddings = data['embeddings'].to(self.device)
            user_recognized = "Unknown"
            start = time.time()
            for frame, bbox in zip(self.frame_capture, self.boxes_capture):
                process_frame_bbox(index,frame, bbox, existing_names, recognized_names, self.device, self.detect_model,self.test_transform)

            stop = time.time()
            print(f"Time taken for face_recognition_operation: {stop - start} seconds")
            print(f"recognized_names: {recognized_names}")
            most_common_name = Counter(recognized_names).most_common(1)[0][0]
            if user_recognized != most_common_name:
                user_recognized = most_common_name
                self.frame_capture = []
                self.boxes_capture = []
                self.authentication("face", user_recognized, task_category)
            else:
                self.frame_capture = []
                self.boxes_capture = []
                self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                self.register_face_guidline_label.configure(text="No permission", fg="red")
        elif task == "register":
            self.switch_frame(self.register_user_frame, self.face_activities_frame, task_category)
            self.register_face_button.config(text="", bg="green", state=DISABLED,width = self.resolution_width//3 + self.resolution_width//5)
            

    def check_user(self,task, authority, task_category):
        self.check_user_allow = True


    def update_camera_frame(self, opencv_image):
        display_frame = cv2.resize(opencv_image,(self.resolution_width, 6 * (self.resolution_height // 7)))
        captured_image = Image.fromarray(display_frame)
        photo_image = ImageTk.PhotoImage(image=captured_image)
        self.camera_label.photo_image = photo_image
        self.camera_label.configure(image=photo_image, width=self.resolution_width, height=6 * (self.resolution_height // 7))


    def make_prediction_thread(self, frame_to_predict):
        bboxes, landmarks, predictions = self.make_prediction(frame_to_predict, self.face_detector, self.anti_spoof_detector, allow_predict_spoof=True)
        self.prediction_queue.put((bboxes, landmarks, predictions))
    
    def make_prediction(self,img, face_detector, anti_spoof, allow_predict_spoof):
        print(allow_predict_spoof)
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
            if 1:
                bbox = np.array([x, y, x + w, y + h])
                bboxes.append(bbox)
                if allow_predict_spoof == True:
                    s= time.time()                  
                    pred = anti_spoof([increased_crop(img, bbox, bbox_inc=1.5)])[0]
                    score = pred[0][0]
                    label = np.argmax(pred)
                    print(f"label is {label}")
                    predictions.append((bbox, label, score, kpt))
        bboxes = np.array(bboxes)
        return bboxes, lanmarks, predictions
        

    def open_camera(self, task, authority, task_category):
        if self.get_face_allow == True or self.load_models_allow == True:
            if self.load_models_allow==False and task == "check":
                self.take_face_confirmation_button.place(x=self.resolution_width - self.take_face_confirmation_button.winfo_reqwidth(), y=0)
                self.retake_face_confirmation_button.place_forget()
            ret, frame = self.vid.read()
            if ret:
                opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                height, width = opencv_image.shape[:2]
                face_area_to_detect = (width // 5, height // 5, 3 * width // 5, 3*height // 5)
                overlay = np.zeros_like(opencv_image)
                overlay[:] = (0, 0, 0, 128)
                x, y, w, h = face_area_to_detect
                overlay[y:y + h, x:x + w] = opencv_image[y:y + h, x:x + w]
                cv2.addWeighted(overlay, 0.5, opencv_image, 0.5, 0, opencv_image)
                frame_to_predict = np.zeros_like(opencv_image)
                frame_to_predict[y:y + h, x:x + w] = opencv_image[y:y + h, x:x + w]
                frame_to_predict = cv2.cvtColor(frame_to_predict, cv2.COLOR_RGBA2BGR)
            # if 1: ##for adjust widgets
                if self.load_models_allow == True:
                    create_widgets(self)
                    s = time.time()
                    test_image = cv2.imread("test_system.jpg")
                    bboxes, landmarks, predictions = self.make_prediction(test_image, self.face_detector,self.anti_spoof_detector, allow_predict_spoof=True)
                    print(f'dummy time use face_model {time.time() - s}')
                    self.load_models_allow = False

                if task == "check" and self.check_user_allow ==  True:
                # if 0: ##for adjust widgets
                    s = time.time()
                    bboxes, landmarks, predictions = self.make_prediction(frame_to_predict, self.face_detector,self.anti_spoof_detector, allow_predict_spoof=True)
                    print(f'official first time use face_model {time.time() - s}')

                    if len(bboxes) == 1:
                        (x1, y1, x2, y2), label, score, kpt = predictions[0]
                        if label == 0:
                            color_bgr = (0, 255, 0)
                        else:
                            color_bgr = (0, 0, 255)
                        color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                        cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                        self.update_camera_frame(opencv_image)
                        if label in [1,2,3,7,8,9]:
                            self.register_face_guidline_label.configure(text="Spoofing detected", fg="red")
                            self.update_camera_frame(opencv_image)
                            self.frame_capture = []
                            self.boxes_capture = []
                            self.take_face_confirmation_button.place_forget()
                            self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                        else:
                            self.frame_capture.append(frame_to_predict)
                            self.boxes_capture.append(bboxes[0])
                            self.face_recogintion_operation(task, authority, task_category)
                    elif len(bboxes) >= 2:
                        self.register_face_guidline_label.configure(text="Only one face is allowed", fg="red")
                        for pred in predictions:
                            (x1, y1, x2, y2), label, score, kpt = pred
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
                        self.register_face_guidline_label.configure(text ="Face not found")
                        self.take_face_confirmation_button.place_forget()
                        self.retake_face_confirmation_button.place(x=self.resolution_width - self.retake_face_confirmation_button.winfo_reqwidth(), y=0)
                elif task == "check" and self.check_user_allow == False:
                    self.update_camera_frame(opencv_image)
                    self.root.after(5, lambda: self.open_camera(task, authority, task_category))
                elif task == "register":
                    if self.prediction_thread is None or not self.prediction_thread.is_alive():
                        self.prediction_thread = threading.Thread(target=self.make_prediction_thread,args=(frame_to_predict,))
                        self.prediction_thread.start()
                    if not self.prediction_queue.empty():
                        bboxes, landmarks, predictions = self.prediction_queue.get()
                        if len(bboxes) == 1:
                            (x1, y1, x2, y2), label, score, kpt = predictions[0]
                            if label == 0:
                                color_bgr = (0, 255, 0)
                            else:
                                color_bgr = (0, 0, 255)
                            color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                            cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                            self.update_camera_frame(opencv_image)
                            if label in [1,2,3,7,8,9]:
                                self.register_face_guidline_label.configure(text="Spoofing detected", fg="red")
                                self.update_camera_frame(opencv_image)
                            else:
                                bbox = bboxes[0]
                                p = landmarks[0]
                                left_eye_x = p[0]
                                right_eye_x = p[1]
                                left_edge_dist = left_eye_x - bbox[0]
                                right_edge_dist = bbox[2] - right_eye_x
                                face_direction = "left" if left_edge_dist < right_edge_dist else "right"
                                threshold_face_direction = 5
                                def calculate_distance(landmark1, landmark2):
                                    return np.sqrt(np.sum((landmark1 - landmark2) ** 2))
                                if self.left_face_count < 5:
                                    self.register_face_guidline_label.configure(text=f"Turn your face to the left: {int((self.right_face_count / 5) * 100)}%",fg="white")
                                    if face_direction == "left":
                                        if not self.left_captures or calculate_distance(self.left_captures[-1], np.array([left_eye_x, right_eye_x])) > threshold_face_direction:
                                            self.frame_capture.append(frame_to_predict)
                                            self.boxes_capture.append(bboxes[0])
                                            self.left_face_count += 1
                                            self.left_captures.append(np.array([left_eye_x, right_eye_x]))
                                elif self.left_face_count >= 5:
                                    #self.register_face_guidline_label.configure(text=f"Turn your face to the right: {int((self.right_face_count / 5) * 100)}%",fg="white")
                                    if face_direction == "right" and self.right_face_count < 5:
                                        if not self.right_captures or calculate_distance(self.right_captures[-1], np.array([left_eye_x, right_eye_x])) > threshold_face_direction:
                                            self.frame_capture.append(frame_to_predict)
                                            self.boxes_capture.append(bboxes[0])
                                            self.right_face_count += 1
                                            self.right_captures.append(np.array([left_eye_x, right_eye_x]))
                                self.update_camera_frame(opencv_image)

                        if len(bboxes) >= 2:
                            self.register_face_guidline_label.configure(text="Only one face is allowed", fg="red")
                            for pred in predictions:
                                (x1, y1, x2, y2), label, score, kpt = pred
                                color_bgr = (0, 0, 255)
                                color_rgba = (color_bgr[2], color_bgr[1], color_bgr[0], 255)
                                cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color_rgba, 3)
                            self.update_camera_frame(opencv_image)
                        if len(bboxes) == 0:
                            self.register_face_guidline_label.configure(text="Face not found",fg="white")
                        if (self.left_face_count >= 5) and len(self.frame_capture) >= 5:
                            self.left_face_count = 0
                            self.right_face_count = 0
                            self.left_captures = []
                            self.right_captures = []
                            self.face_recogintion_operation(task, authority, task_category)
                        else:
                            self.update_camera_frame(opencv_image)
                            self.root.after(10, lambda: self.open_camera(task, authority, task_category))
                    else:
                        self.update_camera_frame(opencv_image)
                        self.root.after(10, lambda: self.open_camera(task, authority, task_category))
      


def make_prediction(img, face_detector, anti_spoof, allow_predict_spoof):
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
        if 1:
            bbox = np.array([x, y, x + w, y + h])
            bboxes.append(bbox)
            if allow_predict_spoof == True:
                s = time.time()
                pred = anti_spoof([increased_crop(img, bbox, bbox_inc=1.5)])[0]
                score = pred[0][0]
                label = np.argmax(pred)

                predictions.append((bbox, label, score, kpt))
    bboxes = np.array(bboxes)
    return bboxes, lanmarks, predictions
def find_available_camera():
    # List of device paths to check
    device_paths = ["/dev/video0", "/dev/video1", "/dev/video2"]

    for device_path in device_paths:
        cap = cv2.VideoCapture(device_path,cv2.CAP_V4L2)
        if cap.isOpened():
            print(f"Camera available at {device_path}")
            return cap  # Return only the cap object if successful
        else:
            cap.release()  # Release if not opened

    print("No available cameras found.")
    return None  # Return None if no camera is available

def main():
    vid = find_available_camera()
    vid.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    vid.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    start = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    s = time.time()
    detect_model = MobileFaceNet(512).to(device)
    detect_model.load_state_dict(torch.load('Weights/MobileFace_Net', map_location=lambda storage, loc: storage))
    detect_model.eval()
    test_transform = trans.Compose([trans.ToTensor(), trans.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])])
    print(f'first time load detetc_embeidng{time.time() - s}')
    s = time.time()
    dummy_input = torch.randn(1, 3, 112, 112).to(device)  # Adjust size according to model input
    with torch.no_grad():
       _ = detect_model(dummy_input)
    print(f'first time dummpy_detetc_embeidng{time.time() - s}')
    s = time.time()
    face_detector = YOLOv8_face("Weights/yolov8n-face.onnx", conf_thres=0.8, iou_thres=0.2)
    print(f'first time load face_model {time.time() - s}')
    s = time.time()
    anti_spoof_detector = AntiSpoof("Weights/AntiSpoofing_print-replay_1.5_128.onnx")
    print(f'first time load antispoof {time.time() - s}')
    s = time.time()
    test_image = cv2.imread("test_system.jpg")
    bboxes, landmarks, predictions = make_prediction(test_image, face_detector,anti_spoof_detector, allow_predict_spoof=True)
    print(f'dummy time use face_model {time.time() - s}')
    print("Models not use threading loading time: ", time.time() - start)
    app = App(root,detect_model,face_detector,anti_spoof_detector,test_transform,device,vid)
    running = True

    def on_close():
        nonlocal running
        running = False
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    while running:
        root.update_idletasks()
        root.update()
    root.destroy()


if __name__ == '__main__':
    main()

