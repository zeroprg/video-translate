import cv2
import numpy as np
from moviepy.editor import VideoFileClip

# Set video file path
input_video = "input_video.mp4"

def detect_threshold(frame1, frame2, w):
    """
    Function to find the adaptive threshold of two consecutive frames
    """
    imgDiff = cv2.absdiff(np.dstack([frame1]), np.dstack([frame2]))
    thresh = np.zeros((imgDiff.shape[0], imgDiff.shape[1])).astype('float32')
    if w > 0:
        ws = cv2.mean(cv2.GaussianBlur(np.dstack([frame1, frame2]), (5, 5), 0))
    else:
        ws = cv2.mean(frame1)
    _, threshold = cv2.threshold(imgDiff > np.abs(ws[..., np.newaxis] - imgDiff), 24, 255, cv2.THRESH_BINARY)[1]
    return threshold.astype('uint8') if w >= 0 else threshold

def find_pauses_or_scenes_change(video, pause_or_scenes_change_threshold=25):
    """
    Function to detect pause or scene change points in a video
    """
    video_clip = VideoFileClip(input_video)
    frames = []
    scene_changes = []

    last_frame = np.zeros((1, 3, int(np.shape(video_clip.image)[0])), dtype="uint8")
    current_frame = video_clip.image.astype('uint8')[:, :, ::]

    frames.append(current_frame)
    prev_diff_threshold = detect_threshold(last_frame[0], current_frame, pause_or_scenes_change_threshold)

    for _ in range(len(video_clip.iter_frames())):
        last_frame, current_frame = current_frame, video_clip.image.astype('uint8')[:, :, ::]
        frames.append(current_frame)
        diff_threshold = detect_threshold(last_frame, current_frame, pause_or_scenes_change_threshold)
        if np.sum(np.logical_xor(prev_diff_threshold, diff_threshold)) > (np.prod([frames[0].shape]) * 0.2): # custom threshold condition based on number of changed pixels in frames
            scene_changes.append(_)
        prev_diff_threshold = np.copy(diff_threshold)

    video_clip.close()
    return frames, scene_changes

def split_video(input_path, output_directory="output"):
    """
    Function to split a video file based on pauses or scene changes
    """
    frames, _ = find_pauses_or_scenes_change(input_video)
    for i, frame in enumerate(frames):
        base_filename = "output_{}.mp4".format(i + 1) if output_directory is not None else f"frame_{i+1:04}.png"
        save_image = False
        save_video = False

        # Split the frames into single images (for optional further use, can be commented out for a video segment instead)
        if save_image:
            output_file = output_directory + os.path.sep if output_directory is not None else ""
            image_clip = VideoFileClip(input_video).save_frame("{output_file}{base_filename}")
            image_clip.close()

        # Split video based on pauses or scene changes and save them
        if save_video:
            start, end = frame.shape[0], (frames[i+1] is None) * (frame.shape[0] + frames[i][..., 0].shape[0])
            output_file = output_directory + os.path.sep if output_directory else ""
            clip = VideoFileClip(input_video, start=int(np.sum([frames[:i].shape[0]])), end=start).write_gif("{output_file}segment_{}.mp4")
            clip.close()
    print(f"Total number of segments detected: {len(scene_changes)}")

# Call the split_video function with your input video file path and optional output directory if needed
input_path = "path/to/your_input_video_file.mp4"
split_video(input_path)
