import numpy as np
import cv2
import time
import random
import collections
from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import dataset_utils
from PIL import Image
from matplotlib import cm
import os


class ObstacleDetector(object):
    '''
    Requires an EdgeTPU for this part to work

    This part will run a EdgeTPU optimized model to run object detection to detect obstacles.
    We are just using a pre-trained model (MobileNet V2 SSD) provided by Google.
    '''

    def __init__(self, min_score, show_bounding_box, debug=False):

        #MODEL_URL = "https://github.com/google-coral/edgetpu/raw/master/test_data/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
        #LABEL_URL = "https://dl.google.com/coral/canned_models/coco_labels.txt"

        MODEL_FILE_NAME = "edgetpu/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
        LABEL_FILE_NAME = "edgetpu/coco_labels.txt"

        self.last_5_scores = collections.deque(np.zeros(5), maxlen=5)
        self.engine = DetectionEngine(MODEL_FILE_NAME)
        self.labels = dataset_utils.read_label_file(LABEL_FILE_NAME)

        self.min_score = min_score
        self.show_bounding_box = show_bounding_box
        self.debug = debug

    def convertImageArrayToPILImage(self, img_arr):
        img = Image.fromarray(img_arr.astype('uint8'), 'RGB')

        return img

    '''
    Return an object if there is a traffic light in the frame
    '''
    def detect_obstacle (self, img_arr):
        img = self.convertImageArrayToPILImage(img_arr)

        ans = self.engine.detect_with_image(img,
                                          threshold=self.min_score,
                                          keep_aspect_ratio=True,
                                          relative_coord=False,
                                          top_k=3)
        max_score = 0
        obstacle_obj = None
        if ans:
            for obj in ans:
                    if (obj.score > max_score):
                        obstacle_obj = obj
                        max_score = obj.score

        if obstacle_obj and self.debug:
            print(f"object {obstacle_obj.label_id} detected, score = {obstacle_obj.score}")

        # if traffic_light_obj:
        #     self.last_5_scores.append(traffic_light_obj.score)
        #     sum_of_last_5_score = sum(list(self.last_5_scores))
        #     # print("sum of last 5 score = ", sum_of_last_5_score)

        #     if sum_of_last_5_score > self.LAST_5_SCORE_THRESHOLD:
        #         return traffic_light_obj
        #     else:
        #         print("Not reaching last 5 score threshold")
        #         return None
        # else:
        #     self.last_5_scores.append(0)
        #     return None

        return obstacle_obj

    def draw_bounding_box(self, obstacle_obj, img_arr):
        xmargin = (obstacle_obj.bounding_box[1][0] - obstacle_obj.bounding_box[0][0]) *0.1

        obstacle_obj.bounding_box[0][0] = obstacle_obj.bounding_box[0][0] + xmargin
        obstacle_obj.bounding_box[1][0] = obstacle_obj.bounding_box[1][0] - xmargin

        ymargin = (obstacle_obj.bounding_box[1][1] - obstacle_obj.bounding_box[0][1]) *0.05

        obstacle_obj.bounding_box[0][1] = obstacle_obj.bounding_box[0][1] + ymargin
        obstacle_obj.bounding_box[1][1] = obstacle_obj.bounding_box[1][1] - ymargin

        cv2.rectangle(img_arr, tuple(obstacle_obj.bounding_box[0].astype(int)),
                        tuple(obstacle_obj.bounding_box[1].astype(int)), (0, 255, 0), 2)

    def run(self, img_arr):
        if img_arr is None:
            return img_arr

        # Detect traffic light object
        obstacle_obj = self.detect_obstacle(img_arr)

        label="--"
        coords="--"
        if obstacle_obj:
            label = f"{self.labels[obstacle_obj.label_id] ({obstacle_obj.score})}"
            coords = f"{obstacle_obj.bounding_box[0][0]},{obstacle_obj.bounding_box[1][0]},{obstacle_obj.bounding_box[0][1]},{obstacle_obj.bounding_box[1][1]}"
            if self.show_bounding_box and obstacle_obj != None:
                self.draw_bounding_box(obstacle_obj, img_arr)
            
        return img_arr, label, coords, 
