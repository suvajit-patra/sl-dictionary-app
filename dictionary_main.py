from math import floor
import os
import re
import numpy as np
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import imageio
import cv2
from PIL import Image, ImageTk
from threading import Thread

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

videos_dir = 'data/videos/'
words_file = 'data/words.txt'

speeds = [1, 2, 0.5]

color_white = '#fff'
button_color = '#00AAFF'

button_font = "Helvetica 12 bold"
list_font = "Helvetica 10 bold"

class main_window:

    def __init__(self, master):
        self.master = master
        self.master.title("ISL Dictionary")
        self.master.iconphoto(False, tk.PhotoImage(file="assets/isl_dict.png"))
        self.master.resizable(True, True)
        self.master.geometry(f"{1100}x{700}")
        self.master.bind('<Return>', self.findWord)
        self.master.bind('<Configure>', self.resize)

        main_menu = tk.Menu(self.master)
        self.master.configure(menu=main_menu)
        main_menu.add_command(label="About", command=self.About)

        #--------------variables----------------
        self.index = None
        self.fps = 65
        self.video_size = (650, 800)
        self.loading_flag = True
        self.speed_index = 0
        self.playing = False
        self.frames_buffer = []
        self.frame_index = 0
        self.searched_text = ''
        self.searched_index = 0
        self.s_index = None
        self.widow_state = None
        self.words = []

        with open(words_file, 'r') as file:
            self.words = file.readlines()
        self.words = [i.rstrip('\n').strip() for i in self.words]

        #--------------frames----------------
        frame1 = ctk.CTkFrame(self.master, bg=color_white)
        frame1.pack(fill=tk.BOTH, padx=10, pady=10, side=tk.RIGHT)
        
        frame0 = ctk.CTkFrame(self.master, bg=color_white)
        frame0.pack(fill=tk.BOTH, side=tk.LEFT, padx=10, pady=10, expand=True)


        frame01 = ctk.CTkFrame(frame0)
        frame01.pack(fill=tk.X, side=tk.TOP, padx=10, pady=10)

        frame02 = ctk.CTkFrame(frame0)
        frame02.pack(fill=tk.BOTH, side=tk.TOP, padx=10, pady=10, expand=True)

        frame03 = ctk.CTkFrame(frame0)
        frame03.pack(fill=tk.BOTH, side=tk.TOP, padx=10, pady=10)

        frame04 = ctk.CTkFrame(frame0)
        frame04.pack(fill=tk.BOTH, side=tk.TOP, padx=10, pady=10)

        frame11 = ctk.CTkFrame(frame1)
        frame11.pack(fill=tk.BOTH, side=tk.TOP, padx=10, pady=10, expand=True)

        #--------------frame01----------------
        self.find_word_entry = ctk.CTkEntry(frame01, bg=color_white)
        self.find_word_entry.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=10, expand=True)

        self.find_word_btn = ctk.CTkButton(frame01, text="Find Word", height=30, width=100, command=self.findWord)
        self.find_word_btn.pack(side=tk.LEFT, padx=10, pady=10)

        #--------------frame02----------------
        self.word_list_box = tk.Listbox(frame02, font=list_font)
        for word in self.words:
            self.word_list_box.insert(tk.END, word)
        self.word_list_box.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)

        self.scrollbar =ctk.CTkScrollbar(frame02, orientation=tk.VERTICAL, command = self.word_list_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        self.word_list_box.config(yscrollcommand = self.scrollbar.set)

        self.word_list_box.bind("<<ListboxSelect>>", self.listCallback)

        #--------------frame03----------------
        self.prv_btn = ctk.CTkButton(frame03, text="Previous Frame", text_font=button_font, command=self.prvFrame)
        self.prv_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)

        self.play_btn = ctk.CTkButton(frame03, text="Play", height=50, width=100, text_font=button_font, command=self.play)
        self.play_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)
        
        self.next_btn = ctk.CTkButton(frame03, text="Next Frame", text_font=button_font, command=self.nextFrame)
        self.next_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)

        #--------------frame04----------------
        self.next_video_btn = ctk.CTkButton(frame04, text="Next Video", height=50, text_font=button_font, command=self.nextVideo)
        self.next_video_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)

        self.play_speed_btn = ctk.CTkButton(frame04, text="Speed : 1x", height=50, text_font=button_font, command=self.changeSpeed)
        self.play_speed_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10, expand=True)

        #--------------frame11----------------
        self.video_frame = ctk.CTkLabel(frame11)
        self.video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        #get time and refresh
        def tick():
            if self.playing and len(self.frames_buffer) > 0 and not self.loading_flag:
                self.setImageToFrame()

            frame0.after(int(1000/(self.fps*speeds[self.speed_index])), tick)
        tick()

        frame_image = ImageTk.PhotoImage(Image.fromarray(cv2.imread('assets/blank.png')))
        self.video_frame.configure(image=frame_image)

        self.master.mainloop()

    def About(self):
        messagebox.showinfo('Developer',"This ISL Dictionary Application \nDeveloped by\nSUVAJIT PATRA (CS PhD Student, RKMVERI, Belur)\ncontact e-mail address: suvajit790@gmail.com")
    
    def resize(self, window):
        if self.master.state() == 'normal' and self.widow_state == 'zoomed':
            self.video_size = (650, 800)
        else:
            height = self.video_frame.winfo_height()
            self.video_size = (int((height - 4) * (650/800)), (height - 4))
        if not self.playing and self.video_size[0] > 0 and self.video_size[1] > 0:
            if len(self.frames_buffer) > 0:
                frame_image = ImageTk.PhotoImage(Image.fromarray(self.frames_buffer[self.getFrameIndex()]).resize(self.video_size))
            else:
                frame_image = ImageTk.PhotoImage(Image.fromarray(cv2.imread('assets/blank.png')).resize(self.video_size))
            self.video_frame.configure(image=frame_image)
            self.video_frame.image = frame_image
        self.widow_state = self.master.state()

    def findWord(self, event=None):
        search_text = self.find_word_entry.get().strip().lower()
        if search_text.strip() == '':
            self.search_indices = []
            self.searched_text = search_text
            return

        if not search_text == self.searched_text:
            self.search_indices = []
            f_index = None
            for i in range(len(self.words)):
                if search_text == self.words[i].lower():
                    f_index = i
                elif search_text in re.split(',| |\(|\)|_|-|!|\+', self.words[i].lower()):
                    self.search_indices.insert(0, i)
                elif search_text in self.words[i].lower():
                    self.search_indices.append(i)
            if not f_index == None:
                self.search_indices.insert(0, f_index)
            self.searched_index = 0
            if len(self.search_indices) == 0:
                self.searched_text = search_text
                messagebox.showerror('Error', 'word is not in the dictionary')
                return
        else:
            self.searched_index += 1
            if len(self.search_indices) <= 1:
                self.s_index = None
            if len(self.search_indices) >= 1:
                self.searched_index %= len(self.search_indices)
        self.word_list_box.see(self.search_indices[self.searched_index])
        self.word_list_box.selection_set(self.search_indices[self.searched_index])
        if not self.s_index == None:
            self.word_list_box.selection_clear(self.s_index)
        self.s_index = self.search_indices[self.searched_index]
        self.searched_text = search_text

    def listCallback(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.index = index
            self.s_index = index
            data = event.widget.get(index)
            self.load(data)
            self.playing = True
            self.play_btn.configure(text='Pause')
    
    def loading(self, word):
        self.frames_buffer = []
        frame_data = imageio.get_reader(os.path.join(videos_dir, word.replace('/', ' or ')+'.mp4'))
        for image in frame_data.iter_data():
            self.frames_buffer.append(image)
        self.frame_index = 0
        self.loading_flag = False

    def load(self, word):
        self.loading_flag = True
        thread = Thread(target=self.loading, args=(word,))
        thread.daemon = 1
        thread.start()
    
    def changeSpeed(self):
        self.speed_index += 1
        self.speed_index %= len(speeds)
        self.play_speed_btn.configure(text="Speed : "+str(speeds[self.speed_index])+"x")
    
    def play(self):
        if not self.playing and len(self.frames_buffer) > 0:
            self.playing = True
            self.play_btn.configure(text='Pause')
        elif self.playing:
            self.playing = False
            self.play_btn.configure(text='Play')
    
    def nextFrame(self):
        if self.playing:
            self.playing = False
            self.play_btn.configure(text='Play')
        if len(self.frames_buffer) > 0:
            self.setImageToFrame(mode=1)
    
    def prvFrame(self):
        if self.playing:
            self.playing = False
            self.play_btn.configure(text='Play')
        if len(self.frames_buffer) > 0:
            self.setImageToFrame(mode=2)
    
    def nextVideo(self):
        if not self.index == None:
            self.index += 1
            self.index %= len(self.words)
            self.word_list_box.see(self.index)
            self.word_list_box.selection_set(self.index)
            if not self.s_index == None:
                self.word_list_box.selection_clear(self.s_index)
            self.s_index = self.index
            self.load(self.words[self.index])
    
    def setImageToFrame(self, mode=0):
        thread = Thread(target=self.processImg2Frm, args=(mode,))
        thread.daemon = 1
        thread.start()
    
    def processImg2Frm(self, mode=0):
        frame_image = ImageTk.PhotoImage(Image.fromarray(self.frames_buffer[self.getFrameIndex()]).resize(self.video_size))
        self.video_frame.configure(image=frame_image)
        self.video_frame.image = frame_image
        if mode == 1:
            self.frame_index += 2
        elif mode == 2:
            self.frame_index -= 2
        else:
            self.frame_index += 1

    def getFrameIndex(self):
        self.frame_index %= len(self.frames_buffer)
        return self.frame_index


if __name__ == '__main__':
    app = main_window(ctk.CTk())