## This program will be used as temporary resource allocator. First the program will accept the bandwidth dictionary for every frame. Assumption
import sys
import os
import math
import random
import numpy as np
import yaml
from flask import Flask, request, jsonify, send_file
import requests
import json
from threading import Thread
from dds_utils import get_average_bandwidth, get_best_configuration_bandwidth
import time
import threading


# Parameter setup
session = requests.Session()

# bandwidths = [[1550, 1850, 500, 800, 1700, 1100, 1400, 1250, 1850, 1250, 1700, 1850, 1250, 1700, 950, 1400, 800, 1550, 500, 1250],
# [500, 1100, 1850, 1400, 1700, 800, 500, 500, 1250, 1850, 1550, 1700, 1850, 1250, 650, 1550, 1550, 1100, 500, 1250],
# [650, 500, 1850, 800, 650, 650, 800, 800, 800, 500, 1850, 1700, 800, 1850, 1700, 800, 1100, 1250, 950, 950],
# [1850, 1550, 1550, 1400, 950, 1550, 1100, 1850, 500, 1700, 1400, 950, 1100, 500, 1100, 1100, 500, 1850, 800, 1400],
# [700, 950, 900, 950, 950, 600, 800, 900, 600, 800, 650, 600, 750, 900, 700, 900, 900, 700, 950, 650]]

# bandwidths = [[1550, 1850, 500, 800, 1700, 1100, 1400, 1250, 1850, 1250, 1700, 1850, 1250, 1700, 950, 1400, 800, 1550, 500, 1250]]
# bandwidths = [[i for j in range(20)] for i in range(400,401)]


# Bandwidth Generation
bandwidths = [[j for k in range(20)] for j in range(2500, 25001, 2500)]


def sendTo(hname, video_name, bandwidth_dict, app, mode):
    response = session.post("http://%s:5000?video_name=%s&app=%d&mode=%s" %(hname, video_name, app, mode), data=json.dumps(bandwidth_dict), timeout=150)
    return response

# default mode
for bandwidth in bandwidths:
    threads = []
    mode = "offline-profile" # fair-allocation, offline-profile
    method = "randomized" # increased, decreased, randomized (default)
    apps = len(sys.argv)-1
    total = 20
    videosName = sys.argv[1:]
    hosts = ["10.140.81.168","10.140.82.123","10.140.83.133"] # Available (the last client hasn't been set up yet)
    # "10.140.81.168" (client2), "10.140.82.123" (client1), "10.140.83.133" (test-cpu)

    # checking the availability

    # generate the bandwidth
    # bandwidth = [random.randrange(600, 1000, 50) for i in range(total)]
    # print(bandwidth)
    # os.system("echo %s >> bandwidthHistory.txt" %(list(bandwidth)))
    # bandwidth = np.array(bandwidth)
    host = [[], [], []]


    # share the bandwidth across the hosts
    # API calling will be called during the program running
    if(mode == "fair-allocation"):
        for i in range(total):
            for app in range(apps):
                host[app].append(bandwidth[i]//apps)
            # ^^ this should be fed to the clients when running the program ^^
    if(mode == "offline-profile"):
        for segment in range(total):
            hostTemp = [0 for i in range(apps)]

            # To obtain the size ratio
            for app in range(apps):
                hostTemp[app] = get_average_bandwidth("./workspace/profile-%s/profile-separated/profile-%d.csv" %(videosName[app],segment))
            total = sum(hostTemp)

            hostAcc = [0 for i in range(apps)]
            remaining = 0
            for app in range(apps):
                hostTemp[app] = int((hostTemp[app]/total) * bandwidth[segment])
            for app in range(apps):
                hostAcc[app], remainingTemp = get_best_configuration_bandwidth(hostTemp[app], "./workspace/profile-%s/profile-separated/profile-%d.csv" %(videosName[app],segment))
                hostTemp[app] -= int(remainingTemp)
                remaining += remainingTemp
            # Assume that there are only 2 hosts
            newAcc0, _ = get_best_configuration_bandwidth(hostTemp[0] + remaining, "./workspace/profile-%s/profile-separated/profile-%d.csv" %(videosName[0],segment))
            newAcc1, _ = get_best_configuration_bandwidth(hostTemp[1] + remaining, "./workspace/profile-%s/profile-separated/profile-%d.csv" %(videosName[1],segment))
            if(hostAcc[0] + newAcc1 > hostAcc[1] + newAcc0):
                hostTemp[1] += remaining
            elif(hostAcc[0] + newAcc1 < hostAcc[1] + newAcc0):
                hostTemp[0] += remaining
            else:
                hostTemp[0] += remaining//2
                hostTemp[1] += remaining//2
            # Assume that there are only 3 hosts

            # Updating process
            for app in range(apps):
                host[app].append(hostTemp[app])
    # should the bandwidth be exported? how? use the format Qingyang has made.

    # # Output format should look like this
    # # frame_id:
    # #   - 0
    # #   - 25
    # #   - 50
    # #   - 75
    # # bandwidth_limit:
    # #   - 10500
    # #   - 10500
    # #   - 10500
    # #   - 10500

    # this is for dynamic adaptive, there is an updating process
    # for segment in range(total):


    # as for now, the frame would be 5


    for app in range(apps):
        bandwidth_dict = {"frame_id":[], "bandwidth_limit":[]}
        for bandwidth in host[app]:
            bandwidth_dict["bandwidth_limit"].append(int(bandwidth))
        for i in range(0, 100, 5):
            bandwidth_dict["frame_id"].append(i)
        # export the dictionary as yaml
        # with open('bandwidthLimit-%s.yml' %(videosName[app]), 'w') as outfile:
        #     yaml.dump(bandwidth_dict, outfile, default_flow_style=False)
        hname=hosts[app]
        video_name = videosName[app]
        # response = session.post("http://%s:5000?video_name=%s" %(hname, video_name), data=json.dumps(bandwidth_dict))
        thread = Thread(target=sendTo, args=(hname, video_name, bandwidth_dict, app+1, mode))
        threads.append(thread)
    
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
    time.sleep(10)
    # running = True
    # while running:
    #     dead = 0
    #     for thread in threads:
    #         if(not thread.isAlive()):
    #             dead += 1
    #     if(dead == apps):
    #         running = False
    # print("done....")
        
    
    # for thread in threads:
    #     print(thread.is_alive())
    # for thread in threads:
    #     print(thread.is_done())
    # print(threading.current_thread())
    
    # time.sleep(100)
    # print(len(threads))
    # isRunning = True
    # while(isRunning):
    #     dead = 0
    #     for thread in threads:
    #         if not thread.is_alive():
    #             dead += 1
    #     if(dead == apps):
    #         isRunning = False
    # print("done...")
    # time.sleep(100)

    
        # sendTo(hname, video_name)
        # try:
        # create thread pool
        # # requests.get("http://127.0.0.1:8000/test/",timeout=0.0000000001)
        #     session.post("http://%s:5000?video_name=%s" %(hname, video_name), data=json.dumps(bandwidth_dict), timeout=0.0000000001)
        # except requests.exceptions.ReadTimeout: 
        #     continue
        
        

