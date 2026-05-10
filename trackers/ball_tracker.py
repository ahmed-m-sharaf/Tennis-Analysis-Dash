import pickle

import cv2
import pandas as pd
from ultralytics import YOLO


class BallTracker:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        import torch
        if torch.backends.mps.is_available():
            device = 'mps'
        elif torch.cuda.is_available():
            device = 'cuda'
        else:
            device = 'cpu'
        self.model.to(device)
        print(f"[BallTracker] Running on device: {device}")

    def interpolate_ball_positions(self, ball_detections):
        ball_positions = [x.get(1, []) for x in ball_detections]
        df_ball_positions = pd.DataFrame(ball_positions, columns = ['x1', 'y1', 'x2', 'y2'])

        # interpolate missing values
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        ball_positions = [{1: x} for x in df_ball_positions.values.tolist()]
        return ball_positions

    def get_ball_shot_frames(self, ball_positions):
        ball_positions = [x.get(1, []) for x in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions, columns = ['x1', 'y1', 'x2', 'y2'])

        df_ball_positions['ball_hit'] = 0
        df_ball_positions['mid_y'] = (df_ball_positions['y1'] + df_ball_positions['y2']) / 2
        df_ball_positions['mid_t_rolling_mean'] = df_ball_positions['mid_y'].rolling(window=5, min_periods=1, center = False).mean()
        df_ball_positions['delta_y'] = df_ball_positions['mid_t_rolling_mean'].diff()

        minimum_change_frames_for_hit = 25
        for i in range(1, len(df_ball_positions)- int(minimum_change_frames_for_hit * 1.2)):
            negative_position_change = df_ball_positions['delta_y'].iloc[i] > 0 and df_ball_positions['delta_y'].iloc[i + 1] < 0
            positive_position_change = df_ball_positions['delta_y'].iloc[i] < 0 and df_ball_positions['delta_y'].iloc[i + 1] > 0

            if negative_position_change or positive_position_change:
                change_count = 0
                for change_frame in range(i + 1, i + int(minimum_change_frames_for_hit * 1.2) + 1):
                    negative_position_change_following_frame = df_ball_positions['delta_y'].iloc[i] > 0 and df_ball_positions['delta_y'].iloc[change_frame] < 0
                    positive_position_change_following_frame = df_ball_positions['delta_y'].iloc[i] < 0 and df_ball_positions['delta_y'].iloc[change_frame] > 0
                    if negative_position_change_following_frame and negative_position_change:
                        change_count += 1
                    elif positive_position_change_following_frame and positive_position_change:
                        change_count += 1

                if  change_count >= minimum_change_frames_for_hit-1:
                    df_ball_positions.loc[df_ball_positions.index[i], 'ball_hit'] = 1

        frame_nums_with_ball_hits = df_ball_positions[df_ball_positions['ball_hit'] == 1].index.tolist()
        return frame_nums_with_ball_hits
    # loop for all frames
    def detect_frames(self, frames, read_from_stubs=False, stub_path=None):
        ball_detections = []

        if read_from_stubs and stub_path is not None:
            with open(stub_path, 'rb') as f:
                return pickle.load(f)

        for frame in frames:
            ball_dict = self.detect_frame(frame)
            ball_detections.append(ball_dict)

        if stub_path is not None:
            with open(stub_path, 'wb') as f:
                pickle.dump(ball_detections, f)

        return ball_detections

    # detect only one frame
    def detect_frame(self, frame):
        # [0] because it only one image
        results = self.model.predict(frame, conf = 0.15)[0]
        ball_dict = {}
        for box in results.boxes:
            result = box.xyxy.tolist()[0]  # [x1, y1, x2, y2]
            ball_dict[1] = result
        return ball_dict

    # draw bounding boxes on the frame
    def draw_boxes(self, frames, ball_detections):
        output_video_frames = []
        for frame, ball_dict in zip(frames, ball_detections):
            output_video_frames.append(self.draw_boxes_single_frame(frame, ball_dict))
        return output_video_frames

    def draw_boxes_single_frame(self, frame, ball_dict):
        # Precise Ball Marker
        COLOR_BALL = (0, 255, 255)
        
        for track_id, box in ball_dict.items():
            x1, y1, x2, y2 = map(int, box)
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            
            # Technical crosshair style
            cv2.line(frame, (center_x - 8, center_y), (center_x + 8, center_y), COLOR_BALL, 1)
            cv2.line(frame, (center_x, center_y - 8), (center_x, center_y + 8), COLOR_BALL, 1)
            cv2.circle(frame, (center_x, center_y), 5, COLOR_BALL, 1, cv2.LINE_AA)
            
        return frame
