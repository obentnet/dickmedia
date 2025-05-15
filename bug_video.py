import cv2
import os
import random
import imageio
from moviepy.editor import VideoFileClip, CompositeVideoClip
from tqdm import tqdm

# 配置本地FFmpeg路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_path = os.path.join(current_dir, 'ffmpeg.exe')
os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
os.environ["FFMPEG_BINARY"] = ffmpeg_path

def process_frames(video_path, output_path):
    """视频帧处理核心函数"""
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 随机参数生成
    start_frame = random.randint(0, max(0, total_frames - 11))
    repeat_times = random.choice([1, 2])

    # 创建临时视频文件
    temp_video = "temp_no_audio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

    target_frames = []
    current_frame = 0
    with tqdm(total=total_frames, desc="处理帧进度") as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 收集目标帧
            if start_frame <= current_frame < start_frame + 10:
                target_frames.append(frame.copy())

            # 注入重复帧
            if current_frame == start_frame + 9:
                for _ in range(repeat_times):
                    for bug_frame in target_frames:
                        out.write(bug_frame)

            out.write(frame)
            current_frame += 1
            pbar.update(1)

    cap.release()
    out.release()
    return temp_video, fps

def merge_audio(original_video, temp_video, output_path):
    """音视频合并函数"""
    video_clip = VideoFileClip(original_video)
    audio_clip = video_clip.audio
    
    processed_clip = VideoFileClip(temp_video)
    final_clip = processed_clip.set_audio(audio_clip.subclip(0, processed_clip.duration))
    
    final_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        ffmpeg_params=['-crf', '23', '-preset', 'fast']
    )
    
    video_clip.close()
    processed_clip.close()
    final_clip.close()
    os.remove(temp_video)

def process_all_videos():
    """批量处理入口函数"""
    input_dir = input("请输入视频目录路径：")
    output_dir = input("请输入输出目录路径：")
    os.makedirs(output_dir, exist_ok=True)

    video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.flv')
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(video_exts):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"BUG_{filename}")
            
            try:
                print(f"\n开始处理：{filename}")
                temp_video, _ = process_frames(input_path, output_path)
                merge_audio(input_path, temp_video, output_path)
                print(f"成功处理：{filename}")
            except Exception as e:
                print(f"处理失败 {filename}: {str(e)}")

if __name__ == "__main__":
    process_all_videos()