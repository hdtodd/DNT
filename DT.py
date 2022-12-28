#! /usr/bin/python3
# DT -- Display Temperatures from neighboring remote
#       thermometers on (touchscreen) display
# Modeled after
#   https://learn.sparkfun.com/tutorials/python-gui-guide-introduction-to-tkinter/experiment-3-sensor-dashboard
# HDTodd, Williston, VT, January, 2022

import tkinter as tk
import tkinter.font as tkFont
import random
import json
import time
from paho.mqtt import client as mqtt_client

##  *** BEGIN LOCAL MODIFICATIONS ***
# mqtt connection management
# variables used to establish the mqtt connection to the rtl_433 receiver mqtt publisher
broker = '<monitorhost>'
port = 1883
topic = "rtl_433/<monitorhost>/events"
# If your mqtt broker is secured, provide login info
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
username = '<myusername>'
password = '<mypassword>'

##  *** Edit the following to label your local sensors  ***
# locations of known sensors; others not reported
location = {
    "Acurite-609TXC 51":"Outside",
    "Acurite-606TX 161":"Porch",
    "LaCrosse-TX141THBv2 168":"Frank",
    "Acurite-Tower 11524":"Acurite-Tower",
    "Acurite-609TXC 164":"Emulator"
    }
# Display known remote sensors; size to allow for header row and control buttons in last row
displaySize = len(location)+2
##  *** END LOCAL MODIFICATIONS ***

# De-duping mqtt records
# set 2-sec threshhold for rejecting duplicate records
thresh = 2.0
# set blank "lastEntry" key record fields for rejecting duplicate records
#   time+/-2sec, model, & id the same count as a duplicate record
lastEntry = {
    "time":0.0,
    "model":"",
    "id":0
    }


###############################################################################
# Display arameters and global variables for tkinter

# Declare global variables
root = None
dfont = None
frame = None
temp_f = None
rh = None
locs = None

# Global variable to remember if we are fullscreen or windowed
fullscreen = False

###############################################################################
# Functions for displaying

# Toggle fullscreen
def toggle_fullscreen(event=None):

    global root
    global fullscreen

    # Toggle between fullscreen and windowed modes
    fullscreen = not fullscreen
    root.attributes('-fullscreen', fullscreen)
    resize()

# Return to windowed mode
def end_fullscreen(event=None):

    global root
    global fullscreen

    # Turn off fullscreen mode
    fullscreen = False
    root.attributes('-fullscreen', False)
    resize()

# Automatically resize font size based on window size
def resize(event=None):

    global dfont
    global frame

    # Resize font based on frame height (minimum size of 12)
    # Use negative number for "pixels" instead of "points"
    new_size = -max(12, int((frame.winfo_height() / 10)))
    dfont.configure(size=new_size)

# MQTT functions and display updating
# Connect to  MQTT broker 
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed attempt to connect to ", client)
            print("  with userdata ", userdata)
            print("Return code %d\n", rc)

    client = mqtt_client.Client(client_id)
#    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Subscribe to rtl_433 publication & process records we receive
def subscribe(client: mqtt_client):

    # on_message does the real work
    # When we get a record, ignore if it's a duplicate, update display if it isn't
    def on_message(client, userdata, msg):
        global root
        global temp_f
        global rh
        global locs

        # parse the json payload
        y = json.loads(msg.payload.decode())

        # if this is a themometer reading, process it; otherwise just note it
        if "temperature_C" in y.keys():

            # OK, we have a temp reading. Set the variables we need
            hum = 0.0 if not ("humidity" in y.keys()) else float(y["humidity"])
            # Is this a duplicate record?  Use time+model+id as a fingerprint to tell.
            # First, get time in seconds since Epoch for comparison purposes, with 2 sec threshhold
            eTime = time.mktime(time.strptime(y["time"], "%Y-%m-%d %H:%M:%S"))

            # If not a duplicate entry, then process & record; else skip
            if eTime>lastEntry["time"]+thresh or y["model"]!=lastEntry["model"] or y["id"]!=lastEntry["id"]:
                device = y["model"]+" "+ str(y["id"])
                loc  = device if not (device in location) else location[device]
                drow = -1 if not (device in location) else list(location).index(device)
                print("{:<3d} {:<20} {:<20} {:<20} {:>8} {:>8.1f}°F {:>5}% snr={:>6.2f}".format(
                    drow,
                    loc,
                    y["time"],
                    y["model"],
                    y["id"],
                    round(float(y["temperature_C"])*9.0/5.0+32.0,1),
                    hum,
                    0.0 if not ('snr' in y) else y['snr'])
                    )

                # Update labels to display temperature and humidity values
                if drow in range(displaySize):
                    try:
                        locs[drow].set(loc)
                        temp_f[drow].set(round(float(y["temperature_C"])*9.0/5.0+32.0,1))
                        rh[drow].set(hum)
                    except:
                        print("exception when trying to set display values")
                        pass
                root.bind('<Configure>', resize)
                # Now note this entry's fingerprint for subsequent de-duping
                lastEntry["time"] = eTime
                lastEntry["model"] = y["model"]
                lastEntry["id"] = y["id"]
        else:
            print("--- NOT A THERMOMETER ---")
            print(y)
            print("-------------------------")
            
    client.subscribe(topic)
    client.on_message = on_message
    print("subscribed to mqtt feed")

def quit_prog(event=None):
    client.loop_stop()
    root.quit()
        
###############################################################################
# Main script

# Create the main window
root = tk.Tk()
root.title("The Big Screen")

print("create big screen")

# Create the main container
frame = tk.Frame(root)

# Lay out the main container (expand to fit window)
frame.pack(fill=tk.BOTH, expand=1)

# Variables for holding temperature and humidity data
temp_f = []
rh = []
locs = []
for i in range(len(location)):
    locs.append(tk.StringVar())
    temp_f.append(tk.DoubleVar())
    rh.append(tk.DoubleVar())

# Create dynamic font for text
dfont = tkFont.Font(size=-18)
lfont = tkFont.Font(size=-48, weight="bold")
qfont = tkFont.Font(size=-36, weight="bold")

# Create widgets
label_loc   = tk.Label(frame, text="Location", font=lfont, foreground='green')
label_temp  = tk.Label(frame, text="Temp °F",  font=lfont, foreground='green')
label_hum   = tk.Label(frame, text="%RH",      font=lfont, foreground='green')
button_quit = tk.Button(frame, text="Quit", font=dfont, foreground='white', background='red', command=quit_prog)
label_f = []
label_rh = []
label_locs = []
for  i in range(len(location)):
    label_f.append(tk.Label(frame, textvariable=temp_f[i], font=dfont))
    label_rh.append(tk.Label(frame, textvariable=rh[i], font=dfont))
    label_locs.append(tk.Label(frame, textvariable=locs[i], font=dfont))
    
# Lay out widgets in a grid in the frame
# First, the header
label_loc.grid(  row=0, column=0, padx=5, pady=5, sticky=tk.W, columnspan=3)
label_temp.grid( row=0, column=3, padx=5, pady=5, sticky=tk.E)
label_hum.grid(  row=0, column=4, padx=5, pady=5, sticky=tk.E)
# Now the bottom (controls) row
button_quit.grid(row=displaySize, column=4, padx=5, pady=5)
# And now the data grid
for i in range(len(location)):
    label_locs[i].grid(row=i+1, column=0, padx=5, pady=5, sticky=tk.W, columnspan=3)
    label_f[i].grid   (row=i+1, column=3, padx=5, pady=5, sticky=tk.E)
    label_rh[i].grid  (row=i+1, column=4, padx=5, pady=5, sticky=tk.E)
    
# Make it so that the grid cells expand out to fill window
for i in range(0, displaySize):
    frame.rowconfigure(i, weight=1)
for i in range(0, 5):
    frame.columnconfigure(i, weight=1)

# Bind F11 to toggle fullscreen and ESC to end fullscreen
root.bind('<F11>', toggle_fullscreen)
root.bind('<Escape>', end_fullscreen)

# Have the resize() function be called every time the window is resized
root.bind('<Configure>', resize)

for i in range(len(location)):
    temp_f[i].set(" ")
    rh[i].set(" ")
    locs[i].set(" ")
#    locs[i].set(list(location)[i])
    
# Start in fullscreen mode and run
toggle_fullscreen()

# connect to the mqtt broker and subscribe to the feed
#   events cause the displayed values to be updated
client = connect_mqtt()
subscribe(client)
client.loop_start()

print("entering run loop")
root.mainloop()
