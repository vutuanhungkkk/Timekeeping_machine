import torch
import torch.onnx
from extract_embedding_model import MobileFaceNet

# Initialize the model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # Use GPU if available
model = MobileFaceNet(embedding_size=512).to(device) #Khoi tao model
model.load_state_dict(torch.load('Weights/MobileFace_Net', map_location=device)) # Load model
model.eval()
dummy_input = torch.randn(1, 3, 112, 112).to(device) # Tạo tensor đầu vào giả
onnx_file = "MobileFaceNet.onnx"
torch.onnx.export(model, dummy_input, onnx_file, input_names=['input'], output_names=['output'], verbose=True,opset_version=13) # Export model sang file ONNX
print(f"Model exported to {onnx_file}")

