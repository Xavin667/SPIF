    # -*- coding: utf-8 -*-
from threading import Thread, Lock
import time
from time import sleep
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from dobot_api import *
import json
from files.alarm_controller import alarm_controller_list
from files.alarm_servo import alarm_servo_list
import matplotlib.pyplot as plt

LABEL_JOINT = [["J1-", "J2-", "J3-", "J4-"],
               ["J1:", "J2:", "J3:", "J4:"],
               ["J1+", "J2+", "J3+", "J4+"]]

LABEL_COORD = [["X-", "Y-", "Z-", "R-"],
               ["X:", "Y:", "Z:", "R"],
               ["X+", "Y+", "Z+", "R+"]]


LABEL_ROBOT_MODE = {
    1:	"ROBOT_MODE_INIT",
    2:	"ROBOT_MODE_BRAKE_OPEN",
    3:	"",
    4:	"ROBOT_MODE_DISABLED",
    5:	"ROBOT_MODE_ENABLE",
    6:	"ROBOT_MODE_BACKDRIVE",
    7:	"ROBOT_MODE_RUNNING",
    8:	"ROBOT_MODE_RECORDING",
    9:	"ROBOT_MODE_ERROR",
    10:	"ROBOT_MODE_PAUSE",
    11:	"ROBOT_MODE_JOG"
}


class RobotUI(object):

    def __init__(self):
        self.tab1 = Tk()
        self.tab1.title("Dobot M1Pro SPIF Mode")
        # fixed window size
        self.tab1.geometry("1200x840")
        # set window icon
        # self.tab1.iconbitmap("images/robot.ico")

        # global state dict
        self.global_state = {}

        self.spif_running = False
        self.selected_file = StringVar()
        self.selected_file_kawasaki = StringVar()      

        # all button
        self.button_list = []

        # all entry
        self.entry_dict = {}
        # Create Notebook
        self.notebook = ttk.Notebook(self.tab1)
        self.notebook.place(x=0, y=0, width=1200, height=800)

        # Create Tab1
        self.tab1 = Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(self.tab1, text="Dobot")

        # Adding components to Tab1
        self.setup_tab1()

        # Create Tab2
        self.tab2 = Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(self.tab2, text="Kawasaki")

        # Adding components to Tab2
        self.setup_tab2()

    def setup_tab1(self):
        # Robot Connect
        self.frame_robot = LabelFrame(self.tab1, text="Robot Connect",
                                    labelanchor="nw", bg="#FFFFFF", width=870, height=120, border=2)

        self.label_ip = Label(self.frame_robot, text="IP Address:")
        self.label_ip.place(rely=0.2, x=10)
        ip_port = StringVar(self.tab1, value="192.168.1.6")
        self.entry_ip = Entry(self.frame_robot, width=12, textvariable=ip_port)
        self.entry_ip.place(rely=0.2, x=90)

        self.label_dash = Label(self.frame_robot, text="Dashboard Port:")
        self.label_dash.place(rely=0.2, x=210)
        dash_port = IntVar(self.tab1, value=29999)
        self.entry_dash = Entry(
            self.frame_robot, width=7, textvariable=dash_port)
        self.entry_dash.place(rely=0.2, x=320)

        self.label_move = Label(self.frame_robot, text="Move Port:")
        self.label_move.place(rely=0.2, x=400)
        move_port = IntVar(self.tab1, value=30003)
        self.entry_move = Entry(
            self.frame_robot, width=7, textvariable=move_port)
        self.entry_move.place(rely=0.2, x=480)

        self.label_feed = Label(self.frame_robot, text="Feedback Port:")
        self.label_feed.place(rely=0.2, x=580)
        feed_port = IntVar(self.tab1, value=30004)
        self.entry_feed = Entry(
            self.frame_robot, width=7, textvariable=feed_port)
        self.entry_feed.place(rely=0.2, x=680)

        # Connect/DisConnect
        self.button_connect = self.set_button(master=self.frame_robot,
                                            text="Disconnect", rely=0.6, x=630, command=self.connect_portThread)
        self.button_connect["width"] = 10
        self.global_state["connect"] = False

        # Dashboard Function
        self.frame_dashboard = LabelFrame(self.tab1, text="Dashboard Function",
                                        labelanchor="nw", bg="#FFFFFF", pady=10, width=870, height=120, border=2)

        # Enable/Disable
        self.button_enable = self.set_button(master=self.frame_dashboard,
                                            text="Enable", rely=0.1, x=10, command=self.enableThread)
        self.button_enable["width"] = 7
        self.global_state["enable"] = False

        # Reset Robot / Clear Error
        self.set_button(master=self.frame_dashboard,
                        text="Reset Robot", rely=0.1, x=145, command=self.reset_robotThread)
        self.set_button(master=self.frame_dashboard,
                        text="Clear Error", rely=0.1, x=290, command=self.clear_errorThread)

        # Speed Ratio
        self.label_speed = Label(self.frame_dashboard, text="Speed Ratio:")
        self.label_speed.place(rely=0.1, x=430)

        s_value = StringVar(self.tab1, value="60")
        self.entry_speed = Entry(self.frame_dashboard,
                                width=6, textvariable=s_value)
        self.entry_speed.place(rely=0.1, x=520)
        self.label_cent = Label(self.frame_dashboard, text="%")
        self.label_cent.place(rely=0.1, x=550)

        self.set_button(master=self.frame_dashboard,
                        text="Confirm", rely=0.1, x=586, command=self.confirm_speedThread)

        # DO:Digital Outputs
        self.label_digitial = Label(
            self.frame_dashboard, text="Digital Outputs: Index:")
        self.label_digitial.place(rely=0.55, x=10)

        i_value = IntVar(self.tab1, value="1")
        self.entry_index = Entry(
            self.frame_dashboard, width=5, textvariable=i_value)
        self.entry_index.place(rely=0.55, x=160)

        self.label_status = Label(self.frame_dashboard, text="Status:")
        self.label_status.place(rely=0.55, x=220)

        self.combo_status = ttk.Combobox(self.frame_dashboard, width=5)
        self.combo_status["value"] = ("On", "Off")
        self.combo_status.current(0)
        self.combo_status["state"] = "readonly"
        self.combo_status.place(rely=0.55, x=275)

        self.set_button(self.frame_dashboard, "Confirm",
                        rely=0.55, x=350, command=self.confirm_do)

        # Calibration
        self.frame_move = LabelFrame(self.tab1, text="Calibration", labelanchor="nw",
                                    bg="#FFFFFF", width=870, pady=0, height=130, border=2)

        self.set_move(text="X:", label_value=10,
                    default_value="330", entry_value=40, rely=0.1, master=self.frame_move)
        self.label_mm1 = Label(self.frame_move, text="mm")
        self.label_mm1.place(rely=0.1, x=80)
        self.set_move(text="Y:", label_value=120,
                    default_value="0", entry_value=150, rely=0.1, master=self.frame_move)
        self.label_mm2 = Label(self.frame_move, text="mm")
        self.label_mm2.place(rely=0.1, x=190)
        self.set_move(text="Z:", label_value=230,
                    default_value="150", entry_value=260, rely=0.1, master=self.frame_move)
        self.label_mm3 = Label(self.frame_move, text="mm")
        self.label_mm3.place(rely=0.1, x=300)
        self.set_move(text="R:", label_value=340,
                    default_value="0", entry_value=370, rely=0.1, master=self.frame_move)
        self.label_rpm = Label(self.frame_move, text="rpm")
        self.label_rpm.place(rely=0.1, x=410)
        self.set_button(master=self.frame_move, text="MovJ",
                        rely=0.05, x=460, command=self.movjThread)
        self.set_button(master=self.frame_move, text="Initial Position",
                        rely=0.05, x=530, command=self.InitialPositionThread) 
        self.set_button(master=self.frame_move, text="Middle Position",
                        rely=0.05, x=645, command=self.MiddlePointThread) 
        ## X
        self.set_button(master=self.frame_move, text="X: -1.0",
                        rely=0.4, x=20, command=self.Xminus1Thread)
        self.set_button(master=self.frame_move, text="X: -5.0",
                        rely=0.4, x=80, command=self.Xminus5Thread)
        self.set_button(master=self.frame_move, text="X: -10.0",
                        rely=0.4, x=140, command=self.Xminus10Thread)
        self.set_button(master=self.frame_move, text="X: +1.0",
                        rely=0.7, x=20, command=self.Xplus1Thread)
        self.set_button(master=self.frame_move, text="X: +5.0",
                        rely=0.7, x=80, command=self.Xplus5Thread)
        self.set_button(master=self.frame_move, text="X: +10.0",
                        rely=0.7, x=140, command=self.Xplus10Thread)
        ## Y
        ttk.Separator(self.frame_move, orient='vertical').place(x=220, rely=0.4, relheight=0.6)
        self.set_button(master=self.frame_move, text="Y: -1.0",
                        rely=0.4, x=240, command=self.Yminus1Thread)
        self.set_button(master=self.frame_move, text="Y: -5.0",
                        rely=0.4, x=300, command=self.Yminus5Thread)
        self.set_button(master=self.frame_move, text="Y: -10.0",
                        rely=0.4, x=360, command=self.Yminus10Thread)
        self.set_button(master=self.frame_move, text="Y: +1.0",
                        rely=0.7, x=240, command=self.Yplus1Thread)
        self.set_button(master=self.frame_move, text="Y: +5.0",
                        rely=0.7, x=300, command=self.Yplus5Thread)
        self.set_button(master=self.frame_move, text="Y: +10.0",
                        rely=0.7, x=360, command=self.Yplus10Thread)
        ## Z
        ttk.Separator(self.frame_move, orient='vertical').place(x=440, rely=0.4, relheight=0.6)
        self.set_button(master=self.frame_move, text="Z: -0.1",
                        rely=0.4, x=460, command=self.Zminus0_1Thread)
        self.set_button(master=self.frame_move, text="Z: -0.5",
                        rely=0.4, x=520, command=self.Zminus0_5Thread)
        self.set_button(master=self.frame_move, text="Z: -1.0",
                        rely=0.4, x=580, command=self.Zminus1_0Thread)
        self.set_button(master=self.frame_move, text="Z: +0.1",
                        rely=0.7, x=460, command=self.Zplus0_1Thread)
        self.set_button(master=self.frame_move, text="Z: +0.5",
                        rely=0.7, x=520, command=self.Zplus0_5Thread)
        self.set_button(master=self.frame_move, text="Z: +1.0",
                        rely=0.7, x=580, command=self.Zplus1_0Thread)
        ## R
        ttk.Separator(self.frame_move, orient='vertical').place(x=660, rely=0.4, relheight=0.6)
        self.set_button(master=self.frame_move, text="R: -1.0",
                        rely=0.4, x=680, command=self.Rminus1Thread)
        self.set_button(master=self.frame_move, text="R: -5.0",
                        rely=0.4, x=740, command=self.Rminus5Thread)
        self.set_button(master=self.frame_move, text="R: -10.0",
                        rely=0.4, x=800, command=self.Rminus10Thread)
        self.set_button(master=self.frame_move, text="R: +1.0",
                        rely=0.7, x=680, command=self.Rplus1Thread)
        self.set_button(master=self.frame_move, text="R: +5.0",
                        rely=0.7, x=740, command=self.Rplus5Thread)
        self.set_button(master=self.frame_move, text="R: +10.0",
                        rely=0.7, x=800, command=self.Rplus10Thread)
        # SPIF - From File
        self.frame_file = LabelFrame(self.tab1, text="SPIF - From File", labelanchor="nw",
                                    bg="#FFFFFF", width=870, pady=0, height=100, border=2)
        # Select move type - MovJ (joint move - throws less errors), MovL - linear mode
        self.label_type_file = Label(self.frame_file, text="Move type:")
        self.label_type_file.place(rely=0.1, x=10)
        self.type_file = ttk.Combobox(self.frame_file, width=10)
        self.type_file["value"] = ("MovJ", "MovL")
        self.type_file.current(0)
        self.type_file["state"] = "readonly"
        self.type_file.place(rely=0.1, x=80)
        # Sync - Yes - robot awaits finishing previous move before sending next one to queue (reduces vibrations but slows the process, needed when small amount of points)
        self.label_sync_file = Label(self.frame_file, text="Sync:")
        self.label_sync_file.place(rely=0.1, x=180)
        self.sync_file = ttk.Combobox(self.frame_file, width=10)
        self.sync_file["value"] = ("Yes", "No")
        self.sync_file.current(1)
        self.sync_file["state"] = "readonly"
        self.sync_file.place(rely=0.1, x=220)
        # Set CP -smoothness of the path
        self.label_cp = Label(self.frame_file, text="CP:")
        self.label_cp.place(rely=0.1, x=320)
        cp_value = StringVar(self.tab1, value="0")
        self.entry_cp = Entry(self.frame_file,
                                width=6, textvariable=cp_value)
        self.entry_cp.place(rely=0.1, x=350)
        self.label_centcp = Label(self.frame_file, text="%")
        self.label_centcp.place(rely=0.1, x=380)
        # Choose a file to be read - 3 first coordinates are taken
        self.set_button(master=self.frame_file, text="Select a File To Read",
                        rely=0.45, x=10, command=self.BrowseFilesThread)
        self.label_browsed_file = Label(self.frame_file, textvariable=self.selected_file)
        self.label_browsed_file.place(rely=0.49, x=150)
        self.set_button(master=self.frame_file, text="Execute Path From File",
                        rely=0.1, x=500, command=self.ExecutePathFromFileThread)  
        self.set_button(master=self.frame_file, text="Show Plot",
                        rely=0.45, x=500, command=self.ShowPlotFile) 
        self.set_button(master=self.frame_file, text="STOP",
                        rely=0.22, x=700, command=self.Stop)
        
 
        self.frame_feed_log = Frame(
            self.tab1, bg="#FFFFFF", width=870, pady=10, height=400, border=2)
        
        # SPIF
        self.frame_spif = LabelFrame(self.tab1, text="SPIF", labelanchor="nw",
                                    bg="#FFFFFF", width=870, pady=0, height=100, border=2)
        ## Figure type
        self.label_type = Label(self.frame_spif, text="Type:")
        self.label_type.place(rely=0.05, x=10)
        self.combo_type = ttk.Combobox(self.frame_spif, width=10)
        self.combo_type["value"] = ("Triangle", "Square", "Circle")
        self.combo_type.current(0)
        self.combo_type["state"] = "readonly"
        self.combo_type.place(rely=0.05, x=60)
        ## Diameter
        self.label_diameter = Label(self.frame_spif, text="Diameter:")
        self.label_diameter.place(rely=0.05, x=180)
        diameter_value = StringVar(self.tab1, value="50")
        self.entry_diameter = Entry(self.frame_spif,
                                width=6, textvariable=diameter_value)
        self.entry_diameter.place(rely=0.05, x=250)
        self.label_mm = Label(self.frame_spif, text="mm")
        self.label_mm.place(rely=0.05, x=290)
        ## Step - every iteration diameter is a step smaller
        self.label_step = Label(self.frame_spif, text="Step:")
        self.label_step.place(rely=0.4, x=10)
        step_value = StringVar(self.tab1, value="0.2")
        self.entry_step = Entry(self.frame_spif,
                                width=6, textvariable=step_value)
        self.entry_step.place(rely=0.4, x=60)
        self.label_mm2 = Label(self.frame_spif, text="mm")
        self.label_mm2.place(rely=0.4, x=100)
        ## Depth
        self.label_depth = Label(self.frame_spif, text="Depth:")
        self.label_depth.place(rely=0.4, x=180)
        depth_value = StringVar(self.tab1, value="30")
        self.entry_depth = Entry(self.frame_spif,
                                width=6, textvariable=depth_value)
        self.entry_depth.place(rely=0.4, x=250)
        self.label_mm3 = Label(self.frame_spif, text="mm")
        self.label_mm3.place(rely=0.4, x=290)
        ## SPIF functions
        self.set_button(master=self.frame_spif, text="Execute Pattern",
                        rely=0.05, x=360, command=self.ExecutePatternThread)
        self.set_button(master=self.frame_spif, text="Show Plot",
                        rely=0.4, x=360, command=self.ShowPlot)
        ttk.Separator(self.frame_spif, orient='vertical').place(relx=0.54, rely=0, relheight=1.2)
        self.set_button(master=self.frame_spif, text="Make 4 Small Figures",
                        rely=0.05, x=480, command=self.Make4SmallFiguresThread)
        self.set_button(master=self.frame_spif, text="Show Plot",
                        rely=0.4, x=480, command=self.ShowPlot4Figures)
        ttk.Separator(self.frame_spif, orient='vertical').place(relx=0.72, rely=0, relheight=1.2)
        self.set_button(master=self.frame_spif, text="Execute Pattern With Die",
                        rely=0.05, x=630, command=self.ExecutePatternWithDieThread)
        self.set_button(master=self.frame_spif, text="Show Plot",
                        rely=0.4, x=630, command=self.ShowPlotWithDie)
        # Feedback
        self.frame_feed = LabelFrame(self.frame_feed_log, text="Feedback", labelanchor="nw",
                                    bg="#FFFFFF", width=550, height=170)

        self.frame_feed.place(relx=0, rely=0, relheight=1)

        # WARNING
        self.set_label(self.frame_feed, text="REENABLE ROBOT AFTER USING THIS BUTTONS TO AVOID ERROR - DISABLE + ENABLE", rely=0.0, x=10)
        # Robot Mode
        self.set_label(self.frame_feed, text="Robot Mode:", rely=0.12, x=10)
        self.label_robot_mode = self.set_label(
            self.frame_feed, "", rely=0.1, x=95)
        # Current Position
        self.set_label(self.frame_feed, text="Current Position:", rely=0.73, x=10)
        self.set_label(self.frame_feed, "X:", rely=0.83, x=10)
        self.label_posx = self.set_label(
            self.frame_feed, "330.0", rely=0.83, x=30)
        self.set_label(self.frame_feed, " Y:", rely=0.83, x=100)
        self.label_posy = self.set_label(
            self.frame_feed, "0.0", rely=0.83, x=120)
        self.set_label(self.frame_feed, " Z:", rely=0.83, x=190)
        self.label_posz = self.set_label(
            self.frame_feed, "200.0", rely=0.83, x=210)
        self.set_label(self.frame_feed, "R:", rely=0.83, x=280)
        self.label_posr = self.set_label(
            self.frame_feed, "0.0", rely=0.83, x=300)
        # Movement Buttons
        self.label_feed_dict = {}
        self.set_feed(LABEL_JOINT, 9, 52, 74, 117)
        self.set_feed(LABEL_COORD, 165, 209, 231, 272)


        # Error Info
        self.frame_err = LabelFrame(self.frame_feed, text="Error Info", labelanchor="nw",
                                    bg="#FFFFFF", width=220, height=50)
        self.frame_err.place(relx=0.58, rely=0.1, relheight=0.7)

        self.text_err = ScrolledText(
            self.frame_err, width=210, height=50, relief="flat")
        self.text_err.place(rely=0.1, relx=0, relheight=0.7, relwidth=1)

        self.set_button(self.frame_feed, "Clear", rely=0.81,
                        x=487, command=self.clear_error_info)

        # Log
        self.frame_log = LabelFrame(self.frame_feed_log, text="Log", labelanchor="nw",
                                    bg="#FFFFFF", width=300, height=150)
        self.frame_log.place(relx=0.65, rely=0, relheight=1)

        self.text_log = ScrolledText(
            self.frame_log, width=270, height=140, relief="flat")
        self.text_log.place(rely=0, relx=0, relheight=1, relwidth=1)

        # Initial client
        self.client_dash = None
        self.client_move = None
        self.client_feed = None

        self.alarm_controller_dict = self.convert_dict(alarm_controller_list)
        self.alarm_servo_dict = self.convert_dict(alarm_servo_list)

    def setup_tab2(self):
        # Kawasaki
        self.frame_kawasaki = LabelFrame(self.tab2, text="Kawasaki", labelanchor="nw",
                                    bg="#FFFFFF", width=870, pady=0, height=800, border=2)
        # Select move type - JMOVE (joint move - throws less errors), LMOVE - linear mode
        self.label_type_kawasaki= Label(self.frame_kawasaki, text="Move type:")
        self.label_type_kawasaki.place(rely=0.0125, x=10)
        self.type_kawasaki = ttk.Combobox(self.frame_kawasaki, width=10)
        self.type_kawasaki["value"] = ("JMOVE", "LMOVE")
        self.type_kawasaki.current(0)
        self.type_kawasaki["state"] = "readonly"
        self.type_kawasaki.place(rely=0.0125, x=80)
        # Set Accuracy - accuracy radius around points
        self.label_acc = Label(self.frame_kawasaki, text="Accuracy:")
        self.label_acc.place(rely=0.0125, x=180)
        acc_value = StringVar(self.tab2, value="0")
        self.entry_acc = Entry(self.frame_kawasaki,
                                width=6, textvariable=acc_value)
        self.entry_acc.place(rely=0.0125, x=240)
        self.label_mm_acc = Label(self.frame_kawasaki, text="mm")
        self.label_mm_acc.place(rely=0.0125, x=270)
        # Set Speed - mm/s
        self.label_speed = Label(self.frame_kawasaki, text="Speed:")
        self.label_speed.place(rely=0.0125, x=320)
        speed_value = StringVar(self.tab2, value="10")
        self.entry_speed = Entry(self.frame_kawasaki,
                                width=6, textvariable=speed_value)
        self.entry_speed.place(rely=0.0125, x=360)
        self.label_mms_speed = Label(self.frame_kawasaki, text="mm/s")
        self.label_mms_speed.place(rely=0.0125, x=390)
        # Choose a file to be read - 3 first coordinates are taken
        self.set_button(master=self.frame_kawasaki, text="Select a File To Read",
                        rely=0.056, x=10, command=self.BrowseFilesThread)
        self.label_browsed_kawasaki = Label(self.frame_kawasaki, textvariable=self.selected_file_kawasaki)
        self.label_browsed_kawasaki.place(rely=0.06, x=150)
        self.set_button(master=self.frame_kawasaki, text="Show Plot",
                        rely=0.056, x=700, command=self.ShowPlotFile) 
        self.set_button(master=self.frame_kawasaki, text="Generate Init File",
                        rely=0.11, x=10, command=self.KawasakiInitFile) 
        self.set_button(master=self.frame_kawasaki, text="Generate SPIF File",
                        rely=0.11, x=130, command=self.KawasakiSPIFFile) 
        self.set_button(master=self.frame_kawasaki, text="Generate Main File",
                        rely=0.11, x=250, command=self.KawasakiMainFile) 
    # File with global robot settings
    def KawasakiInitFile(self):
        content = f""".PROGRAM Init()
        ACCURACY {str(self.entry_acc.get())} ALWAYS                 ; Default accuracy
        SPEED {str(self.entry_speed.get())} mm/s ALWAYS                    ; Default Speed
        ABS.SPEED OFF                       ; Switch off absolute speed
        PALMODE OFF                         ; Switch off palletizing mode
        QTOOL OFF                           ; Switch off block tool
        ZTCHSPDCHKAS ON                     ; Switch on speed check for real robot
        ;ZTCHSPDCHKAS OFF                    ; Switch off speed check for virtual robot (K-Roset)
        ;WEIGHT Wg_t_m, Wg_t_x, Wg_t_y, Wg_t_z  ; WEIGHT <Mass>, <x>, <y>, <z> (center of gravity)\n.END"""
        # Open a file in write mode
        with open("kawasaki_code/init.txt", "w") as file:
            # Write the content to the file
            file.write(content)
            file.close()
    # File with SPIF movement
    def KawasakiSPIFFile(self):
        file_path = self.selected_file_kawasaki.get()
        with open(file_path, 'r') as file:
            coordinates = file.read()
        coordinates = list(map(float, coordinates.split()))
        x, y, z = [], [], []
        for i in range(0, len(coordinates), 3):
            x.append(coordinates[i])
            y.append(coordinates[i+1])
            z.append(coordinates[i+2])
        # Open a file in write mode
        with open("kawasaki_code/spif.txt", "w") as file:
            # Write the content to the file
            file.write("  POINT curpos = HERE\n")
            for i in range(len(x)):
                if i == 0:
                    file.write(f"  {self.type_kawasaki.get()} SHIFT (curpos BY {x[i]}, {y[i]}, {z[i]+20})\n")
                    file.write(f"  {self.type_kawasaki.get()} SHIFT (curpos BY {x[i]}, {y[i]}, {z[i]})\n")
                else:
                    file.write(f"  {self.type_kawasaki.get()} SHIFT (curpos BY {x[i]}, {y[i]}, {z[i]})\n")
            file.close()
    # File with code to start SPIF process
    def KawasakiMainFile(self):
        content = """.PROGRAM Main()
        CALL Init
        CALL SPIF
        LMOVE SHIFT (curpos BY 0, 0, 50)
        PRINT "Program finished"\n.END"""

        # Open a file in write mode
        with open("kawasaki_code/main.txt", "w") as file:
            # Write the content to the file
            file.write(content)
            file.close()
    # Emergency STOP
    def Stop(self):
        self.client_dash.EmergencyStop()
    # Execute path from provided file
    def ExecutePathFromFile(self):
        """Read selected file, format it and proviide coordinates to MovL or MovJ function"""
        file_path = self.selected_file.get()
        type = str(self.type_file.get())
        sync = str(self.sync_file.get())
        cp = int(self.entry_cp.get())
        self.client_dash.CP(cp)
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        if file_path:
            try:
                # Open and read the file
                with open(file_path, 'r') as file:
                    coordinates = file.read()
                coordinates = list(map(float, coordinates.split()))
                x, y, z = [], [], []
                for i in range(0, len(coordinates), 3):
                    x.append(coordinates[i])
                    y.append(coordinates[i+1])
                    z.append(coordinates[i+2])
                start_time = time.time()
                for i in range(0, len(x)):
                    if not self.spif_running:
                        break
                    print(f"Current iteration: {i+1}")
                    print(f"Current time: {time.time() - start_time}\n")
                    try:
                        # Circle needs to use MovJ function for arced lines
                        if type == "MovJ" and sync == "No":
                            if i == 0:
                                # On first move we first move it to position straight above first point and then move to the metal sheet - \
                                # made to avoid dragging pin across the sheet
                                self.client_move.MovJ(positionx + x[i], positiony + y[i], 10 + positionz + z[i], 0)
                                self.client_move.MovJ(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                                sleep(2)
                            else:
                                self.client_move.MovJ(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                        # Circle needs to use MovJ function for arced lines
                        if type == "MovJ" and sync == "Yes":
                            if i == 0:
                                # On first move we first move it to position straight above first point and then move to the metal sheet - \
                                # made to avoid dragging pin across the sheet
                                self.client_move.MovJ(positionx + x[i], positiony + y[i], 10 + positionz + z[i], 0)
                                self.client_move.MovJ(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                                sleep(2)
                            else:
                                self.client_move.MovJ(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                                self.client_move.Sync()
                        # Square and triangle need MovL to move in linear style - if we use MovJ lines are arced
                        if type == "MovL" and sync == "No":
                            if i == 0:
                                # On first move we first move it to position straight above first point and then move to the metal sheet - \
                                # made to avoid dragging pin across the sheet
                                self.client_move.MovJ(positionx + x[i], positiony + y[i] + positiony, 10 + positionz + z[i], 0)
                                self.client_move.MovL(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                                sleep(2)
                            else:
                                self.client_move.MovL(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                        if type == "MovL" and sync == "Yes":
                            if i == 0:
                                # On first move we first move it to position straight above first point and then move to the metal sheet - \
                                # made to avoid dragging pin across the sheet
                                self.client_move.MovJ(positionx + x[i], positiony + y[i] + positiony, 10 + positionz + z[i], 0)
                                self.client_move.MovL(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                                sleep(2)
                            else:
                                self.client_move.MovL(positionx + x[i], positiony + y[i], positionz + z[i], 0)
                                self.client_move.Sync()
                    except IndexError:
                        pass
                    # Update GUI in the main thread
                    self.tab1.after(10, self.update_gui)
            except Exception as e:
                print(f"Error reading the file: {e}")
        else:
            print("No file selected.")
        end_time = time.time()
        # On finish move pin upwards to help with sheet removal and to indicate finish
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        self.client_move.MovJ(positionx, positiony, positionz + 50, 0)
        print(f"Time of execution: {end_time - start_time}")
    def BrowseFiles(self):
        file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("All Files", "*.*")])
        if file_path:
            # Update the selected file path
            self.selected_file.set(file_path)
            self.selected_file_kawasaki.set(file_path)
    def InitialPosition(self):
        # Move arm to initial position (400, 0, 200, 0)
        self.client_move.MovJ(400, 0, 200, 0)
    def MiddlePoint(self):
        # Move arm to the middle point of a die (330, 0, 160, 0)
        self.client_move.MovJ(330, 0, 160, 0)        
    def update_gui(self):
        # You can add GUI updates here if needed
        pass
    # In separate window show planned trajectory of your SPIF function with set parameters
    def ShowPlot(self):
        # Get type from dropdown table and choose appropriate function according to type
        type = str(self.combo_type.get())
        if type == "Triangle":
            x, y = self.CreateTriangle()
        elif type == "Square":
            x, y = self.CreateSquare()
        elif type == "Circle":
            x, y = self.CreateCircle()
        depth = float(self.entry_depth.get())
        # Create scene
        ax = plt.figure(figsize=(8,8), num="Planned Trajectory").add_subplot(projection='3d')
        # Calculate step to go down every iteration based on depth parameter and total iterations
        length = len(x)
        z_step = depth/length
        N = 5 * 0.1 / z_step  
        ax.set_box_aspect((N, N, 1))
        # Draw Die limit
        l, m = self.client_move.CircleSPIF(0.2, 139)
        ax.plot(l[0], m[0], -z_step*0)
        # Draw trajectory
        for i in range(0, length):
            ax.plot(x[i], y[i], -z_step*i)
        # Add axis labels with "mm" suffix
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        plt.show()
    # In separate window show planned trajectory of your SPIF with die (reversed) function with set parameters
    def ShowPlotWithDie(self):
        # Get type from dropdown table and choose appropriate function according to type
        type = str(self.combo_type.get())
        if type == "Triangle":
            x, y = self.CreateTriangle()
        elif type == "Square":
            x, y = self.CreateSquare()
        elif type == "Circle":
            x, y = self.CreateCircle()
        depth = float(self.entry_depth.get())
        # Create scene
        ax = plt.figure(figsize=(8,8), num="Planned Trajectory").add_subplot(projection='3d')
        # Calculate step to go down every iteration based on depth parameter and total iterations
        length = len(x)
        z_step = depth / (length)
        N = 5 * 0.1 / z_step  
        ax.set_box_aspect((N, N, 1))
        # Draw Die limit
        l, m = self.client_move.CircleSPIF(0.2, 139)
        ax.plot(l[0], m[0], -z_step*0)
        # Draw trajectory
        for i in range(0, length):
            ax.plot(x[length-1-i], y[length-1-i], -z_step*i)
        # Add axis labels with "mm" suffix
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        plt.show()
    def ShowPlotFile(self):
        file_path = self.selected_file.get()
        with open(file_path, 'r') as file:
            coordinates = file.read()
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        coordinates = list(map(float, coordinates.split()))
        x, y, z = [], [], []
        for i in range(0, len(coordinates), 3):
            x.append(coordinates[i])
            y.append(coordinates[i+1])
            z.append(coordinates[i+2])
        ax = plt.figure(figsize=(8,8), num="Planned Trajectory").add_subplot(projection='3d')
        N = 5 * 0.1 / 0.3   
        ax.set_box_aspect((N, N, 1))  
        l, m = self.client_move.CircleSPIF(0.2, 139)
        ax.plot(l[0]+330, m[0], 125)
        for i in range(0, len(x)):
            x[i] = x[i] + positionx
            y[i] = y[i] + positiony
            z[i] = z[i] + positionz
        ax.plot(x,y,z, linewidth=0.3)
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        plt.show()
    def ShowPlot4Figures(self):
        ax = plt.figure(figsize=(8,8), num="Planned Trajectory").add_subplot(projection='3d')
        type = str(self.combo_type.get())
        if type == "Triangle":
            x, y = self.CreateTriangle()
        elif type == "Square":
            x, y = self.CreateSquare()
        elif type == "Circle":
            x, y = self.CreateCircle()
        depth = float(self.entry_depth.get())
        length = len(x)
        z_step = depth/length
        N = 5 * 0.1 / z_step  
        ax.set_box_aspect((N, N, 1))  
        # Draw Die limit
        l, m = self.client_move.CircleSPIF(0.2, 139)
        ax.plot(l[0]+330, m[0], -z_step*0)
        if type == "Circle":
            for i in range(0, length):
                ax.plot(x[i]+300, y[i]+27.5, -z_step*i)
            for i in range(0, length):
                ax.plot(x[i] + 300, y[i]-27.5, -z_step*i)
            for i in range(0, length):
                ax.plot(x[i] + 360, y[i]+27.5, -z_step*i)
            for i in range(0, length):
                ax.plot(x[i] + 360, y[i]-27.5, -z_step*i)    
        else:  
            for i in range(0, length):
                for j in range(len(x[i])):
                    x[i][j] = x[i][j]+300
                    y[i][j] = y[i][j]+27.5
                ax.plot(x[i], y[i], -z_step*i)
            for i in range(0, length):
                for j in range(len(x[i])):
                    x[i][j] = x[i][j]
                    y[i][j] = y[i][j]-55
                ax.plot(x[i], y[i], -z_step*i)
            for i in range(0, length):
                for j in range(len(x[i])):
                    x[i][j] = x[i][j]+60
                    y[i][j] = y[i][j]+55
                ax.plot(x[i], y[i], -z_step*i)
            for i in range(0, length):
                for j in range(len(x[i])):
                    x[i][j] = x[i][j]
                    y[i][j] = y[i][j]-55
                ax.plot(x[i], y[i], -z_step*i)
        # Add axis labels with "mm" suffix
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        plt.show()
    # Use CircleSPIF function in dobot_api.py file to calculate coordinates
    def CreateCircle(self):
        """Calculate coordinates of Circle for SPIF and set according parameters"""
        step = float(self.entry_step.get())
        diameter = float(self.entry_diameter.get())
        x, y = self.client_move.CircleSPIF(step, diameter)
        # Speed set to 100 because interpolating 360 points every second takes a lot fo time
        self.client_dash.SpeedFactor(100)
        # Set smoothness of a path to max(interpolating values), needed to avoid vibrations of a robot during making circles
        self.client_dash.CP(100)
        return x, y
    # Use SquareSPIF function in dobot_api.py file to calculate coordinates
    def CreateSquare(self):
        """Calculate coordinates of Square for SPIF and set according parameters"""
        step = float(self.entry_step.get())
        diameter = float(self.entry_diameter.get())
        x, y = self.client_move.SquareSPIF(step, diameter)
        # Set smoothness of a path to 0 - if set to more than 0 it makes 90 degree angles to be arcs
        self.client_dash.CP(0)
        return x, y
    # Use TriangleSPIF function in dobot_api.py file to calculate coordinates
    def CreateTriangle(self):
        """Calculate coordinates of Triangle for SPIF and set according parameters"""
        step = float(self.entry_step.get())
        diameter = float(self.entry_diameter.get())
        x, y = self.client_move.TriangleSPIF(step, diameter)
        # Set smoothness of a path to 0 - if set to more than 0 it makes 90 degree angles to be arcs
        self.client_dash.CP(0)
        return x, y
    # Send coordinates values to Dobot M1Pro so it can start SPIF
    def ExecutePattern(self):
        """Get all parameters from UI and send appropriate info about speed, CP and coordinates to Dobot M1Pro"""
        if float(self.entry_diameter.get()) > 130:
            print("Diameter is too large - LIMIT: 130")
            return 
        # Get type from dropdown table and choose appropriate function according to type
        type = str(self.combo_type.get())
        if type == "Triangle":
            x, y = self.CreateTriangle()
        elif type == "Square":
            x, y = self.CreateSquare()
        elif type == "Circle":
            x, y = self.CreateCircle()
        depth = float(self.entry_depth.get())
        # Calculate step to go down every iteration based on depth parameter and total iterations
        z_step = depth / len(x)
        # Get current robot position - it's a middle of a circle in which shape will be calculated
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        start_time = time.time()
        for i in range(len(x)):
            for j in range(len(x[i])):
                if not self.spif_running:
                    break
                print(f"Current iteration: {i+1}")
                print(f"Current time: {time.time() - start_time}\n")
                try:
                    # Circle needs to use MovJ function for arced lines
                    if type == "Circle":
                        if i == 0 and j == 0:
                            # On first move we first move it to position straight above first point and then move to the metal sheet - \
                            # made to avoid dragging pin across the sheet
                            self.client_move.MovJ(x[i][j] + positionx, y[i][j] + positiony, 10 + positionz - z_step * (i - 1), 0)
                            self.client_move.MovJ(x[i][j] + positionx, y[i][j] + positiony, positionz - z_step * (i - 1), 0)
                            sleep(2)
                        else:
                            self.client_move.MovJ(x[i][j] + positionx, y[i][j] + positiony, positionz - z_step * (i - 1), 0)
                    # Square and triangle need MovL to move in linear style - if we use MovJ lines are arced
                    if type == "Square" or type == "Triangle":
                        if i == 0 and j == 0:
                            # On first move we first move it to position straight above first point and then move to the metal sheet - \
                            # made to avoid dragging pin across the sheet
                            self.client_move.MovJ(x[i][j] + positionx, y[i][j] + positiony, 10 + positionz - z_step * (i - 1), 0)
                            self.client_move.MovL(x[i][j] + positionx, y[i][j] + positiony, positionz - z_step * (i - 1), 0)
                            sleep(2)
                        else:
                            self.client_move.MovL(x[i][j] + positionx, y[i][j] + positiony, positionz - z_step * (i - 1), 0)
                            self.client_move.Sync()
                        # Update GUI in the main thread
                        self.tab1.after(10, self.update_gui)
                except IndexError:
                    pass
        end_time = time.time()
        # On finish move pin upwards to help with sheet removal and to indicate finish
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        self.client_move.MovJ(positionx, positiony, positionz + 50, 0)
        print(f"Time of execution: {end_time - start_time}")
    # Start forming from the middle to the outside - to use when die is installed in base
    def ExecutePatternWithDie(self):
        """Reverse process so it starts in the middle and goes outwards - to use with die installed in base"""
        if float(self.entry_diameter.get()) > 130:
            print("Diameter is too large - LIMIT: 130")
            return 
        # Get type from dropdown table and choose appropriate function according to type
        type = str(self.combo_type.get())
        if type == "Triangle":
            x, y = self.CreateTriangle()
        elif type == "Square":
            x, y = self.CreateSquare()
        elif type == "Circle":
            x, y = self.CreateCircle()
        depth = float(self.entry_depth.get())
        # Calculate step to go down every iteration based on depth parameter and total iterations
        z_step = depth / (len(x))
        # Get current robot position - it's a middle of a circle in which shape will be calculated
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        it = 0
        start_time = time.time()
        for i in range(0,len(x)):
            for j in range(len(x[i])):
                if not self.spif_running:
                    break
                print(f"Current iteration: {i+1}")
                print(f"Current time: {time.time() - start_time}\n")
                try:
                    # Circle needs to use MovJ function for arced lines
                    if type == "Circle":
                        if it == 0 and j == 0:
                            # On first move we first move it to position straight above first point and then move to the metal sheet - \
                            # made to avoid dragging pin across the sheet
                            self.client_move.MovJ(x[len(x) - i][j] + positionx, y[len(x) - i][j] + positiony, 10 + positionz - z_step * (it - 1), 0)
                            self.client_move.MovJ(x[len(x) - i][j] + positionx, y[len(x) - i][j] + positiony, positionz - z_step * (it - 1), 0)
                        else:
                            self.client_move.MovJ(x[len(x) - i][j] + positionx, y[len(x) - i][j] + positiony, positionz - z_step * (it - 1), 0)
                    # Square and triangle need MovL to move in linear style - if we use MovJ lines are arced
                    if type == "Square" or type == "Triangle":
                        if it == 0 and j == 0:
                            # On first move we first move it to position straight above first point and then move to the metal sheet - \
                            # made to avoid dragging pin across the sheet
                            self.client_move.MovJ(x[len(x) - i][j] + positionx, y[len(x) - i][j] + positiony, 10 + positionz - z_step * (it - 1), 0)
                            self.client_move.MovL(x[len(x) - i][j] + positionx, y[len(x) - i][j] + positiony, positionz - z_step * (it - 1), 0)
                        else:
                            self.client_move.MovL(x[len(x) - i][j] + positionx, y[len(x) - i][j] + positiony, positionz - z_step * (it - 1), 0)
                            self.client_move.Sync()
                except IndexError:
                    pass
                # Update GUI in the main thread
                self.tab1.after(10, self.update_gui)
            it += 1
        end_time = time.time()
        # On finish move pin upwards to help with sheet removal and to indicate finish
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        self.client_move.MovJ(positionx, positiony, positionz + 50, 0)
        print(f"Time of execution: {end_time - start_time}")
    # Make 4 smaller figures (max diameter is 50) on one sheet
    def Make4SmallFigures(self):
        """SPIF 4 smaller figures, function makes one iteration on each figure and moves to the next so every figure is made simultaneously"""
        # Get current robot position, for this function only starting height is needed
        position = self.client_dash.GetPose()
        positionz = float(position.split(",")[3])
        depth = float(self.entry_depth.get())
        # When diameter is over the limit - stop the function from progressing
        if float(self.entry_diameter.get()) > 50:
            print("Diameter is too large - LIMIT: 50")
            return 
        # Get type from dropdown table and choose appropriate function according to type
        type = str(self.combo_type.get())
        if type == "Circle":
            x, y = self.CreateCircle()
        elif type == "Triangle":
            x, y = self.CreateTriangle()
        elif type == "Square":
            x, y = self.CreateSquare()
        # Move to the middle of a base
        self.client_move.MovJ(331, 0, 180, 0)
        sleep(1)
        # Set starting positions foor every figure - the only parameter we set is starting height
        position1 = [300, 27.5, positionz]
        position2 = [300, -27.5, positionz]
        position3 = [360, -27.5, positionz]
        position4 = [360, 27.5, positionz]
        z_step = depth / len(x)
        start_time = time.time()
        for i in range(len(x)):
            for j in range(len(x[i])):
                if not self.spif_running:
                    break
                print(f"Current iteration: {i+1}")
                print(f"Current time: {time.time() - start_time}\n")
                # We do one iteration on a figure and move to the next one
                try:
                    # Circle needs to use MovJ function for arced lines
                    if type == "Circle":
                        if j == 0:
                            # On first move we first move it to position straight above first point and then move to the metal sheet - \
                            # made to avoid dragging pin across the sheet. Lower the speed to avoid punching through metal
                            self.client_move.MovJ(x[i][j] + position1[0], y[i][j] + position1[1], 50 + position1[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovJ(x[i][j] + position1[0], y[i][j] + position1[1], position1[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(100)
                        else:
                            self.client_move.MovJ(x[i][j] + position1[0], y[i][j] + position1[1], position1[2] - z_step * (i - 1), 0)
                            # After last move of each figure iteration we move pin upwards so it doesn't drag across metal
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position1[0], y[i][j] + position1[1], 50 + position1[2] - z_step * (i - 1), 0)
                    if type == "Square" or type == "Triangle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position1[0], y[i][j] + position1[1], 50 + position1[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovL(x[i][j] + position1[0], y[i][j] + position1[1], position1[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(50)
                        else:
                            self.client_move.MovL(x[i][j] + position1[0], y[i][j] + position1[1], position1[2] - z_step * (i - 1), 0)
                            self.client_move.Sync()
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position1[0], y[i][j] + position1[1], 50 + position1[2] - z_step * (i - 1), 0)
                                self.client_move.Sync()
                except IndexError:
                    pass
                # Update GUI in the main thread
                self.tab1.after(10, self.update_gui)
            for j in range(len(x[i])):
                if not self.spif_running:
                    break
                print(f"Current iteration: {i+1}")
                print(f"Current time: {time.time() - start_time}\n")
                try:
                    if type == "Circle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position2[0], y[i][j] + position2[1], 50 + position2[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovJ(x[i][j] + position2[0], y[i][j] + position2[1], position2[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(100)
                        else:
                            self.client_move.MovJ(x[i][j] + position2[0], y[i][j] + position2[1], position2[2] - z_step * (i - 1), 0)
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position2[0], y[i][j] + position2[1], 50 + position2[2] - z_step * (i - 1), 0)
                    if type == "Square" or type == "Triangle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position2[0], y[i][j] + position2[1], 50 + position2[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovL(x[i][j] + position2[0], y[i][j] + position2[1], position2[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(50)
                        else:
                            self.client_move.MovL(x[i][j] + position2[0], y[i][j] + position2[1], position2[2] - z_step * (i - 1), 0)
                            self.client_move.Sync()
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position2[0], y[i][j] + position2[1], 50 + position2[2] - z_step * (i - 1), 0)
                                self.client_move.Sync()
                except IndexError:
                    pass 
                # Update GUI in the main thread
                self.tab1.after(10, self.update_gui)                 
            for j in range(len(x[i])):
                if not self.spif_running:
                    break
                print(f"Current iteration: {i+1}")
                print(f"Current time: {time.time() - start_time}\n")
                try:
                    if type == "Circle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position3[0], y[i][j] + position3[1], 50 + position3[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovJ(x[i][j] + position3[0], y[i][j] + position3[1], position3[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(100)
                        else:
                            self.client_move.MovJ(x[i][j] + position3[0], y[i][j] + position3[1], position3[2] - z_step * (i - 1), 0)
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position3[0], y[i][j] + position3[1], 50 + position3[2] - z_step * (i - 1), 0)
                    if type == "Square" or type == "Triangle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position3[0], y[i][j] + position3[1], 50 + position3[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovL(x[i][j] + position3[0], y[i][j] + position3[1], position3[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(50)
                        else:
                            self.client_move.MovL(x[i][j] + position3[0], y[i][j] + position3[1], position3[2] - z_step * (i - 1), 0)
                            self.client_move.Sync()      
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position3[0], y[i][j] + position3[1], 50 + position3[2] - z_step * (i - 1), 0)
                                self.client_move.Sync()                  
                except IndexError:
                    pass
                # Update GUI in the main thread
                self.tab1.after(10, self.update_gui)
            for j in range(len(x[i])):
                if not self.spif_running:
                    break
                print(f"Current iteration: {i+1}")
                print(f"Current time: {time.time() - start_time}\n")
                try:
                    if type == "Circle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position4[0], y[i][j] + position4[1], 50 + position4[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovJ(x[i][j] + position4[0], y[i][j] + position4[1], position4[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(100)
                        else:
                            self.client_move.MovJ(x[i][j] + position4[0], y[i][j] + position4[1], position4[2] - z_step * (i - 1), 0)
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position4[0], y[i][j] + position4[1], 50 + position4[2] - z_step * (i - 1), 0)
                    if type == "Square" or type == "Triangle":
                        if j == 0:
                            self.client_move.MovJ(x[i][j] + position4[0], y[i][j] + position4[1], 50 + position4[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(10)
                            self.client_move.MovL(x[i][j] + position4[0], y[i][j] + position4[1], position4[2] - z_step * (i - 1), 0)
                            self.client_dash.SpeedFactor(50)
                        else:
                            self.client_move.MovL(x[i][j] + position4[0], y[i][j] + position4[1], position4[2] - z_step * (i - 1), 0)
                            self.client_move.Sync()
                            if j == len(x[i]) - 1:
                                self.client_move.MovL(x[i][j] + position4[0], y[i][j] + position4[1], 50 + position4[2] - z_step * (i - 1), 0)
                                self.client_move.Sync()
                except IndexError:
                    pass
                # Update GUI in the main thread
                self.tab1.after(10, self.update_gui)
        end_time = time.time()
        # On finish move pin upwards to help with sheet removal and to indicate finish
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        self.client_move.MovJ(positionx, positiony, positionz + 50, 0)
        print(f"Time of execution: {end_time - start_time}")
    
    def convert_dict(self, alarm_list):
        alarm_dict = {}
        for i in alarm_list:
            alarm_dict[i["id"]] = i
        return alarm_dict
    def print(self):
        print(self.combo_type.get())
    def read_file(self, path):
        # self.read_file("files/alarm_controller.json")
        with open(path, "r", encoding="utf8") as fp:
            json_data = json.load(fp)
        return json_data

    def mainloop(self):
        self.tab1.mainloop()

    def pack(self):
        self.frame_robot.pack()
        self.frame_dashboard.pack()
        self.frame_move.pack()
        self.frame_spif.pack()
        self.frame_file.pack()
        self.frame_feed_log.pack()
        self.frame_kawasaki.pack()

    def set_move(self, text, label_value, default_value, entry_value, rely, master):
        self.label = Label(master, text=text)
        self.label.place(rely=rely, x=label_value)
        value = StringVar(self.tab1, value=default_value)
        self.entry_temp = Entry(master, width=6, textvariable=value)
        self.entry_temp.place(rely=rely, x=entry_value)
        self.entry_dict[text] = self.entry_temp

    def move_jog(self, text):
        if self.global_state["connect"]:
            self.client_move.MoveJog(text)

    def move_stop(self, event):
        if self.global_state["connect"]:
            self.client_move.MoveJog("")

    def set_button(self, master, text, rely, x, **kargs):
        self.button = Button(master, text=text, padx=5,
                            command=kargs["command"])
        self.button.place(rely=rely, x=x)

        # if text != "Connect":
        #     self.button["state"] = "disable"
        #     self.button_list.append(self.button)
        return self.button

    def set_button_bind(self, master, text, rely, x, **kargs):
        self.button = Button(master, text=text, padx=5)
        self.button.bind("<ButtonPress-1>",
                        lambda event: self.move_jog(text=text))
        self.button.bind("<ButtonRelease-1>", self.move_stop)
        self.button.place(rely=rely, x=x)

        # if text != "Connect":
        #     self.button["state"] = "disable"
        #     self.button_list.append(self.button)
        return self.button

    def set_label(self, master, text, rely, x):
        self.label = Label(master, text=text)
        self.label.place(rely=rely, x=x)
        return self.label

    def connect_port(self):
        if self.global_state["connect"]:
            print("Disconnected successfully!")
            self.client_dash.close()
            self.client_feed.close()
            self.client_move.close()
            self.client_dash = None
            self.client_feed = None
            self.client_move = None

            for i in self.button_list:
                i["state"] = "disable"
            self.button_connect["text"] = "Connect"
        else:
            try:
                print("Connection establishing...")
                self.client_dash = DobotApiDashboard(
                    self.entry_ip.get(), int(self.entry_dash.get()), self.text_log)
                self.client_move = DobotApiMove(
                    self.entry_ip.get(), int(self.entry_move.get()), self.text_log)
                self.client_feed = DobotApi(
                    self.entry_ip.get(), int(self.entry_feed.get()), self.text_log)
            except Exception as e:
                messagebox.showerror("Attention!", f"Connection Error:{e}")
                return

            for i in self.button_list:
                i["state"] = "normal"
            self.button_connect["text"] = "Disconnect"
        self.global_state["connect"] = not self.global_state["connect"]
        self.set_feed_back()

    def set_feed_back(self):
        if self.global_state["connect"]:
            thread = Thread(target=self.feed_back)
            thread.setDaemon(True)
            thread.start()

    def enable(self):
        if self.global_state["enable"]:
            self.client_dash.DisableRobot()
            self.button_enable["text"] = "Enable"
        else:
            self.client_dash.EnableRobot()
            # if need time sleep
            # time.sleep(0.5)
            self.button_enable["text"] = "Disable"

        self.global_state["enable"] = not self.global_state["enable"]
    def reset_robot(self):
        self.client_dash.ResetRobot()
    def clear_error(self):
        self.client_dash.ClearError()
    def confirm_speed(self):
        self.client_dash.SpeedFactor(int(self.entry_speed.get()))

    def movj(self):
        self.client_move.MovJ(float(self.entry_dict["X:"].get()), float(self.entry_dict["Y:"].get()), float(self.entry_dict["Z:"].get()),
                            float(self.entry_dict["R:"].get()))

    def movl(self):
        self.client_move.MovL(float(self.entry_dict["X:"].get()), float(self.entry_dict["Y:"].get()), float(self.entry_dict["Z:"].get()),
                            float(self.entry_dict["R:"].get()))

    def joint_movj(self):
        self.client_move.JointMovJ(float(self.entry_dict["J1:"].get()), float(self.entry_dict["J2:"].get()), float(self.entry_dict["J3:"].get()),
                                float(self.entry_dict["J4:"].get()))

    def confirm_do(self):
        if self.combo_status.get() == "On":
            print("高电平")
            self.client_dash.DO(int(self.entry_index.get()), 1)
        else:
            print("低电平")
            self.client_dash.DO(int(self.entry_index.get()), 0)

    def set_feed(self, text_list, x1, x2, x3, x4):
        self.set_button_bind(
            self.frame_feed, text_list[0][0], rely=0.22, x=x1, command=lambda: self.move_jog(text_list[0][0]))
        self.set_button_bind(
            self.frame_feed, text_list[0][1], rely=0.34, x=x1, command=lambda: self.move_jog(text_list[0][1]))
        self.set_button_bind(
            self.frame_feed, text_list[0][2], rely=0.46, x=x1, command=lambda: self.move_jog(text_list[0][2]))
        self.set_button_bind(
            self.frame_feed, text_list[0][3], rely=0.58, x=x1, command=lambda: self.move_jog(text_list[0][3]))

        self.set_button_bind(
            self.frame_feed, text_list[2][0], rely=0.22, x=x2, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][1], rely=0.34, x=x2, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][2], rely=0.46, x=x2, command=lambda: self.move_jog(text_list[2][0]))
        self.set_button_bind(
            self.frame_feed, text_list[2][3], rely=0.58, x=x2, command=lambda: self.move_jog(text_list[2][0]))

    def feed_back(self):
        hasRead = 0
        while True:
            print("self.global_state(connect)", self.global_state["connect"])
            if not self.global_state["connect"]:
                break
            data = bytes()
            while hasRead < 1440:
                temp = self.client_feed.socket_dobot.recv(1440 - hasRead)
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0

            a = np.frombuffer(data, dtype=MyType)
            print("robot_mode:", a["robot_mode"][0])
            print("test_value:", hex((a['test_value'][0])))
            if hex((a['test_value'][0])) == '0x123456789abcdef':
                # print('tool_vector_actual',
                #       np.around(a['tool_vector_actual'], decimals=4))
                # print('q_actual', np.around(a['q_actual'], decimals=4))

                # Refresh Properties
                self.label_robot_mode["text"] = LABEL_ROBOT_MODE[a["robot_mode"][0]]

                # check alarms
                if a["robot_mode"] == 9:
                    self.display_error_info()
                position = self.client_dash.GetPose()
                positionx = float(position.replace("{", "").split(",")[1])
                positiony = float(position.split(",")[2])
                positionz = float(position.split(",")[3])
                positionr = float(position.split(",")[4])
                # Current robot position
                self.label_posx["text"] = positionx
                self.label_posy["text"] = positiony
                self.label_posz["text"] = positionz
                self.label_posr["text"] = positionr

            time.sleep(0.005)

    def display_error_info(self):
        error_list = self.client_dash.GetErrorID().split("{")[1].split("}")[0]

        error_list = json.loads(error_list)
        print("error_list:", error_list)
        if error_list[0]:
            for i in error_list[0]:
                self.form_error(i, self.alarm_controller_dict,
                                "Controller Error")

        for m in range(1, len(error_list)):
            if error_list[m]:
                for n in range(len(error_list[m])):
                    self.form_error(n, self.alarm_servo_dict, "Servo Error")

    def form_error(self, index, alarm_dict: dict, type_text):
        if index in alarm_dict.keys():
            date = datetime.datetime.now().strftime("%Y.%m.%d:%H:%M:%S ")
            error_info = f"Time Stamp:{date}\n"
            error_info = error_info + f"ID:{index}\n"
            error_info = error_info + \
                f"Type:{type_text}\nLevel:{alarm_dict[index]['level']}\n" + \
                f"Solution:{alarm_dict[index]['en']['solution']}\n"

            self.text_err.insert(END, error_info)

    def clear_error_info(self):
        self.text_err.delete("1.0", "end")

    def set_feed_joint(self, label, value):
        array_value = np.around(value, decimals=4)
        self.label_feed_dict[label[1][0]]["text"] = array_value[0][0]
        self.label_feed_dict[label[1][1]]["text"] = array_value[0][1]
        self.label_feed_dict[label[1][2]]["text"] = array_value[0][2]
        self.label_feed_dict[label[1][3]]["text"] = array_value[0][3]
    # Define buttons moving robot by step
    # X
    def Xminus1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx - 1, positiony, positionz, positionr)
    def Xminus5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx - 5, positiony, positionz, positionr)    
    def Xminus10(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx - 10, positiony, positionz, positionr)
    def Xplus1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx + 1, positiony, positionz, positionr)
    def Xplus5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx + 5, positiony, positionz, positionr)
    def Xplus10(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx + 10, positiony, positionz, positionr)      
    # Y
    def Yminus1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony - 1, positionz, positionr)
    def Yminus5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony - 5, positionz, positionr)
    def Yminus10(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony - 10, positionz, positionr)
    def Yplus1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony + 1, positionz, positionr)
    def Yplus5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony + 5, positionz, positionr)
    def Yplus10(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony + 10, positionz, positionr)       
    # Height
    def Zminus0_1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz - 0.1, positionr)
    def Zminus0_5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz - 0.5, positionr)
    def Zminus1_0(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz - 1.0, positionr)
    def Zplus0_1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz + 0.1, positionr)
    def Zplus0_5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz + 0.5, positionr)
    def Zplus1_0(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz + 1.0, positionr)

    # Rotation
    def Rminus1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz, positionr - 1)
    def Rminus5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz, positionr - 5)
    def Rminus10(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz, positionr - 10)
    def Rplus1(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz, positionr + 1)
    def Rplus5(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz, positionr + 5)
    def Rplus10(self):
        position = self.client_dash.GetPose()
        positionx = float(position.replace("{", "").split(",")[1])
        positiony = float(position.split(",")[2])
        positionz = float(position.split(",")[3])
        positionr = float(position.split(",")[4])
        self.client_move.MovJ(positionx, positiony, positionz, positionr + 10.0)
    # Threads
    # Make it work in a different thread
    def ExecutePathFromFileThread(self):
        # Start SPIF loop in a separate thread
        self.execute_file_thread = Thread(target=self.ExecutePathFromFile)
        self.spif_running = True
        self.execute_file_thread.start()
    def InitialPositionThread(self):
        # Start SPIF loop in a separate thread
        self.initial_thread = Thread(target=self.InitialPosition)
        self.spif_running = True
        self.initial_thread.start()
    def movjThread(self):
        # Start SPIF loop in a separate thread
        self.movj_thread = Thread(target=self.movj)
        self.spif_running = True
        self.movj_thread.start()
    def ExecutePatternThread(self):
        # Start SPIF loop in a separate thread
        self.execute_pattern_thread = Thread(target=self.ExecutePattern)
        self.spif_running = True
        self.execute_pattern_thread.start()
    def ExecutePatternWithDieThread(self):
        # Start SPIF loop in a separate thread
        self.execute_pattern_die_thread = Thread(target=self.ExecutePatternWithDie)
        self.spif_running = True
        self.execute_pattern_die_thread.start()
    def Make4SmallFiguresThread(self):
        # Start SPIF loop in a separate thread
        self.make_4_thread = Thread(target=self.Make4SmallFigures)
        self.spif_running = True
        self.make_4_thread.start()
    def reset_robotThread(self):
        # Start SPIF loop in a separate thread
        self.reset_robot_thread = Thread(target=self.reset_robot)
        self.spif_running = True
        self.reset_robot_thread.start()
    def enableThread(self):
        # Start SPIF loop in a separate thread
        self.enable_thread = Thread(target=self.enable)
        self.spif_running = True
        self.enable_thread.start()
    def clear_errorThread(self):
        # Start SPIF loop in a separate thread
        self.clear_error_thread = Thread(target=self.clear_error)
        self.spif_running = True
        self.clear_error_thread.start()
    def connect_portThread(self):
        # Start SPIF loop in a separate thread
        self.connect_port_thread = Thread(target=self.connect_port)
        self.spif_running = True
        self.connect_port_thread.start()
    def confirm_speedThread(self):
        # Start SPIF loop in a separate thread
        self.confirm_speed_thread = Thread(target=self.confirm_speed)
        self.spif_running = True
        self.confirm_speed_thread.start()

    def Xminus1Thread(self):
        # Start SPIF loop in a separate thread
        self.x1m_thread = Thread(target=self.Xminus1)
        self.spif_running = True
        self.x1m_thread.start()
    def Xminus5Thread(self):
        # Start SPIF loop in a separate thread
        self.x5m_thread = Thread(target=self.Xminus5)
        self.spif_running = True
        self.x5m_thread.start()
    def Xminus10Thread(self):
        # Start SPIF loop in a separate thread
        self.xm10_thread = Thread(target=self.Xminus10)
        self.spif_running = True
        self.xm10_thread.start()
    def Xplus1Thread(self):
        # Start SPIF loop in a separate thread
        self.x1p_thread = Thread(target=self.Xplus1)
        self.spif_running = True
        self.x1p_thread.start()
    def Xplus5Thread(self):
        # Start SPIF loop in a separate thread
        self.x5p_thread = Thread(target=self.Xplus5)
        self.spif_running = True
        self.x5p_thread.start()
    def Xplus10Thread(self):
        # Start SPIF loop in a separate thread
        self.x10p_thread = Thread(target=self.Xplus10)
        self.spif_running = True
        self.x10p_thread.start()

    def Yminus1Thread(self):
        # Start SPIF loop in a separate thread
        self.y1m_thread = Thread(target=self.Yminus1)
        self.spif_running = True
        self.y1m_thread.start()
    def Yminus5Thread(self):
        # Start SPIF loop in a separate thread
        self.y5m_thread = Thread(target=self.Yminus5)
        self.spif_running = True
        self.y5m_thread.start()
    def Yminus10Thread(self):
        # Start SPIF loop in a separate thread
        self.ym10_thread = Thread(target=self.Yminus10)
        self.spif_running = True
        self.ym10_thread.start()
    def Yplus1Thread(self):
        # Start SPIF loop in a separate thread
        self.y1p_thread = Thread(target=self.Yplus1)
        self.spif_running = True
        self.y1p_thread.start()
    def Yplus5Thread(self):
        # Start SPIF loop in a separate thread
        self.y5p_thread = Thread(target=self.Yplus5)
        self.spif_running = True
        self.y5p_thread.start()
    def Yplus10Thread(self):
        # Start SPIF loop in a separate thread
        self.y10p_thread = Thread(target=self.Yplus10)
        self.spif_running = True
        self.y10p_thread.start()

    def Zminus0_1Thread(self):
        # Start SPIF loop in a separate thread
        self.minus0_1_thread = Thread(target=self.Zminus0_1)
        self.spif_running = True
        self.minus0_1_thread.start()
    def Zminus0_5Thread(self):
        # Start SPIF loop in a separate thread
        self.minus0_5_thread = Thread(target=self.Zminus0_5)
        self.spif_running = True
        self.minus0_5_thread.start()
    def Zminus1_0Thread(self):
        # Start SPIF loop in a separate thread
        self.minus1_0_thread = Thread(target=self.Zminus1_0)
        self.spif_running = True
        self.minus1_0_thread.start()
    def Zplus0_1Thread(self):
        # Start SPIF loop in a separate thread
        self.plus0_1_thread = Thread(target=self.Zplus0_1)
        self.spif_running = True
        self.plus0_1_thread.start()
    def Zplus0_5Thread(self):
        # Start SPIF loop in a separate thread
        self.plus0_5_thread = Thread(target=self.Zplus0_5)
        self.spif_running = True
        self.plus0_5_thread.start()
    def Zplus1_0Thread(self):
        # Start SPIF loop in a separate thread
        self.plus1_0_thread = Thread(target=self.Zplus1_0)
        self.spif_running = True
        self.plus1_0_thread.start()

    def Rminus1Thread(self):
        # Start SPIF loop in a separate thread
        self.r1m_thread = Thread(target=self.Rminus1)
        self.spif_running = True
        self.r1m_thread.start()
    def Rminus5Thread(self):
        # Start SPIF loop in a separate thread
        self.r5m_thread = Thread(target=self.Rminus5)
        self.spif_running = True
        self.r5m_thread.start()
    def Rminus10Thread(self):
        # Start SPIF loop in a separate thread
        self.rm10_thread = Thread(target=self.Rminus10)
        self.spif_running = True
        self.rm10_thread.start()
    def Rplus1Thread(self):
        # Start SPIF loop in a separate thread
        self.r1p_thread = Thread(target=self.Rplus1)
        self.spif_running = True
        self.r1p_thread.start()
    def Rplus5Thread(self):
        # Start SPIF loop in a separate thread
        self.r5p_thread = Thread(target=self.Rplus5)
        self.spif_running = True
        self.r5p_thread.start()
    def Rplus10Thread(self):
        # Start SPIF loop in a separate thread
        self.r10p_thread = Thread(target=self.Rplus10)
        self.spif_running = True
        self.r10p_thread.start()
    def MiddlePointThread(self):
        # Start SPIF loop in a separate thread
        self.middle_thread = Thread(target=self.MiddlePoint)
        self.spif_running = True
        self.middle_thread.start()
    def BrowseFilesThread(self):
        # Start SPIF loop in a separate thread
        self.browse_thread = Thread(target=self.BrowseFiles)
        self.spif_running = True
        self.browse_thread.start()