import time
import numpy as np
import serial
import csv
import tkinter as tk
import threading
import queue
import winsound
from pathlib import Path

# ===========================================================
# Parallel Port
# ===========================================================
# ParalPort = parallel.Parallel()
# ParalPort.setData(0)

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


# ============================================================
# GUI
# ============================================================

def create_status_window(master):
    global root
    global left_panel, right_panel
    global left_touch_label, right_touch_label
    global left_label, right_label

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


def process_gui_queue():
    while not gui_queue.empty():
        command = gui_queue.get()

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

        elif command == "BOTH_RED":
            set_left_color("red")
            set_right_color("red")

        elif command == "CLOSE":
            root.destroy()
            return

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

def startTrial(nTrials, trial, output_matrix, output_file, trial_vec_s1, trial_vec_s2):
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
            #SOLO PER PROVA
            t0=time.time() #provare a mettere ParalPort = parallel.Parallel()

            winsound.PlaySound(trial_vec_s1[trial - 1], winsound.SND_FILENAME | winsound.SND_ASYNC)
            winsound.PlaySound(trial_vec_s2[trial - 1], winsound.SND_FILENAME | winsound.SND_ASYNC)
            t1=time.time() #provare a mettere # ParalPort.setData(0)
            print(f"Tempo esecuzione: {t1-t0:.3f} secondi")

            start_time = time.time()

            print('Timer avviato.')

            completeTrial(trial, trial_vec, start_time, output_matrix)

            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(output_matrix)

            print(f'Trial {trial} salvato.')

            trial = trial + 1
            if trial > nTrials - 1:
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


def completeTrial(trial, trial_vec, start_time, output_matrix):
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


def createBlock(condition, trial_vec, nTrials):
    UP = r"C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Up.wav"
    DOWN = r"C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Down.wav"
    OPPO = r"C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Oppo.wav"
    UGUA = r"C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Ugua.wav"
    UP-SAME
    UP-OPPO
    if condition == "FREE/OPPOSITE":
        for i in range(0, nTrials):
            trial_vec[i] = OPPO
        trial_vec_s1 = trial_vec.copy()
        trial_vec_s2 = trial_vec.copy()

    elif condition == "FREE/SAME":
        for i in range(0, nTrials):
            trial_vec[i] = UGUA
        trial_vec_s1 = trial_vec.copy()
        trial_vec_s2 = trial_vec.copy()

    elif condition == "LEAD1/SAME":
        for i in range(0, nTrials):
            if i < nTrials / 2:
                trial_vec[i] = UP
            else:
                trial_vec[i] = DOWN
        np.random.shuffle(trial_vec)
        trial_vec_s1 = trial_vec.copy()
        for i in range(0, nTrials):
            trial_vec[i] = UGUA
        trial_vec_s2 = trial_vec.copy()

    elif condition == "LEAD1/OPPOSITE":
        for i in range(0, nTrials):
            if i < nTrials / 2:
                trial_vec[i] = UP
            else:
                trial_vec[i] = DOWN
        np.random.shuffle(trial_vec)
        trial_vec_s1 = trial_vec.copy()
        for i in range(0, nTrials):
            trial_vec[i] = OPPO
        trial_vec_s2 = trial_vec.copy()

    elif condition == "LEAD2/SAME":
        for i in range(0, nTrials):
            if i < nTrials / 2:
                trial_vec[i] = UP
            else:
                trial_vec[i] = DOWN
        np.random.shuffle(trial_vec)
        trial_vec_s2 = trial_vec.copy()
        for i in range(0, nTrials):
            trial_vec[i] = UGUA
        trial_vec_s1 = trial_vec.copy()

    elif condition == "LEAD2/OPPOSITE":
        for i in range(0, nTrials):
            if i < nTrials / 2:
                trial_vec[i] = UP
            else:
                trial_vec[i] = DOWN
        np.random.shuffle(trial_vec)
        trial_vec_s2 = trial_vec.copy()
        for i in range(0, nTrials):
            trial_vec[i] = OPPO
        trial_vec_s1 = trial_vec.copy()

    elif condition == "CUED/SAME":
        for i in range(0, nTrials):
            trial_vec[i] = UGUA
        trial_vec_s1 = trial_vec.copy()
        trial_vec_s2 = trial_vec.copy()

    elif condition == "CUED/OPPOSITE":
        for i in range(0, nTrials):
            trial_vec[i] = OPPO
        trial_vec_s1 = trial_vec.copy()
        trial_vec_s2 = trial_vec.copy()

    return trial_vec_s1, trial_vec_s2


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

        trial_vec_s1, trial_vec_s2 = createBlock(condition, trial_vec, nTrials)

        output_file = f"{output_path}\\{participant}\\{condition}_{block}.csv"

        output_matrix = np.zeros((nTrials + 1, 11), dtype=object)

        output_matrix[0, :] = [
            'Tempo Movimento SUB 1',
            'Tempo Movimento SUB 2',
            'Asincronia Tempo Movimento',
            'Start SUB1',
            'Start SUB2',
            'Asincronia Start',
            'Stop SUB 1',
            'Stop SUB 2',
            'Asincronia Grasp',
            'Tocco Effettivo SUB1',
            'Tocco Effettivo SUB2'
        ]

        trial = 1

        ser = open_serial(PORT, BAUDRATE)

        start_button_thread()

        trial_thread = threading.Thread(
            target=startTrial,
            args=(nTrials, trial, output_matrix, output_file, trial_vec_s1, trial_vec_s2),
            daemon=True
        )

        trial_thread.start()

        process_gui_queue()