#!/usr/bin/python
from BeautifulSoup import BeautifulSoup,NavigableString
import re
import urllib2
import sys
import pyrowl
import argparse
import time
try:
    import yaml
except ImportError:
    print "!"*50
    print "YAML extention is not installed."
    sys.exit(1)


if sys.version_info < (2, 7):
    raise "must use python 2.7 or greater"



def load_config_yaml(config_filename):
    """ Load the config file in YAML format"""
    yaml_conf = yaml.load(open(config_filename).read())
    return yaml_conf




def time_to_next_bus(url):
    headers = { 'User-Agent' : 'Mobile Safari 1.1.3 (iPhone; U; CPU like Mac OS X; en)' }
    req = urllib2.Request(url, '', headers)
    response = urllib2.urlopen(req).read()
    soup = BeautifulSoup(response)
    text_div = soup.findAll("div",dir="rtl")
    text = eval(text_div[0].contents[0].string.__repr__())
    # try the two numbers RE 
    re_res = re.search("(\d+)\s.*\s(\d+).*$",text)
    # else try the one number RE (1 or 2 minutes left)
    if re_res == None:
        re_res = re.search("(\d+)\s.*",text)
    re_res_groups = re_res.groups()
    line_number = int(re_res_groups[0])
    if len (re_res_groups) == 1:
        if u'\u05d0\u05d7\u05ea' in text:
            time_to = 1
        else:
            time_to = 2
    else:
        time_to = int(re_res_groups[1])
    print "Next %d bus will be in %d minutes" %(line_number,time_to)
    return line_number,time_to



def send_messege(p,bus_line,in_time,url,prowl_priority,messege = ""):
    print "Sending messege"
    p.push("BusProwl", "Monitoring %s" %bus_line , "Arrives in %s minutes"%in_time,bus_station_url, prowl_priority)
    
    

if __name__ == '__main__':
    # Get config from YAML
    config = load_config_yaml("config.yaml")
    api_key = config["prowl_api_key"]
    bus_stations = config["bus_stations"]
    
    # Arguments configuration
    parser = argparse.ArgumentParser(description='Bus monitoring using prowl and the Metropolin "on time" ')
    parser.add_argument("-b","--busstop",choices = bus_stations.keys(),default = bus_stations.keys()[0],help = "Bus station name")

    args = parser.parse_args()
    
    bus_station_url = bus_stations[args.busstop]
    bus_station_name = args.busstop
    normal_priority = config["normal_priority"]
    high_priority = config["high_priority"]
    minute_threshold = config["minute_threshold"]
    check_interval = config["check_interval"]

    # Add API key to the prowl object
    p = pyrowl.Pyrowl(api_key)

    # First time check
    line_num,time_to = time_to_next_bus(bus_station_url)
    send_messege(p,line_num,time_to,bus_station_url,normal_priority)
    last_time = time_to
    
    # if time_to < threshold, wait for the next bus also
    if time_to < minute_threshold:
        print "Skipping this bus"
        while time_to < minute_threshold:
            time.sleep(check_interval)
            line_num,time_to = time_to_next_bus(bus_station_url)
            if time_to < last_time:
                send_messege(p,line_num,time_to,bus_station_url,normal_priority)
                last_time = time_to
    
    # main bus wait loop
    print "Entering bus wait loop"
    while time_to != 0:
        time.sleep(check_interval)
        line_num,time_to = time_to_next_bus(bus_station_url)
        if time_to < last_time:
            if time_to <=3 :
                send_messege(p,line_num,time_to,bus_station_url,high_priority)
            else:
                send_messege(p,line_num,time_to,bus_station_url,normal_priority)
            last_time = time_to
    
    

