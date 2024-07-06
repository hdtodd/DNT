# DNT v2.0.0 Release Notes

This release adds information about the thermometers observed to the display:

* Alert and warning status flags for changes in the condition of the remote thermometers are noted by "!"
* Low-battery warnings are noted by "!!"
* The "WRst" button on the table resets the warnings.

This release also streamlines the installation and on-going operation configuration by using environment variables and command-line parameters to configure DNT for the local rtl\_433 MQTT host server.

### Providing MQTT parameters

DNT requires information about the host that is serving as rtl\_433 MQTT broker to gather and publish neighborhood ISM broadcasts:

*  MQTT host name
*  MQTT topic
*  [if MQTT is secured] MQTT login username
*  [if MQTT is secured] MQTT login password
*  [if the MQTT port is not the 1883 standard] host MQTT port

These parameters may be provided in four different ways.  In decreasing order of precedence:

1.  Command line switches [-H, -T, -U,-P, -p] override all other sources to specify HOST, TOPIC, USER, PASSWORD, or PORT, respectively.
2.  These environment variables override internal variable assignments and avoid prompting:
	*  MQTT\_HOST
	*  MQTT\_TOPIC
	*  MQTT\_USER (defaults to \"\" if not specified and not provided on command line)
	*  MQTT\_PASSWORD (defaults to \"\" if not specified and not provided on command line)
	*  MQTT\_PORT (defaults to 1883 if not specified and not provided on command line)
3. The required parameter values can be assigned within the program source code.  (Location noted at the beginning of the program)
4. If not specified on command line, provided via environment, or set as internal variable assignments in the Python source code, the program prompts for HOST and TOPIC and assigns defaults to USER, PASSWORD, and PORT.


 
