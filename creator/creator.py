#!/bin/python3.5
import os
import sys
import glob
import urllib2
from bs4 import BeautifulSoup as Soup

def download(url):
    response = urllib2.urlopen(url)
    html = response.read()
    return html

def read(filename):
    file = open(filename,'r').read()
    return file

def create_content(frq_td,fl_tr):
    ccount = 0
    for transponder in frq_td:
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
        # print first two lines
        print("#Adapter: $ Freq: "+freq+" SRate: "+srate+" Volt: "+volt+" Mod: "+mod)
        print("#Unicable: $ Freq: $ ID: $ Satnum: 0")

        # loop over all stations of this one frequency
        count = 1;
        for td in fl_tr[ccount]:
            station = td[2].get_text(strip=True)
            sid = td[7].get_text(strip=True)
            print("239.19$.$$." + str(count) + ":1234 1 " + sid + " # " + station )
            count += 1
        ccount =+1

def append_tid(frq_td,fl_tr,tid):
    bouquet_frq_td = []
    bouquet_fl_tr = []
    for transponder in frq_td:
        transponder_id = transponder[11].get_text(strip=True)
        if transponder_id in tid:
            index = frq_td.index(transponder)
            bouquet_frq_td.append(frq_td[int(index)])
            bouquet_fl_tr.append(fl_tr[int(index)])
    return bouquet_frq_td, bouquet_fl_tr

def main(path):
    # test url
    url = 'https://en.kingofsat.net/tv-19.2E.php'
    # get page and soup it
    #content = Soup(download(url),'html.parser')
    content = Soup(read('tv-19.2E.php'),'html.parser')
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
    tid = ['1049','1050']
    bouquet = append_tid(frq_td,fl_tr,tid)
    create_content(bouquet[0],bouquet[1])

if __name__ == "__main__":
    if len(sys.argv)==2:
        main(sys.argv[1])
    else:
        main('.')
