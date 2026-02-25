Lenovo OneCli System Product Data Tool

OVERVIEW This Windows GUI utility wraps Lenovo OneCli to simplify
setting system product data through the BMC. It removes the need to
manually type long OneCli commands in a command prompt. The tool is
intended for field and operational use and can be run by anyone. Python
is not required.

FUNCTIONALITY The tool allows setting the following values using Lenovo
OneCli. System Identifier System Product Number System Serial Number All
actions are performed remotely through the system BMC.

FEATURES Windows graphical user interface Single executable file No
Python installation required Automatically detects OneCli.exe when
placed in the same folder Allows browsing for OneCli.exe if installed
elsewhere Displays a download link for OneCli when it is not found
Includes a read-only BMC connectivity test Displays live OneCli output
and errors Provides clear success or failure feedback Footer indicates
tested Lenovo OneCli version

TESTED ENVIRONMENT Windows 10 Windows 11 Lenovo OneCli version 4.3.0
Lenovo ThinkSystem servers

RECOMMENDED FOLDER LAYOUT OneCliSysInfoTool OneCliSysInfoTool.exe
OneCli.exe README.txt

USAGE Launch the executable. Provide BMC IP or hostname, username, and
password. Enter system identifier, product number, and serial number.
Optionally test BMC connectivity. Run commands and review output.

COMMANDS EXECUTED 
OneCli.exe config set
SYSTEM_PROD_DATA.SysInfoProdIdentifier “IDENTIFIER” –bmc
USER:PASS@BMC_IP 
OneCli.exe config set SYSTEM_PROD_DATA.SysInfoProdName
“PRODUCT_NAME” –bmc USER:PASS@BMC_IP 
OneCli.exe config set
SYSTEM_PROD_DATA.SysInfoSerialNum “SERIAL_NUMBER” –bmc USER:PASS@BMC_IP
OneCli.exe misc show system –bmc USER:PASS@BMC_IP

NOTES No data is modified until Run Commands is selected. BMC test is
read-only. Credentials are not saved.
