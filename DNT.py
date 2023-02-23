#!/usr/bin/python3
# NT -- Display Temperatures from neighborhood remote thermometers
# Usage: /usr/bin/python3 NT.py [-h | -c | -f]
# To install, modify the information in the designated section below
#   to provide the MQTT broker information and the dictionary of known local sensors to watch
# Modeled after
#   https://learn.sparkfun.com/tutorials/python-gui-guide-introduction-to-tkinter/experiment-3-sensor-dashboard
#
# HDTodd, Williston, VT, February, 2023

import tkinter as tk
import tkinter.font as tkFont
import random
import json
import time
import getopt, sys
from paho.mqtt import client as mqtt_client

###############################################################################
##  *** BEGIN LOCAL MODIFICATIONS ***

# MQTT connection management
# Parameters used to establish the mqtt connection to the rtl_433 receiver mqtt publisher
broker = 'pi-1'
port = 1883
topic = "rtl_433/pi-1/events"
# If your mqtt broker is secured, provide login info
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
username = '<myusername>'
password = '<mypassword>'

# Known local sensors to be monitored
# Dictionary entries are "model+id":"Familiar Name".
# Run this program from a terminal session to see a list of models and ids 
# Just use "model+id" in place of familiar name if you haven't yet identified the sensors
location = {
    "Acurite-609TXC 51"       : "Outside",
    "Acurite-606TX 161"       : "Porch",
    "LaCrosse-TX141THBv2 168" : "Frank 168",
    "LaCrosse-TX141Bv3 253"   : "Not Frank 253",
    "Acurite-Tower 11524"     : "Acurite-Tower",
    "Acurite-606TX 134"       : "Neighbor",
    "Oregon-THN132N 138"      : "Oregon-THN132N 138"
#    "Acurite-609TXC 164"     : "Emulator"
    }
# Display known remote sensors; size to allow for header row 
displaySize = len(location)+1

##  *** END LOCAL MODIFICATIONS ***

###############################################################################
# Global variable initialization

# By default, use Fahrenheit scale for display
useF=True

# Remember if we are fullscreen or windowed; toggle starts fullscreen
fullscreen = False

# Set blank "lastEntry" key record fields for rejecting duplicate records
#   time+/-2sec with model & id the same count as a duplicate record
lastEntry = { "time":0.0, "model":"", "id":0 }
# Set 2-sec threshhold for rejecting duplicate records
thresh = 2.0

###############################################################################
# Command line processor: options are [<none> | -h | -f | -c]
def getarg():

    global useF
    options = "hcf"
    long_options = ["Help", "Celsius", "Fahrenheit"]

    def helper():
        print("NT: program to display neighborhood temperatures by monitoring")
        print("      remote thermometer broadcasts (433.92MHz in US)")
        print("      as rebroadcast by RTL_433 MQTT broker on your local area network")
        print("NT -h for this help message")
        print("NT -f to display temperatures in Fahrenheit")
        print("NT -c to display temperatures in Celsius")

    # Remove program name from the list of command line arguments
    argumentList = sys.argv[1:]

    try:
        # Parse argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # Act on it if valid, else give help msg and quit
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "-H", "--Help"):
                helper()
                quit()
            elif currentArgument in ("-c", "--Celsius"):
                useF=False
            elif currentArgument in ("-f", "--Fahrenheit"):
                useF=True

    except getopt.error as err:
        # output error msg, help, and quit
        print (str(err))
        helper()
        quit()

###############################################################################
# Functions for displaying

# Toggle fullscreen
def toggle_fullscreen(event=None):
    global win
    global fullscreen

    fullscreen = not fullscreen
    win.attributes('-fullscreen', fullscreen)
    resize()

# Automatically resize font size based on window size
def resize(event=None):
    global dfont
    global lfont
    global frm

    # Resize font based on frame height (minimum size of 12)
    # Use negative number for "pixels" instead of "points"
    dfont.configure(size=-max(12, int((frm.winfo_height() / 12))))
    lfont.configure(size=-max(18, int((frm.winfo_height() / 9))))

    for j in range(3):
        lbl_data[0][j].configure(font=lfont)
        for i in range(1,displaySize-1):
            lbl_data[i][j].configure(font=dfont)

    btn_quit.config(font=dfont)
    btn_toggle.config(font=dfont)
    
###############################################################################
# MQTT functions and display updating
# Connect to  MQTT broker 
def connect_mqtt() -> mqtt_client:
    def on_connect(mqtt, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed attempt to connect to ", mqtt)
            print("  with userdata ", userdata)
            print("Return code %d\n", rc)

    mqtt = mqtt_client.Client(client_id, clean_session=False)
    mqtt.username_pw_set(username, password)
    mqtt.on_connect = on_connect
    mqtt.connect(broker, port)
    subscribe(mqtt)
    return mqtt

# Subscribe to rtl_433 publication & process records we receive
def subscribe(mqtt: mqtt_client):

    # on_message does the real work
    # When we get a record, ignore if it's a duplicate, update display if it isn't
    def on_message(mqtt, userdata, msg):
        global locs
        global temp
        global rh

        # parse the json payload
        y = json.loads(msg.payload.decode())

        # if this is a themometer reading, process it; otherwise just note it
        if "temperature_C" in y.keys():

            # OK, we have a temp reading. Set the variables we need
            # First, get temp & convert to Fahrenheit if requested
            ltemp = y["temperature_C"]
            if useF:
                ltemp = ltemp*9.0/5.0+32.0
            # Now get humidity if reading has it
            hum = 0 if not ("humidity" in y.keys()) else int(y["humidity"])
            # Is this a duplicate record?  Use time+model+id as a fingerprint to tell.
            # Get time in seconds since Epoch for comparison purposes, with 2 sec threshhold
            eTime = time.mktime(time.strptime(y["time"], "%Y-%m-%d %H:%M:%S"))

            # If not a duplicate entry, then process & record; else skip
            if eTime>lastEntry["time"]+thresh or y["model"]!=lastEntry["model"] or y["id"]!=lastEntry["id"]:
                device = y["model"]+" "+ str(y["id"])
                loc  = device if not (device in location) else location[device]
                drow = -1 if not (device in location) else list(location).index(device)
                print("{:<3d} {:<20} {:<20} {:<20} {:>8} {:>8.1f}{:2} {:>5}% snr={:>3.0f}".format(
                    drow,
                    loc,
                    y["time"],
                    y["model"],
                    y["id"],
                    round(ltemp,1),
                    tScale,
                    hum,
                    0.0 if not ('snr' in y) else y['snr'])
                    )

                # Update labels to display temperature and humidity values
                if drow in range(displaySize):
                    try:
                        locs[drow].set(loc)
                        temp[drow].set(round(ltemp,1))
                        rh[drow].set(hum)
                    except:
                        print("exception when trying to set display values")
                        pass
                resize()
                # Now note this entry's fingerprint for subsequent de-duping
                lastEntry["time"] = eTime
                lastEntry["model"] = y["model"]
                lastEntry["id"] = y["id"]
        else:
            print("--- NOT A THERMOMETER ---")
            print(y)
            print("-------------------------")
            
    mqtt.subscribe(topic)
    mqtt.on_message = on_message
    print("subscribed to mqtt feed")

def quit_prog(event=None):
    mqtt.loop_stop()
    mqtt.disconnect()
    win.quit()
        
###############################################################################
# Main script

getarg()
tScale = "°F" if useF else "°C"

# Create the main window
win = tk.Tk()
win.title("Neighborhood Temperatures")

# Create dynamic font for text
dfont = tkFont.Font(size=-18)
lfont = tkFont.Font(size=-48, weight="bold")

# Create the main container
frm = tk.Frame(win)

# Variables for holding temperature and humidity data
locs = []
temp = []
rh = []
for i in range(len(location)):
    locs.append(tk.StringVar())
    temp.append(tk.DoubleVar())
    rh.append(tk.IntVar())

# Create widgets
lbl_data = []

# First, the header
lbl_data.append( (tk.Label(frm, text="Location",        font=lfont, fg='green'),
                  tk.Label(frm, text=("Temp "+tScale),  font=lfont, fg='green'),
                  tk.Label(frm, text="%RH",             font=lfont, fg='green')) )

# Now the table of readings
for i in range(len(location)):
    lbl_data.append( (tk.Label(frm, textvariable=locs[i], font=dfont),
                      tk.Label(frm, textvariable=temp[i], font=dfont),
                      tk.Label(frm, textvariable=rh[i],   font=dfont)) )

# Lay out widgets in a grid in the frame
for i in range(displaySize-1):
    lbl_data[i][0].grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
    lbl_data[i][1].grid(row=i, column=1, padx=5, pady=5, sticky=tk.E)
    lbl_data[i][2].grid(row=i, column=2, padx=5, pady=5, sticky=tk.E)

# Make the grid cells expand to fill frame
for i in range(displaySize):
    frm.rowconfigure(i, weight=1)
for j in range(3):
    frm.columnconfigure(j, weight=1)

frm.pack(fill=tk.BOTH, expand=1)

# And add the buttons at the bottom
btn_quit=tk.Button(win, text="Quit", width=6, height=2, font=dfont, fg='red', command=quit_prog)
btn_quit.pack(side=tk.LEFT)
btn_toggle=tk.Button(win, text="Toggle\nScreen", width=10, height=2, font=dfont, fg='blue', command=toggle_fullscreen)
btn_toggle.pack(side=tk.LEFT)

# Have <ESC> toggle window, and call resize() every time the window is resized
win.bind('<Escape>', toggle_fullscreen)
win.bind("<ButtonRelease-1>", resize)

for i in range(len(location)):
    locs[i].set(" ")
    temp[i].set(" ")
    rh[i].set(" ")
    
# connect to the mqtt broker and subscribe to the feed.
#   MQTT events cause the displayed values to be updated
mqtt = connect_mqtt()
mqtt.loop_start()

print("entering run loop")
win.mainloop()
