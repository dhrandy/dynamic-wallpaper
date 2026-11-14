#!/usr/bin/env python3
"""Set your KDE Plasma wallpaper based on the time of day.

Picks one of three images (day, dusk/dawn, night) using your real
sunrise and sunset times, calculated from your latitude and longitude.
No network needed, no extra packages, just Python 3.

How it decides:
  dawn/dusk:  30 minutes either side of sunrise and sunset -> duskdawn image
  day:        sunrise + 30 min to sunset - 30 min          -> day image
  night:      everything else                              -> night image

It only changes the wallpaper when the image is different from last
time, so it is cheap to run every few minutes from a systemd timer.
"""

import argparse
import math
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


def sun_times_utc(day, lat, lon):
    """Return (sunrise, sunset) in UTC for a given date and location.

    NOAA solar approximation, accurate to about a minute. No network.
    """
    n = day.timetuple().tm_yday
    gamma = 2 * math.pi / 365.0 * (n - 1)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma)
                       - 0.032077 * math.sin(gamma)
                       - 0.014615 * math.cos(2 * gamma)
                       - 0.040849 * math.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.00148 * math.sin(3 * gamma))
    lat_r = math.radians(lat)
    cos_ha = (math.cos(math.radians(90.833))
              - math.sin(lat_r) * math.sin(decl)) / (math.cos(lat_r) * math.cos(decl))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    ha = math.degrees(math.acos(cos_ha))
    noon_min = 720.0 - 4.0 * lon - eqtime
    sunrise_min = noon_min - ha * 4.0
    sunset_min = noon_min + ha * 4.0
    base = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return (base + timedelta(minutes=sunrise_min),
            base + timedelta(minutes=sunset_min))


def pick_image(now, sunrise, sunset, window, day_img, duskdawn_img, night_img):
    """Pick the right image for the current time. Returns (image, period name)."""
    dawn_start = sunrise - timedelta(minutes=window)
    dawn_end = sunrise + timedelta(minutes=window)
    dusk_start = sunset - timedelta(minutes=window)
    dusk_end = sunset + timedelta(minutes=window)
    if dawn_start <= now < dawn_end or dusk_start <= now < dusk_end:
        return duskdawn_img, "duskdawn"
    if dawn_end <= now < dusk_start:
        return day_img, "day"
    return night_img, "night"


def main():
    home = Path.home()
    parser = argparse.ArgumentParser(
        description="Set your KDE Plasma wallpaper based on sunrise and sunset.")
    parser.add_argument("--lat", type=float, required=True,
                        help="Your latitude in decimal degrees (e.g. 40.71 for New York)")
    parser.add_argument("--lon", type=float, required=True,
                        help="Your longitude in decimal degrees, negative for west (e.g. -74.00)")
    parser.add_argument("--day", default=str(home / "Pictures/Wallpaper/day.jpg"),
                        help="Daytime image (default: ~/Pictures/Wallpaper/day.jpg)")
    parser.add_argument("--duskdawn", default=str(home / "Pictures/Wallpaper/duskdawn.jpg"),
                        help="Dawn/dusk image (default: ~/Pictures/Wallpaper/duskdawn.jpg)")
    parser.add_argument("--night", default=str(home / "Pictures/Wallpaper/night.jpg"),
                        help="Night image (default: ~/Pictures/Wallpaper/night.jpg)")
    parser.add_argument("--window", type=int, default=30,
                        help="Minutes either side of sunrise/sunset to use the dusk/dawn image (default: 30)")
    parser.add_argument("--state", default=str(home / ".cache/dynamic-wallpaper.state"),
                        help="File that remembers the last image used (default: ~/.cache/dynamic-wallpaper.state)")
    args = parser.parse_args()

    now = datetime.now().astimezone()
    sunrise_utc, sunset_utc = sun_times_utc(now.date(), args.lat, args.lon)
    sunrise = sunrise_utc.astimezone(now.tzinfo)
    sunset = sunset_utc.astimezone(now.tzinfo)

    img, period = pick_image(now, sunrise, sunset, args.window,
                             args.day, args.duskdawn, args.night)

    # Only change the wallpaper if it is different from last time.
    last = ""
    try:
        with open(args.state) as f:
            last = f.read().strip()
    except OSError:
        pass
    if last != img:
        subprocess.run(["plasma-apply-wallpaperimage", img], check=False)
        os.makedirs(os.path.dirname(args.state), exist_ok=True)
        with open(args.state, "w") as f:
            f.write(img)

    print(f"{now:%H:%M} sunrise {sunrise:%H:%M} sunset {sunset:%H:%M} -> {period} {img}")


if __name__ == "__main__":
    main()
