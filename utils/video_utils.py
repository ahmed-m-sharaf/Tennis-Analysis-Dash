import cv2


def read_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def get_video_frames_generator(video_path):
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield frame
    cap.release()

'''
def save_video(frames, output_path, fps=24):
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for frame in frames:
        out.write(frame)
    out.release()
'''
def save_video(frames_generator, output_path, fps=24):
    out = None
    fourcc = cv2.VideoWriter_fourcc(*'vp80')

    for frame in frames_generator:
        if out is None:
            height, width, _ = frame.shape
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame = frame.astype('uint8')
        out.write(frame)

    if out:
        out.release()
