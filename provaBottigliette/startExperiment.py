import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import json
from pathlib import Path
import Block

# Config file per salvare l'ultima COM usata
CONFIG_FILE = Path.home() / ".bottigliette_config.json"

output_path = ""

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


def save_last_com(com_port):
    try:
        CONFIG_FILE.write_text(json.dumps({"last_com": com_port}))
    except Exception:
        pass


def load_last_com():
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("last_com", "")
    except Exception:
        return ""


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
    temp_com_port = com_var.get().strip().upper()

    if not temp_participant or not temp_block:
        messagebox.showwarning("Missing fields", "Insert both Participant and Block.")
        return

    if not temp_com_port:
        messagebox.showwarning("COM Port mancante", "Inserisci la porta COM, ad es. COM3.")
        return

    if temp_com_port == "COM":
        messagebox.showwarning("COM Port invalida", "Inserisci anche il numero della porta, ad es. COM3.")
        return

    if not temp_com_port.startswith("COM"):
        messagebox.showwarning("COM Port invalida", "La porta deve iniziare con 'COM', ad es. COM3.")
        return

    if not temp_com_port[3:].isdigit():
        messagebox.showwarning("COM Port invalida", "Dopo 'COM' deve esserci un numero, ad es. COM3.")
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
        temp_condition_order,
        temp_com_port
    )


def show_confirmation_window(
    temp_participant,
    temp_block,
    temp_condition,
    temp_condition_order,
    temp_com_port
):
    confirmation_window = tk.Toplevel(root)
    confirmation_window.title("Confirm Data")
    confirmation_window.geometry("420x320")
    confirmation_window.resizable(False, False)
    confirmation_window.grab_set()

    frame = ttk.Frame(confirmation_window, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Are the entered data correct?",
        font=("Arial", 11, "bold")
    ).pack(pady=(0, 12))

    if temp_condition_order is None:
        data_text = (
            f"Participant: {temp_participant}\n"
            f"Block: {temp_block}\n"
            f"Condition: {temp_condition}\n"
            f"COM Port: {temp_com_port}"
        )
    else:
        data_text = (
            f"Participant: {temp_participant}\n"
            f"Block: {temp_block}\n"
            f"COM Port: {temp_com_port}\n\n"
            "Randomized condition order:\n"
            f"Block 1: {temp_condition_order[0]}\n"
            f"Block 2: {temp_condition_order[1]}\n"
            f"Block 3: {temp_condition_order[2]}"
        )

    ttk.Label(frame, text=data_text, justify="left").pack(pady=8)

    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=14)

    yes_button = ttk.Button(
        button_frame,
        text="Yes",
        command=lambda: save_data(
            temp_participant,
            temp_block,
            temp_condition,
            temp_condition_order,
            temp_com_port,
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
    temp_com_port,
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
    print("com_port =", temp_com_port)

    if condition_order is not None:
        print("condition_order =", condition_order)

    # salva l'ultima COM usata
    save_last_com(temp_com_port)

    Block.StartBlock(
        participant,
        block,
        condition,
        condition_order,
        output_path,
        master=root,
        com_port=temp_com_port
    )


# Creazione finestra principale
root = tk.Tk()
root.title("Experiment Setup")
root.geometry("450x360")
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
    command=toggle_condition_menu,
    state="disabled"
)
shuffle_checkbox.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

# Selezione Output Path
ttk.Label(main_frame, text="Output Folder").grid(row=4, column=0, sticky="w", pady=5)

browse_button = ttk.Button(main_frame, text="Browse", command=browse_output_path)
browse_button.grid(row=4, column=1, pady=5, sticky="w")

output_path_label = ttk.Label(main_frame, text="No folder selected", foreground="gray")
output_path_label.grid(row=5, column=0, columnspan=2, sticky="w")

# COM Port
com_port_label = ttk.Label(main_frame, text="COM Port", foreground="black")
com_port_label.grid(row=6, column=0, sticky="w", pady=5)

com_var = tk.StringVar(value=load_last_com())
com_entry = ttk.Entry(main_frame, width=25, textvariable=com_var)
com_entry.grid(row=6, column=1, pady=5)

confirm_button = ttk.Button(main_frame, text="Start", command=submit)
confirm_button.grid(row=7, column=0, columnspan=2, pady=18)

participant_entry.focus()

root.mainloop()