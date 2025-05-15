import tkinter  # 修正拼写错误
from tkinter import filedialog

Folderpath = filedialog.askdirectory()
Filepath = filedialog.askopenfilename()

print('Folder:', Folderpath)
print('Filepath:', Filepath)