import cv2
import onnxruntime as ort
import numpy as np
import os

# onnx model
class AntiSpoof:
    def __init__(self,weights: str = None,model_img_size: int = 128): # Load model
        super().__init__() # Gọi hàm khởi tạo của lớp cha
        self.weights = weights # Đường dẫn tới file model
        self.model_img_size = model_img_size # Kích thước ảnh đầu vào
        self.ort_session, self.input_name = self._init_session_(self.weights) # Khởi tạo phiên làm việc

    def _init_session_(self, onnx_model_path: str): # Khởi tạo phiên làm việc
        ort_session = None
        input_name = None
        if os.path.isfile(onnx_model_path):
            try:
                ort_session = ort.InferenceSession(onnx_model_path, providers=['TensorrtExecutionProvider'])
            except:
                ort_session = ort.InferenceSession(onnx_model_path, providers=['CUDAExecutionProvider'])
            input_name = ort_session.get_inputs()[0].name
        return ort_session, input_name

    def preprocessing(self, img):  # Tiền xử lý ảnh
        new_size = self.model_img_size # Kích thước ảnh đầu vào
        old_size = img.shape[:2]   # Kích thước ảnh gốc
        ratio = float(new_size)/max(old_size) # Tính tỉ lệ giữa kích thước ảnh đầu vào và ảnh gốc
        scaled_shape = tuple([int(x*ratio) for x in old_size]) # Tính kích thước ảnh sau khi resize
        img = cv2.resize(img, (scaled_shape[1], scaled_shape[0])) # Resize ảnh
        delta_w = new_size - scaled_shape[1] # Tính độ chênh lệch chiều rộng
        delta_h = new_size - scaled_shape[0] # Tính độ chênh lệch chiều cao
        top, bottom = delta_h//2, delta_h-(delta_h//2) # Tính độ chênh lệch phía trên và phía dưới
        left, right = delta_w//2, delta_w-(delta_w//2) # Tính độ chênh lệch phía trái và phía phải
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0]) # Thêm viền đen vào ảnh
        img = img.transpose(2, 0, 1).astype(np.float32) / 255.0 # Chuyển ảnh về dạng mảng numpy và chuẩn hóa giá trị pixel về khoảng [0, 1]
        img = np.expand_dims(img, axis=0) # Thêm chiều batch_size
        return img  # Trả về ảnh sau khi tiền xử lý

    def postprocessing(self, prediction): # Hậu xử lý dự đoán
        softmax = lambda x: np.exp(x)/np.sum(np.exp(x)) # Hàm softmax
        pred = softmax(prediction)
        return pred

    def __call__(self, imgs : list):
        if not self.ort_session:
            return False
        preds = []
        for img in imgs:
            onnx_result = self.ort_session.run([],{self.input_name: self.preprocessing(img)}) # Dự đoán
            pred = onnx_result[0] # Lấy kết quả dự đoán
            pred = self.postprocessing(pred) # Hậu xử lý
            preds.append(pred) # Thêm kết quả vào danh sách
        return preds
