import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def draw_player_stats(frames, player_stats):
    """Legacy wrapper for multi-frame drawing (unused in streaming pipeline)."""
    output_frames = []
    for frame, row in zip(frames, player_stats):
        frame = draw_player_stats_single_frame(frame, row)
        output_frames.append(frame)
    return output_frames

def draw_player_stats_single_frame(frame, row):
    """Expert-level broadcast overlay using PIL for anti-aliasing and depth."""
    if row is None:
        return frame

    # Setup colors
    COLOR_BG     = (10, 15, 20, 180)
    COLOR_ACCENT = (29, 158, 117)
    COLOR_P1     = (29, 158, 117)
    COLOR_P2     = (210, 153, 34)
    COLOR_TEXT   = (230, 237, 243)

    # Dimensions
    width, height = 440, 280
    margin  = 40
    start_x = frame.shape[1] - width - margin
    start_y = frame.shape[0] - height - margin

    # Convert BGR → RGB for PIL
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(frame_rgb)
    draw   = ImageDraw.Draw(pil_im, 'RGBA')

    # Load fonts
    try:
        font_path  = "/System/Library/Fonts/SFNS.ttf"
        font_bold  = ImageFont.truetype(font_path, 22)
        font_main  = ImageFont.truetype(font_path, 16)
        font_label = ImageFont.truetype(font_path, 12)
        font_mono  = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 14)
    except Exception:
        font_bold = font_main = font_label = font_mono = ImageFont.load_default()

    # ── Background panel ──────────────────────────────────────────────────────
    draw.rounded_rectangle(
        [start_x - 4, start_y - 4, start_x + width + 4, start_y + height + 4],
        radius=24, fill=(255, 255, 255, 15)
    )
    draw.rounded_rectangle(
        [start_x, start_y, start_x + width, start_y + height],
        radius=20, fill=COLOR_BG
    )

    # Header
    draw.text((start_x + 25, start_y + 25), "MATCH ANALYTICS", font=font_label, fill=COLOR_ACCENT)
    draw.text((start_x + 180, start_y + 55), "PLAYER 1", font=font_label, fill=COLOR_P1)
    draw.text((start_x + 310, start_y + 55), "PLAYER 2", font=font_label, fill=COLOR_P2)

    # ── Helper — must be defined BEFORE first call ────────────────────────────
    def draw_stat_row(y_offset, label, val1, val2, unit="km/h"):
        draw.text((start_x + 25,  start_y + y_offset),     label.upper(), font=font_label, fill=(139, 148, 158))
        draw.text((start_x + 180, start_y + y_offset - 4), f"{val1:.1f}", font=font_mono,  fill=COLOR_TEXT)
        draw.text((start_x + 240, start_y + y_offset - 2), unit,          font=font_label, fill=(110, 118, 129))
        draw.text((start_x + 310, start_y + y_offset - 4), f"{val2:.1f}", font=font_mono,  fill=COLOR_TEXT)
        draw.text((start_x + 370, start_y + y_offset - 2), unit,          font=font_label, fill=(110, 118, 129))
        draw.line([start_x + 20, start_y + y_offset + 25,
                   start_x + width - 20, start_y + y_offset + 25], fill=(255, 255, 255, 10))

    # ── Stats — fall back to averages when live value is 0 ───────────────────
    avg_p1_shot = (row.get('player_1_average_shot_speed')   or
                   row.get('player_1_average_player_speed') or 0)
    avg_p2_shot = (row.get('player_2_average_shot_speed')   or
                   row.get('player_2_average_player_speed') or 0)
    avg_p1_spd  = row.get('player_1_average_player_speed', 0) or 0
    avg_p2_spd  = row.get('player_2_average_player_speed', 0) or 0

    raw_p1_shot = row.get('player_1_last_shot_speed',   0) or 0
    raw_p2_shot = row.get('player_2_last_shot_speed',   0) or 0
    raw_p1_spd  = row.get('player_1_last_player_speed', 0) or 0
    raw_p2_spd  = row.get('player_2_last_player_speed', 0) or 0

    p1_shot_spd = raw_p1_shot if raw_p1_shot > 0 else avg_p1_shot
    p2_shot_spd = raw_p2_shot if raw_p2_shot > 0 else avg_p2_shot
    p1_spd      = raw_p1_spd  if raw_p1_spd  > 0 else avg_p1_spd
    p2_spd      = raw_p2_spd  if raw_p2_spd  > 0 else avg_p2_spd

    draw_stat_row(90,  "Live Shot Speed", p1_shot_spd, p2_shot_spd)
    draw_stat_row(140, "Movement Speed",  p1_spd,      p2_spd)
    draw_stat_row(190, "Avg Shot Speed",  avg_p1_shot, avg_p2_shot)
    draw_stat_row(240, "Avg Move Speed",  avg_p1_spd,  avg_p2_spd)

    # Accent bar at the top
    draw.rectangle([start_x + 20, start_y + 15, start_x + 40, start_y + 17], fill=COLOR_ACCENT)

    # Convert back to BGR
    res = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
    return res
