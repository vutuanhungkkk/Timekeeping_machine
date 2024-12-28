import cv2
import numpy as np
import math
import argparse
import time

class YOLOv8_face:
    def __init__(self, path, conf_thres=0.2, iou_thres=0.5):
        self.conf_threshold = conf_thres # Ngưỡng độ tin cậy để chấp nhận dự đoán
        self.iou_threshold = iou_thres # Ngưỡng IoU để loại bỏ các dự đoán trùng lặp
        self.class_names = ['face'] # Danh sách tên lớp
        self.num_classes = len(self.class_names) # Số lớp
        # Initialize model
        #self.net = cv2.dnn.readNet(path)
        self.net = cv2.dnn.readNetFromONNX(path) # Load model từ file ONNX
        self.input_height = 640
        self.input_width = 640
        self.reg_max = 16 # Số lớp regression

        self.project = np.arange(self.reg_max) # Tạo mảng từ 0 đến reg_max
        self.strides = (8, 16, 32) # Kích thước stride của mỗi lớp
        self.feats_hw = [(math.ceil(self.input_height / self.strides[i]), math.ceil(self.input_width / self.strides[i]))
                         for i in range(len(self.strides))] # Kích thước feature map của mỗi lớp
        self.anchors = self.make_anchors(self.feats_hw) # Tạo anchor boxes

    def make_anchors(self, feats_hw, grid_cell_offset=0.5): # Tạo anchor boxes
        """Generate anchors from features."""
        anchor_points = {} # Tạo một dictionary chứa anchor boxes
        for i, stride in enumerate(self.strides):  # stride: 8, 16, 32
            h, w = feats_hw[i] # Kích thước feature map
            x = np.arange(0, w) + grid_cell_offset  # shift x
            y = np.arange(0, h) + grid_cell_offset  # shift y
            sx, sy = np.meshgrid(x, y) # Tạo lưới tọa độ
            anchor_points[stride] = np.stack((sx, sy), axis=-1).reshape(-1, 2)
        return anchor_points

    def softmax(self, x, axis=1): # Hàm softmax
        x_exp = np.exp(x) # Tính e^x
        x_sum = np.sum(x_exp, axis=axis, keepdims=True)  # Tính tổng e^x
        s = x_exp / x_sum
        return s

    def resize_image(self, srcimg, keep_ratio=True): # Resize ảnh
        top, left, newh, neww = 0, 0, self.input_width, self.input_height
        if keep_ratio and srcimg.shape[0] != srcimg.shape[1]:
            hw_scale = srcimg.shape[0] / srcimg.shape[1]
            if hw_scale > 1:
                newh, neww = self.input_height, int(self.input_width / hw_scale)
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                left = int((self.input_width - neww) * 0.5)
                img = cv2.copyMakeBorder(img, 0, 0, left, self.input_width - neww - left, cv2.BORDER_CONSTANT,value=(0, 0, 0))  # add border
            else:
                newh, neww = int(self.input_height * hw_scale), self.input_width
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                top = int((self.input_height - newh) * 0.5)
                img = cv2.copyMakeBorder(img, top, self.input_height - newh - top, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        else:
            img = cv2.resize(srcimg, (self.input_width, self.input_height), interpolation=cv2.INTER_AREA)
        return img, newh, neww, top, left

    def detect(self, srcimg):
        input_img, newh, neww, padh, padw = self.resize_image(cv2.cvtColor(srcimg, cv2.COLOR_BGR2RGB))
        scale_h, scale_w = srcimg.shape[0] / newh, srcimg.shape[1] / neww
        input_img = input_img.astype(np.float32) / 255.0

        blob = cv2.dnn.blobFromImage(input_img)
        self.net.setInput(blob)
        outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())
        det_bboxes, det_conf, det_classid, landmarks = self.post_process(outputs, scale_h, scale_w, padh, padw)
        return det_bboxes, det_conf, det_classid, landmarks

    def post_process(self, preds, scale_h, scale_w, padh, padw):
        bboxes, scores, landmarks = [], [], []
        for i, pred in enumerate(preds):
            stride = int(self.input_height / pred.shape[2])
            pred = pred.transpose((0, 2, 3, 1))

            box = pred[..., :self.reg_max * 4]
            cls = 1 / (1 + np.exp(-pred[..., self.reg_max * 4:-15])).reshape((-1, 1))
            kpts = pred[..., -15:].reshape((-1, 15))  ### x1,y1,score1, ..., x5,y5,score5
            tmp = box.reshape(-1, 4, self.reg_max)
            bbox_pred = self.softmax(tmp, axis=-1)
            bbox_pred = np.dot(bbox_pred, self.project).reshape((-1, 4))
            bbox = self.distance2bbox(self.anchors[stride], bbox_pred,max_shape=(self.input_height, self.input_width)) * stride
            kpts[:, 0::3] = (kpts[:, 0::3] * 2.0 + (self.anchors[stride][:, 0].reshape((-1, 1)) - 0.5)) * stride
            kpts[:, 1::3] = (kpts[:, 1::3] * 2.0 + (self.anchors[stride][:, 1].reshape((-1, 1)) - 0.5)) * stride
            kpts[:, 2::3] = 1 / (1 + np.exp(-kpts[:, 2::3]))
            bbox -= np.array([[padw, padh, padw, padh]])
            bbox *= np.array([[scale_w, scale_h, scale_w, scale_h]])
            kpts -= np.tile(np.array([padw, padh, 0]), 5).reshape((1, 15))
            kpts *= np.tile(np.array([scale_w, scale_h, 1]), 5).reshape((1, 15))
            bboxes.append(bbox)
            scores.append(cls)
            landmarks.append(kpts)

        bboxes = np.concatenate(bboxes, axis=0)
        scores = np.concatenate(scores, axis=0)
        landmarks = np.concatenate(landmarks, axis=0)

        bboxes_wh = bboxes.copy()
        bboxes_wh[:, 2:4] = bboxes[:, 2:4] - bboxes[:, 0:2]
        classIds = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)
        mask = confidences > self.conf_threshold
        bboxes_wh = bboxes_wh[mask]
        confidences = confidences[mask]
        classIds = classIds[mask]
        landmarks = landmarks[mask]
        indices = cv2.dnn.NMSBoxes(bboxes_wh.tolist(), confidences.tolist(), self.conf_threshold, self.iou_threshold)
        if isinstance(indices, np.ndarray):
            indices = indices.flatten()
        if len(indices) > 0:
            mlvl_bboxes = bboxes_wh[indices]
            confidences = confidences[indices]
            classIds = classIds[indices]
            landmarks = landmarks[indices]
            return mlvl_bboxes, confidences, classIds, landmarks
        else:
            return np.array([]), np.array([]), np.array([]), np.array([])

    def distance2bbox(self, points, distance, max_shape=None): # Tính toán bounding box từ điểm và khoảng cách
        x1 = points[:, 0] - distance[:, 0]
        y1 = points[:, 1] - distance[:, 1]
        x2 = points[:, 0] + distance[:, 2]
        y2 = points[:, 1] + distance[:, 3]
        if max_shape is not None:
            x1 = np.clip(x1, 0, max_shape[1])
            y1 = np.clip(y1, 0, max_shape[0])
            x2 = np.clip(x2, 0, max_shape[1])
            y2 = np.clip(y2, 0, max_shape[0])
        return np.stack([x1, y1, x2, y2], axis=-1)


def increased_crop(img, bbox: tuple, bbox_inc: float = 1.5): # Cắt ảnh theo bounding box
    real_h, real_w = img.shape[:2]
    x, y, w, h = bbox
    w, h = w - x, h - y
    l = max(w, h)
    xc, yc = x + w / 2, y + h / 2
    x, y = int(xc - l * bbox_inc / 2), int(yc - l * bbox_inc / 2)
    x1 = 0 if x < 0 else x
    y1 = 0 if y < 0 else y
    x2 = real_w if x + l * bbox_inc > real_w else x + int(l * bbox_inc)
    y2 = real_h if y + l * bbox_inc > real_h else y + int(l * bbox_inc)
    img = img[y1:y2, x1:x2, :]
    img = cv2.copyMakeBorder(img,y1 - y, int(l * bbox_inc - y2 + y),x1 - x, int(l * bbox_inc) - x2 + x,cv2.BORDER_CONSTANT, value=[0, 0, 0])
    return img


def make_prediction(img, face_detector, anti_spoof, allow_predict_spoof):
    n = 10
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    frame_area = img.shape[0] * img.shape[1]
    min_face_area = frame_area / n
    boxes, scores, classids, kpts = face_detector.detect(img)
    predictions = []
    bboxes = []
    lanmarks = kpts
    for box, kpt, score in zip(boxes, kpts, scores):
        x, y, w, h = box.astype(int)
        face_area = w * h
        # if face_area >= min_face_area:## bo khuon mat qua nho ( nho hon n lan so voi khung hinh)
        if 1:
            bbox = np.array([x, y, x + w, y + h])
            bboxes.append(bbox)
            if allow_predict_spoof == True:
                s = time.time()
                pred = anti_spoof([increased_crop(img, bbox, bbox_inc=1.5)])[0]
                score = pred[0][0]
                label = np.argmax(pred)

                predictions.append((bbox, label, score, kpt))
    bboxes = np.array(bboxes)
    return bboxes, lanmarks, predictions

