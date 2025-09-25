from win10toast import ToastNotifier


def show_notification(text: str, color: str) -> None:
    toaster = ToastNotifier()
    if color == "green":
        title = "Success"
    elif color == "amber":
        title = "Warning"
    elif color == "red":
        title = "Error"
    else:
        title = "Notification"
    try:
        toaster.show_toast(title, text, duration=3, threaded=True)
    except Exception as e:
        print(f"Failed to show notification: {e}")