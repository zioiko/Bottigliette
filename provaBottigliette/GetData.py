import serial
import time
import csv

PORT = 'COM5'
BAUDRATE = 9600
line = ''  # current line read from Arduino
lines = [] # save outputs red by Arduino in this list
output_file = r"C:\Users\frossano\Desktop\Bottigliette\provaBottigliette\output_times.csv"
output = []

with open (output_file, mode='a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Grasp Time SUB 1', 'Grasp Time SUB 2', 'Total Time SUB 1', 'Total Time SUB 2'])

def open_serial(PORT, BAUDRATE):
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(1)  # aspetta reset Arduino
    ser.reset_input_buffer()
    return ser

def parseOutputs(lines):
    GraspSubj1 = []
    GraspSubj2 = [] 
    TotalTimeSubj1 = []
    TotalTimeSubj2 = []

    for line in lines:
        output = line.split(':')
    # Save output times based on participant
        if ('Grasping time UP1' or 'Grasping time DOWN1') in line:
            GraspSubj1 = int(output[1])
        if ('Grasping time UP2' or 'Grasping time DOWN2') in line:
            GraspSubj2 = int(output[1])
        if ('Total time UP1' or 'Total time DOWN1') in line:
            TotalTimeSubj1 = int(output[1])
        if ('Total time UP2' or 'Total time DOWN2') in line:
            TotalTimeSubj2 = int(output[1])
    with open(output_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([GraspSubj1, GraspSubj2, TotalTimeSubj1, TotalTimeSubj2])
    

ser = open_serial(PORT, BAUDRATE)

try:
    while ser.is_open:
        while 'Total time UP1'  not in line: # poi da sostituire con "time difference between grasps:"
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

        parseOutputs(lines)
        lines = []
        line = []
        
except KeyboardInterrupt:
    pass
finally:
    ser.close()