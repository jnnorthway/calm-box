import os
import time
import yaml
import pathlib
import random
from threading import Thread
from gpiozero import Button
from rpi_ws281x import Adafruit_NeoPixel, Color


MODE = 1
CONFIG = None
STRIP = None
RUNNING = False


def load_config():
    calm_directory = pathlib.Path(__file__).parent.resolve()
    config_path = os.path.join(calm_directory, "config.yaml")
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    if config:
        return config
    print(f"Failed to load config from: {config_path}")
    exit(1)


def interpolate(value, range_one, range_two):
    span_one = range_one[1] - range_one[0]
    span_two = range_two[1] - range_two[0]
    valueScaled = float(value - range_one[0]) / float(span_one)
    return int(range_two[0] + (valueScaled * span_two))


def color_fade_off(strip, brightness, timer_length, sleep_time_ms=20):
    """Fade strip to black."""
    if strip.getBrightness() == 0:
        return
    current_time = time.time()
    end_time = current_time + timer_length
    while current_time < end_time:
        progress = timer_length - (end_time - current_time)
        px_brightness = interpolate(progress, (0, timer_length), (brightness, 0))
        strip.setBrightness(px_brightness)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)
        current_time = time.time()
    strip.setBrightness(0)
    strip.show()


def color_fade_on(
    strip, end_brightness, timer_length, start_color=None, sleep_time_ms=20
):
    """Fade strip to color."""
    strip.setBrightness(0)
    if start_color:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, start_color)
    strip.show()
    current_time = time.time()
    end_time = current_time + timer_length
    while current_time < end_time:
        progress = timer_length - (end_time - current_time)
        px_brightness = interpolate(progress, (0, timer_length), (0, end_brightness))
        strip.setBrightness(px_brightness)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)
        current_time = time.time()


def color_blink(strip, brightness, timer_length, sleep_time_ms=20):
    current_time = time.time()
    end_time = current_time + timer_length
    while current_time < end_time:
        color_fade_off(strip, brightness, 5)
        time.sleep(sleep_time_ms / 1000.0)
        color_fade_on(strip, brightness, 5)
        time.sleep(sleep_time_ms / 1000.0)
        current_time = time.time()
    color_fade_off(strip, brightness, 5)


def get_timer_color(timer_length, current_time, end_time, start_color, end_color):
    progress = timer_length - (end_time - current_time)
    r = interpolate(progress, (0, timer_length), (start_color.r, end_color.r))
    g = interpolate(progress, (0, timer_length), (start_color.g, end_color.g))
    b = interpolate(progress, (0, timer_length), (start_color.b, end_color.b))
    return Color(r, g, b)


def get_dance_colour():
    return Color(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def dance_dance():
    """Dance!"""
    global MODE, CONFIG, STRIP, RUNNING
    if MODE == 1:
        speed = 5
    else:
        speed = 0.5
    RUNNING = True
    brightness = int(CONFIG["led"]["brightness"])
    color_fade_on(STRIP, brightness, 5, get_dance_colour())
    while RUNNING:
        color_fade_off(STRIP, brightness, speed)
        if not RUNNING:
            return
        color_fade_on(STRIP, brightness, speed, get_dance_colour())
    color_fade_off(STRIP, brightness, 2)


def timer(
    strip,
    start_color,
    middle_color,
    end_color,
    brightness,
    timer_length=60,
    sleep_time_ms=20,
):
    """transition between colors over time period."""
    global RUNNING
    current_time = time.time()
    transition_time = timer_length * 0.05
    timer_length -= transition_time
    half_time = timer_length / 2
    middle_time = current_time + half_time
    end_time = current_time + timer_length
    RUNNING = True
    color_fade_on(strip, brightness, 5, start_color)
    while current_time < middle_time and RUNNING:
        px_color = get_timer_color(
            half_time, current_time, middle_time, start_color, middle_color
        )
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, px_color)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)
        current_time = time.time()
    while current_time < end_time and RUNNING:
        px_color = get_timer_color(
            half_time, current_time, end_time, middle_color, end_color
        )
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, px_color)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)
        current_time = time.time()
    if RUNNING:
        color_blink(strip, brightness, transition_time)
    else:
        color_fade_off(STRIP, brightness, 0.5)


def start_timer():
    global MODE, CONFIG, STRIP
    if MODE == 1:
        mode_str = "mode_one"
    else:
        mode_str = "mode_two"
    color_start = Color(*CONFIG["general"][mode_str]["start"])
    color_middle = Color(*CONFIG["general"][mode_str]["middle"])
    color_end = Color(*CONFIG["general"][mode_str]["end"])
    timer_length = CONFIG["general"][mode_str]["timer_length"]
    brightness = int(CONFIG["led"]["brightness"])
    timer(
        STRIP,
        color_start,
        color_middle,
        color_end,
        brightness,
        timer_length,
    )


def end_timer():
    global MODE, CONFIG
    MODE = 1
    brightness = int(CONFIG["led"]["brightness"])
    color_fade_off(STRIP, brightness, 3)


def start_up():
    global MODE, CONFIG, STRIP
    white = Color(255, 255, 255)
    brightness = int(CONFIG["led"]["brightness"])
    STRIP.setBrightness(0)
    color_fade_off(STRIP, brightness, 1)
    time.sleep(20 / 1000.0)
    color_fade_on(STRIP, brightness, 0.5, white)
    time.sleep(20 / 1000.0)
    color_fade_off(STRIP, brightness, 0.5)
    time.sleep(20 / 1000.0)
    color_fade_on(STRIP, brightness, 0.5)
    time.sleep(20 / 1000.0)
    color_fade_off(STRIP, brightness, 0.5)


def set_mode():
    global MODE, CONFIG, STRIP
    # Cycle the selection
    if MODE == 1:
        MODE = 2
    else:
        MODE = 1
    white = Color(255, 255, 255)
    brightness = int(CONFIG["led"]["brightness"])
    color_fade_off(STRIP, brightness, 1)
    time.sleep(20 / 1000.0)
    color_fade_on(STRIP, brightness, 1, white)
    time.sleep(20 / 1000.0)
    color_fade_off(STRIP, brightness, 1)
    if MODE == 2:
        time.sleep(20 / 1000.0)
        color_fade_on(STRIP, brightness, 1)
        time.sleep(20 / 1000.0)
        color_fade_off(STRIP, brightness, 1)


if __name__ == "__main__":
    CONFIG = load_config()
    STRIP = Adafruit_NeoPixel(
        CONFIG["led"]["count"],
        CONFIG["led"]["pin"],
        CONFIG["led"]["frequency"],
        CONFIG["led"]["dma"],
        CONFIG["led"]["inverted"],
        CONFIG["led"]["brightness"],
        CONFIG["led"]["channel"],
    )
    STRIP.begin()

    primary_btn = Button(CONFIG["button"]["primary"])
    # Click:
    #   if off: start timer
    #   else: reset timer
    # Hold:
    #   turn off timer
    secondary_btn = Button(CONFIG["button"]["secondary"])
    # Click:
    #   change mode + reset timer
    # Hold:
    #   dance dance

    pb_was_pressed = False
    pb_press_time = None
    sb_was_pressed = False
    sb_press_time = None
    start_timer_thread = Thread(target=start_timer, args=())
    dance_dance_thread = Thread(target=dance_dance, args=())
    brightness = int(CONFIG["led"]["brightness"])
    start_up()
    while True:
        try:
            if primary_btn.is_pressed and not pb_was_pressed:
                # New press, mark the time
                pb_press_time = time.time()
                pb_was_pressed = True
            elif pb_was_pressed and not primary_btn.is_pressed:
                # button released, check the time
                pb_was_pressed = False
                RUNNING = False
                if start_timer_thread.is_alive():
                    start_timer_thread.join()
                if dance_dance_thread.is_alive():
                    dance_dance_thread.join()
                if time.time() - pb_press_time > 1.5:
                    print("Primary button was held")
                    end_timer()
                else:
                    print("Primary button was pressed")
                    start_timer_thread = Thread(target=start_timer, args=())
                    start_timer_thread.start()
            if secondary_btn.is_pressed and not sb_was_pressed:
                # New press, mark the time
                sb_press_time = time.time()
                sb_was_pressed = True
            elif sb_was_pressed and not secondary_btn.is_pressed:
                # button released, check the time
                sb_was_pressed = False
                RUNNING = False
                if start_timer_thread.is_alive():
                    start_timer_thread.join()
                if dance_dance_thread.is_alive():
                    dance_dance_thread.join()
                if time.time() - sb_press_time > 4:
                    print("Secondary button was held")
                    dance_dance_thread = Thread(target=dance_dance, args=())
                    dance_dance_thread.start()
                else:
                    print("Secondary button was pressed")
                    set_mode()
        except KeyboardInterrupt:
            color_fade_off(STRIP, brightness, 3)
            exit(0)
        except Exception as ex:
            print(f"Exception: {ex}")
            color_fade_off(STRIP, brightness, 3)
