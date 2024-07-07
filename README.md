# DNT: Display Neighborhood Temperatures Version 2.2
### Display thermometer readings from around your neighborbood

`DNT` is a Python program that uses the output from `rtl_433` to display temperature and humidity readings from remote thermometers around your neighborhood.  

The readings are obtained from the `rtl_433` program that monitors the Industrial-Scientific-Medical (ISM) radio-frequency band used by remote devices to communicate with their owners' base stations.  Acurite and LaCrosse indoor/outdoor thermometers are examples of such devices.  `rtl_433` receives and analyzes those broadcast packets.  `DNT` uses the output of `rtl_433` to display the temperature (in Fahrenheit or Celsius) and relative-humidity readings from probes in your neighborhood, across a variety of manufacturers' devices, even if you don't own those displays.

<img width="748" alt="image" src="https://user-images.githubusercontent.com/5464284/236265077-57af447f-7258-4b07-8ca4-7473b459f953.png">

## Use

`DNT` requires Python3 and Paho-MQTT on the displaying computer and an `rtl_433` system running on your local area network (description in subsequent section).  Paho-MQTT v2 broke v1 callback invocations, but v2.2 of `DNT` incorporates a workaround so that it will operate with either v1.x or v2.x of Paho-MQTT.

If your system already has the required components, the command `./DNT` is all that's needed to display local temperatures.  `./DNT` starts the program and  prompts for the name of the `rtl_433` host on your local area network that provides MQTT subscription service.  `./DNT -H <hostname>` starts the program without the prompt.

The program opens a scrollable, resizable display window with columns for the thermometer identity, temperature, humidity, and warning flags; appends new remote thermometer devices and associated data as they are observed by the `rtl_433` host system; and updates subsequent readings as they are reported.

`./DNT -h` provides more information about command-line options.  Additional configuration options are described in a later section.

## The Display Window

In its upper panel, the display window indicates the `rtl_433` host that it is monitoring.  It also provides three buttons:

1.  "WRst" is the *Warning Reset* button: it clears the warning flags for all devices (the last column of the data display -- see below).
1. "Togl" toggles the display window between full screen and reduced size.
1. "Quit" exits the program.  (CNTL-C in the controlling terminal window also works) 

The data panel lists the location ("familiar name" -- see configuration section below) or thermometer identifier, temperature, % relative humidity, and warning flags for each individual thermometer seen.  By default, temperature is reported in Fahrenheit: to have the temperature reported in Celsius, invoke with `DNT -C`.

The thermometer identifier is a concatenation of "model"/"channel"/"id" as reported by `rtl_433` and looks something like "Acurite-Tower/A/11524".  Unless you've configured `DNT` to associate the thermometer identifier with a "familiar name" or "location", the data display will list devices in the order in which they were observed by `rtl_433` beginning when `DNT` first started seeing MQTT events.

If you've configured `DNT` to associate the thermometer identifier with location, those devices will be moved to the top of the display list as they're observed by `rtl_433`.

### Warning Flags

`DNT` monitors packets decoded by `rtl_433` for two signals that might indicate that maintenance of a remote sensor is needed:

1.  *Battery Low* is indicated by "!!" in the warning flags column.  Though not universally standard, devices generally indicate an impending low-battery condition by changing the `battery_low` flag from 1 to 0 in its broadcast packets.  *Any* occurence of `battery_low` = 0 causes `DNT` to post the "!!" warning flag for that device.  That flag is sticky: the warning flag remains, even if `battery_low` returns to 1, since the battery voltage may be fluctuating with ambient temperature and the device may need attention in any case.
1. *Status Change* is indicated by "?!" in the warning flags column.  The remote-device status field is not present in the packets for all devices and is not standardized.  But a change in status may indicate that the device needs attention and so is flagged.  The "Status Change" flag is also sticky: once set for a device, it remains set despite any subsequent changes in packet status field values.

*Battery Low* takes precedence over *Status Change*, so only "!!" will be displayed if the battery-low flag has been seen even if a status-change has occurred.

The "WRst" button clears both the battery-low and status-change flags for *all* devices.  If warning flags reappear after a reset, they are due to new warning conditions appearing for the device. 


## Architecture

This system uses several components, all of which could be hosted on one computer but can also be distributed over several systems:

* The `DNT` Python program itself, which displays the current readings from a set of neighboring remote probes.  `DNT` receives the readings over your local-area network via MQTT from an `rtl_433` monitoring system.  `DNT` can actually run on the monitoring computer itself or on any number of other computers connected to the same local-area network as the monitoring computer.
* A host monitoring system that:
	* Has an RTL_SDR dongle attached, to receive ISM broadcasts.  In the US, that band is at 433.92MHz, but the devices and software components function across the range of ISM bands used around the world. 
	* Runs the `rtl_433` program to collect and analyze the ISM packets and publish the analyzed packets as JSON messages via MQTT over your local network.
	* Runs an MQTT broker to publish the ISM events seen by `rtl_433`.

The components are standard hardware and software components, easily obtained from online sources and well maintained. The only component included here is `DNT`: sources for the other components are provided in sections below.

## Installation

`DNT` was developed on MacOSX and Raspberry Pi OS and should function on any system that supports the requisite Python3, tkinter, and Paho-MQTT components. The `DNT` program was originally designed to run on a Raspberry Pi 7" touchscreen display but functions equally well on a large display.

If you already have an `rtl_433` host running on your network and publishing events via MQTT, `DNT` is ready to go.  If not, follow the instructions in the section below to set up an `rtl_433` monitoring host.

Then perform these steps on the computers you intend to use to display temperatures from neighborhood thermometer remotes:

1. If you haven't already done so, download this package: `git clone https://github.com/hdtodd/DNT` on a system that will run XWindows and has a touchscreen or has a keyboard/mouse/display attached.  The remaining work is on that system.
1. Install the Python3 `mqtt` library used to receive the `mqtt` JSON packets from the monitoring system over your local network: `pip3 install paho-mqtt`.  New installs will install v2 of paho-mqtt, but `DNT` will function with older v1 versions of paho-mqtt as well.  
1. Start up the MQTT verification program: `./mqTest`, and provide the name of the `rtl_433` monitoring host on your local area network. If your monitoring system is in operation, `mqTest` will simply type out on the terminal screen the information about the packets that the monitoring system is receiving via the RTL\_SDR dongle and publishing via `mqtt`.  If it isn't working, but testing with `mosquitto_sub` is working on your monitoring system, add command-line parameters  to `mqTest` to identify the correct host, topic, port and (if secured) username and password needed for the host computer MQTT subscription. `DNT` relies on the same connection system as `mqTest`, so once you've confirmed those parameters with `mqTest`, provide those parameters to `DNT`.  
1. Finally, test `DNT`: 
	* Run `./DNT` by issuing that command in a terminal window on an XWindows display.  If you want temperatures in Celsius, use the command `DNT -C`.  Over several minutes, the list on the screen will be populated, then regularly updated, with thermometer readings.  The frequency of updating varies by manufacturer and model, but readings are usually reported every 30-to-60 seconds, so individual lines in the display will be updated at different frequencies.
	* `rtl_433` reports the model, channel, and id number of the devices it sees, but those identifiers might not be familiar to you.  `DNT` has a small dictionary of thermometers you might want to watch and label with familiar names such as "porch" or "Schmidts".  Those identifier-label associations are listed as a dictionary near the beginning of the `DNT` code.  The thermometers are identified by keyword constructed from a model name, channel used, and a model id, as a single concatenated string.  Near the beginning of the `DNT` code is a dictionary of "model/channel/id" keywords and an associated location label. If you know the "model/channel/id" for your own thermometer remote, or that of neighbors, edit the "model/channel/id" keyword and corresponding location label to identify those. If present, the "location" value will be displayed in the data table and listed at the top of the table. 
1. If you want to be able to start `DNT` by touching or clicking an icon on your Linux desktop, perform these additional steps from the `DNT` installation directory:
	* Edit the file `DNT.desktop` to append `-H <hostname>` and any other needed MQTT parameters to the invocation of `/usr/local/bin/DNT`. 
	* If you want readings in Celsius, edit the file `DNT.desktop` to add ` -C` at the end of the DNT command line.
	* `sudo mkdir -p /usr/local/bin`
	* `sudo mkdir -p /usr/local/share/pixmaps`
	* `mkdir ~/Desktop`
	* `sudo cp DNT /usr/local/bin/`
	* `sudo cp DNT.png /usr/local/share/pixmaps/`
	* `cp DNT.desktop ~/Desktop/`

### Providing MQTT parameters

DNT requires information about the `rtl_433` MQTT publishing host:

*  MQTT host name
*  MQTT topic
*  MQTT login username [if MQTT is secured] 
*  MQTT login password [if MQTT is secured] 
*  host MQTT port [if the MQTT port is not the 1883 standard]

All but the host name are set to default values and may not need to be changed.  But if your `rtl_433` host MQTT broker parameters are set differently, these parameters may be provided in four different ways.  In decreasing order of precedence:

1.  Command line switches [-H, -T, -U,-P, -p] override all other sources to specify HOST, TOPIC, USER, PASSWORD, or PORT, respectively.
2.  These environment variables override internal variable assignments and avoid prompting:
	*  MQTT\_HOST
	*  MQTT\_TOPIC
	*  MQTT\_USER (defaults to \"\" if not specified and not provided on command line)
	*  MQTT\_PASSWORD (defaults to \"\" if not specified and not provided on command line)
	*  MQTT\_PORT (defaults to 1883 if not specified and not provided on command line)
3.  The required parameter values can be assigned within the program source code.   Default values are  set near the beginning of the DNT source code.
4. If not specified on command line, provided via environment, or set as internal variable assignments in the Python source code, the program prompts for HOST and assigns defaults to TOPIC, USER, PASSWORD, and PORT.

## Operation and Maintenance

You may have trouble identifying the location of the various thermometer remotes from which your RTL-SDR receives signals.  But you can likely identify those that are closest to you by observing the average signal-to-noise ratio over time and selecting those with the highest SNR for display in your table.  See the section below on how to do that.

**Over time, the "id" number of your dictionary entries will change!**  When the batteries on the remote are depleted, the owner must reinstall new  batteries and re-synch the remote with the indoor thermometer: for most devices, the "id" changes.  Use `mosquitto_sub` or `mqTest` or `DNT -d` to monitor the devices transmitting in your neighborhood and update the "model/channel/id" value in the association dictionary accordingly.  Or catalog devices using the method below and edit entries from the list `rtl_433_stats` generates.

### Debugging

Two command-line options may be useful for debugging or verifying `DNT` operation:

* `-d` causes a variety of processing messages to be printed on the controlling terminal as the program processes MQTT packets.  This might be most useful in first running `DNT` as it then prints extended information about received packets, including the signal-to-noise (SNR) ratio.  SNR may be helpful in identifying relative distance of various remote sensors seen by the RTL-SDR dongle, as higher values indicate closer proximity.  (Generally, an SNR of 15-20 is a close device from which you will routinely see transmissions; an SNR of 10 or less indicates a remote device from which transmissions are likely to be unreliable.)
* `-W` only activates if `-d` is also invoked.  `-W` causes `DNT` to artificially inject *battery-low* and *status-change* conditions in packets to verify that the warning flags activate and that the "WRst" button clears them.

### Cataloging Nearby Devices with `rtl_433_stats`

The `rtl_433.conf` configuration file entry `output json:/var/log/rtl_433/rtl_433.json` in the setup of the monitoring system above creates a log file on that monitoring system of all JSON packets published via `mqtt`.  It can be analyzed to catalog the devices from which the monitoring RTL_SDR dongle has received ISM packets.

The `rtl_433_stats` program analyzes the JSON log files generated by the `rtl_433` host system.  So either install the stats program on that computer, or copy the log file to the system on which you do install the stats program.

 Install and invoke the `rtl_433_stats` program:

1. Connect to your download directory and get the `rtl_433_stats` package: `https://github.com/hdtodd/rtl_433_stats`.
1. Follow the installation instructions in the README in that package.
1. Test your local installation with the `xaa.json` file that is provided with the package.
1. **STOP the monitoring process** on your `rtl_433` host with `sudo systemctl stop rtl_433`.  The `rtl_433` program appends JSON records very quickly, and the analysis is more reliable if the log file is not being appended to by `rtl_433`.
1. Analyze your recorded data with `rtl_433_stats -f /var/log/rtl_433/rtl_433.log > rtl.txt`, then restart `rtl_433` with `sudo systemctl start rtl_433`.
1. `cat rtl.txt` or `less rtl.txt` to browse the report.  Look, in particular, for thermometer devices with a relatively large number of recorded entries and large SNR values: those are likely devices that are static and near to your location.  [You may also see tire-pressure gauges, fuel-oil readings, security systems, etc.]
1. Use the information from the `rtl_433_stats` catalog to update the "model/channel/id":location association dictionary at the beginning of the `DNT` code.

## The Monitoring Computer
These instructions are for a Linux system.  It should be possible to install the monitoring system on OSX as well since the software components of the monitoring system are available for Mac (not tried -- use `brew` or `port` to install the MQTT component).

Perform these steps on the computer you intend to use to monitor the ISM-band radio signals.

1. If you don't already have one, purchase an RTL-SDR receiver.  Use your favorite search engine to search for "rtl sdr receiver".  They cost about $30US.  But be sure to get one with an antenna appropriate for your region's ISM frequency band.  Then you simply plug it in to a USB port on your monitoring computer.
1. If you're not sure of the frequency of ISM bands in use in your location, use a tool such as `CubicSDR` (https://cubicsdr.com/) to observe the various ISM bands and discover which ones have activity in your region.  Set the frequency in `rtl_433` (below) accordingly.
1. Install mosquitto: `sudo apt-get install mosquitto mosquitto-client`.  The broker will be started by `systemd` and will be restarted whenever the system is rebooted.
1. Connect to a download directory on your monitoring computer and use `git` to install `rtl_433`: `git clone https://github.com/merbanan/rtl_433`.
1. Connect to the installed rtl\_433 directory and follow the instructions in `./docs/BUILDING.md`to build and install the rtl\_433 program. **Be sure to install the prerequisite programs needed by rtl_433 before starting `cmake`.**  
1. **INITIAL TEST** Following the build and install, you can simply invoke `sudo /usr/local/bin/rtl_433` to verify that it starts up, finds the RTL_SDR dongle, and identifies ISM packets.  You may need to adjust the frequency via command line, e.g.,  `-f 315M`, if you're not in the US.
1. `rtl_433` is a *very* sophisticated program with *many* options, and you may want to explore its use by reading through the help message or browsing the configuration file.  But for regular operation, it's easiest to create the configuration file and, once it's working as you want it to, add `rtl_433` as a system service following instructions:
   * `cp /usr/local/etc/rtl_433/rtl_433.example.conf /usr/local/etc/rtl_433/rtl_433.conf`
   * Edit `/usr/local/etc/rtl_433/rtl_433.conf`:
     * If your regional ISM band is not 433.92MHz, set the correct frequency in the "frequency" entry.
     * Under `## Analyze/Debug options`, comment out stats reporting: `#report_meta stats`
     * Under `## Data output options`/`# as command line option:` add `output mqtt` and `output json:/var/log/rtl_433/rtl_433.json`.  The former has the program publish received packets via MQTT and the latter logs received packets to a log file in case you want to do subsequent analysis of devices in your neighborhood.  More options for MQTT publishing service are available, but this will get you started.
     *Create the directory for that log file: `sudo mkdir /var/log/rtl_433`
1. **PRODUCTION TEST** Now `sudo /usr/local/bin/rtl_433` from the command line of one terminal screen on the monitoring computer.  From the command line of another terminal screen on that computer, or from another computer with mosquitto client installed, type `mosquitto_sub -h <monitorhost> -t "rtl_433/<monitorhost>/events"`, where you substitute your monitoring computer's hostname for "\<monitorhost>".  If you have ISM-band traffic in your neighborhood, and if you've tuned `rtl_433` to the correct frequency, you should be seeing the JSON-format records of packets received by the RTL\_SDR dongle.  If you don't, first verify that you can publish to `mosquitto` on that monitoring computer and receive via a client (use the native `mosquitto_pub` and `mosquitto_sub` commands).  If `mosquitto` is functioning correctly, check that the rtl\_433 configuration file specifies mqtt output correctly.
1. Finally, install the rtl_433 monitor as a service:
	* `sudo cp rtl_433.service /etc/systemd/system/` to copy the .service file from this download directory (where this README file is located) into the systemd directory
	* `sudo systemctl enable rtl_433` and `sudo systemctl start rtl_433` to enable and start the service
	* Now, whenever the monitoring system is rebooted, it will restart the rtl_433 service and the mqtt service needed to broadcast in JSON format the information received by the RTL\_433 dongle as ISM packets.

The JSON log file grows quickly, so you will, over time, need to remove the JSON log file on the monitoring computer (`/var/log/rtl_433/rtl_433.json`).  Or you may want to use `logrotate` to manage those JSON files, in which case you could `sudo mv rtl_433.logrotate /etc/logrotate.d/rtl_433` on the host monitoring system to compress and manage the log files.

The developers of `rtl_433` continually update the list of devices that the program recognizes, so connect to the `rtl_433` download directory, `git pull`, re-build, and re-install `rtl_433` periodically to add recognition of new devices in your neighborhood.

## Outstanding Issues
On occasion, clicking the "Quit" button fails to shut down `DNT` on Mac OSX.  This appears to be a Python GIL issue caused by interaction between `tkinter` and `mqtt` loops.  Feedback and suggested solutions would be welcome.

## Release History

*  V1.0: First operational version
*  V2.0: Make display table scrollable; add warning flags
*  V2.1: Introduce use of environmental and  command-line parameters
*  V2.2: Add workaround for paho_mqtt v1/v2 callback incompatibility 

## Author
Written by David Todd, hdtodd@gmail.com, 2023.04; V2.2 2024.07.
