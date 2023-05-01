import pandas as pd
import os

# stats_path = 'results_archive/01-02-2-rene/stats'
videos = ["coldwater", "roppongi"]
path = ["statsColdwater", "statsRoppongi"]
# videos = ["uav-2"]
iteration = 0
for video_name in videos:
    dirName = "./profile-%s-aws/profile-separated/" % (video_name)
    os.makedirs(dirName, exist_ok=True)
    stats_path = path[iteration]
    duration = 20
    fluctuation_threshold = 0

    for segment in range(20):
    # the profile should be separated, need a verification system

        stats = pd.read_csv(stats_path)
        stats = stats[stats["video-name"].str.match('^results/%s-5-%d_aws' % (video_name, segment)) == True]
        # print(stats)

        stats_dds = stats[stats['mode'] == 'emulation']
        bandwidth_f1 = stats_dds.sort_values(by=['total-size'])
        bandwidth_f1['bandwidth'] = bandwidth_f1['total-size'] * (8/(1024 * (duration/20)))

        bandwidth_f1_remove_fluc = bandwidth_f1.copy()

        num_row = bandwidth_f1.shape[0]
        # print(bandwidth_f1)
        # exit()

        for i in range(1, num_row):
            j = i
            while (bandwidth_f1.iloc[j].F1 - bandwidth_f1.iloc[i-1].F1 <= -fluctuation_threshold):
                try:
                    bandwidth_f1_remove_fluc = bandwidth_f1_remove_fluc.drop(bandwidth_f1.iloc[j].name)
                except:
                    pass
                j += 1
                if (j >= num_row):
                    break

        # for i in range(0, num_row-1):
        #     currentConf = i
        #     if(bandwidth_f1.iloc[currentConf].bandwidth != bandwidth_f1.iloc[currentConf+1].bandwidth):
        #         pass
        #     else:
        #         bandwidth_f1_remove_fluc = bandwidth_f1_remove_fluc.drop(bandwidth_f1.iloc[currentConf].name)

        #     currentConf += 1
        bandwidth_f1_remove_fluc.to_csv('./profile-%s-aws/profile-separated/profile-%d.csv' %(video_name, segment))
    iteration += 1