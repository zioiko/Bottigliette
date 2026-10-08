import serial
import time
import csv
import numpy as np
import tkinter as tk

PORT = 'COM3'
BAUDRATE = 9600
line = ''  # current line read from Arduino
lines = [] # save outputs red by Arduino in this list
output_file = r"C:\\Users\\feder\\Documents\\GitHub\\Bottigliette\\provaBottigliette\\output_arduino_temp.csv"
output_matrix = np.zeros((200, 9),dtype=object)
output_matrix[0,:] = ['GraspSubj1', 'GraspSubj2','DeltaTempoMov','Button_time_released_1','Button_time_released_2']
i=1 #counter for rows in output array
# Pannello per visualizzare i pulsanti premuti


def open_serial(PORT, BAUDRATE):
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(1)  # aspetta reset Arduino
    ser.reset_input_buffer()
    return ser

def parseOutputs(lines,output_matrix,i):
    GraspSubj1 = []
    GraspSubj2 = [] 
    TotalTimeSubj1 = []
    TotalTimeSubj2 = []

    for line in lines:
        output = line.split(':')
    # Save output times based on participant
        if (('Grasping time UP1' in line) or ('Grasping time DOWN1' in line)):
            GraspSubj1 = int(output[1])
        if (('Grasping time UP2' in line) or ('Grasping time DOWN2' in line)):
            GraspSubj2 = int(output[1])
        #if (('Total time UP1' in line) or ('Total time DOWN1' in line)):
            TotalTimeSubj1 = int(output[1])
        #if (('Total time UP2' in line) or ('Total time DOWN2' in line)):
            TotalTimeSubj2 = int(output[1])
        output_matrix[i,0] = GraspSubj1 #rilascio pulsante fino a tocco
        output_matrix[i,1] = GraspSubj2
       # output_matrix[i,2] = TotalTimeSubj1 #rilascio pulsante a ritorno pulsante
       # output_matrix[i,3] = TotalTimeSubj2
        output_matrix[i,2] = np.abs(GraspSubj1-GraspSubj2)

ser = open_serial(PORT, BAUDRATE)

try:
    while ser.is_open:
        while 'time difference between grasps:'  not in line: # poi da sostituire con "time difference between grasps:"
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
                Button_time_released_1 = time.time()
                output_matrix[i,3] = Button_time_released_1
            if 'Button 2 released' in line:
                Button_time_released_2 = time.time()
                output_matrix[i,4] = Button_time_released_2
                
        parseOutputs(lines,output_matrix,i)
        i+=1
        lines = []
        line = []
       
        
except KeyboardInterrupt:
    pass
finally:
    ser.close()