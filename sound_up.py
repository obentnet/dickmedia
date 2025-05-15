import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

def get_video_files(directory):
    """递归获取所有视频文件路径[1,3,4](@ref)"""
    video_ext = ['.mp4', '.mkv', '.avi', '.mov', '.mpg', '.mpeg', '.wmv', '.flv']
    video_list = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_ext):
                video_list.append(os.path.join(root, file))
    return video_list

def process_video(input_path, db_gain, ffmpeg_path):
    """使用FFmpeg调整音频增益[7,8](@ref)"""
    output_path = os.path.splitext(input_path)[0] + "_boosted" + os.path.splitext(input_path)[1]
    
    cmd = [
        os.path.join(ffmpeg_path, 'ffmpeg.exe'),
        '-y',  # 覆盖已存在文件
        '-i', f'"{input_path}"',
        '-filter:a', f'volume={db_gain}dB',
        '-c:v', 'copy',  # 保持视频流不变
        f'"{output_path}"'
    ]
    
    try:
        result = subprocess.run(
            ' '.join(cmd),
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
            
        return (True, input_path, output_path)
        
    except Exception as e:
        return (False, input_path, str(e))

def main():
    # 获取用户输入
    target_dir = input("请输入要处理的目录路径：").strip()
    db_gain = input("请输入要提升的音量分贝数：").strip()
    ffmpeg_path = os.getcwd()  # FFmpeg在当前目录[1](@ref)
    
    # 输入验证
    if not os.path.isdir(target_dir):
        print("错误：输入的目录路径无效")
        return
        
    try:
        db_gain = float(db_gain)
    except ValueError:
        print("错误：分贝值必须是数字")
        return
    
    # 获取视频文件列表
    video_files = get_video_files(target_dir)
    total = len(video_files)
    if total == 0:
        print("未找到视频文件")
        return
    
    # 多线程处理[11](@ref)
    success_count = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for video in video_files:
            futures.append(executor.submit(process_video, video, db_gain, ffmpeg_path))
        
        for i, future in enumerate(futures):
            status, input_path, msg = future.result()
            progress = (i+1)/total*100
            sys.stdout.write(f"\r处理进度: {i+1}/{total} ({progress:.1f}%)")
            
            if status:
                success_count += 1
                print(f"\n成功处理: {os.path.basename(input_path)} -> {os.path.basename(msg)}")
            else:
                print(f"\n处理失败: {os.path.basename(input_path)} | 原因: {msg}")
    
    print(f"\n处理完成！成功率: {success_count}/{total}")

if __name__ == "__main__":
    main()