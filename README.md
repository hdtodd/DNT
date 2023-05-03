# DNT: Display Neighborhood Temperatures
### Display thermometer readings from around your neighborbood

`DNT` is a Python program that uses the output from `rtl_433` to display temperature and humidity readings from remote thermometers around your neighborhood.  

The readings are obtained by using the `rtl_433` program to monitor the Industrial-Scientific-Medical (ISM) radio-frequency band used by remote devices to communicate with their owners' base stations.  Acurite and LaCrosse indoor/outdoor thermometers are examples of such devices.  `rtl_433` receives and analyzes those broadcast packets.  This program uses the output of `rtl_433` to display the temperature (in Fahrenheit or Celsius) and relative-humidity readings from probes in your neighborhood, across a variety of manufacturers' devices, even if you don't own one of those displays.

### Use

`DNT` requires Python3.  The command `./DNT` starts the program and prompts for the name of the `rtl_433` host on your local area network that provides MQTT subscription service.  `./DNT -H <hostname>` starts the program without the prompt.

The program opens a scrollable, resizable display window, appends new remote thermometer devices as they are observed by the `rtl_433` host system, and updates readings as they are reported.

`./DNT -h` provides more information about options.

## Architecture

This system uses several components, all of which could be hosted on one computer but can also be distributed over several systems:

* The `DNT` Python program itself, which displays the current readings from a set of neighboring remote probes.  `DNT` receives the readings over your local-area network via MQTT from an `rtl_433` monitoring system.  `DNT` can actually run on the monitoring computer itself or on any number of other computers connected to the same local-area network as the monitoring computer.
* A host monitoring system that:
	* Has an RTL_SDR dongle attached, to receive ISM broadcasts.  In the US, that band is at 433.92MHz, but the devices and software components function across the range of ISM bands used around the world. 
	* Runs the `rtl_433` program to collect and analyze the ISM packets and publish the analyzed packets as JSON messages via MQTT over your local network.
	* Runs an MQTT broker to publish the ISM events seen by `rtl_433`.

The components are standard hardware and software components, easily obtained from online sources and well maintained. The only component included here is `DNT`: sources for the other components are provided in sections below.

## Installation

`DNT` was developed on MacOSX and Raspberry Pi Linux. It should be possible to install the monitoring system on OSX as well since the software components of the monitoring system are available for Mac (not tried -- use `brew` or `port` to install the MQTT component).

The first step is to clone this distribution into a working area.  Connect to a download working directory and then `git clone https://github.com/hdtodd/DNT` to download the display-program file and this README.

If you already have an `rtl_433` host running on your network and publishing events via MQTT, `DNT` is ready to go.  If not, follow the instructions below to set up an `rtl_433` monitoring host.

The monitoring system simply broadcasts the JSON `mqtt` packets on your local network, so any number of other computers on your network can display current readings by running `DNT`.

### Operation and Maintenance

You may have trouble identifying the location of the various thermometer remotes from which your RTL-SDR receives signals.  But you can likely identify those that are closest to you by observing the average signal-to-noise ratio over time and selecting those with the highest SNR for display in your table.  See the section below on how to do that.

**Over time, the "id" number of your dictionary entries will change!**  When the batteries on the remote are depleted, the owner must reinstall new  batteries and re-synch the remote with the indoor thermometer: the "id" changes.  So if your display table starts losing entries, use `mosquitto_sub` or `mqTest` to monitor the devices transmitting in your neighborhood and update the "id" value in the association dictionary accordingly.  Or catalog devices using the method below and edit entries from the list `snr` generates.

You will, over time, need to remove the JSON log file on the monitoring computer (`/var/log/rtl_433/rtl_433.json`).  Or you may want to use `logrotate` to manage those JSON files, in which case `sudo mv rtl_433.logrotate /etc/logrotate.d/rtl_433` on the host monitoring system to compress and manage the log files.

The developers of `rtl_433` continually update the list of devices that the program recognizes, so `git pull`, re-build, and re-install `rtl_433` periodically to add new devices in your neighborhood.

### Cataloging Nearby Devices with `snr`

The `rtl_433.conf` configuration file entry `output json:/var/log/rtl_433/rtl_433.json` in the setup of the monitoring system above creates a log file on that monitoring system of all JSON packets published via `mqtt`.  It can be analyzed to catalog the devices from which the monitoring RTL_SDR dongle has received ISM packets.

Install and invoke the `snr` program:

1. Connect to your download directory and get the `snr` package: `git clone https://github.com/hdtodd/rtl_snr`.
1. Follow the installation instructions in the README in that package.
1. Test your local installation with the `xaa.json` file that is provided with the package.
1. **STOP the monitoring process** with `sudo systemctl stop rtl_433`.  The `rtl_433` program appends JSON records very quickly, and the analysis is more reliable if the log file is not being appended to by `rtl_433`.
1. Analyze your recorded data with `snr -f /var/log/rtl_433/rtl_433.log > rtl.txt`, then restart `rtl_433` with `sudo systemctl start rtl_433`.
1. `cat rtl.txt` or `less rtl.txt` to browse the report.  Look, in particular, for thermometer devices with a relatively large number of recorded entries and large SNR values: those are likely devices that are static and near to your location.  [You'll also see tire-pressure gauges, fuel-oil readings, security systems, etc.]
1. Use the information from the `snr` catalog to update the "model+id"-label association dictionary at the beginning of the `DNT.py` code.

## The Monitoring Computer
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

### Displaying Temperatures
The `DNT` program was designed to run on a Raspberry Pi 7" touchscreen display, but it will function on any system for which the `tkinter` library is available. 

Perform these steps on the computers you intend to use to display temperatures from neighborhood thermometer remotes:

1. If you haven't already done so, download this package: `git clone https://github.com/hdtodd/DNT` on a system that will run XWindows and has a touchscreen or has a keyboard/mouse/display attached.  The remaining work is on that system.
1. Install the Python3 `mqtt` library used to receive the `mqtt` JSON packets from the monitoring system over your local network: `pip3 install paho-mqtt`.  
1. Edit the python files to install the hostname of the monitoring system on your local network: `sed s/\<mymonitor\>/xxxx/mqTest.py.template > mqTest.py` and `sed s/\<mymonitor\>/xxxx/ DNT.py.template > DNT.py`, where "xxxx" is the hostname of your local monitor,  to replace the placeholder "\<mymonitor\>" with the name of your local host, "xxxx".  (Or just edit the files to change those names). If you secured your mqtt publishing, you'll need to provide the username and password for that service by editing those Python files.
1. Now start it up: `python3 mqTest.py`.  If your monitoring system is in operation, `mqTest` will simply type out on the terminal screen the information about the packets that the monitoring system is receiving via the RTL\_SDR dongle and publishing via `mqtt`.  If it isn't working, but testing with `mosquitto_sub` is working on your monitoring system, check parameters in `mqTest` and try the `mosquitto_sub` command on that display computer, adjusting parameters until `mqTest` functions correctly.  `DNT.py` relies on the same connection system as `mqTest`.  The terminal output line includes the signal-to-noise ratio (SNR) reported by `rtl_433`: those with a higher SNR are likely closer to you in proximity, and those with an SNR greater than 15-20 are likely your closest neighbors.
1. Finally, test `DNT.py`:
	* `rtl_433` reports the model and id number of the devices it sees, but those identifiers might not be familiar to you.  `DNT.py` has a small table of thermometers you might want to watch and label with familiar names such as "porch" or "Schmidts".  Those identifier-label associations are listed as a dictionary near the beginning of the `DNT.py` code.  The thermometers are identified by keyword constructed from a model name and a model id, as a single concatenated string.  Near the beginning of the `DNT.py` code is a dictionary of "model+id" keywords and an associated label. If you know the "model+id" for your own thermometer remote, or that of neighbors, edit the "model+id" keyword and corresponding label to identify those.  Otherwise, observe some of the "model" and "id" values in packets reported by `mosquitto_sub` or `mqTest.py` and enter "model+id" as both keyword and label values in that dictionary.
	* Run `python3 DNT.py` by issuing that command in a terminal window on an XWindows display.  If you want temperatures in Celsius, use the command `python3 DNT.py -c` or in `DNT.py`, set `useF=False` in the initialization section.  Over several minutes, the list on the screen will be populated, then regularly updated, with thermometer readings.  The frequency of updating varies by manufacturer and model, but readings are usually reported every 30-to-60 seconds, so individual lines in the display will be updated at different frequencies.
1. If you want to be able to start `DNT.py` by touching or clicking an icon on your desktop, perform these additional steps from the `DNT` installation directory:
	* If you want readings in Celsius, edit the file `NT.desktop` to add ` -c` at the end of the DNT.py command line.
	* `sudo mkdir -p /usr/local/bin`
	* `sudo mkdir -p /usr/local/share/pixmaps`
	* `mkdir ~/Desktop`
	* `sudo cp DNT.py /usr/local/bin/`
	* `sudo cp DNT.png /usr/local/share/pixmaps/`
	* `cp DNT.desktop ~/Desktop/`


## Outstanding Issues
On occasion, clicking the "Quit" button fails to shut down `DNT` on Mac OSX.  This appears to be a Python GIL issue caused by interaction between `tkinter` and `mqtt` loops.  Feedback and suggested solutions would be welcome.

## Author
Written by David Todd, hdtodd@gmail.com, 2023.04.
