import os
import subprocess
import chardet

def get_video_duration(video_path):
    """使用ffprobe获取视频时长（秒）"""
    cmd = [
        os.path.join(os.getcwd(), 'ffmpeg.exe'), 
        '-i', video_path
    ]
    try:
        result = subprocess.run(cmd, stderr=subprocess.PIPE, check=True)
        output = result.stderr.decode('utf-8', errors='replace')  # 强制UTF-8解码并替换错误字节[3,5](@ref)
    except subprocess.CalledProcessError as e:
        output = e.stderr.decode('utf-8', errors='replace')
    
    for line in output.split('\n'):
        if 'Duration:' in line:
            time_str = line.split('Duration:')[1].split(',')[0].strip()
            h, m, s = time_str.split(':')
            return int(h)*3600 + int(m)*60 + float(s)
    raise Exception(f"无法获取视频时长：{video_path}")

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(1024)  # 读取前1KB检测编码
    return chardet.detect(raw_data)['encoding'] or 'utf-8'  # 默认UTF-8[1,8](@ref)

def process_videos(input_dir, output_dir):
    """遍历处理所有视频文件"""
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                try:
                    file_path = os.path.join(root, file)
                    # 检测并转换文件名编码[4,8](@ref)
                    detected_enc = detect_encoding(file_path)
                    safe_path = file_path.encode('utf-8', 'surrogateescape').decode('utf-8')
                    
                    duration = get_video_duration(safe_path)
                    start = 0.0
                    while start < duration:
                        end = min(start + 5, duration)
                        split_video(safe_path, output_dir, start, end)
                        start += 5
                except Exception as e:
                    print(f"处理视频 {file_path} 出错：{str(e)}")

def split_video(input_path, output_dir, start, end):
    """执行视频切割"""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_name = f"{base_name}_{int(start)}_{int(end)}.mp4"
    output_path = os.path.join(output_dir, output_name)
    
    cmd = [
        os.path.join(os.getcwd(), 'ffmpeg.exe'),
        '-ss', str(start),
        '-i', input_path,
        '-t', str(end - start),
        '-c', 'copy',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"成功切割：{output_path}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='replace')
        print(f"切割失败：{input_path}，错误：{error_msg}")

if __name__ == "__main__":
    input_dir = input("请输入源目录路径：").strip()
    output_dir = input("请输入输出目录路径：").strip()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    process_videos(input_dir, output_dir)
    print("全部视频处理完成！")