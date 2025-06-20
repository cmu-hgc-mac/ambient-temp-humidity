from machine import I2C, Pin
from HTU21DF import HTU21D
import time, network, micropg_lite, ntptime
#import ubinascii

def wifi_connect(ssid, password):
    while wlan.isconnected() == False:
        wlan.connect(ssid, password)
        print('Connecting to wifi...')
        time.sleep(5)
    print("Connected to "+ ssid)
    return(None)
        
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
#    lt = time.localtime(time.time())
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
db_database = 'hgcdb'
log_location = 'main_clean_room'
    
htu = HTU21D(22,21) ### SDA and SCL pins

### Connect to wifi
ssid = 'CMU-DEVICE'
password = ""
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wifi_connect(ssid, password)

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

def log_to_DB(ssid, password, db_host, db_user, db_password, db_database):
    start_time = time.ticks_ms()
    wifi_connect(ssid, password)
    try:
        print("Connecting to local DB...")
        conn = micropg_lite.connect(host=db_host,
                        user=db_user,
                        password=db_password,
                        database=db_database)
        print("Connected to local DB")
    except OSError:
        print("Unable to connect to DB, try again in 1 minute")
        return(60)
    cur = conn.cursor()
    log_timestamp = get_timestamp()
    print(log_timestamp)
    rel_hum = str(round(htu.humidity,2))
    temp_c = str(round(htu.temperature,2))
    print('Humidity: ' + rel_hum)
    print('Temperature: ' + temp_c)
    print("*****************************")
    cur.execute("INSERT INTO temp_humidity (log_timestamp, log_location, temp_c, rel_hum) VALUES (%s, %s, %s, %s)", [log_timestamp, log_location, temp_c, rel_hum])
    conn.commit()
    conn.close()
    return(600-((time.ticks_ms()-start_time)/1000))

while True:
    log_time = log_to_DB(ssid, password, db_host, db_user, db_password, db_database)
    time.sleep(log_time)
    
