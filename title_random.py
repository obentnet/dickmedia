import os
import random
import sys
import tkinter
from tkinter import filedialog

def shuffle_titles(input_file, output_file=None):
    """
    读取指定txt文件，打乱行顺序后保存到新文件
    :param input_file: 输入文件名（需带路径）
    :param output_file: 输出文件名，默认生成 shuffled_原文件名
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        random.shuffle(lines)

        # 修正路径生成逻辑：将shuffled_添加至原文件名前
        if output_file is None:
            dir_name = os.path.dirname(input_file)
            base_name = os.path.basename(input_file)
            output_file = os.path.join(dir_name, f"shuffled_{base_name}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"生成成功！输出文件：{output_file}")

    except FileNotFoundError:
        print(f"错误：文件 {input_file} 不存在")
    except Exception as e:
        print(f"发生未知错误：{str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        input_path = filedialog.askopenfilename()
        if input_path:  # 确保用户未取消选择
            shuffle_titles(input_path)
        else:
            print("未选择文件")
    else:
        shuffle_titles(sys.argv[1])