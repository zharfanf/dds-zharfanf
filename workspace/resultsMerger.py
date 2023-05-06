import os
import csv

# with open('./results/uav-1-0_gt') as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=',')
#     for row in csv_reader:
#         print(row)

videos = ["jakarta", "highway"]
modes = ["dds", "aws"]

low_qp = [30, 32, 34]
low_res = ["0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8"]
high_qp = [24, 26, 28]
high_res = ["0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"]

# for video in videos:
#     for mode in modes:
#         for hqp in high_qp:
#             for hres in high_res:
#                 for qp in low_qp:
#                     for res in low_res:
#                         toBeWritten = []
#                         skip = False
#                         for i in range(20):
#                             fileName = './results/%s-5-%d_%s_%s_%s_%d_%d_0.0_twosides_batch_5_0.5_0.8_0.4' %(video, i, mode, res, hres, qp, hqp)
#                             try:
#                                 with open('./results/%s-5-%d_%s_%s_%s_%d_%d_0.0_twosides_batch_5_0.5_0.8_0.4' %(video, i, mode, res, hres, qp, hqp)) as csv_file:
#                                     csv_reader = csv.reader(csv_file, delimiter=',')
#                                     rows = list(csv_reader)
#                                     for j in range(len(rows)):
#                                         if i != 0:
#                                             rows[j][0] = str(int(rows[j][0]) + 5*i)
#                                         toBeWritten.append(rows[j])
#                             except FileNotFoundError:
#                                 skip = True
#                                 pass
                            
#                         if(not(skip)):
#                             with open('./results/%s_%s_%s_%s_%d_%d_0.0_twosides_batch_5_0.5_0.8_0.4' %(video, mode, res, hres, qp, hqp), mode='w') as csv_file:
#                                 csv_writer = csv.writer(csv_file, delimiter=',')
#                                 for row in toBeWritten:
#                                     csv_writer.writerow(row)
    
# for video in videos:
#     toBeWritten = []
#     videoC = video.capitalize()
#     for i in range(20):
#         with open('./results%s/%s-5-%d_gt' %(videoC, video, i)) as csv_file:
#             csv_reader = csv.reader(csv_file, delimiter=',')
#             rows = list(csv_reader)
#             for j in range(len(rows)):
#                 if i != 0:
#                     rows[j][0] = str(int(rows[j][0]) + 5*i)
#                 toBeWritten.append(rows[j])
                
            
#     with open('./results%s/%s_gt' % (videoC, video), mode='w') as csv_file:
#         csv_writer = csv.writer(csv_file, delimiter=',')
#         for row in toBeWritten:
#             # print(row)
#             csv_writer.writerow(row)

for video in videos:
    for qp in low_qp:
        for res in low_res:
            toBeWritten = []
            for i in range(20):
                if video != "coldwater" or video != "roppongi":
                    videoC = ""
                else:
                    videoC = video.capitalize()
                with open('./results%s/%s-5-%d_mpeg_%s_%d' %(videoC, video, i, res, qp)) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    rows = list(csv_reader)
                    for j in range(len(rows)):
                        if i != 0:
                            rows[j][0] = str(int(rows[j][0]) + 5*i)
                        toBeWritten.append(rows[j])

            with open('./results%s/%s_mpeg_%s_%d' % (videoC, video, res, qp), mode='w') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',')
                for row in toBeWritten:
                    # print(row)
                    csv_writer.writerow(row)