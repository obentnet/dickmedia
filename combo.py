import os
import random
import subprocess
import shlex
from glob import glob
import tkinter  # 修正拼写错误
from tkinter import filedialog

os.system('cls' if os.name == 'nt' else 'clear')

print('         __   ___  __      __   __         __   __   ')
print(r' \  / | |  \ |__  /  \    /  ` /  \  |\/| |__) /  \  ')  # 使用原始字符串
print(r'  \/  | |__/ |___ \__/    \__, \__/  |  | |__) \__/ ')   # 使用原始字符串
print('                     v2.0.3')
print('                     拼接模块已启动')
print('                     当前模式：【拼接1 头部+主视频】\n\n\n\n\n')

def get_video_files(directory):
    """递归获取目录及子目录下所有视频文件"""
    video_ext = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(video_ext):
                video_files.append(os.path.join(root, file))
    return video_files

def get_video_codec(file_path):
    """获取视频文件的编码格式"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        codec = result.stdout.decode('utf-8', errors='replace').strip().lower()
        if not codec:
            raise RuntimeError(f"未检测到视频编码：{file_path}")
        return codec
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='replace')
        raise RuntimeError(f"获取编码失败：{file_path}\n错误信息：{error_msg}")

def convert_to_h264_ts(input_path, output_path):
    """将视频转码为h264编码的TS格式"""
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264',  # 使用h264编码
        '-preset', 'medium',  # 平衡编码速度和质量
        '-crf', '23',        # 通用质量设置
        '-c:a', 'aac',       # 音频转码为通用格式
        '-f', 'mpegts',      # 输出为TS容器
        '-y', output_path    # 覆盖已有文件
    ]
    try:
        subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='replace')
        raise RuntimeError(f"转码失败：{input_path} 到 h264 TS\n错误信息：{error_msg}")

def process_combination(header, main, output_dir, idx, output_prefix):  # 修改：新增output_prefix参数
    """处理单个组合的拼接流程（强制使用h264编码）"""
    header_ts = f"temp_header_{idx}.ts"
    main_ts = f"temp_main_{idx}.ts"
    combined_ts = f"temp_combined_{idx}.ts"
    concat_file = f"concat_list_{idx}.txt"
    
    try:
        main_name = os.path.splitext(os.path.basename(main))[0]  # 新增代码
        # 获取编码信息
        header_codec = get_video_codec(header)
        main_codec = get_video_codec(main)
        print(f"处理组合 {idx}: 头部原始编码={header_codec}, 主原始编码={main_codec}")

        # 处理头部视频转码
        if header_codec != 'h264':
            print(f"转码头部视频为h264 TS...")
            convert_to_h264_ts(header, header_ts)
        else:
            # 直接生成TS（h264流）
            subprocess.run(
                [
                    'ffmpeg', '-i', header,
                    '-c', 'copy',
                    '-bsf:v', 'h264_mp4toannexb',
                    '-f', 'mpegts',
                    '-vsync', '0',
                    '-avoid_negative_ts', 'make_zero',
                    '-y', header_ts
                ],
                stderr=subprocess.PIPE,
                check=True
            )

        # 处理主视频转码
        if main_codec != 'h264':
            print(f"转码主视频为h264 TS...")
            convert_to_h264_ts(main, main_ts)
        else:
            # 直接生成TS（h264流）
            subprocess.run(
                [
                    'ffmpeg', '-i', main,
                    '-c', 'copy',
                    '-bsf:v', 'h264_mp4toannexb',
                    '-f', 'mpegts',
                    '-vsync', '0',
                    '-avoid_negative_ts', 'make_zero',
                    '-y', main_ts
                ],
                stderr=subprocess.PIPE,
                check=True
            )

        # 生成拼接列表
        with open(concat_file, 'w', encoding='utf-8') as f:
            f.write(f"file {shlex.quote(header_ts)}\n")
            f.write(f"file {shlex.quote(main_ts)}\n")

        # 拼接TS文件
        subprocess.run(
            ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', '-y', combined_ts],
            stderr=subprocess.PIPE,
            check=True
        )

        # 转换TS为MP4（使用自定义前缀）  # 修改点：文件名格式
        output_mp4 = os.path.join(output_dir, f"{output_prefix}_{main_name}_{idx}.mp4")  # 修改这行
        subprocess.run(
            ['ffmpeg', '-i', combined_ts, '-c', 'copy', '-y', output_mp4],
            stderr=subprocess.PIPE,
            check=True
        )

        print(f"成功生成：{output_mp4}")

    except Exception as e:
        print(f"\n[错误] 处理组合 {idx} 失败")
        print(f"头部文件：{os.path.basename(header)}")
        print(f"主文件：{os.path.basename(main)}")
        print(f"错误详情：{str(e)}")
        raise
    finally:
        # 清理临时文件
        temp_files = [header_ts, main_ts, combined_ts, concat_file]
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"清理临时文件 {f} 失败：{str(e)}")

if __name__ == "__main__":
    input('按任意键开始')
    # 新增：获取输出文件前缀
    print('头部目录')
    header_dir = filedialog.askdirectory()
    print(header_dir)

    print('主视频目录')
    main_dir = filedialog.askdirectory()
    print(main_dir)

    print('输出目录')
    output_dir = filedialog.askdirectory()
    print(output_dir)

    output_prefix = input("前缀（留空默认为'拼接'）：").strip() or "拼接"  # 处理默认值

    print('指令已接受，载入中......')

    os.makedirs(output_dir, exist_ok=True)

    headers = get_video_files(header_dir)
    mains = get_video_files(main_dir)
    
    if not headers or not mains:
        print("错误：未找到视频文件！")
        exit(1)

    # 预加载头部视频（不再筛选编码）
    valid_headers = []
    for header in headers:
        try:
            get_video_codec(header)  # 仅验证能否获取编码
            valid_headers.append(header)
        except Exception as e:
            print(f"跳过头部视频 {header}，原因：{e}")
    headers = valid_headers

    # 新增：总进度提示
    total_files = len(mains)
    print(f"\n准备就绪，即将处理 {total_files} 个主视频...\n")
    success_count = 0
    
    for idx, main_video in enumerate(mains):
        current_num = idx + 1
        # 新增：进度提示
        print(f"\n{'='*30}")
        print(f"处理进度：{current_num}/{total_files}（{current_num/total_files:.0%}）")
        print(f"{'='*30}")
        
        try:
            if not headers:
                print(f"无可用头部视频，跳过主视频 {os.path.basename(main_video)}")
                continue
            
            selected_header = random.choice(headers)
            print(f"随机选中头部文件：{os.path.basename(selected_header)}")
            print(f"正在处理主文件：{os.path.basename(main_video)}")
            
            process_combination(
                header=selected_header,
                main=main_video,
                output_dir=output_dir,
                idx=current_num,  # 使用自然序号
                output_prefix=output_prefix  # 传递前缀参数
            )
            success_count += 1
        except Exception as e:
            print(f"当前组合处理失败，错误信息：{str(e)}")
            continue

    # 新增：最终统计信息
    print(f"\n{'='*30}")
    print(f"处理完成！成功生成 {success_count} 个文件")
    print(f"失败数量：{total_files - success_count}")
    print(f"输出目录：{os.path.abspath(output_dir)}")
    print(f"{'='*30}")