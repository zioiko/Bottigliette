#This script interfaces with an Arduino device to extract key behavioral measures from bottle sensors and their corresponding table buttons during a dyadic task.
#The script generates an output matrix (output_matrix), which is saved as a .csv file and contains the following variables:

#output_matrix[0, :] = [
        #'Tempo Movimento SUB1': extracted from Arduino; time elapsed from button release to bottle grasp for Subject 1.
        #'Tempo Movimento SUB2': extracted from Arduino; time elapsed from button release to bottle grasp for Subject 2.
        #'Asincronia Tempo Movimento': computed in this script as the difference between the two movement times.
        #'Start SUB1': computed in Python; time elapsed between sound onset and button release for Subject 1.
        #'Start SUB2': computed in Python; time elapsed between sound onset and button release for Subject 2.
        #'Asincronia Start': computed in this script as the difference between the two start times.
        #'Stop SUB1': computed in Python; time elapsed between sound onset and bottle grasp for Subject 1 (shared temporal reference).
        #'Stop SUB2': computed in Python; time elapsed between sound onset and bottle grasp for Subject 2 (shared temporal reference).
        #'Asincronia Grasp': computed in this script as the difference between the two stop times (common zero reference).
        #'Tocco Effettivo SUB1': extracted from Arduino; categorical value (1 = upper sensor, 2 = lower sensor).
        #'Tocco Effettivo SUB2': extracted from Arduino; categorical value (1 = upper sensor, 2 = lower sensor).
        #'numero di trials': total number of trials per block; defined by the variable ntrials, which can be adjusted at the end of the script.
        #'Sub-conditions': defined by the vector trial_vec, specifying whether a trial belongs to a specific sub-condition within a condition (e.g., in cued/opposite conditions: SUB1-down & SUB2-up vs. SUB1-up & SUB2-down).
        #'Tocco Atteso SUB1': vector of expected responses (values 1 or 2), generated in Python based on the experimental condition and trial list.
        #'Tocco Atteso SUB2': vector of expected responses (values 1 or 2), generated in Python based on the experimental condition and trial list.
        #'Accuratezza SUB1': computed by comparing expected and actual touch (1 = correct, 0 = incorrect).
        #'Accuratezza SUB2': computed by comparing expected and actual touch (1 = correct, 0 = incorrect).
        #'Accuratezza Coppia': equals 1 if both subjects are correct; equals 0 if both are incorrect or if only one is correct.
        #'Participant': participant identifier selected at the beginning of the experiment (see startExperiment.py).
        #'Session': session number.
        #'Condition': experimental condition corresponding to each trial.
        #'Triggers': event markers sent to electrophysiological recording devices to highlight the trial beginning. These are generated within the createBlock function according to the selected condition and are also saved in the .csv file for verification purposes.
        #'Trial Start (clock time)':
        #'Trial Stop (clock time)':
        #'trigger_offset': event markers sent to electrophysiological recording devices to highlight the trial offset. These are generated within the createBlock function according to the selected condition and are also saved in the .csv file for verification purposes.
#Notes:
#Auditory stimuli are generated in stereo (left/right channels), with separate channels assigned to each member of the dyad.
#Python uses multithreading to simultaneously: (i) read dependent variables from the Arduino, and 
#                                              (ii) continuously monitor the state of buttons and bottle sensors to provide real-time feedback in the graphical user interface (GUI).



#import the needed library 
import time
import numpy as np
import serial
import csv
import tkinter as tk
import threading
import queue
import winsound
from pathlib import Path
from datetime import datetime
import trgenpy as tp
from gopro_webcam_recorder import GoProRecorder
from time import sleep


# ===========================================================
# Parallel Port through NEW trigger box
# ============================================================
client = tp.TrgenClient()
client.connect()
isAavailable = client.is_available()
# ============================================================


# ===========================================================
# GoPro
# ===========================================================
VIDEO_ROOT = Path(r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/video_save") #where to save the videos
GOPRO_DEVICE_INDEX = 0        # verifica con: python gopro_webcam_recorder.py --list

rec = None                    # creato in StartBlock, quando il participant è noto

# ============================================================
# PARAMETRI
# ============================================================

BAUDRATE = 9600

# ============================================================
# CONVENZIONE INDICI TRIAL
# ------------------------------------------------------------
# - `trial` è 1-based: va da 1 a nTrials.
# - Gli array per-trial (trial_vec, tocco_atteso_S1/S2, trigger_list,
#   trigger_offset) hanno lunghezza nTrials e sono 0-based:
#   si indicizzano SEMPRE con [trial - 1].
# - output_matrix ha nTrials + 1 righe: la riga 0 è l'header,
#   quindi la riga del trial `trial` è output_matrix[trial, :].
# ============================================================

# ============================================================
# VARIABILI GLOBALI per i Feedback nella finestra a comparsa durante il task
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
# GUI per i feedback
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

# ---------------------------------
# PANNELLO ASINCRONIA
# ---------------------------------

    global asincronia_label
    asincronia_label = tk.Label(
        root,
        text="Asincronia Grasp: ---",
        font=("Arial", 20, "bold"),
        bg="white",
        fg="black"
    )
    asincronia_label.pack(side="bottom", pady=10)

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
        
        elif isinstance(command, tuple) and command[0] == "UPDATE_ASINCRONIA":
            asincronia_label.config(text=f"Asincronia Grasp: {command[1]} ms")

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

def build_video_name(condition, trial):
    """LEAD1/SAME + trial 3  ->  'LEAD1_SAME_3' (lo slash non è legale su Windows)."""
    safe_condition = condition.replace("/", "_")
    return f"{safe_condition}_{trial}"


def unique_video_name(out_dir, name, ext=".mp4"):
    """Non sovrascrive mai un video già registrato: aggiunge _run2, _run3, ..."""
    out_dir = Path(out_dir)
    candidate = name
    n = 2
    while (out_dir / f"{candidate}{ext}").exists():
        candidate = f"{name}_run{n}"
        n += 1
    if candidate != name:
        print(f"ATTENZIONE: {name}{ext} esiste già -> salvo come {candidate}{ext}")
    return candidate


def save_output(output_file, output_matrix):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output_matrix)


def startTrial(nTrials, trial, output_matrix, output_file, 
               trial_vec, tocco_atteso_S1, tocco_atteso_S2, trigger_list, Participant, Session, Condition, trigger_offset):
    
    client.setDefaultDuration(1000) #durata del trigger/marker dalla triggerBox a gTec (ATTENZIONE: dopo alcune prove è stato consolidato questo valore di 1000 nanosecondi = 1 ms, affinché gtec lo veda. NeuroScan ne richiede anche meno)


    rec.open() #inizializzare la GoPro

    try:
        while True:
            idx = trial - 1   # indice 0-based negli array per-trial (trial è 1-based)

            client.sendMarker(markerNS= trigger_list[idx], LSB= True, autoStart=False) #trigger di inzio trial caricato ma ancora NON inviato

            user_input = input(f"[Trial {trial}/{nTrials}] Premi 'a' per avviare il trial, 'q' per uscire: ")

            if user_input == 'q':
                print('Uscita.')
                stop_button_thread_func()
                gui_queue.put("CLOSE")
                break

            elif user_input == 'a':
                stop_button_thread_func()

                ser.reset_input_buffer()

                gui_queue.put("CLEAR_TOUCH_TEXTS")


                # ---- avvio registrazione video ----
                video_name = unique_video_name(rec.out_dir,
                                                build_video_name(Condition, trial))
                rec.start_recording(video_name)

                trial_time_start = time.perf_counter()

                ser.write(b"start")

                winsound.PlaySound(trial_vec[idx], winsound.SND_FILENAME | winsound.SND_ASYNC) #invio dei comandi tramite cuffie ai partecipanti

                start_time = time.perf_counter() #tiene il tempo di ogni inizio trial (trasformo in millisencods)
                
                #time.sleep(1.2)
                client.start() #invio del trigger 

                client.sendMarker(markerNS= trigger_offset[idx], LSB= True, autoStart=False) #trigger di fine trial caricato ma ancora NON inviato
                

                
                
                print('Timer avviato.')

                completeTrial( trial,
                        trial_vec,
                        start_time,
                        output_matrix,
                        tocco_atteso_S1,
                        tocco_atteso_S2,
                        trigger_list, Participant, Session, Condition)

                trial_time_stop = time.perf_counter() #tiene il tempo di ogni fine trial

                # ---- salvataggio orario di inizio/fine trial (clock time, per confronto col video) ----
                output_matrix[trial, 22] = datetime.fromtimestamp(trial_time_start).strftime('%H:%M:%S.%f')[:-3]
                output_matrix[trial, 23] = datetime.fromtimestamp(trial_time_stop).strftime('%H:%M:%S.%f')[:-3]

                time.sleep(0.3) #questo time serve per non far droppare gli ultimi frame del video (da verificare?)

                video_path = rec.stop_recording()
                print(f"Video salvato: {video_path}")


                save_output(output_file, output_matrix)

                print(f'Trial {trial}/{nTrials} salvato.')

                trial = trial + 1
                if trial > nTrials:
                    print('Blocco completato')
                    gui_queue.put("CLOSE")
                    break

                start_button_thread()

            elif user_input == 'r':
                trial = resetTrial(output_matrix, trial)

                save_output(output_file, output_matrix)

                gui_queue.put("CLEAR_TOUCH_TEXTS")

                print(f'Trial resettato: si ripete il trial {trial}.')
    finally:
        rec.close()

def resetTrial(output_matrix, trial):
    """
    Cancella l'ultimo trial COMPLETATO (riga trial - 1) e torna indietro di uno,
    così quel trial viene ripetuto. Se non è ancora stato completato nessun trial,
    non fa nulla.
    """
    if trial <= 1:
        print('Nessun trial completato da resettare.')
        return 1

    trial = trial - 1
    output_matrix[trial, :] = 0   # tutte le 24 colonne, non solo le prime 20

    return trial


def completeTrial(trial,
    trial_vec,
    start_time,
    output_matrix,
    tocco_atteso_S1,
    tocco_atteso_S2,
    trigger_list, Participant, Session, Condition):
    # ===============================
    # INFO TRIAL
    # ===============================
    idx = trial - 1   # indice 0-based negli array per-trial

    output_matrix[trial, 11] = trial
    output_matrix[trial, 12] = Path(trial_vec[idx]).stem
    output_matrix[trial, 13] = tocco_atteso_S1[idx]
    output_matrix[trial, 14] = tocco_atteso_S2[idx]
    output_matrix[trial, 18] = Participant
    output_matrix[trial, 19] = Session
    output_matrix[trial, 20] = Condition
    output_matrix[trial, 21] = trigger_list[idx]
    #output_matrix[trial, 24] = trigger_offset[idx]

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
            ButtonTimeReleased1 = time.perf_counter()
            output_matrix[trial, 3] = float((ButtonTimeReleased1 - start_time) * 1000)

        if 'Button 2 pressed' in line:
            gui_queue.put("SUB2_GREEN")

        if 'Button 2 released' in line:
            gui_queue.put("SUB2_RED")
            ButtonTimeReleased2 = time.perf_counter()
            output_matrix[trial, 4] = float((ButtonTimeReleased2 - start_time) * 1000)

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
            StopSub1 = time.perf_counter()
            output_matrix[trial, 6] = float((StopSub1 - start_time))

        if 'SUB2 Grasped' in line:
            StopSub2 = time.perf_counter()
            output_matrix[trial, 7] = float((StopSub2 - start_time))


    client.start() #invio trigger offset

    parseOutputs(lines, output_matrix, trial)

    output_matrix[trial, 5] = np.abs(output_matrix[trial, 3] - output_matrix[trial, 4])
    output_matrix[trial, 8] = np.abs(output_matrix[trial, 6] - output_matrix[trial, 7])

    gui_queue.put(("UPDATE_ASINCRONIA", output_matrix[trial, 8]))

    if output_matrix[trial, 9] == tocco_atteso_S1[idx]:
        output_matrix[trial, 15] = 1
    else:
        output_matrix[trial, 15] = 0

    if output_matrix[trial, 10] == tocco_atteso_S2[idx]:
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
    # StopSub1 = 0
    # StopSub2 = 0

    for line in lines:
        output = line.split(':')

        # if 'SUB1 Grasped' in line:
        #     StopSub1 = float(output[1])

        # if 'SUB2 Grasped' in line:
        #     StopSub2 = float(output[1])

        if len(output) < 2:
            continue

        if ('Grasping time UP1' in line) or ('Grasping time DOWN1' in line):
            TempoMovimentoSub1 = int(output[1])

        if ('Grasping time UP2' in line) or ('Grasping time DOWN2' in line):
            TempoMovimentoSub2 = int(output[1])

    output_matrix[trial, 0] = TempoMovimentoSub1
    output_matrix[trial, 1] = TempoMovimentoSub2
    output_matrix[trial, 2] = np.abs(TempoMovimentoSub1 - TempoMovimentoSub2)
    # output_matrix[trial, 6] = StopSub1
    # output_matrix[trial, 7] = StopSub2
    # output_matrix[trial, 8] = np.abs(StopSub1 - StopSub2)


def createBlock(condition, trial_vec, nTrials, tocco_atteso_S1, tocco_atteso_S2, trigger_list, trigger_offset):
    UP_UP = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/su-su.wav"
    UP_DOWN = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/su-giu.wav"
    DOWN_DOWN = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/giu-giu.wav"
    DOWN_UP = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/giu-su.wav"
    OPPO_OPPO = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/oppo-oppo.wav"
    SAME_SAME = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/ugua-ugua.wav"
    UP_OPPO = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/su-oppo.wav"   #Lead1 - Bott1
    UP_SAME = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/su-uga.wav"   #Lead1 - Bott1
    DOWN_OPPO = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/giu-oppo.wav"  #Lead1 - Bott1
    DOWN_SAME = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/giu-ugua.wav"  #Lead1 - Bott1
    OPPO_UP = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/oppo-su.wav"  #Lead2 - Bott2
    OPPO_DOWN = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/oppo-giu.wav"  #Lead2 - Bott2
    SAME_UP = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/ugua-su.wav"  #Lead2 - Bott2
    SAME_DOWN = r"C:/Users/User/Documents/GitHub/Bottigliette/DUAL_task/FINAL_Experiment/Stimoli_Audio/ugua-giu.wav"  #Lead2 - Bott2

    
    if condition == "FREE/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            lista_vec.append(
                (OPPO_OPPO,
                 None,
                 None, 
                 1,
                 11))
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            

    elif condition == "FREE/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            lista_vec.append(
                (SAME_SAME,
                 None,
                 None, 
                 2,
                 12))
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            


    elif condition == "LEAD1/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_SAME,
                    1,
                    1, 
                    4,
                    14))
            else:
                lista_vec.append(
                    (DOWN_SAME,
                    2,
                    2, 
                    4,
                    14))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            

    elif condition == "LEAD1/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_OPPO,
                    1,
                    2, 
                    3,
                    13))
            else:
                lista_vec.append(
                    (DOWN_OPPO,
                    2,
                    1, 
                    3,
                    13))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            

    elif condition == "LEAD2/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (SAME_UP,
                    1,
                    1, 
                    7,
                    17))
            else:
                lista_vec.append(
                    (SAME_DOWN,
                    2,
                    2, 
                    7,
                    17))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            

    elif condition == "LEAD2/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (OPPO_UP,
                    2,
                    1, 
                    8,
                    18))
            else:
                lista_vec.append(
                    (OPPO_DOWN,
                    1,
                    2, 
                    8,
                    18))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            
    elif condition == "CUED/SAME":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_UP,
                    1,
                    1, 
                    6,
                    16))
            else:
                lista_vec.append(
                    (DOWN_DOWN,
                    2,
                    2, 
                    6,
                    16))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            

    elif condition == "CUED/OPPOSITE":
        lista_vec = []
        for i in range(0, nTrials):
            if i < nTrials / 2:
                lista_vec.append(
                    (UP_DOWN,
                    1,
                    2, 
                    5,
                    15))
            else:
                lista_vec.append(
                    (DOWN_UP,
                    2,
                    1, 
                    5,
                    15))
        np.random.shuffle(lista_vec)
        for i, trial in enumerate(lista_vec):
            trial_vec[i] = trial[0]
            tocco_atteso_S1[i] = trial[1]
            tocco_atteso_S2[i] = trial[2]
            trigger_list[i] = trial[3]
            trigger_offset[i] = trial[4]
            
    
    return 


# ============================================================
# MAIN
# ============================================================

def StartBlock(participant, block, condition, condition_order, output_path, master,com_port):
    global ser
    global Participant, Session, Condition
    global rec


    Participant = participant
    Session = block
    Condition = condition


    participant_dir = VIDEO_ROOT / str(participant)
    participant_dir.mkdir(parents=True, exist_ok=True)

    rec = GoProRecorder(
        device_index=GOPRO_DEVICE_INDEX,
        out_dir=participant_dir,
        width=1280,
        height=720,
        fps=30,
    )
    print(f"Video di questo participant in: {participant_dir}")
    
    create_status_window(master)

    if condition_order is None:

        nTrials = 4 #cambia in base al numero di trials desiderato

        if nTrials % 2 != 0 and not condition.startswith("FREE"):
            print(f"ATTENZIONE: nTrials = {nTrials} è dispari -> le sotto-condizioni "
                  f"SU/GIU non saranno bilanciate ({nTrials // 2 + 1} vs {nTrials // 2}).")

        trial_vec = np.empty(nTrials, dtype=object)
        tocco_atteso_S1 = np.empty(nTrials, dtype=object)
        tocco_atteso_S2 = np.empty(nTrials, dtype=object)
        trigger_list = np.empty(nTrials, dtype=object)
        trigger_offset = np.empty(nTrials, dtype=object)

        createBlock(condition, trial_vec, nTrials, tocco_atteso_S1, tocco_atteso_S2,trigger_list, trigger_offset)


        safe_condition = condition.replace("/", "_") #permette non leggere la condizione come percorso a causa dello slash 
        output_file = f"{output_path}/{participant}_{safe_condition}_{block}.csv"

        # riga 0 = header, righe 1..nTrials = un trial ciascuna
        output_matrix = np.zeros((nTrials + 1, 24), dtype=object)

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
            'triggers', #22
            'Trial Start (clock time)', #23
            'Trial Stop (clock time)' #24
            
        ]

        trial = 1

        ser = open_serial(com_port, BAUDRATE)

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
                trigger_list, Participant, Session, Condition, trigger_offset
            ),
            daemon=True
        )

        trial_thread.start()

        process_gui_queue()
