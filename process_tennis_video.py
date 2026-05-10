from copy import deepcopy
from typing import Any

import cv2
import pandas as pd

import constants
from court_line_detector import CourtLineDetector
from mini_court import MiniCourt
from trackers import BallTracker, PlayerTracker
from utils import (
    convert_pixel_distance_to_meters,
    draw_player_stats_single_frame,
    get_video_frames_generator,
    measure_distance,
    save_video,
)


def process_tennis_video(input_video_path: str, output_video_path: str) -> dict[str, Any]:
    print("Initializing models...")
    player_tracker = PlayerTracker(model_path="models/yolov8x.pt")
    ball_tracker = BallTracker(model_path="models/yolo5_last.pt")
    court_line_detector = CourtLineDetector(model_path="models/keypoints_model.pth")

    # --- PASS 1: Detection (Low Memory) ---
    print("Pass 1: Running detections...")
    player_detections = []
    ball_detections_raw = []
    court_keypoints = None
    mini_court = None
    frame_count = 0

    frame_gen = get_video_frames_generator(input_video_path)
    for frame in frame_gen:
        if frame_count == 0:
            court_keypoints = court_line_detector.predict(frame)
            mini_court = MiniCourt(frame)

        player_detections.append(player_tracker.detect_frame(frame))
        ball_detections_raw.append(ball_tracker.detect_frame(frame))
        frame_count += 1

    print("Interpolating and filtering...")
    # filter player detections based on court keypoints
    player_detections = player_tracker.choose_and_filter_players(player_detections, court_keypoints)
    ball_detections = ball_tracker.interpolate_ball_positions(ball_detections_raw)

    # Convert To Mini Court Coordinates
    player_mini_court_detection, ball_mini_court_detection = mini_court.convert_bounding_boxes_to_mini_court_coordinates(
        player_detections, ball_detections, court_keypoints
    )

    ball_shots_frames = ball_tracker.get_ball_shot_frames(ball_detections)

    # Calculate Stats
    print("Calculating statistics...")
    player_stats_data = [{
        'frame_num': 0,
        'player_1_number_of_shots': 0,
        'player_1_total_shot_speed': 0,
        'player_1_last_shot_speed': 0,
        'player_1_total_player_speed': 0,
        'player_1_last_player_speed': 0,

        'player_2_number_of_shots': 0,
        'player_2_total_shot_speed': 0,
        'player_2_last_shot_speed': 0,
        'player_2_total_player_speed': 0,
        'player_2_last_player_speed': 0,
    }]

    ball_speeds = []
    for ball_shot_ind in range(len(ball_shots_frames)-1):
        start_frame = ball_shots_frames[ball_shot_ind]
        end_frame = ball_shots_frames[ball_shot_ind+1]
        ball_shot_time_in_seconds = (end_frame - start_frame) / 24

        # Distances
        distance_covered_by_ball_pixels = measure_distance(
            ball_mini_court_detection[start_frame][1],
            ball_mini_court_detection[end_frame][1]
        )
        distance_covered_by_ball_meters = convert_pixel_distance_to_meters(
            distance_covered_by_ball_pixels,
            constants.DOUBLE_LINE_WIDTH,
            mini_court.get_width_of_mini_court()
        )

        speed_of_ball_shot = distance_covered_by_ball_meters / ball_shot_time_in_seconds * 3.6
        ball_speeds.append(speed_of_ball_shot)

        # Player Who Shot The Ball
        player_positions = player_mini_court_detection[start_frame]
        dist1 = measure_distance(player_positions.get(1, [0,0]), ball_mini_court_detection[start_frame][1])
        dist2 = measure_distance(player_positions.get(2, [0,0]), ball_mini_court_detection[start_frame][1])
        player_shot_ball = 1 if dist1 < dist2 else 2

        # Oponnent Player speed
        opponent_player_id = 1 if player_shot_ball == 2 else 2

        if opponent_player_id in player_mini_court_detection[start_frame] and opponent_player_id in player_mini_court_detection[end_frame]:
            dist_opp_pixels = measure_distance(
                player_mini_court_detection[start_frame][opponent_player_id],
                player_mini_court_detection[end_frame][opponent_player_id]
            )
            dist_opp_meters = convert_pixel_distance_to_meters(
                dist_opp_pixels,
                constants.DOUBLE_LINE_WIDTH,
                mini_court.get_width_of_mini_court()
            )
            speed_of_opponent = dist_opp_meters / ball_shot_time_in_seconds * 3.6
        else:
            speed_of_opponent = 0.0

        current_player_stats = deepcopy(player_stats_data[-1])
        current_player_stats['frame_num'] = start_frame
        current_player_stats[f"player_{player_shot_ball}_number_of_shots"] += 1
        current_player_stats[f"player_{player_shot_ball}_total_shot_speed"] += speed_of_ball_shot
        current_player_stats[f"player_{player_shot_ball}_last_shot_speed"] = speed_of_ball_shot

        current_player_stats[f"player_{opponent_player_id}_total_player_speed"] += speed_of_opponent
        current_player_stats[f"player_{opponent_player_id}_last_player_speed"] = speed_of_opponent

        player_stats_data.append(current_player_stats)

    player_stats_data_df = pd.DataFrame(player_stats_data)
    frames_df = pd.DataFrame({'frame_num': list(range(frame_count))})
    player_stats_data_df = pd.merge(frames_df, player_stats_data_df, on='frame_num', how='left').ffill()

    player_stats_data_df['player_1_average_shot_speed'] = player_stats_data_df['player_1_total_shot_speed'] / player_stats_data_df['player_1_number_of_shots'].replace(0, 1)
    player_stats_data_df['player_2_average_shot_speed'] = player_stats_data_df['player_2_total_shot_speed'] / player_stats_data_df['player_2_number_of_shots'].replace(0, 1)

    player_stats_data_df['player_1_average_player_speed'] = player_stats_data_df['player_1_total_player_speed'] / player_stats_data_df['player_2_number_of_shots'].replace(0, 1)
    player_stats_data_df['player_2_average_player_speed'] = player_stats_data_df['player_2_total_player_speed'] / player_stats_data_df['player_1_number_of_shots'].replace(0, 1)

    # --- PASS 2: Rendering (Low Memory) ---
    print("Pass 2: Rendering output video...")
    def output_frame_generator():
        frame_gen_pass2 = get_video_frames_generator(input_video_path)
        for i, frame in enumerate(frame_gen_pass2):
            if i >= frame_count:
                break
            # Draw Player & Ball Bounding Boxes
            frame = player_tracker.draw_boxes_single_frame(frame, player_detections[i])
            frame = ball_tracker.draw_boxes_single_frame(frame, ball_detections[i])

            # Draw Court Keypoints
            frame = court_line_detector.draw_keypoints(frame, court_keypoints)

            # Draw Mini Court
            frame = mini_court.draw_mini_court_single_frame(frame)
            frame = mini_court.draw_points_on_mini_court_single_frame(frame, player_mini_court_detection[i])
            frame = mini_court.draw_points_on_mini_court_single_frame(frame, ball_mini_court_detection[i], color=(0,255,255))

            # Draw Player Stats
            row_stats = player_stats_data_df.iloc[i]
            frame = draw_player_stats_single_frame(frame, row_stats)

            # Draw Frame Number
            cv2.putText(frame, f"Frame: {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            yield frame

    # save video using generator
    cap = cv2.VideoCapture(input_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    cap.release()

    save_video(output_frame_generator(), output_video_path, fps=fps)

    final_stats_row = player_stats_data_df.iloc[-1].to_dict() if not player_stats_data_df.empty else {}
    stats = {
        "ball_shots": max(0, len(ball_shots_frames) - 1),
        "max_ball_speed": max(ball_speeds) if ball_speeds else 0,
        "min_ball_speed": min(ball_speeds) if ball_speeds else 0,
        "avg_ball_speed": sum(ball_speeds)/len(ball_speeds) if ball_speeds else 0,
        "court_keypoints": len(court_keypoints) // 2 if hasattr(court_keypoints, '__len__') else 14,
        "frames": frame_count,
        "player_1_shots": final_stats_row.get('player_1_number_of_shots', 0),
        "player_2_shots": final_stats_row.get('player_2_number_of_shots', 0),
        "player_1_avg_shot_speed": final_stats_row.get('player_1_average_shot_speed', 0),
        "player_2_avg_shot_speed": final_stats_row.get('player_2_average_shot_speed', 0),
        "player_1_avg_player_speed": final_stats_row.get('player_1_average_player_speed', 0),
        "player_2_avg_player_speed": final_stats_row.get('player_2_average_player_speed', 0),
    }
    return stats
