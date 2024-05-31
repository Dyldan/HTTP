import socket
import tkinter as tk
from tkinter import ttk
import sv_ttk
import threading



HOST = "127.0.0.1"
PORT = 8888

cur_request = b''
locked = True
cur_response = ''
cur_action = ''
done = False

##################################################
################# SOCKET THREAD ##################
##################################################

def start_sock():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((HOST, PORT))

    global cur_request
    global locked
    global cur_response
    global cur_action

    while True:
        if locked == False:
            s.sendall(cur_request)
            data = s.recv(8192)
            cur_response = data.decode("UTF-8")
            line, headers, body = parse_response(cur_response)
            update_status(line, headers)

            match cur_action:
                case 'GET':
                    lbl_output["text"] = ''
                    users = []
                    for i in range(3, len(body), 4):
                        if len(body)-4 > i:
                            userid = (body[i].split(': '))[1]
                            name = (body[i+1].split(': '))[1]
                            for char in userid:
                                if char in "\" ,":
                                    userid = userid.replace(char,'')
                            for char in name:
                                if char in "\" ,":
                                    name = name.replace(char,'')
                            users.append((userid, name))
                    for x in users:
                        lbl_output["text"] += x[0] + '\n' + x[1] + '\n\n'
                case 'POST':
                    lbl_output["text"] = ''
                    for line in body:
                        lbl_output["text"] += line
                case 'DELETE':
                    lbl_output["text"] = ''
                    for line in body:
                        lbl_output["text"] += line
                case _:
                    pass

            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((HOST, PORT))
            locked = True
        if done == True:
            break

##################################################
################## HTTP FUNCTIONS ################
##################################################

# GET
def do_GET():
    global cur_request
    global locked
    global cur_action

    request_line = b'GET /users.json HTTP/1.1\r\n'
    request_headers = b'Content-Type : application/json\r\n'
    request = b"".join([request_line, request_headers])

    cur_request = request
    locked = False
    cur_action = 'GET'
    
# POST
def do_POST():
    global cur_request
    global locked
    global cur_action
    global ent_userid
    global ent_name

    user_id = ent_userid.get()
    name = ent_name.get()

    ent_userid.delete(0, 'end')
    ent_name.delete(0, 'end')

    request_line = b'POST /users.json HTTP/1.1\r\n'
    request_headers = b'Content-Type : application/json\r\n'
    blank_line = b"\r\n"
    request_body = 'user_id: ' + user_id + '\r\n' + 'name: ' + name
    request = b"".join([request_line, request_headers, blank_line, request_body.encode()])

    cur_request = request
    locked = False
    cur_action = 'POST'

# PUT
def do_PUT():
    pass

# DELETE
def do_DELETE():
    global cur_request
    global locked
    global cur_action
    global ent_userid

    user_id = ent_userid.get()
    ent_userid.delete(0, 'end')

    request_line = b'DELETE /users.json HTTP/1.1\r\n'
    request_headers = b'Content-Type : application/json\r\n'
    blank_line = b"\r\n"
    request_body = user_id
    request = b"".join([request_line, request_headers, blank_line, request_body.encode()])

    cur_request = request
    locked = False
    cur_action = 'DELETE'

##################################################
################ HELPER FUNCTIONS ################
##################################################

# Parse the new response
def parse_response(res):

    lines = res.split('\r\n')
    blank_line_idx = -1

    response_line = lines[0]

    response_headers = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line == '':
            blank_line_idx = i
            break

        response_headers.append(line)

    response_body = []
    for i in range(blank_line_idx+1, len(lines)):
        # Some weird bs where if a newline doesn't include \r then I have to split over just \n
        if '\n' in lines[i]:
            temp = lines[i]
            new_lines = temp.split('\n')
            for nl in new_lines:
                response_body.append(nl.encode())
        else:
            response_body.append(lines[i])

    return response_line, response_headers, response_body

# Exit the infinite loop when user closes window
def on_closing():
    global done

    done = True
    window.destroy()

def update_status(line, headers):
    global lbl_status

    lbl_status['text'] = ''
    lbl_status['text'] += line + '\n___'
    for x in headers:
        lbl_status['text'] += '\n\n' + x

##################################################
################ MAIN LOGIC + GUI ################
##################################################

# Start socket thread
thread1 = threading.Thread(target=start_sock)
thread1.start()

# Main window
window = tk.Tk()
window.title('HTTP Users JSON')
window.minsize(1000,650)
window.columnconfigure(0, minsize=400)
window.columnconfigure(1, weight=3, minsize=400)
window.rowconfigure(0, weight=1, minsize=350)
window.rowconfigure(1, weight=1, minsize=250)
window.protocol("WM_DELETE_WINDOW", on_closing)

# Frames and other top-level widgets
frm_input = ttk.LabelFrame(window, style="Card.TFrame", text="Input")
frm_output = ttk.LabelFrame(window, style="Card.TFrame", text="Output")
frm_status = ttk.LabelFrame(window, style="Card.TFrame", text="Status")

frm_buttons = ttk.Frame(frm_input)
frm_entries = ttk.Frame(frm_input)

# Build sub-widgets
btn_get = ttk.Button(
    frm_buttons,
    text="Get Users",
    width=15,
    style="Accent.TButton",
    command=do_GET
)
btn_post = ttk.Button(
    frm_buttons,
    text="Add User",
    width=15,
    command=do_POST
)
btn_delete = ttk.Button(
    frm_buttons,
    text="Delete User",
    width=15,
    command=do_DELETE
)

lbl_userid = ttk.Label(
    frm_entries,
    text="User ID"
)
lbl_name = ttk.Label(
    frm_entries,
    text="Name"
)
ent_userid = ttk.Entry(
    frm_entries
)
ent_name = ttk.Entry(
    frm_entries
)

lbl_status = ttk.Label(frm_status)

lbl_output = ttk.Label(frm_output)

# Place everything
frm_input.grid(column=0, row=0, padx=(20,10), pady=(35,5), sticky='nsew')
frm_output.grid(column=1, row=0, rowspan=2, padx=(10,20), pady=35, sticky='nsew')
frm_status.grid(column=0, row=1, padx=(20,10), pady=(5,35), sticky="nsew")

lbl_output.grid(padx=20, pady=20)

frm_buttons.grid(column=0, row=0, padx=10, pady=10)
frm_entries.grid(column=0, row=1, padx=40, pady=20, sticky='nsw')

btn_get.grid(column=0, row=0, padx=(20,10), pady=10)
btn_post.grid(column=1, row=0, padx=10, pady=10)
btn_delete.grid(column=2, row=0, padx=(10,20), pady=10)

lbl_userid.grid(column=0, row=0, sticky='e')
lbl_name.grid(column=0, row=1, sticky='e')
ent_userid.grid(column=1, row=0, padx=10, pady=10)
ent_name.grid(column=1, row=1, padx=10, pady=10)

lbl_status.grid(column=0, row=0, padx=40, pady=(50,10), sticky='sw')

# Set the theme
sv_ttk.set_theme('dark')

# Run main GUI loop
window.mainloop()