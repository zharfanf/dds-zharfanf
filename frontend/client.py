import logging
import os
import shutil
import requests
import json
from dds_utils import (Results, read_results_dict, cleanup, Region,
                       compute_regions_size, extract_images_from_video,
                       merge_boxes_in_results, get_best_configuration)
import yaml


class Client:
    """The client of the DDS protocol
       sends images in low resolution and waits for
       further instructions from the server. And finally receives results
       Note: All frame ranges are half open ranges"""

    def __init__(self, hname, config, server_handle=None):
        if hname:
            self.hname = hname
            self.session = requests.Session()
        else:
            self.server = server_handle
        self.config = config

        self.logger = logging.getLogger("client")
        handler = logging.NullHandler()
        self.logger.addHandler(handler)

        self.logger.info(f"Client initialized")

    def analyze_video_mpeg(self, video_name, raw_images_path, enforce_iframes):

        # calculate the number of frames
        number_of_frames = len(
            [f for f in os.listdir(raw_images_path) if ".png" in f])

        final_results = Results()
        final_rpn_results = Results()
        total_size = 0
        for i in range(0, number_of_frames, self.config.batch_size):
            start_frame = i
            end_frame = min(number_of_frames, i + self.config.batch_size)

            batch_fnames = sorted([f"{str(idx).zfill(10)}.png"
                                   for idx in range(start_frame, end_frame)])

            req_regions = Results()

            # The entire frame is a region
            for fid in range(start_frame, end_frame):
                req_regions.append(
                    Region(fid, 0, 0, 1, 1, 1.0, 2,
                           self.config.low_resolution))

            # compute the video size of the batch
            batch_video_size, _ = compute_regions_size(
                req_regions, f"{video_name}-base-phase", raw_images_path,
                self.config.low_resolution, self.config.low_qp,
                enforce_iframes, True)
            self.logger.info(f"{batch_video_size / 1024}KB sent "
                             f"in base phase using {self.config.low_qp}QP")

            #TODO: what does this do?
            extract_images_from_video(f"{video_name}-base-phase-cropped",
                                      req_regions)
            
            # run DNN
            results, rpn_results = (
                self.server.perform_detection(
                    f"{video_name}-base-phase-cropped",
                    self.config.low_resolution, batch_fnames))

            self.logger.info(f"Detection {len(results)} regions for "
                             f"batch {start_frame} to {end_frame} with a "
                             f"total size of {batch_video_size / 1024}KB")

            # Add results to final_results (empty Result)
            final_results.combine_results(
                results, self.config.intersection_threshold)
            
            # Add rpn_results to final_rpn_results (empty Result)
            final_rpn_results.combine_results(
                rpn_results, self.config.intersection_threshold)

            # Remove encoded video manually
            shutil.rmtree(f"{video_name}-base-phase-cropped")
            total_size += batch_video_size

        # Remove regions with confid < 0.3
        # 
        final_results = merge_boxes_in_results(
            final_results.regions_dict, 0.3, 0.3)
        final_results.fill_gaps(number_of_frames)

        # Add RPN regions
        final_results.combine_results(
            final_rpn_results, self.config.intersection_threshold)

        final_results.write(video_name)

        return final_results, [total_size, 0]

    def analyze_video_emulate(self, video_name, high_images_path,
                              enforce_iframes, low_results_path=None,
                              debug_mode=False, adaptive_mode=False, bandwidth_limit_dict=None, aws_mode=False):
        final_results = Results()
        low_phase_results = Results()
        high_phase_results = Results()

        number_of_frames = len(
            [x for x in os.listdir(high_images_path) if "png" in x])

        profile_no = None
        bandwidth_limit = None
        if adaptive_mode:
            profile_no = 0

        low_results_dict = None
        if low_results_path:
            low_results_dict = read_results_dict(low_results_path)

        total_size = [0, 0]
        total_regions_count = 0
        for i in range(0, number_of_frames, self.config.batch_size):
            start_fid = i
            end_fid = min(number_of_frames, i + self.config.batch_size)

            if (adaptive_mode):
                # If reach the next segment
                if (profile_no < len(bandwidth_limit_dict['frame_id'])):
                    if (start_fid >= bandwidth_limit_dict['frame_id'][profile_no]):
                        bandwidth_limit = bandwidth_limit_dict['bandwidth_limit'][profile_no]
                        try:
                            low_res_best, low_qp_best, high_res_best, high_qp_best = get_best_configuration(bandwidth_limit, f'{self.config.profile_folder_path}/{self.config.profile_folder_name}/profile-{profile_no}.csv')
                        except:
                            raise RuntimeError(f"Cannot get the best configuration at segment {profile_no} after frame {start_fid} with a bandwidth limit of {bandwidth_limit}. Aborting...")
                    
                        # here calling the api to limit the bandwidth
                        
                        self.config.low_qp = low_qp_best
                        self.config.low_resolution = low_res_best
                        self.config.high_qp = high_qp_best
                        self.config.high_resolution = high_res_best

                        video_name = (f"results/{self.config.real_video_name}_dds_{self.config.low_resolution}_{self.config.high_resolution}_{self.config.low_qp}_{self.config.high_qp}_"
                            f"{self.config.rpn_enlarge_ratio}_twosides_batch_{self.config.batch_size}_"
                            f"{self.config.prune_score}_{self.config.objfilter_iou}_{self.config.size_obj}")
                        
                        low_results_path = f'results/{self.config.real_video_name}_mpeg_{self.config.low_resolution}_{self.config.low_qp}'
                        low_results_dict = read_results_dict(low_results_path)

                        profile_no += 1

            self.logger.info(f"Processing batch from {start_fid} to {end_fid} with parameters {self.config.low_resolution}, {self.config.low_qp}, {self.config.high_resolution}, {self.config.high_qp}")           

            # Encode frames in batch and get size
            # Make temporary frames to downsize complete frames
            base_req_regions = Results()
            for fid in range(start_fid, end_fid):
                base_req_regions.append(
                    Region(fid, 0, 0, 1, 1, 1.0, 2,
                           self.config.high_resolution))
            encoded_batch_video_size, batch_pixel_size = compute_regions_size(
                base_req_regions, f"{video_name}-base-phase", high_images_path,
                self.config.low_resolution, self.config.low_qp,
                enforce_iframes, True)
            self.logger.info(f"Sent {encoded_batch_video_size / 1024} "
                             f"in base phase")
            total_size[0] += encoded_batch_video_size

            # Low resolution phase
            low_images_path = f"{video_name}-base-phase-cropped"
            r1, req_regions = self.server.simulate_low_query(
                start_fid, end_fid, low_images_path, low_results_dict, False,
                self.config.rpn_enlarge_ratio)
            total_regions_count += len(req_regions)

            low_phase_results.combine_results(
                r1, self.config.intersection_threshold)
            final_results.combine_results(
                r1, self.config.intersection_threshold)

            # High resolution phase
            if not aws_mode and len(req_regions) > 0:
                # Crop, compress and get size
                regions_size, _ = compute_regions_size(
                    req_regions, video_name, high_images_path,
                    self.config.high_resolution, self.config.high_qp,
                    enforce_iframes, True)
                self.logger.info(f"Sent {len(req_regions)} regions which have "
                                 f"{regions_size / 1024}KB in second phase "
                                 f"using {self.config.high_qp}")
                total_size[1] += regions_size

                # High resolution phase every three filter
                r2 = self.server.emulate_high_query(
                    video_name, low_images_path, req_regions)
                self.logger.info(f"Got {len(r2)} results in second phase "
                                 f"of batch")

                high_phase_results.combine_results(
                    r2, self.config.intersection_threshold)
                final_results.combine_results(
                    r2, self.config.intersection_threshold)

            # Cleanup for the next batch
            cleanup(video_name, debug_mode, start_fid, end_fid)

        self.logger.info(f"Got {len(low_phase_results)} unique results "
                         f"in base phase")
        self.logger.info(f"Got {len(high_phase_results)} positive "
                         f"identifications out of {total_regions_count} "
                         f"requests in second phase")

        # Fill gaps in results
        final_results.fill_gaps(number_of_frames)

        # Write results
        if (adaptive_mode):
            video_name = (f"results/{self.config.real_video_name}_dds_adaptive_{self.config.adaptive_test_display}_"
                            f"{self.config.rpn_enlarge_ratio}_twosides_batch_{self.config.batch_size}_"
                            f"{self.config.prune_score}_{self.config.objfilter_iou}_{self.config.size_obj}")

        final_results.write(f"{video_name}")

        self.logger.info(f"Writing results for {video_name}")
        self.logger.info(f"{len(final_results)} objects detected "
                         f"and {total_size[1]} total size "
                         f"of regions sent in high resolution")

        rdict = read_results_dict(f"{video_name}")
        final_results = merge_boxes_in_results(rdict, 0.3, 0.3)

        final_results.fill_gaps(number_of_frames)
        final_results.write(f"{video_name}")
        return final_results, total_size

    def init_server(self, nframes):
        self.config['nframes'] = nframes
        response = self.session.post(
            "http://" + self.hname + "/init", data=yaml.dump(self.config))
        if response.status_code != 200:
            self.logger.fatal("Could not initialize server")
            # Need to add exception handling
            exit()

    def get_first_phase_results(self, vid_name):
        encoded_vid_path = os.path.join(
            vid_name + "-base-phase-cropped", "temp.mp4")
        video_to_send = {"media": open(encoded_vid_path, "rb")}
        headers = self.session.headers
        endIdx = vid_name.find("_dds")
        headers["vid_name"] = vid_name[8:endIdx]
        response = self.session.post(
            "http://" + self.hname + "/low", files=video_to_send, headers=headers)
        response_json = json.loads(response.text)

        results = Results()
        for region in response_json["results"]:
            results.append(Region.convert_from_server_response(
                region, self.config.low_resolution, "low-res"))
        rpn = Results()
        for region in response_json["req_regions"]:
            rpn.append(Region.convert_from_server_response(
                region, self.config.low_resolution, "low-res"))

        return results, rpn

    def get_second_phase_results(self, vid_name):
        encoded_vid_path = os.path.join(vid_name + "-cropped", "temp.mp4")
        video_to_send = {"media": open(encoded_vid_path, "rb")}
        headers = self.session.headers
        endIdx = vid_name.find("_dds")
        headers["vid_name"] = vid_name[8:endIdx]
        response = self.session.post(
            "http://" + self.hname + "/high", files=video_to_send, headers=headers)
        response_json = json.loads(response.text)

        results = Results()
        for region in response_json["results"]:
            results.append(Region.convert_from_server_response(
                region, self.config.high_resolution, "high-res"))

        return results

    def analyze_video(
            self, vid_name, raw_images, config, enforce_iframes, low_results_path=None, adaptive_mode=False, bandwidth_limit_dict=None, aws_mode=False):
        final_results = Results()
        all_required_regions = Results()
        low_phase_size = 0
        high_phase_size = 0
        nframes = sum(map(lambda e: "png" in e, os.listdir(raw_images)))
        profile_no = None
        bandwidth_limit = None
        if adaptive_mode:
            profile_no = 0

        low_results_dict = None
        if low_results_path:
            low_results_dict = read_results_dict(low_results_path)

        self.init_server(nframes)

        for i in range(0, nframes, self.config.batch_size):
            start_frame = i
            end_frame = min(nframes, i + self.config.batch_size)
            if (adaptive_mode):
                # If reach the next segment
                if (profile_no < len(bandwidth_limit_dict['frame_id'])):
                    if (start_frame >= bandwidth_limit_dict['frame_id'][profile_no]):
                        bandwidth_limit = bandwidth_limit_dict['bandwidth_limit'][profile_no]
                        try:
                            low_res_best, low_qp_best, high_res_best, high_qp_best = get_best_configuration(bandwidth_limit, f'{self.config.profile_folder_path}/{self.config.profile_folder_name}/profile-{profile_no}.csv')
                        except:
                            raise RuntimeError(f"Cannot get the best configuration at segment {profile_no} after frame {start_fid} with a bandwidth limit of {bandwidth_limit}. Aborting...")
                    
                        # here calling the api to limit the bandwidth
                        os.system("curl \"http://10.140.83.205:5001?bandwidth=%skbit&ipAddress=\"" %(bandwidth_limit))
                        self.config.low_qp = low_qp_best
                        self.config.low_resolution = low_res_best
                        self.config.high_qp = high_qp_best
                        self.config.high_resolution = high_res_best

                        video_name = (f"results/{self.config.real_video_name}_dds_{self.config.low_resolution}_{self.config.high_resolution}_{self.config.low_qp}_{self.config.high_qp}_"
                            f"{self.config.rpn_enlarge_ratio}_twosides_batch_{self.config.batch_size}_"
                            f"{self.config.prune_score}_{self.config.objfilter_iou}_{self.config.size_obj}")
                        
                        low_results_path = f'results/{self.config.real_video_name}_mpeg_{self.config.low_resolution}_{self.config.low_qp}'
                        low_results_dict = read_results_dict(low_results_path)

                        profile_no += 1

            self.logger.info(f"Processing batch from {start_frame} to {end_frame} with parameters {self.config.low_resolution}, {self.config.low_qp}, {self.config.high_resolution}, {self.config.high_qp}")           

            # self.logger.info(f"Processing frames {start_frame} to {end_frame}")

            # First iteration
            req_regions = Results()
            for fid in range(start_frame, end_frame):
                req_regions.append(Region(
                    fid, 0, 0, 1, 1, 1.0, 2, self.config.low_resolution))
            batch_video_size, _ = compute_regions_size(
                req_regions, f"{vid_name}-base-phase", raw_images,
                self.config.low_resolution, self.config.low_qp,
                enforce_iframes, True)
            low_phase_size += batch_video_size
            self.logger.info(f"{batch_video_size / 1024}KB sent in base phase."
                             f"Using QP {self.config.low_qp} and "
                             f"Resolution {self.config.low_resolution}.")
            results, rpn_regions = self.get_first_phase_results(vid_name)
            final_results.combine_results(
                results, self.config.intersection_threshold)
            all_required_regions.combine_results(
                rpn_regions, self.config.intersection_threshold)


            # If AWStream mode is True, the following code block won't run
            # Start of AWStream block
            # Second Iteration
            if not aws_mode and len(rpn_regions) > 0:
                batch_video_size, _ = compute_regions_size(
                    rpn_regions, vid_name, raw_images,
                    self.config.high_resolution, self.config.high_qp,
                    enforce_iframes, True)
                high_phase_size += batch_video_size
                self.logger.info(f"{batch_video_size / 1024}KB sent in second "
                                 f"phase. Using QP {self.config.high_qp} and "
                                 f"Resolution {self.config.high_resolution}.")
                results = self.get_second_phase_results(vid_name)
                final_results.combine_results(
                    results, self.config.intersection_threshold)

            # Cleanup for the next batch
            cleanup(vid_name, False, start_frame, end_frame)

            # End of AWStream

        self.logger.info(f"Merging results")
        final_results = merge_boxes_in_results(
            final_results.regions_dict, 0.3, 0.3)
        self.logger.info(f"Writing results for {vid_name}")
        final_results.fill_gaps(nframes)

        final_results.combine_results(
            all_required_regions, self.config.intersection_threshold)
        
        if (adaptive_mode):
            video_name = (f"results/{self.config.real_video_name}_dds_adaptive_{self.config.adaptive_test_display}_"
                            f"{self.config.rpn_enlarge_ratio}_twosides_batch_{self.config.batch_size}_"
                            f"{self.config.prune_score}_{self.config.objfilter_iou}_{self.config.size_obj}")

        final_results.write(f"{vid_name}")

        return final_results, (low_phase_size, high_phase_size)
