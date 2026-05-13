# Start trial
import time

while True:
    user_input = input("Premi 'a' per avviare la prova, 'q' per uscire: ")
    if user_input == 'q':
        print('Uscita.')
        break
    elif user_input == 'a':
        start_time = time.time()
        print('Timer avviato.')
        