import os
import csv

# with open('./results/uav-1-0_gt') as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=',')
#     for row in csv_reader:
#         print(row)

videos = ["coldwater"]

low_qp = [30, 32, 34, 36, 38]
low_res = ["0.1","0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8"]
high_qp = [24, 26, 28, 30, 32]
high_res = ["0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"]

for video in videos:
    for hqp in high_qp:
        for hres in high_res:
            for qp in low_qp:
                for res in low_res:
                    toBeWritten = []
                    skip = False
                    for i in range(20):
                        fileName = './results/%s-5-%d_aws_%s_%s_%d_%d_0.0_twosides_batch_5_0.5_0.8_0.4' %(video, i, res, hres, qp, hqp)
                        try:
                            with open('./results/%s-5-%d_aws_%s_%s_%d_%d_0.0_twosides_batch_5_0.5_0.8_0.4' %(video, i, res, hres, qp, hqp)) as csv_file:
                                csv_reader = csv.reader(csv_file, delimiter=',')
                                rows = list(csv_reader)
                                for j in range(len(rows)):
                                    if i != 0:
                                        rows[j][0] = str(int(rows[j][0]) + 5*i)
                                    toBeWritten.append(rows[j])
                        except FileNotFoundError:
                            skip = True
                            pass
                        
                    if(not(skip)):
                        with open('./results/%s_aws_%s_%s_%d_%d_0.0_twosides_batch_5_0.5_0.8_0.4' %(video, res, hres, qp, hqp), mode='w') as csv_file:
                            csv_writer = csv.writer(csv_file, delimiter=',')
                            for row in toBeWritten:
                                csv_writer.writerow(row)
    # toBeWritten = []
    # for i in range(4):
    #     with open('./results/uav-1-%d_gt' %(i)) as csv_file:
    #         csv_reader = csv.reader(csv_file, delimiter=',')
    #         rows = list(csv_reader)
    #         for j in range(len(rows)):
    #             if i != 0:
    #                 rows[j][0] = str(int(rows[j][0]) + 25*i)
    #             toBeWritten.append(rows[j])
                
            
    # with open('./results/uav-1_gt', mode='w') as csv_file:
    #     csv_writer = csv.writer(csv_file, delimiter=',')
    #     for row in toBeWritten:
    #         # print(row)
    #         csv_writer.writerow(row)