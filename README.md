# ambient-temp-humidity
How to set up a temperature and humidity sensor to automatically send ambient data to the local database. There are many different options for open-source microcontrollers and temperature and humidity sensors, and the items listed below do not have to be used.
## Hardware
* ESP32 microcontroller: https://www.amazon.com/ESP32-WROOM-32-Development-ESP-32S-Bluetooth-Arduino/dp/B084KWNMM4
* HTU21DF temperature and humidity sensor: https://www.adafruit.com/product/3515
  * Note that this item is no longer sold with soldered headers. Check Adafruit, Digikey, Amazon, etc. for options.
* jumper cables: https://www.amazon.com/EDGELEC-Breadboard-Optional-Assorted-Multicolored/dp/B07GD2BWPY/?th=1
* Micro USB cable

## Setup
* Download Thonny: https://thonny.org/
* Download the latest firmware: https://micropython.org/download/ESP32_GENERIC/
* Connect the ESP32 to the PC via micro USB cable.
* In Thonny:
  * Click the Stop button or ctrl+c if needed.
  * Click on the text in the lower right corner. Select *Configure Interpreter...*
  * A window called *Thonny Options* should appear.
    * In the *Interpreter* tab, select *Micropython (ESP32)* to run your code.
    * Select the USB port that is connected to the ESP32.
    * In the lower right corner of this window, select *Install or update firmware*
      * Another window called *ESP32 firmware installer* should appear.
      * Select the port connected to the ESP32 for *Port* and the recently downloaded ESP32 firmware bin file for *Firmware*. Select install. This will take a few minutes.
      * After completing, close the firmware installer.
    * Select *OK* on the Thonny Options window.
  * In the Thonny main menu, ensure that *Files* under *View* is selected. This allows the user to view and modify files on the ESP32.
  * Also in the main menu, go to Tools and select *Manage Packages...*
  * Install the following:
    * adafruit-circuitpython-htu21d
    * micropg_lite
  * Download main.py from this repository and save to the ESP32.
  * Modify credentials in this file, such as wifi and database information.
  * Be sure to select the correct institution in the get_timestamp funtion to adjust for Daylight Savings Time.
    * When the ESP32 in not connected to a PC, time initializes to 01-01-2000.
  * Use the jumper wires to connect the following from sensor to ESP32:
    * Vin to Vin
    * GND to GND
    * SDA to D21
    * SCL to D22
  * Select the Run button under the main menu. Verify that valid temperature and humidity readings are being recorded in the local database every 5 minutes.
* Stop running the ESP32 and unplug from the PC. Connect the ESP32 to external power. We use a power strip with a USB port.
