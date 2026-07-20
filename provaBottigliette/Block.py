import time
import numpy as np
import serial
import csv
import tkinter as tk
import threading
import queue
import winsound
from pathlib import Path
#import parallel

# ===========================================================
# Parallel Port
# ===========================================================
#ParalPort = parallel.Parallel()
#ParalPort.setData(0)

# ============================================================
# PARAMETRI
# ============================================================

PORT = 'COM3'
BAUDRATE = 9600

# ============================================================
# VARIABILI GLOBALI
# ============================================================

ser = None

gui_queue = queue.Queue()

button_thread = None
stop_button_thread = threading.Event()

Participant = ""
Session = ""
Condition = ""

root = None
left_panel = None
right_panel = None
left_touch_label = None
right_touch_label = None
left_label = None
right_label = None

# Label utilizzata per mostrare l'asincronia grasp
asincronia_label = None


# ============================================================
# GUI
# ============================================================

def create_status_window(master):
    global root
    global left_panel, right_panel
    global left_touch_label, right_touch_label
    global left_label, right_label
    global asincronia_label

    root = tk.Toplevel(master)
    root.title("Stato pulsanti")
    root.geometry("800x400")

    left_panel = tk.Frame(root, bg="red")
    right_panel = tk.Frame(root, bg="red")

    left_panel.pack(side="left", fill="both", expand=True)
    right_panel.pack(side="right", fill="both", expand=True)

    # ----------------------------
    # PANNELLO SINISTRO - SUB 1
    # ----------------------------

    left_touch_label = tk.Label(
        left_panel,
        text="",
        font=("Arial", 30, "bold"),
        bg="red",
        fg="white"
    )

    left_label = tk.Label(
        left_panel,
        text="SUB 1",
        font=("Arial", 40),
        bg="red",
        fg="white"
    )

    left_touch_label.pack(side="top", pady=30)
    left_label.pack(expand=True)

    # ----------------------------
    # PANNELLO DESTRO - SUB 2
    # ----------------------------

    right_touch_label = tk.Label(
        right_panel,
        text="",
        font=("Arial", 30, "bold"),
        bg="red",
        fg="white"
    )

    right_label = tk.Label(
        right_panel,
        text="SUB 2",
        font=("Arial", 40),
        bg="red",
        fg="white"
    )

    right_touch_label.pack(side="top", pady=30)
    right_label.pack(expand=True)

# ---------------------------------
# PANNELLO ASINCRONIA
# ---------------------------------

    #global asincronia_label
    #asincronia_label = tk.Label(master, text="Asincronia Grasp: ---", font=("Arial", 16))
    #asincronia_label.pack(pady=10)

    asincronia_label = tk.Label(
        root,
        text="",
        font=("Arial", 24, "bold"),
        bg="black",
        fg="white",
        padx=20,
        pady=8
    )

    asincronia_label.place(
        relx=0.5,
        rely=0.75,
        anchor="center"
    )

    asincronia_label.lift()


def set_left_color(color):
    left_panel.config(bg=color)
    left_label.config(bg=color)
    left_touch_label.config(bg=color)


def set_right_color(color):
    right_panel.config(bg=color)
    right_label.config(bg=color)
    right_touch_label.config(bg=color)


def set_left_touch_text(text):
    left_touch_label.config(text=text)


def set_right_touch_text(text):
    right_touch_label.config(text=text)


def clear_touch_texts():
    left_touch_label.config(text="")
    right_touch_label.config(text="")


def set_asincronia_grasp(value):
    asincronia_label.config(
        text=f"Asincronia Grasp: {value} ms"
    )

    asincronia_label.lift()


def clear_asincronia_grasp():
    asincronia_label.config(text="")


def process_gui_queue():
    while not gui_queue.empty():
        command = gui_queue.get()

        if isinstance(command, tuple):
            if command[0] == "UPDATE_ASINCRONIA":
                set_asincronia_grasp(command[1])

            continue

        if command == "SUB1_GREEN":
            set_left_color("green")

        elif command == "SUB1_RED":
            set_left_color("red")

        elif command == "SUB2_GREEN":
            set_right_color("green")

        elif command == "SUB2_RED":
            set_right_color("red")

        elif command == "SUB1_TOUCH_UP":
            set_left_touch_text("TOCCO SU")

        elif command == "SUB1_TOUCH_DOWN":
            set_left_touch_text("TOCCO GIU")

        elif command == "SUB2_TOUCH_UP":
            set_right_touch_text("TOCCO SU")

        elif command == "SUB2_TOUCH_DOWN":
            set_right_touch_text("TOCCO GIU")

        elif command == "CLEAR_TOUCH_TEXTS":
            clear_touch_texts()

        elif command == "CLEAR_ASINCRONIA":
            clear_asincronia_grasp()

        elif command == "BOTH_RED":
            set_left_color("red")
            set_right_color("red")

        elif command == "CLOSE":
            root.destroy()
            return
        
        #elif isinstance(msg, tuple) and msg[0] == "UPDATE_ASINCRONIA":
            #asincronia_label.config(text=f"Asincronia Grasp: {msg[1]}")   

    root.after(20, process_gui_queue)


# ============================================================
# SERIALE
# ============================================================

def open_serial(PORT, BAUDRATE):
    ser = serial.Serial(PORT, BAUDRATE, timeout=0.05)
    time.sleep(1)
    ser.reset_input_buffer()
    return ser


# ============================================================
# GUI INPUT DATI ESPERIMENTO
# ============================================================

def get_experiment_info(root):
    input_window = tk.Toplevel(root)
    input_window.title("Dati Esperimento")
    input_window.geometry("300x250")

    tk.Label(input_window, text="Participant:").pack(pady=5)
    participant_entry = tk.Entry(input_window)
    participant_entry.pack()

    tk.Label(input_window, text="Session:").pack(pady=5)
    session_entry = tk.Entry(input_window)
    session_entry.pack()

    tk.Label(input_window, text="Condition:").pack(pady=5)
    condition_entry = tk.Entry(input_window)
    condition_entry.pack()

    result = {}

    def submit():
        result["participant"] = participant_entry.get()
        result["session"] = session_entry.get()
        result["condition"] = condition_entry.get()
        input_window.destroy()

    tk.Button(input_window, text="Start", command=submit).pack(pady=20)

    root.wait_window(input_window)

    return result


# ============================================================
# LETTURA BUTTON_THREAD
# ============================================================

def readButtons():
    """
    Questa funzione legge Arduino quando non c'è un trial in corso.
    Serve solo ad aggiornare i colori della GUI.
    """
    global ser

    while not stop_button_thread.is_set():
        raw = ser.readline()

        if not raw:
            continue

        line = raw.decode('utf-8', errors='ignore').rstrip()

        if not line:
            continue

        if 'Button 1 pressed' in line:
            gui_queue.put("SUB1_GREEN")

        if 'Button 1 released' in line:
            gui_queue.put("SUB1_RED")

        if 'Button 2 pressed' in line:
            gui_queue.put("SUB2_GREEN")

        if 'Button 2 released' in line:
            gui_queue.put("SUB2_RED")


def start_button_thread():
    global button_thread

    if button_thread is not None and button_thread.is_alive():
        return

    stop_button_thread.clear()

    button_thread = threading.Thread(
        target=readButtons,
        daemon=True
    )

    button_thread.start()


def stop_button_thread_func():
    global button_thread

    stop_button_thread.set()

    if button_thread is not None:
        button_thread.join(timeout=1)

    button_thread = None


# ============================================================
# TRIAL
# ============================================================

def startTrial(nTrials, trial, output_matrix, output_file, 
               trial_vec, tocco_atteso_S1, tocco_atteso_S2, trigger_list, Participant, Session, Condition):
    while True:
        user_input = input("Premi 'a' per avviare il trial, 'r' per resettare, 'q' per uscire: ")

        if user_input == 'q':
            print('Uscita.')
            stop_button_thread_func()
            gui_queue.put("CLOSE")
            break

        elif user_input == 'a':
            stop_button_thread_func()

            ser.reset_input_buffer()

            gui_queue.put("CLEAR_TOUCH_TEXTS")
            gui_queue.put("CLEAR_ASINCRONIA")
            #gui_queue.put(("UPDATE_ASINCRONIA", "---"))

            #provare a mettere ParalPort = parallel.Parallel()
            #provare a mettere # ParalPort.setData(trigger_list[trial-1])
            #time.sleep(0.01)
            # trigger OFF
            #ParalPort.setData(0)

            winsound.PlaySound(trial_vec[trial - 1], winsound.SND_FILENAME | winsound.SND_ASYNC)


            start_time = time.time() #comincia a contare il parallelo al suono?
            



            

            print('Timer avviato.')

            completeTrial(
                trial,
                trial_vec,
                start_time,
                output_matrix,
                tocco_atteso_S1,
                tocco_atteso_S2,
                trigger_list,
                Participant,
                Session,
                Condition
            )
            
            #asincronia = output_matrix[trial, 8]  # colonna Asincronia Grasp
            #gui_queue.put(("UPDATE_ASINCRONIA", asincronia))


            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(output_matrix)

            print(f'Trial {trial} salvato.')

            trial = trial + 1
            if trial > nTrials:
                print('Blocco completato')
                gui_queue.put("CLOSE")
                break

            start_button_thread()

        elif user_input == 'r':
            trial = resetTrial(output_matrix, trial)

            gui_queue.put("CLEAR_TOUCH_TEXTS")

            print('Trial resettato.')


def resetTrial(output_matrix, trial):
    output_matrix[trial, 0:20] = 0

    trial = trial - 1

    if trial < 1:
        trial = 1

    return trial


def completeTrial(
    trial,
    trial_vec,
    start_time,
    output_matrix,
    tocco_atteso_S1,
    tocco_atteso_S2,
    trigger_list,
    Participant,
    Session,
    Condition
):
    # ===============================
    # INFO TRIAL
    # ===============================
    output_matrix[trial, 11] = trial
    output_matrix[trial, 12] = trial_vec[trial - 1]
    output_matrix[trial, 13] = tocco_atteso_S1[trial - 1]
    output_matrix[trial, 14] = tocco_atteso_S2[trial - 1]
    output_matrix[trial, 18] = Participant
    output_matrix[trial, 19] = Session
    output_matrix[trial, 20] = Condition
    output_matrix[trial, 21] = trigger_list[trial - 1]

    line = ''
    lines = []

    while 'time difference between grasps' not in line:
        raw = ser.readline()

        if not raw:
            continue

        line = raw.decode('utf-8', errors='ignore').rstrip()

        if not line:
            continue

        if len(lines) == 0 or lines[-1] != line:
            lines.append(line)
            print(line)

        # ====================================================
        # AGGIORNAMENTO COLORI GUI DURANTE IL TRIAL
        # ====================================================

        if 'Button 1 pressed' in line:
            gui_queue.put("SUB1_GREEN")

        if 'Button 1 released' in line:
            gui_queue.put("SUB1_RED")
            ButtonTimeReleased1 = time.time()
            output_matrix[trial, 3] = int((ButtonTimeReleased1 - start_time) * 1000)

        if 'Button 2 pressed' in line:
            gui_queue.put("SUB2_GREEN")

        if 'Button 2 released' in line:
            gui_queue.put("SUB2_RED")
            ButtonTimeReleased2 = time.time()
            output_matrix[trial, 4] = int((ButtonTimeReleased2 - start_time) * 1000)

        # ====================================================
        # SCRITTE TOCCO SU / TOCCO GIU
        # ====================================================

        if 'SUB1 UP' in line:
            output_matrix[trial, 9] = 1
            gui_queue.put("SUB1_TOUCH_UP")

        if 'SUB1 DOWN' in line:
            output_matrix[trial, 9] = 2
            gui_queue.put("SUB1_TOUCH_DOWN")

        if 'SUB2 UP' in line:
            output_matrix[trial, 10] = 1
            gui_queue.put("SUB2_TOUCH_UP")

        if 'SUB2 DOWN' in line:
            output_matrix[trial, 10] = 2
            gui_queue.put("SUB2_TOUCH_DOWN")

        # ====================================================
        # DATI TRIAL
        # ====================================================

        if 'SUB1 Grasped' in line:
            StopSub1 = time.time()
            output_matrix[trial, 6] = int((StopSub1 - start_time) * 1000)

        if 'SUB2 Grasped' in line:
            StopSub2 = time.time()
            output_matrix[trial, 7] = int((StopSub2 - start_time) * 1000)

    parseOutputs(lines, output_matrix, trial)

    output_matrix[trial, 5] = np.abs(output_matrix[trial, 3] - output_matrix[trial, 4])
    output_matrix[trial, 8] = np.abs(output_matrix[trial, 6] - output_matrix[trial, 7])

    gui_queue.put(
        ("UPDATE_ASINCRONIA", int(output_matrix[trial, 8]))
    )

    if output_matrix[trial, 9] == tocco_atteso_S1[trial - 1]:
        output_matrix[trial, 15] = 1
    else:
        output_matrix[trial, 15] = 0

    if output_matrix[trial, 10] == tocco_atteso_S2[trial - 1]:
        output_matrix[trial, 16] = 1
    else:
        output_matrix[trial, 16] = 0

    if output_matrix[trial, 15] & output_matrix[trial, 16] == 1:
        output_matrix[trial, 17] = 1
    else:
        output_matrix[trial, 17] = 0


def parseOutputs(lines, output_matrix, trial):
    TempoMovimentoSub1 = 0
    TempoMovimentoSub2 = 0

    for line in lines:
        output = line.split(':')

        if len(output) < 2:
            continue

        if ('Grasping time UP1' in line) or ('Grasping time DOWN1' in line):
            TempoMovimentoSub1 = int(output[1])

        if ('Grasping time UP2' in line) or ('Grasping time DOWN2' in line):
            TempoMovimentoSub2 = int(output[1])

    output_matrix[trial, 0] = TempoMovimentoSub1
    output_matrix[trial, 1] = TempoMovimentoSub2
    output_matrix[trial, 2] = np.abs(TempoMovimentoSub1 - TempoMovimentoSub2)


def createBlock(condition, trial_vec, nTrials, tocco_atteso_S1, tocco_atteso_S2, trigger_list):
    UP_UP = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/su-su.wav"
    UP_DOWN = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/su-giu.wav"
    DOWN_DOWN = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/giu-giu.wav"
    DOWN_UP = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/giu-su.wav"
    OPPO_OPPO = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/oppo-oppo.wav"
    SAME_SAME = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/ugua-ugua.wav"
    UP_OPPO = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/su-ugua.wav"
    UP_SAME = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/su-oppo.wav"
    DOWN_OPPO = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/giu-oppo.wav"
    DOWN_SAME = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/giu-ugua.wav"
    OPPO_UP = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/oppo-su.wav"
    OPPO_DOWN = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/oppo-giu.wav"
    SAME_UP = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/ugua-su.wav"
    SAME_DOWN = r"C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/ugua-giu.wav"

    
    if condition == "FREE/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            lista_vec.append(
                (OPPO_OPPO,
                 None,
                 None, 
                 1))
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            

    elif condition == "FREE/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            lista_vec.append(
                (SAME_SAME,
                 None,
                 None, 
                 2))
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            


    elif condition == "LEAD1/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_SAME,
                    1,
                    None, 
                    3))
            else:
                lista_vec.append(
                    (DOWN_SAME,
                    2,
                    None, 
                    4))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            

    elif condition == "LEAD1/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_OPPO,
                    1,
                    None, 
                    5))
            else:
                lista_vec.append(
                    (DOWN_OPPO,
                    2,
                    None, 
                    6))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            

    elif condition == "LEAD2/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (SAME_UP,
                    None,
                    1, 
                    7))
            else:
                lista_vec.append(
                    (SAME_DOWN,
                    None,
                    2, 
                    8))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            

    elif condition == "LEAD2/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (OPPO_UP,
                    None,
                    1, 
                    9))
            else:
                lista_vec.append(
                    (OPPO_DOWN,
                    None,
                    2, 
                    10))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            
    elif condition == "CUED/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_UP,
                    1,
                    1, 
                    11))
            else:
                lista_vec.append(
                    (DOWN_DOWN,
                    2,
                    2, 
                    12))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            

    elif condition == "CUED/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_DOWN,
                    1,
                    2, 
                    13))
            else:
                lista_vec.append(
                    (DOWN_UP,
                    2,
                    1, 
                    14))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            

    return 


# ============================================================
# MAIN
# ============================================================

def StartBlock(participant, block, condition, condition_order, output_path, master):
    global ser
    global Participant, Session, Condition

    Participant = participant
    Session = block
    Condition = condition

    create_status_window(master)

    if condition_order is None:

        nTrials = 60
        trial_vec = np.empty(nTrials, dtype=object)
        tocco_atteso_S1 = np.empty(nTrials, dtype=object)
        tocco_atteso_S2 = np.empty(nTrials, dtype=object)
        trigger_list = np.empty(nTrials, dtype=object)
        

        createBlock(condition, trial_vec, nTrials, tocco_atteso_S1, tocco_atteso_S2,trigger_list)


        safe_condition = condition.replace("/", "_")
        output_file = f"{output_path}/{participant}_{safe_condition}_{block}.csv"

        output_matrix = np.zeros((nTrials + 1, 22), dtype=object)

        output_matrix[0, :] = [
            'Tempo Movimento SUB 1', #1
            'Tempo Movimento SUB 2', #2
            'Asincronia Tempo Movimento', #3
            'Start SUB1', #4
            'Start SUB2', #5
            'Asincronia Start', #6
            'Stop SUB 1', #7
            'Stop SUB 2', #8
            'Asincronia Grasp', #9
            'Tocco Effettivo SUB1', #10
            'Tocco Effettivo SUB2', #11
            'numero di trials', #12
            'Sub-conditions', #13 
            'Tocco Atteso SUB1', #14
            'Tocco Atteso SUB2', #15
            'Accuratezza SUB1', #16
            'Accuratezza SUB2', #17
            'Accuratezza Coppia', #18
            'Participant', #19
            'Session', #20
            'Condition', #21
            'triggers' #22
        ]

        trial = 1

        ser = open_serial(PORT, BAUDRATE)

        start_button_thread()

        trial_thread = threading.Thread(
            target=startTrial,
            args=(
                nTrials,
                trial,
                output_matrix,
                output_file,
                trial_vec,
                tocco_atteso_S1,
                tocco_atteso_S2,
                trigger_list,
                Participant,
                Session,
                Condition
            ),
            daemon=True
        )

        trial_thread.start()

        process_gui_queue()