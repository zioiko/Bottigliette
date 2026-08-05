import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog #per fare browising dell'output_path
import random
import Block

#cosa fa lo script
#input-ouput
#autori

output_path = "" #aggiungere il BROWSE sulla GUI inziale

# Variabili finali salvate
participant = None
block = None
condition = None
condition_order = None

CONDITIONS = [
    "FREE/OPPOSITE",
    "FREE/SAME",
    "LEAD1/SAME",
    "LEAD1/OPPOSITE",
    "LEAD2/SAME",
    "LEAD2/OPPOSITE",
    "CUED/SAME",
    "CUED/OPPOSITE"
]


def browse_output_path():
    global output_path
    folder_selected = filedialog.askdirectory()

    if folder_selected:
        output_path = folder_selected
        output_path_label.config(text=output_path)

def toggle_condition_menu():
    if shuffle_var.get():
        condition_menu.config(state="disabled")
    else:
        condition_menu.config(state="readonly")


def submit():
    temp_participant = participant_entry.get().strip()
    temp_block = block_entry.get().strip()
    temp_condition = condition_var.get()

    if not temp_participant or not temp_block:
        messagebox.showwarning("Missing fields", "Insert both Participant and Block.")
        return

    try:
        temp_block_int = int(temp_block)
    except ValueError:
        messagebox.showwarning("Invalid Block", "Block must be a number.")
        return

    if temp_block_int < 1 or temp_block_int > 3:
        messagebox.showwarning("Invalid Block", "Block must be 1, 2 or 3.")
        return

    temp_condition_order = None

    if shuffle_var.get():
        temp_condition_order = random.sample(CONDITIONS, len(CONDITIONS))
        temp_condition = temp_condition_order[temp_block_int - 1]
    else:
        if temp_condition == "Select":
            messagebox.showwarning("Missing Condition", "Please select a Condition.")
            return

    show_confirmation_window(
        temp_participant,
        temp_block,
        temp_condition,
        temp_condition_order
    )


def show_confirmation_window(
    temp_participant,
    temp_block,
    temp_condition,
    temp_condition_order
):
    confirmation_window = tk.Toplevel(root)
    confirmation_window.title("Confirm Data")
    confirmation_window.geometry("400x360")
    confirmation_window.resizable(False, False)
    confirmation_window.grab_set()

    frame = ttk.Frame(confirmation_window, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Are the entered data correct?",
        font=("Arial", 11, "bold")
    ).pack(pady=(0, 15))

    if temp_condition_order is None:
        data_text = (
            f"Participant: {temp_participant}\n"
            f"Block: {temp_block}\n"
            f"Condition: {temp_condition}"
        )

    if temp_condition_order is not None:
        data_text = (
            f"Participant: {temp_participant}\n"
            f"Block: {temp_block}\n"
            "\nRandomized condition order:\n"
            f"Block 1: {temp_condition_order[0]}\n"
            f"Block 2: {temp_condition_order[1]}\n"
            f"Block 3: {temp_condition_order[2]}"
        )

    ttk.Label(frame, text=data_text, justify="left").pack(pady=10)

    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=15)

    yes_button = ttk.Button(
        button_frame,
        text="Yes",
        command=lambda: save_data(
            temp_participant,
            temp_block,
            temp_condition,
            temp_condition_order,
            confirmation_window
        )
    )
    yes_button.grid(row=0, column=0, padx=10)

    cancel_button = ttk.Button(
        button_frame,
        text="Cancel",
        command=confirmation_window.destroy
    )
    cancel_button.grid(row=0, column=1, padx=10)


def save_data(
    temp_participant,
    temp_block,
    temp_condition,
    temp_condition_order,
    confirmation_window
):
    global participant, block, condition, condition_order

    participant = temp_participant
    block = temp_block
    condition = temp_condition
    condition_order = temp_condition_order

    confirmation_window.destroy()

    print("Saved variables:")
    print("participant =", participant)
    print("block =", block)
    print("condition =", condition)

    if condition_order is not None:
        print("condition_order =", condition_order)

    Block.StartBlock(
        participant,
        block,
        condition,
        condition_order,
        output_path,
        master=root
    )


# Creazione finestra principale
root = tk.Tk()
root.title("Experiment Setup")
root.geometry("380x260")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

# Campo Participant
ttk.Label(main_frame, text="Participant").grid(row=0, column=0, sticky="w", pady=5)
participant_entry = ttk.Entry(main_frame, width=25)
participant_entry.grid(row=0, column=1, pady=5)

# Campo Block
ttk.Label(main_frame, text="Block").grid(row=1, column=0, sticky="w", pady=5)
block_entry = ttk.Entry(main_frame, width=25)
block_entry.grid(row=1, column=1, pady=5)

# Menu a tendina Condition
ttk.Label(main_frame, text="Condition").grid(row=2, column=0, sticky="w", pady=5)

condition_var = tk.StringVar(value="Select")
condition_menu = ttk.Combobox(
    main_frame,
    textvariable=condition_var,
    values=["Select"] + CONDITIONS,
    state="readonly",
    width=22
)
condition_menu.grid(row=2, column=1, pady=5)

# Checkbox per mescolare le condizioni
shuffle_var = tk.BooleanVar(value=False)

shuffle_checkbox = ttk.Checkbutton(
    main_frame,
    text="Shuffle condition order automatically",
    variable=shuffle_var,
    command=toggle_condition_menu
)
shuffle_checkbox.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

# Selezione Output Path
ttk.Label(main_frame, text="Output Folder").grid(row=4, column=0, sticky="w", pady=5)

browse_button = ttk.Button(main_frame, text="Browse", command=browse_output_path)
browse_button.grid(row=4, column=1, pady=5, sticky="w")

output_path_label = ttk.Label(main_frame, text="No folder selected", foreground="gray")
output_path_label.grid(row=5, column=0, columnspan=2, sticky="w")

# Pulsante conferma
submit_button = ttk.Button(main_frame, text="Confirm", command=submit)
submit_button.grid(row=6, column=0, columnspan=2, pady=20)

participant_entry.focus()

root.mainloop()