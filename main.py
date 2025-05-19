from machine import I2C, Pin
import time, network, micropg_lite, ntptime
#import ubinascii


class HTU21D(object):
    ADDRESS = 0x40
    ISSUE_TEMP_ADDRESS = 0xE3
    ISSUE_HU_ADDRESS = 0xE5

    def __init__(self, scl, sda):
        """Initiate the HUT21D
        Args:
            scl (int): Pin id where the sdl pin is connected to
            sda (int): Pin id where the sda pin is connected to
        """
        self.i2c = I2C(scl=Pin(scl), sda=Pin(sda), freq=100000)


    def _crc_check(self, value):
        """CRC check data
        Notes:
            stolen from https://github.com/sparkfun/HTU21D_Breakout

        Args:
            value (bytearray): data to be checked for validity
        Returns:
            True if valid, False otherwise
        """
        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]
        divsor = 0x988000

        for i in range(0, 16):
            if remainder & 1 << (23 - i):
                remainder ^= divsor
            divsor >>= 1

        if remainder == 0:
            return True
        else:
            return False

    def _issue_measurement(self, write_address):
        """Issue a measurement.
        Args:
            write_address (int): address to write to
        :return:
        """
        #self.i2c.start()
        self.i2c.writeto_mem(int(self.ADDRESS), int(write_address), '')
        #self.i2c.stop()
        time.sleep_ms(50)
        data = bytearray(3)
        self.i2c.readfrom_into(self.ADDRESS, data)
        if not self._crc_check(data):
            raise ValueError()
        raw = (data[0] << 8) + data[1]
        raw &= 0xFFFC
        return raw

    @property
    def temperature(self):
        """Calculate temperature"""
        raw = self._issue_measurement(self.ISSUE_TEMP_ADDRESS)
        return -46.85 + (175.72 * raw / 65536)

    @property
    def humidity(self):
        """Calculate humidity"""
        raw =  self._issue_measurement(self.ISSUE_HU_ADDRESS)
        return -6 + (125.0 * raw / 65536)

def UTC_DST_adj(): ### Daylight Savings Time accounted for: https://forum.micropython.org/viewtopic.php?f=2&t=4034
    inst = "CMU"
    now=time.time()
    if inst in ["NTU","IHEP"]:
        return(time.localtime(now+(3600*(8)))) ### No DST for China Standard Time +8
    elif inst == "TIFR":
        return(time.localtime(now+(3600*(5.5)))) ### No DST for India Standard Time +5:30
    else:
        dst_dates = [2025,9,2,2026,8,1,2027,14,7,2028,12,5,2029,11,4,2030,10,3]
        year = time.localtime()[0]
        dst_days = dst_dates.index(year) # get index of current year
        start_day = dst_dates[dst_days+1]   # get +1 from index for DST start day
        end_day = dst_dates[dst_days+2]   # get +2 from index for DST end day
        DST_start = time.mktime((year,3 ,start_day,1,0,0,0,0,0)) #Time of March change to DST
        DST_end = time.mktime((year,11,end_day,1,0,0,0,0,0)) #Time of November change to DST
        tz = 0
        if inst == "CMU":
            tz = -5   ### EST time zone
        elif inst == "TTU":
            tz = -6
        elif inst == "UCSB":
            tz = -8
        else:
            None
        if now < DST_start:               # we are before 2nd Sunday March
            return(time.localtime(now+(3600*tz)))
        elif now < DST_end:           # we are before 1st Sunday November
            return(time.localtime(now+(3600*(tz+1))))
        else:                            # we are after 1st Sunday November
            return(time.localtime(now+(3600*tz)))
  
def get_timestamp():
    lt=UTC_DST_adj()
    lt_str = []
    for item in lt:
        if item < 10:
            item = "0" + str(item)
        else:
            item = str(item)
        lt_str.append(item)
    local_time = lt_str[0]+'-'+lt_str[1]+'-'+lt_str[2]+' '+lt_str[3]+':'+lt_str[4]+':'+lt_str[5]
    return(local_time)


### Initialization ###

### Database login
db_host = 'cmsmac04.phys.cmu.edu'
db_user = 'shipper'
db_password = 'hgcal'
db_database = 'hgcdb_test'
log_location = 'main_clean_room'
    
htu = HTU21D(22,21) ### SDA and SCL pins

### Connect to wifi
ssid = 'CMU-DEVICE'
password = ""
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
while wlan.isconnected() == False:
    wlan.connect(ssid, password)
    print('Connecting to wifi...')
    time.sleep(5)
print("Connected to "+ ssid)
#print("MAC address is " + ubinascii.hexlify(wlan.config('mac')).decode())

### Sync with NTP
NTPerror = True
while NTPerror == True:
    try:
        ntptime.settime()
        NTPerror = False
    except:
        print("Syncing time with NTP...")
        NTPerror = True
        time.sleep(5)
print("Clock synced with NTP")    

#rtc = RTC() ### sync time 

### Connect to Local DB
print("Connecting to local DB...")
conn = micropg_lite.connect(host=db_host,
                        user=db_user,
                        password=db_password,
                        database=db_database)
print("Connected to local DB")
cur = conn.cursor()

while True:
    log_timestamp = get_timestamp()
    print(log_timestamp)
    rel_hum = str(round(htu.humidity,2))
    temp_c = str(round(htu.temperature,2))
    print('Humidity: ' + rel_hum)
    print('Temperature: ' + temp_c)
    print("*****************************")
    cur.execute("INSERT INTO temp_humidity (log_timestamp, log_location, temp_c, rel_hum) VALUES (%s, %s, %s, %s)", [log_timestamp, log_location, temp_c, rel_hum])
    conn.commit()
    time.sleep(5*60)   # log every 5 minutes
    
conn.close()