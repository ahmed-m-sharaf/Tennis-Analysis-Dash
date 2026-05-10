import cv2
import torch
import torchvision.models as models
import torchvision.transforms as transforms


class CourtLineDetector:
    def __init__(self, model_path):
        # load architecture
        self.model = models.resnet50(pretrained=False)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, 28)
        # load weights
        self.model.load_state_dict(torch.load(model_path, map_location = 'cpu'))

        # apply same transformations as during training
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def predict(self, frame):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_tensor = self.transform(img_rgb).unsqueeze(0)  # Add batch dimension
        with torch.no_grad():
            output = self.model(image_tensor)
        keypoints = output.squeeze().cpu().numpy()

        # to map keypoints back to original image size
        original_h, original_w = img_rgb.shape[:2]
        keypoints[0::2] *= original_w/224.0  # Scale x-coordinates
        keypoints[1::2] *= original_h/224.0  # Scale y-coordinates
        return keypoints

    def draw_keypoints(self, image, keypoints):
        for i in range(0, len(keypoints), 2):
            x, y = int(keypoints[i]), int(keypoints[i+1])
            cv2.putText(image, str(i//2), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  # Draw red text
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)  # Draw red circles
        return image

    def draw_keypoints_on_video(self, video_frames, keypoints):
        output_frames = []
        for frame in video_frames:
            output_frame = self.draw_keypoints(frame, keypoints)
            output_frames.append(output_frame)
        return output_frames
