# Start trial
import time
import numpy as np
import serial
import csv

def startTrial(trial,output_matrix):
    while True:
        user_input = input("Premi 'a' per avviare la prova, 'q' per uscire: ")
        if user_input == 'q':
            print('Uscita.')

            break
        elif user_input == 'a':
            start_time = time.time()
            print('Timer avviato.')
            completeTrial(trial,start_time,output_matrix)
          
            


def completeTrial(trial,start_time,output_matrix):
    line = ''  # current line read from Arduino
    lines = [] # save outputs red by Arduino in this list
    while 'time difference between grasps'  not in line: # poi da sostituire con "time difference between grasps:"
        raw = ser.readline()              
        if not raw:
            continue
    
        line = raw.decode('utf-8', errors='ignore').rstrip()
        try:
            if lines[-1]!=line:  # avoid duplicates
                lines.append(line)  # aspetta una nuova linea
                print(line)                       # stampa sulla debug console
        except: 
            if lines==[]:  # avoid duplicates
                lines.append(line)  # aspetta una nuova linea
                print(line)                       # stampa sulla debug console


        if 'Button 1 released' in line:
            ButtonTimeReleased1 = time.time()
            output_matrix[trial,3] = int((ButtonTimeReleased1-start_time)*1000)
        if 'Button 2 released' in line:
            ButtonTimeReleased2 = time.time()
            output_matrix[trial,4] = int((ButtonTimeReleased2-start_time)*1000)
        if 'SUB1 Grasped' in line:
            StopSub1 = time.time()
            output_matrix[trial,6] = int((StopSub1-start_time)*1000)
        if 'SUB2 Grasped' in line:
            StopSub2 = time.time()
            output_matrix[trial,7] = int((StopSub2-start_time)*1000)
            
    parseOutputs(lines,output_matrix,trial)
    output_matrix[trial,5] = np.abs(output_matrix[trial,3]-output_matrix[trial,4])
    output_matrix[trial,8] = np.abs(output_matrix[trial,6]-output_matrix[trial,7])
    line = []

def open_serial(PORT, BAUDRATE):
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(1)  # aspetta reset Arduino
    ser.reset_input_buffer()
    return ser

def parseOutputs(lines,output_matrix,trial):
    TempoMovimentoSub1 = []
    TempoMovimentoSub2 = [] 
    TotalTimeSubj1 = []
    TotalTimeSubj2 = []

    for line in lines:
        output = line.split(':')
    # Save output times based on participant
        if (('Grasping time UP1' in line) or ('Grasping time DOWN1' in line)):
            TempoMovimentoSub1 = int(output[1])
        if (('Grasping time UP2' in line) or ('Grasping time DOWN2' in line)):
            TempoMovimentoSub2 = int(output[1])
        #if (('Total time UP1' in line) or ('Total time DOWN1' in line)):
            #TotalTimeSubj1 = int(output[1])
        #if (('Total time UP2' in line) or ('Total time DOWN2' in line)):
           # TotalTimeSubj2 = int(output[1])
    output_matrix[trial,0] = TempoMovimentoSub1 #rilascio pulsante fino a tocco
    output_matrix[trial,1] = TempoMovimentoSub2
    # output_matrix[trial,2] = TotalTimeSubj1 #rilascio pulsante a ritorno pulsante
    # output_matrix[trial,3] = TotalTimeSubj2
    output_matrix[trial,2] = np.abs(TempoMovimentoSub1-TempoMovimentoSub2)

PORT = 'COM3'
BAUDRATE = 9600
ser = open_serial(PORT, BAUDRATE)
output_file = r"C:\\Users\\feder\\Documents\\GitHub\\Bottigliette\\provaBottigliette\\output_python_temp.csv"
output_matrix = np.zeros((200, 9),dtype=object)
output_matrix[0,:] = ['Tempo Movimento SUB 1', 'Tempo Movimento SUB 2','Asincronia Tempo Movimento','Start SUB1','Start SUB 2',',Asincronia Start','Stop SUB 1', 'Stop SUB 2','Asincronia Grasp']
trial=1
startTrial(trial,output_matrix)
#save output_matrix
with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(output_matrix)