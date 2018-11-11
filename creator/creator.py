#!/bin/python3.5
import os
import sys
import glob
import urllib2
import socket
from bs4 import BeautifulSoup as Soup

# set encoding to utf-8
reload(sys)
sys.setdefaultencoding('utf-8')

# unicable frequency lookup table
unicable = ["1210","1420","1680","2040","984","1020","1056","1092","1128","1164","1256","1292","1328","1364","1458","1494","1530","1566","1602","1638","1716","1752","1788","1824","1860","1896","1932","1968","2004","2076","2112","2148"]

# contract loopup table
gema = ["ARD Digital","ZDF Vision","ORF Digital"]
vgmedia = ["HD +", "ProSiebenSat.1", "Beta Digital"]
rtl = ["RTL"]

def download(url):
    response = urllib2.urlopen(url)
    html = response.read()
    return html

def read(filename):
    file = open(filename,'r').read()
    return file

def getmapping():
    # read mapping file
    mapping = Soup(read("mapping.xml"),"xml")
    grouping = []
    # loop over all satpos
    for satpos in mapping.find_all("satpos"):
        satposition = []
        # and over all groupings
        for satgroups in satpos.find_all("group"):
            satgroup = []
            # and over all adapters
            for adapters in satgroups.find_all("adapters"):
                # add hostname + adapter to this group
                satgroup.append([adapters.hostname.get_text(),adapters.adapternumber.get_text()])
            # add group number and hostname/adapters to this position
            satposition.append([satgroups.number.get_text(),satgroup])
        # add it to our grouping with position name and all groups/adapters
        grouping.append([satpos.position.get_text(),satposition])
    return grouping


def create_content(path,satpos,mapping,frq_td,fl_tr):
    ccount = 0
    acount = 0
    for transponder in frq_td:
        transponder_id = transponder[11].get_text(strip=True)
        print("Transponder " + transponder_id)
        # Example:
        # #Adapter: 0 Freq: 10714250 SRate: 22000000 Volt: 18 Mod: psk_8
        # #Unicable: 2 Freq: 1210000 ID: 0 Satnum: 0
        # 239.192.10.1:1234 1 5900 # Mainfranken HD
        #
        # Frequency first in kHz
        freq = frq_td[ccount][2].get_text().replace(".","")+"0"
        # Symbol rate in Sym/s
        srate = frq_td[ccount][8].get_text().split(' ')[0]+"000"
        # Voltage H/V
        if frq_td[ccount][3].get_text(strip=True) == 'H':
            volt = '18'
        else:
            volt = '13'
        # modulation
        if frq_td[ccount][7].get_text() == '8PSK':
            mod = 'psk_8'
        else:
            mod = 'qam_auto'

        # get hostname and adapter for this satpos
        for position in mapping:
            satcount = 0
            if satpos == position[0]:
                # sat[group][adapterposition][hostname|adapter]
                # go to next group if group is empty
                if (len(position[1][satcount][1]) == 0) and len(position[1]) != satcount:
                    satcount += 1
                sat = position[1][satcount]
                #p
                if len(sat[1]) != 0:
                    hostname = sat[1][0][0]
                    adapter = sat[1][0][1]
                    del sat[1][0]
                else:
                    raise Exception('Too much TID for this orbital position specified!')
                print(hostname)
                print(adapter)

        # throw error if oprital position not found in mapping
        try:
            hostname
        except NameError:
            raise Exception('Orbital Position not found in mapping!')


        # open cfg file write
        cfg_file = open(path + "/" + hostname + "-a"+ adapter + ".cfg", "w")

        # print first two lines
        cfg_file.write("#Adapter: " + adapter + " Freq: " + freq + " SRate: " + srate + " Volt: " + volt + " Mod: " + mod + "\n")
        cfg_file.write("#Unicable: 2 Freq: " + unicable[acount] + " ID: " + str(acount) + " Satnum: 0\n")

        # loop over all stations of this one frequency
        count = 1;
        for td in fl_tr[ccount]:
            # station name
            station = td[2].get_text(strip=True)
            # get pack for contract id check
            pack = td[5].get_text(strip=True)
            # check for right contract id
            if pack in gema:
                contractid = "2"
            elif pack in vgmedia:
                contractid = "3"
            elif pack in rtl:
                contractid = "4"
            else:
                contractid = "5"
            # get service id
            sid = td[7].get_text(strip=True)
            # get server id
            if socket.gethostname() == "dvb-1":
                server = "1"
            elif socket.gethostname() == "dvb-2":
                server = "2"
            else:
                server = ""

            # write file
            cfg_file.write("239.19" + contractid + "." + server + str(ccount) + "." + str(count) + ":1234 1 " + sid + " # " + station  + "\n")
            count += 1
        # close cfg file write
        cfg_file.close()
        ccount += 1
        if acount == 31:
            acount = 0
        else:
            acount += 1

def append_tid(frq_td,fl_tr,tid):
    # create new arrays as buffers
    bouquet_frq_td = []
    bouquet_fl_tr = []
    # check if all tids should be matched
    if len(tid) == 0:
        all_tid = True
    else:
        all_tid = False
    # loop over all in frq tables
    for transponder in frq_td:
        # get tid of entry
        transponder_id = transponder[11].get_text(strip=True)
        # add to bouquet if it is in our desired list
        if (transponder_id in tid) or (all_tid):
            index = frq_td.index(transponder)
            bouquet_frq_td.append(frq_td[int(index)])
            bouquet_fl_tr.append(fl_tr[int(index)])
            # check if it was an empty transponder and delete it if there is no corresponding table
            if len(fl_tr[int(index)]) == 1:
                del bouquet_frq_td[-1]
                del bouquet_fl_tr[-1]
    return bouquet_frq_td, bouquet_fl_tr

def main(path,satpos,tid):
    # delete old config files
    for item in os.listdir( path ):
        if item.endswith(".cfg"):
            os.remove( os.path.join( path, item ) )
    # read mapping file for servers
    mapping = getmapping()

    # test url
    url = 'https://en.kingofsat.net/pos-'+satpos+'.php'
    # get page and soup it
    #content = Soup(download(url),'html.parser')
    content = Soup(read('pos-19.2E.php'),'html.parser')

    # init frq settings array
    frq_td = []
    # loop over all frq tables and append result of tds to array
    for table in content.find_all("table", {"class": "frq"}):
        frq_td.append(table.find_all("td"))
    # delete first table with legend
    del frq_td[0]

    # init fl array
    fl_tr = []
    # loop over all fl tables and append result of trs to array
    for table in content.find_all("table", {"class": "fl"}):
        # init td array
        fl_td = []
        for tr in table.find_all("tr"):
            fl_td.append(tr.find_all("td"))
        fl_tr.append(fl_td)

    # get data to write files for (our tid tables)
    bouquet = append_tid(frq_td,fl_tr,tid)
    # print the bouquet to files
    create_content(path,satpos,mapping,bouquet[0],bouquet[1])

if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("Usage: creator.py path satpos tids")
        print("  path = folder to save config files to")
        print("  satpos = satpos in orbit e.g. '19.2E'")
        print("  tids = tids of transponders you want to generate, leave empty for all")
    elif len(sys.argv) == 3:
        print("Generating for all TID")
        tids = []
        main(sys.argv[1],sys.argv[2],tids)
    else:
        tids = []
        count = 3
        while count < len(sys.argv):
            tids.append(sys.argv[count])
            count += 1
        main(sys.argv[1],sys.argv[2],tids)
