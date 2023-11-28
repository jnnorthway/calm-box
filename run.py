import time
import yaml
import pathlib
from rpi_ws281x import Adafruit_NeoPixel, Color


def load_config():
    calm_directory = pathlib.Path(__file__).parent.resolve()
    config_path = pathlib.Path.joinpath(calm_directory, "config.yaml")
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
    return range_two[0] + (valueScaled * span_two)


def color_fade_off(strip, timer_length, sleep_time_ms=20):
    """Fade strip to black."""
    start_brightness = strip.getBrightness()
    current_time = time.time()
    end_time = current_time + timer_length
    while current_time < end_time:
        current_time = time.time()
        progress = end_time - current_time
        px_brightness = interpolate(progress, (0, timer_length), (start_brightness, 0))
        strip.setBrightness(px_brightness)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)


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
        current_time = time.time()
        progress = end_time - current_time
        px_brightness = interpolate(progress, (0, timer_length), (0, end_brightness))
        strip.setBrightness(px_brightness)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)


def color_blink(strip, brightness, timer_length, sleep_time_ms=20):
    current_time = time.time()
    end_time = current_time + timer_length
    while current_time < end_time:
        color_fade_off(strip, 5)
        time.sleep(sleep_time_ms / 1000.0)
        color_fade_on(strip, brightness, 5)
        time.sleep(sleep_time_ms / 1000.0)
    color_fade_off(strip, 5)


def get_timer_color(timer_length, current_time, end_time, start_color, end_color):
    progress = end_time - current_time
    r = interpolate(progress, (0, timer_length), (start_color.r, end_color.r))
    g = interpolate(progress, (0, timer_length), (start_color.g, end_color.g))
    b = interpolate(progress, (0, timer_length), (start_color.b, end_color.b))
    return Color(r, g, b)


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
    current_time = time.time()
    transition_time = timer_length * 0.05
    timer_length -= transition_time
    half_time = timer_length / 2
    middle_time = current_time + half_time
    end_time = current_time + timer_length
    color_fade_on(strip, brightness, 5, start_color)
    while current_time < middle_time:
        current_time = time.time()
        px_color = get_timer_color(
            half_time, current_time, middle_time, start_color, middle_color
        )
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, px_color)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)
    while current_time < end_time:
        current_time = time.time()
        px_color = get_timer_color(
            half_time, current_time, end_time, middle_color, end_color
        )
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, px_color)
        strip.show()
        time.sleep(sleep_time_ms / 1000.0)
    color_blink(strip, brightness, transition_time)


def start_timer(config, mode):
    if mode == 1:
        mode_str = "mode_one"
    else:
        mode_str = "mode_two"

    color_start = Color(*config["general"][mode_str]["start"])
    color_middle = Color(*config["general"][mode_str]["middle"])
    color_end = Color(*config["general"][mode_str]["end"])
    timer_length = Color(*config["general"]["timer_length"])
    brightness = (config["led"]["brightness"],)
    timer(
        strip,
        color_start,
        color_middle,
        color_end,
        brightness,
        timer_length,
    )


if __name__ == "__main__":
    config = load_config()
    strip = Adafruit_NeoPixel(
        config["led"]["count"],
        config["led"]["pin"],
        config["led"]["frequency"],
        config["led"]["dma"],
        config["led"]["inverted"],
        config["led"]["brightness"],
        config["led"]["channel"],
    )
    strip.begin()
    print("Starting loop...")
    print("Press Ctrl-C to quit.")
    while True:
        try:
            start_timer(config, mode=1)
        except KeyboardInterrupt:
            color_fade_off(strip, 3)
            exit(0)
        except Exception as ex:
            print(f"Exception: {ex}")
            color_fade_off(strip, 3)
