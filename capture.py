import mss
from PIL import Image
import pyautogui
import base64
from io import BytesIO


def detect_monitor_under_mouse() -> dict:
    """
    Detects the monitor that contains the current cursor position.

    Returns:
        dict: MSS monitor dictionary containing the cursor position.
              Returns the primary monitor if cursor is not found on any monitor.
    """
    cursor_x, cursor_y = pyautogui.position()
    with mss.mss() as sct:
        monitors = sct.monitors
        for monitor in monitors[1:]:  # Skip the first 'all monitors' entry
            if (monitor['left'] <= cursor_x < monitor['left'] + monitor['width'] and
                monitor['top'] <= cursor_y < monitor['top'] + monitor['height']):
                return monitor
        # If not found, return primary monitor (index 1)
        return monitors[1] if len(monitors) > 1 else monitors[0]


def capture_monitor(mon: dict) -> Image.Image:
    """
    Captures a full screenshot of the specified monitor.

    Args:
        mon (dict): MSS monitor dictionary specifying the monitor to capture.

    Returns:
        PIL.Image.Image: Screenshot of the monitor as a PIL Image.
    """
    with mss.mss() as sct:
        screenshot = sct.grab(mon)
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        return img


def crop_percent(img: Image.Image, top_pct: int, bot_pct: int) -> Image.Image:
    """
    Crops the top and bottom percentages from the image.

    Args:
        img (PIL.Image.Image): The input image.
        top_pct (int): Percentage of the image height to crop from the top (0-100).
        bot_pct (int): Percentage of the image height to crop from the bottom (0-100).

    Returns:
        PIL.Image.Image: The cropped image.
    """
    width, height = img.size
    top_crop = int(height * top_pct / 100)
    bot_crop = int(height * bot_pct / 100)
    cropped_img = img.crop((0, top_crop, width, height - bot_crop))
    return cropped_img


def downscale_max_width(img: Image.Image, max_w: int) -> Image.Image:
    """
    Downscales the image to a maximum width while maintaining aspect ratio.

    Args:
        img (PIL.Image.Image): The input image.
        max_w (int): The maximum width for the image.

    Returns:
        PIL.Image.Image: The downscaled image if original width exceeds max_w,
                         otherwise the original image.
    """
    width, height = img.size
    if width <= max_w:
        return img
    aspect_ratio = height / width
    new_height = int(max_w * aspect_ratio)
    resized_img = img.resize((max_w, new_height), Image.LANCZOS)
    return resized_img


def encode_png_base64(img: Image.Image) -> str:
    """
    Encodes the image to PNG format and returns it as a base64 data URL.

    Args:
        img (PIL.Image.Image): The input image.

    Returns:
        str: Base64 encoded PNG image in data URL format ('data:image/png;base64,<base64>').
    """
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"