import tkinter as tk
import sys

if not hasattr(sys, 'argv'):
    sys.argv  = ['']

def RadioUI(label, choices, default_idx):

    root = tk.Tk()
    v = tk.IntVar()

    v.set(default_idx)

    def CancelPressed():
        v.set(-1)
        root.destroy()

    tk.Label(root, text=label, justify = tk.LEFT, padx = 20).grid(sticky=tk.W, columnspan=2)

    for counter, choice in enumerate(choices):
        tk.Radiobutton(root, 
                       text = choice,
                       padx = 20, 
                       variable = v, 
                       value = counter).grid(sticky=tk.W, columnspan=2)

    tk.Button(root, text="OK", command = root.destroy).grid(row=len(choices) + 1)
    tk.Button(root, text="Cancel", command = CancelPressed).grid(column=1, row=len(choices) + 1)

    root.eval('tk::PlaceWindow . center')
    root.mainloop()

    return v.get()
