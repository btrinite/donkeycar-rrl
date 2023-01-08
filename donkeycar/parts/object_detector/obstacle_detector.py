import numpy as np
import cv2
import time
import random
import collections
from pycoral.adapters import classify
from pycoral.adapters import detect
from pycoral.adapters import common
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from PIL import Image
from matplotlib import cm
import os
import logging
from donkeycar.utilities.logger import init_special_logger

lanelogger = init_special_logger ("Obstacle")
lanelogger.setLevel(logging.INFO)


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

        self.labels = read_label_file(LABEL_FILE_NAME)

        self.interpreter = make_interpreter(MODEL_FILE_NAME)
        self.interpreter.allocate_tensors()

        lanelogger.info(f"Obstacle detector model loaded.")
        if common.input_details(self.interpreter, 'dtype') != np.uint8:
            raise ValueError('Only support uint8 input type.')

        self.size = common.input_size(self.interpreter)

        self.last_5_scores = collections.deque(np.zeros(5), maxlen=5)

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
        _, scale = common.set_resized_input(
            self.interpreter, img.size, lambda size: img.resize(size, Image.ANTIALIAS))
        self.interpreter.invoke()
        objects = detect.get_objects(self.interpreter, score_threshold=self.min_score, image_scale=scale)

        max_score = 0
        obstacle_obj = None
        if objects:
            for obj in objects:
                    if (obj.score > max_score):
                        obstacle_obj = obj
                        max_score = obj.score

        if obstacle_obj and self.debug:
            print(f"object {self.labels.get(obstacle_obj.id, obstacle_obj.id)} detected, score = {obstacle_obj.score}")

        return obstacle_obj

    def draw_bounding_box(self, obstacle_obj, img_arr):
        xmargin = (obstacle_obj.bbox.xmax - obstacle_obj.bbox.xmin) *0.1

        obstacle_obj.bbox.xmin = obstacle_obj.bbox.xmin + xmargin
        obstacle_obj.bbox.xmax = obstacle_obj.bbox.xmax - xmargin

        ymargin = (obstacle_obj.bbox.ymax - obstacle_obj.bbox.ymin) *0.05

        obstacle_obj.bbox.ymin = obstacle_obj.bbox.ymin + ymargin
        obstacle_obj.bbox.ymax = obstacle_obj.bbox.ymax - ymargin

        cv2.rectangle(img_arr, (obstacle_obj.bbox.xmin, obstacle_obj.bbox.xmax),
                        (obstacle_obj.bbox.ymin, obstacle_obj.bbox.ymax), (0, 255, 0), 2)

    def run(self, img_arr):
        if img_arr is None:
            return img_arr

        # Detect traffic light object
        obstacle_obj = self.detect_obstacle(img_arr)

        label="--"
        coords="--"
        if obstacle_obj:
            label = f"{self.labels.get(obstacle_obj.id, obstacle_obj.id)} ({obstacle_obj.score})"
            coords = f"{obstacle_obj.bbox.xmin},{obstacle_obj.bbox.ymin},{obstacle_obj.bbox.xmax},{obstacle_obj.bbox.ymax}"
            if self.show_bounding_box and obstacle_obj != None:
                self.draw_bounding_box(obstacle_obj, img_arr)
            
        return img_arr, label, coords, 
