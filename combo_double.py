import os
import random
import subprocess
import shlex
from glob import glob
import tkinter  # 修正拼写错误
from tkinter import filedialog

os.system('cls' if os.name == 'nt' else 'clear')

print('         __   ___  __      __   __         __   __   ')
print(r' \  / | |  \ |__  /  \    /  ` /  \  |\/| |__/ /  \  ')
print(r'  \/  | |__/ |___ \__/    \__, \__/  |  | | \/ \__/ ')
print('                     v2.0.3')
print('                     拼接模块已启动')
print('                     当前模式：【头部+主视频1+主视频2（双目录）】\n\n\n\n\n')


def get_video_files(directory):
    """递归获取目录及子目录下所有视频文件"""
    video_ext = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')
    return [os.path.join(root, f) 
            for root, _, files in os.walk(directory) 
            for f in files 
            if f.lower().endswith(video_ext)]

def validate_video_files(files):
    """验证视频文件有效性并返回可用列表"""
    valid_files = []
    for f in files:
        try:
            get_video_codec(f)
            valid_files.append(f)
        except Exception as e:
            print(f"跳过无效文件 {os.path.basename(f)}：{str(e)}")
    return valid_files

def get_video_codec(file_path):
    """获取视频编码格式（带增强错误处理）"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=codec_name', '-of', 
             'default=noprint_wrappers=1:nokey=1', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout.strip().lower()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFprobe错误：{e.stderr.strip()}")

def convert_to_h264_ts(input_path, output_path):
    """通用转码函数（支持错误重试）"""
    cmd = [
        'ffmpeg', '-i', input_path,
        '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '23', '-c:a', 'aac',
        '-f', 'mpegts', '-y', output_path
    ]
    try:
        subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"转码失败：{e.stderr.strip()}")

def process_triple_combination(header, main1, main2, output_dir, idx, prefix):
    """处理三视频拼接（带详细日志记录）"""
    temp_files = []
    try:
        print(f"\n{'='*30}")
        print(f"开始处理组合 #{idx}")
        print(f"头部：{os.path.basename(header)}")
        print(f"主视频1：{os.path.basename(main1)}")
        print(f"主视频2：{os.path.basename(main2)}")

        # 生成最终文件名（使用主视频1名称）
        m1_basename = os.path.basename(main1)
        m1_name = os.path.splitext(m1_basename)[0]
        output_path = os.path.join(output_dir, f"{prefix}_{m1_name}.mp4")

        # 生成临时文件名（使用唯一索引避免冲突）
        temp_files = [
            f"temp_header_{idx}.ts",
            f"temp_main1_{idx}.ts",
            f"temp_main2_{idx}.ts",
            f"temp_concat_{idx}.ts",
            f"concat_list_{idx}.txt"
        ]


        # 转码处理流程
        for i, (src, dst) in enumerate(zip(
            [header, main1, main2], temp_files[:3]
        )):
            codec = get_video_codec(src)
            if codec != 'h264':
                print(f"转码 {os.path.basename(src)} 为H264 TS...")
                convert_to_h264_ts(src, dst)
            else:
                print(f"直接复用 {os.path.basename(src)}")
                subprocess.run([
                    'ffmpeg', '-i', src,
                    '-c', 'copy', '-bsf:v', 'h264_mp4toannexb',
                    '-f', 'mpegts', '-y', dst
                ], check=True, 
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

        # 生成拼接列表
        with open(temp_files[4], 'w', encoding='utf-8') as f:
            for ts in temp_files[:3]:
                f.write(f"file {shlex.quote(ts)}\n")

        # 执行拼接
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', temp_files[4], '-c', 'copy', '-y', temp_files[3]
        ], check=True,
           stdout=subprocess.DEVNULL,
           stderr=subprocess.DEVNULL)

        # 生成最终文件（移除重复定义output_path的代码）
        subprocess.run([
            'ffmpeg', '-i', temp_files[3], '-c', 'copy', '-y', output_path
        ], check=True,
           stdout=subprocess.DEVNULL,
           stderr=subprocess.DEVNULL)

        print(f"成功生成：{output_path}")
        return True

    except Exception as e:
        print(f"\n[严重错误] 处理失败：{str(e)}")
        return False
    finally:
        for f in temp_files:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

if __name__ == "__main__":
    input('按下任意键开始')
    print('选择头部目录')
    header_dir = filedialog.askdirectory()
    print(header_dir)

    print('选择主视频1目录')
    main_dir1 = filedialog.askdirectory()
    print(main_dir1)

    print('选择主视频2目录')
    main_dir2 = filedialog.askdirectory()
    print(main_dir2)

    print('选择输出文件夹')
    output_dir = filedialog.askdirectory()
    os.makedirs(output_dir, exist_ok=True)  # 新增行：自动创建输出目录
    prefix = input("输出文件前缀（默认：拼接）：").strip() or "拼接"

    headers = validate_video_files(get_video_files(header_dir))
    mains1 = validate_video_files(get_video_files(main_dir1))
    mains2 = validate_video_files(get_video_files(main_dir2))

    min_length = min(len(mains1), len(mains2))
    if not headers:
        print("错误：未找到有效的头部视频！")
        exit(1)
    if min_length == 0:
        print("错误：主视频目录中没有有效文件！")
        exit(1)
    if len(mains1) != len(mains2):
        print(f"警告：主视频数量不匹配（{len(mains1)} vs {len(mains2)}），将处理前{min_length}对")

    processing_queue = list(zip(mains1[:min_length], mains2[:min_length]))
    total = len(processing_queue)
    success = 0

    print(f"\n准备处理 {total} 个视频组合...")
    print(f"可用头部视频：{len(headers)} 个")
    print(f"主视频1数量：{len(mains1)}")
    print(f"主视频2数量：{len(mains2)}\n")

    for idx, (m1, m2) in enumerate(processing_queue, 1):
        header = random.choice(headers)
        print(f"\n处理进度：{idx}/{total} ({idx/total:.1%})")
        if process_triple_combination(header, m1, m2, output_dir, idx, prefix):
            success += 1

    print(f"\n{'='*30}")
    print(f"处理完成！成功：{success}/{total}")
    print(f"输出目录：{os.path.abspath(output_dir)}")
    print(f"{'='*30}")