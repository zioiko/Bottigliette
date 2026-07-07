import time
import numpy as np
import serial
import csv
import tkinter as tk
import threading
import queue
import winsound #proviamo questa libreria (nativa windows) per rirpodurre audio
#import simpleaudio as sa
#from goprocam import GoProCamera
#import parallel

# ===========================================================
# Parallel Port
# ===========================================================
#ParalPort = parallel.Parallel() #se non funziona aggiungere l'address; esempio: address=0x378
#ParalPort.setData(0)


# ===========================================================
# Creo Webcam
# ===========================================================

#go_pro = GoProCamera.GoPro() # Da vedere bene

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

#aggiungi audio condizione specifica (2 x 2)
# Cued1 = sa.WaveObject.from_wave_file("C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Up.wav")
# Cued2 = sa.WaveObject.from_wave_file("C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Down.wav")
# Cued3 = sa.WaveObject.from_wave_file("C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Oppo.wav")
# Cued4 = sa.WaveObject.from_wave_file("C:/Users/feder/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Ugua.wav")
Cued1 = ("C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Up.wav")
Cued2 = ("C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Down.wav")
Cued3 = ("C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Oppo.wav")
Cued4 = ("C:/Users/piero/Documents/GitHub/Bottigliette/provaBottigliette/Stimoli/Ugua.wav")
# ============================================================
# GUI
# ============================================================

root = tk.Tk()
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
# Inviare trigger tramite porta parallela
# ============================================================
#def send_trigger(value):
    #ParalPort.setData(int(value))
    #time.sleep(0.005)   # 5 ms pulse #**ATTENZIONE**: Così fermi per 5 ms tutto lo script, anche il tempo che vai a registrare con starttime.time()
                            #piuttosto ci conviene mandare il trigger con ParalPort.setData(value) e poi, qualche riga dopo (così che l'ECG "veda" il trigger)
                            # ParalPort.setData(0) senza sleep, così non blocchiamo tutto il programma.
    #ParalPort.setData(0)

# ============================================================
# SERIALE
# ============================================================

def open_serial(PORT, BAUDRATE):
    ser = serial.Serial(PORT, BAUDRATE, timeout=0.05)
    time.sleep(1)
    ser.reset_input_buffer()
    return ser

# ============================================================
# Webcam
# ============================================================

#def start_recording():
    try:
        go_pro.shoot_video(0)  # 0 = start recording
        print("Recording started")
    except Exception as e:
        print(f"Error starting recording: {e}")


#def stop_recording():
    try:
        go_pro.shoot_video(1)  # 1 = stop recording
        print("Recording stopped")
    except Exception as e:
        print(f"Error stopping recording: {e}")

# to rename the video recorded
#def save_last_video(trial_number):
    try:
        media_list = go_pro.getMedia()  # get media list
        last_video = media_list[-1]     # last recorded file

        new_name = f"trial_{trial_number}.mp4"

        go_pro.downloadLastMedia(custom_filename=new_name)
        print(f"Saved video as {new_name}")

    except Exception as e:
        print(f"Error saving video: {e}")


# ============================================================
# GUI INPUT DATI ESPERIMENTO
# ============================================================

def get_experiment_info(root):
    input_window = tk.Toplevel(root)  # ✅ invece di Tk()
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

    root.wait_window(input_window)  # 🔥 BLOCCA finché non chiudi

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

def startTrial(trial, output_matrix,trial_vec):
    while True:
        user_input = input("Premi 'a' per avviare il trial, 'r' per resettare, 'q' per uscire: ")

        if user_input == 'q':
            print('Uscita.')
            #stop_recording()
            stop_button_thread_func()
            gui_queue.put("CLOSE")
            break

        elif user_input == 'a':
            stop_button_thread_func()
            #start_recording() #questo permetterà di cominciare la registrazione dopo la pressione del tasto "a"
            

            ser.reset_input_buffer()

            gui_queue.put("CLEAR_TOUCH_TEXTS")

            trigger_value = trigger_EEG_vec[trial - 1]
            #send_trigger(trigger_value)   # invece di mandare trigger con la sua funzione con time.sleep farei:  
            # ParalPort.setData(trigger_value)  # manda trigger   
            if trial_vec[trial-1] == 1:       #IF PER AUDIO DIVERSI IN BASE AL VETTORE RANDOMICIZZATO TRIAL_VEC
                winsound.PlaySound(Cued1, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif trial_vec[trial-1] == 2:
                winsound.PlaySound(Cued2, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif trial_vec[trial-1] == 3:
                winsound.PlaySound(Cued3, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif trial_vec[trial-1] == 4:  
                winsound.PlaySound(Cued4, winsound.SND_FILENAME | winsound.SND_ASYNC)

            start_time = time.time()
            #ParalPort.setData(0)  # reset trigger subito dopo senza sleep, così non blocchiamo tutto il programma.
                                    #il pc dovrebbe leggere una linea in 1 o 0.5 ms. Possiamo fare diverse prove ma raccomanderei questa modalità per mandare trigger
                                    #senza mai inserire time.sleep().
            print('Timer avviato.')

            completeTrial(trial, start_time, output_matrix)

            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(output_matrix)

            print(f'Trial {trial} salvato.')

            trial = trial + 1

            start_button_thread()

        elif user_input == 'r': #discutiamo se tenere questa opzione, perché nelle fisiologiche non puoi sottrare il trial quindi si potrebbe creare un mismatch
                                #qui è facile. in post-processing cerchi quante volte compare uno stesso trigger (dato che sono numerati in base al trial specifico (trial_vec))
                                # e poi ti prendi solo l'ultimo trial sulle fisiologiche. 
            #stop_recording()
            trial = resetTrial(output_matrix, trial)

            gui_queue.put("CLEAR_TOUCH_TEXTS")

            print('Trial resettato.')


def resetTrial(output_matrix, trial):
    output_matrix[trial, 0:11] = 0

    trial = trial - 1

    if trial < 1:
        trial = 1

    return trial


def completeTrial(trial, start_time, output_matrix):
    # ===============================
    # INFO TRIAL
    # ===============================
    output_matrix[trial, 11] = trial #forse da reimpostare
    output_matrix[trial, 12] = trial_vec[trial-1]
    output_matrix[trial, 13] = tocco_atteso_S1[trial-1]
    output_matrix[trial, 14] = tocco_atteso_S2[trial-1]
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

    #stop_recording() #interrompe la registrazione
    #time.sleep(1) #serve veramente #Perchè???
    #save_last_video(trial) #salva il video


    output_matrix[trial, 5] = np.abs(output_matrix[trial, 3] - output_matrix[trial, 4])
    output_matrix[trial, 8] = np.abs(output_matrix[trial, 6] - output_matrix[trial, 7])

    if output_matrix[trial, 9] == tocco_atteso_S1[trial-1]:
        output_matrix[trial, 15] = 1
    else:
        output_matrix[trial, 15] = 0

    if output_matrix[trial, 10] == tocco_atteso_S2[trial-1]:
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




# ============================================================
# MAIN
# ============================================================
# Creare un vettore trial per i 4 livelli di Cued (Giu{2}-Su{1}, Su{1}-Giu{2}, Giu{2}-Giu{2}, Su{1}-Su{1})
#per ogni livello, dovremmo creare dei vettori di tocco atteso codificati come 1 & 2 per calcolare accuratezza soggetto singolo e accurateza di coppia

block = 1
trials = 4
trial_vec = np.zeros(trials,dtype=int)
trigger_EEG_vec = np.zeros(trials,dtype=int)
conditions=[1,2,3,4] #conditions: Cued1[Giu{2}-Su{1}], Cued2[Su{1}-Giu{2}], Cued3[Giu{2}-Giu{2}], Cued4[Su{1}-Su{1}]
tocco_atteso_S1 = np.zeros(trials,dtype=int)
tocco_atteso_S2 = np.zeros(trials,dtype=int)

for i in range(0,trials): #DA RICONTROLLARE BENE PERCHE POTREBBERO VARIARE UN Pò
    if i < trials/4:
        trial_vec[i]=conditions[0]
    elif i < 2*trials/4 and i >= trials/4:
        trial_vec[i]=conditions[1]
    elif i < 3*trials/4 and i >= 2*trials/4:
        trial_vec[i]=conditions[2]
    elif i < trials and i >= 3*trials/4:
        trial_vec[i]=conditions[3]

# randomicizzazione trial_vec
np.random.shuffle(trial_vec)

#creazione dei vettori tocco atteso per 
for i in range(0, trials):
    if trial_vec[i] == 1:
        tocco_atteso_S1[i] = 2 
        tocco_atteso_S2[i] = 1
    elif trial_vec[i] == 2:
        tocco_atteso_S1[i] = 1 
        tocco_atteso_S2[i] = 2
    elif trial_vec[i] == 3:
        tocco_atteso_S1[i] = 2 
        tocco_atteso_S2[i] = 2
    elif trial_vec[i] == 4:
        tocco_atteso_S1[i] = 1 
        tocco_atteso_S2[i] = 1

#creazione del vettore trigger EEG
for i in range(0, trials):
    if trial_vec[i] == 1:
        trigger_EEG_vec[i] = 11 #numeri al momento casuali, dispari perché l'ampli li preferisce #Fede: COOOSA?!
    elif trial_vec[i] == 2:
        trigger_EEG_vec[i] = 13
    elif trial_vec[i] == 3:
        trigger_EEG_vec[i] = 15
    elif trial_vec[i] == 4:
        trigger_EEG_vec[i] = 17


#otteniamo info sperimentali da salvare nella matrice finale
exp_info = get_experiment_info(root)

Participant = exp_info["participant"]
Session = exp_info["session"]
Condition = exp_info["condition"]

output_file = f"C:/Users/piero/Desktop/{Participant}_{Session}_{Condition}.csv"

output_matrix = np.zeros((trials+1, 21), dtype=object) #14 colonne

output_matrix[0, :] = [
    'Tempo Movimento SUB 1',
    'Tempo Movimento SUB 2',
    'Asincronia Tempo Movimento',
    'Start SUB1',
    'Start SUB2',
    'Asincronia Start',
    'Stop SUB 1',
    'Stop SUB 2',
    'Asincronia Stop',
    'Tocco Effettivo SUB1',
    'Tocco Effettivo SUB2',
    'numero di trials',
    'sotto-condizione', 
    'Tocco Atteso SUB1',  
    'Tocco Atteso SUB2',  
    'Accuratezza SUB1',
    'Accuratezza SUB2',
    'Accuratezza Coppia',
    'Participant',
    'Session',
    'Condition'
] #Aggiungere il save dei trigger EEG

#porte parallele


trial = 1

ser = open_serial(PORT, BAUDRATE)

start_button_thread()

trial_thread = threading.Thread(
    target=startTrial,
    args=(trial, output_matrix, trial_vec),
    daemon=True
)

trial_thread.start()

process_gui_queue()

root.mainloop()