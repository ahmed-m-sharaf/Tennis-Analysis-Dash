from utils import (read_video, 
                   save_video, 
                   measure_distance, 
                   draw_player_stats,
                   convert_pixel_distance_to_meters,
                convert_meters_to_pixel_distance
                   )
from trackers import PlayerTracker, BallTracker
from court_line_detector import CourtLineDetector
from mini_court import MiniCourt
import cv2
import pandas as pd
from copy import deepcopy
import constants

def process_tennis_video(input_video_path, output_video_path):
    # read video
    frames = read_video(input_video_path)

    # detecting players and balls
    player_tracker = PlayerTracker(model_path="models/yolov8x.pt")
    ball_tracker = BallTracker(model_path="models/yolo5_last.pt")
    
    player_detections = player_tracker.detect_frames(frames, 
                                                     read_from_stubs=False,
                                                     stub_path="tracker_stubs/player_detections.pkl")
    ball_detections = ball_tracker.detect_frames(frames,
                                                  read_from_stubs=False,
                                                  stub_path="tracker_stubs/ball_detections.pkl")
    ball_detections = ball_tracker.interpolate_ball_positions(ball_detections)
    # Court Line Detection
    court_line_detector = CourtLineDetector(model_path="models/keypoints_model.pth")
    court_keypoints = court_line_detector.predict(frames[0])                  
    
    
    # filter player detections based on court keypoints (closer to court points)
    player_detections = player_tracker.choose_and_filter_players(player_detections, court_keypoints)
    
    # MiniCourt
    mini_court = MiniCourt(frames[0])
    
    # Detect Ball Shots
    ball_shots_frames = ball_tracker.get_ball_shot_frames(ball_detections)
    # print("Ball Shots Detected at Frames: ", ball_shots_frames)
    
    # Convert The Position To Mini Court Position
    player_mini_court_detection, ball_mini_court_detection = mini_court.convert_bounding_boxes_to_mini_court_coordinates(player_detections, ball_detections, court_keypoints)
    
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

        # Get Distances Covered BY Ball
        distance_covered_by_ball_pixels = measure_distance(
            ball_mini_court_detection[start_frame][1], 
            ball_mini_court_detection[end_frame][1]
        )
        distance_covered_by_ball_pixels = convert_pixel_distance_to_meters(distance_covered_by_ball_pixels, 
                                                                           constants.DOUBLE_LINE_WIDTH,
                                                                           mini_court.get_width_of_mini_court())

        # Speed Of The Ball SHot in kmh
        speed_of_ball_shot = distance_covered_by_ball_pixels / ball_shot_time_in_seconds * 3.6
        ball_speeds.append(speed_of_ball_shot)
        
        # Player Who Shot The Ball
        player_positions = player_mini_court_detection[start_frame]
        player_shot_ball = min(
            player_positions.keys(),
            key=lambda player_id: measure_distance(player_positions[player_id], ball_mini_court_detection[start_frame][1])
        )
        
        
        # Oponnent Player speed
        opponent_player_id = 1 if player_shot_ball == 2 else 2
        distance_covered_by_opponent_pixels = measure_distance(
            player_mini_court_detection[start_frame][opponent_player_id], 
            player_mini_court_detection[end_frame][opponent_player_id]
        )
        distance_covered_by_opponent_meters = convert_pixel_distance_to_meters(distance_covered_by_opponent_pixels, 
                                                                           constants.DOUBLE_LINE_WIDTH,
                                                                           mini_court.get_width_of_mini_court())
        speed_of_opponent = distance_covered_by_opponent_meters / ball_shot_time_in_seconds * 3.6
        
        current_player_stats = deepcopy(player_stats_data[-1])
        current_player_stats['frame_num'] = start_frame
        current_player_stats[f"player_{player_shot_ball}_number_of_shots"] += 1
        current_player_stats[f"player_{player_shot_ball}_total_shot_speed"] += speed_of_ball_shot
        current_player_stats[f"player_{player_shot_ball}_last_shot_speed"] = speed_of_ball_shot
        
        current_player_stats[f"player_{opponent_player_id}_total_player_speed"] += speed_of_opponent
        current_player_stats[f"player_{opponent_player_id}_last_player_speed"] = speed_of_opponent
        
        player_stats_data.append(current_player_stats)


    player_stats_data_df = pd.DataFrame(player_stats_data)
    frames_df = pd.DataFrame({'frame_num': list(range(len(frames)))})
    player_stats_data_df = pd.merge(frames_df, player_stats_data_df, on='frame_num', how='left').ffill()
    
    player_stats_data_df['player_1_average_shot_speed'] = player_stats_data_df['player_1_total_shot_speed'] / player_stats_data_df['player_1_number_of_shots']
    player_stats_data_df['player_2_average_shot_speed'] = player_stats_data_df['player_2_total_shot_speed'] / player_stats_data_df['player_2_number_of_shots']
    
    player_stats_data_df['player_1_average_player_speed'] = player_stats_data_df['player_1_total_player_speed'] / player_stats_data_df['player_2_number_of_shots']
    player_stats_data_df['player_2_average_player_speed'] = player_stats_data_df['player_2_total_player_speed'] / player_stats_data_df['player_1_number_of_shots']

    
    
    # Draw Output
    
    # Draw Player Bounding Boxes
    output_video_frames = player_tracker.draw_boxes(frames, player_detections)
    
    # Draw Ball Bounding Boxes
    output_video_frames = ball_tracker.draw_boxes(output_video_frames, ball_detections)

    # Draw Court Keypoints
    output_video_frames = court_line_detector.draw_keypoints_on_video(output_video_frames, court_keypoints)
    
    # Draw Mini Court
    output_video_frames = mini_court.draw_mini_court(output_video_frames)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames, player_mini_court_detection)
    output_video_frames = mini_court.draw_points_on_mini_court(output_video_frames, ball_mini_court_detection, color=(0,255,255))
    
    
    # Draw Player Stats
    output_video_frames = draw_player_stats(output_video_frames,player_stats_data_df)


    # Draw Frame Number 
    for i, frame in enumerate(output_video_frames):
        cv2.putText(frame, f"Frame: {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # save video
    save_video(output_video_frames, output_video_path)

    final_stats_row = player_stats_data_df.iloc[-1].to_dict()
    stats = {
        "ball_shots": len(ball_shots_frames) - 1,
        "max_ball_speed": max(ball_speeds) if ball_speeds else 0,
        "min_ball_speed": min(ball_speeds) if ball_speeds else 0,
        "avg_ball_speed": sum(ball_speeds)/len(ball_speeds) if ball_speeds else 0,
        "court_keypoints": len(court_keypoints) // 2 if hasattr(court_keypoints, '__len__') else 14,
        "frames": len(frames),
        "player_1_shots": final_stats_row.get('player_1_number_of_shots', 0),
        "player_2_shots": final_stats_row.get('player_2_number_of_shots', 0),
        "player_1_avg_shot_speed": final_stats_row.get('player_1_average_shot_speed', 0),
        "player_2_avg_shot_speed": final_stats_row.get('player_2_average_shot_speed', 0),
        "player_1_avg_player_speed": final_stats_row.get('player_1_average_player_speed', 0),
        "player_2_avg_player_speed": final_stats_row.get('player_2_average_player_speed', 0),
    }
    return stats
