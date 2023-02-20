import pandas as pd
import os

# stats_path = 'results_archive/01-02-2-rene/stats'
videos = ["rene", "uav-1", "uav-2", "thailand-1st-half"]
for video_name in videos:
    dirName = "./profile-%s/profile-separated/" % (video_name)
    os.makedirs(dirName)
    stats_path = 'stats'
    duration = 4
    fluctuation_threshold = 0

    for segment in range(20):
    # the profile should be separated, need a verification system

        stats = pd.read_csv(stats_path)
        stats = stats[stats["video-name"].str.match('^results/%s-%d_dds' % (video_name, segment)) == True]
        # print(stats)

        stats_dds = stats[stats['mode'] == 'emulation']
        bandwidth_f1 = stats_dds.sort_values(by=['total-size'])
        bandwidth_f1['bandwidth'] = bandwidth_f1['total-size'] * 8 / 1024 / duration

        bandwidth_f1_remove_fluc = bandwidth_f1.copy()

        num_row = bandwidth_f1.shape[0]

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

        bandwidth_f1_remove_fluc.to_csv('./profile-%s/profile-separated/profile-%d.csv' %(video_name, segment))