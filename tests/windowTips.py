from win10toast import ToastNotifier
tip_one = 0
while tip_one < 20:
    toaster = ToastNotifier()
    toaster.show_toast("通知标题", "通知内容", duration=0)
    tip_one += 1