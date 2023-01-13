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
from PIL import ImageDraw
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

    def __init__(self, cfg, debug=False):

        #MODEL_URL = "https://github.com/google-coral/edgetpu/raw/master/test_data/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite"
        #LABEL_URL = "https://dl.google.com/coral/canned_models/coco_labels.txt"
        #https://raw.githubusercontent.com/google-coral/test_data/master/tf2_mobilenet_v3_edgetpu_1.0_224_ptq_edgetpu.tflite
        #https://raw.githubusercontent.com/google-coral/test_data/master/imagenet_labels.txt

        MODEL_FILE_NAME = "edgetpu/tf2_mobilenet_v3_edgetpu_1.0_224_ptq_edgetpu.tflite"
        LABEL_FILE_NAME = "edgetpu/imagenet_labels.txt"

        self.labels = read_label_file(LABEL_FILE_NAME)

        self.interpreter = make_interpreter(MODEL_FILE_NAME)
        self.interpreter.allocate_tensors()

        lanelogger.info(f"Obstacle detector model loaded.")
        if common.input_details(self.interpreter, 'dtype') != np.uint8:
            raise ValueError('Only support uint8 input type.')

        self.size = common.input_size(self.interpreter)

        self.last_5_scores = collections.deque(np.zeros(5), maxlen=5)

        self.cfg = cfg          
        self.min_score = self.cfg.OBSTACLE_MIN_SCORE
        self.show_bounding_box = self.cfg.OBSTACLE_SHOW_BOUNDING_BOX
        self.debug = debug

    def convertImageArrayToPILImage(self, img_arr):
        img = Image.fromarray(img_arr.astype('uint8'), 'RGB')
        return img

    def convertPILToImageArray(self, img_pil):
        img = np.array(img_pil) 
        return img

    def getRoiLeft(self, frame):
        width, height = frame.size
        roi = frame.crop((0, int(height*self.cfg.OBSTACLE_DETECTOR_ROI_TOP), int(width*self.cfg.OBSTACLE_DETECTOR_ROI_RIGHT), int(height*self.cfg.OBSTACLE_DETECTOR_ROI_BOTTOM)))
        return roi

    def getRoiRight(self, frame):
        width, height = frame.size
        roi = frame.crop((int(width*self.cfg.OBSTACLE_DETECTOR_ROI_LEFT), int(height*self.cfg.OBSTACLE_DETECTOR_ROI_TOP), int(width), int(height*self.cfg.OBSTACLE_DETECTOR_ROI_BOTTOM)))
        return roi

    def classify_img (self, img):

        img_to_classify = img.resize(self.size, Image.ANTIALIAS)
        params = common.input_details(self.interpreter, 'quantization_parameters')
        scale = params['scales']
        zero_point = params['zero_points']
        mean = 128.0
        std = 128.0
        if abs(scale * std - 1) < 1e-5 and abs(mean - zero_point) < 1e-5:
            # Input data does not require preprocessing.
            common.set_input(self.interpreter, img_to_classify)
        else:
            # Input data requires preprocessing
            normalized_input = (np.asarray(img_to_classify) - mean) / (std * scale) + zero_point
            np.clip(normalized_input, 0, 255, out=normalized_input)
            common.set_input(self.interpreter, normalized_input.astype(np.uint8))

        self.interpreter.invoke()
        
        classes = classify.get_classes(self.interpreter, top_k=3, score_threshold=self.min_score)

        max_score = 0
        obstacle_obj = None
        if classes:
            for obj in classes:
                    if (obj.score > max_score):
                        obstacle_obj = obj
                        max_score = obj.score

        if obstacle_obj and self.debug:
            print(f"object {self.labels.get(obstacle_obj.id, obstacle_obj.id)} detected, score = {obstacle_obj.score}")

        return obstacle_obj

    '''
    Return an object if there is a traffic light in the frame
    '''
    def detect_obstacle (self, img_arr):
        img = self.convertImageArrayToPILImage(img_arr)
        left_img = self.getRoiLeft (img)
        obstacle = self.classify_img(left_img)

        label="---"
        if obstacle:
            label = f"{self.labels.get(obstacle.id, obstacle.id)} ({obstacle.score})"

        return left_img, label

    def run(self, img_arr, full_img_arr):
        if img_arr is None:
            return img_arr

        # Detect traffic light object
        if full_img_arr is not None:
            img_for_detect = full_img_arr
        else :
            img_for_detect = img_arr

        left_img, right_label = self.detect_obstacle(img_for_detect)
        right_img, right_label = self.detect_obstacle(img_for_detect)
        lanelogger.info(f" {left_label} <--- car ---> {right_label}")

            
        return img_arr, "--" 
