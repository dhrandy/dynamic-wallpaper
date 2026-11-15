# Dynamic Wallpaper for KDE Plasma

A tiny Python script that changes your wallpaper based on the time of day,
using your real sunrise and sunset times. No network, no extra packages,
just Python 3 and four images.

It picks one of four wallpapers:

- **Dawn** — 30 minutes either side of sunrise
- **Day** — from 30 minutes after sunrise until 30 minutes before sunset
- **Dusk** — 30 minutes either side of sunset
- **Night** — everything else

Sunrise and sunset are calculated from your latitude and longitude, so they
stay correct all year as the days get longer and shorter.

If you only have three images, use the same file for dawn and dusk. See
"How to edit it" below.

## What you need

- KDE Plasma (uses `plasma-apply-wallpaperimage`)
- Python 3 (already on most Linux systems)
- Four wallpaper images: one for day, one for dawn, one for dusk, one for night

## Quick start

**1. Put your images in place.**

Save four images as:

```
~/Pictures/Wallpaper/day.jpg
~/Pictures/Wallpaper/dawn.jpg
~/Pictures/Wallpaper/dusk.jpg
~/Pictures/Wallpaper/night.jpg
```

Any image format Plasma supports works (JPG, PNG). The names are the
defaults, you can use different names or paths, see below.

**2. Find your latitude and longitude.**

Search the web for your city, for example "Raleigh NC latitude longitude".
You need two decimal numbers. Latitude is positive north of the equator,
longitude is negative west of Greenwich (all of the USA is negative).

**3. Test it.**

```bash
python3 dynamic-wallpaper.py --lat 40.71 --lon -74.00
```

Replace the numbers with your own. It prints the time, today's sunrise and
sunset, and which image it picked. Your wallpaper should change right away
if it is a different period than the last run.

**4. Run it automatically.**

The included systemd timer runs it every 5 minutes, starting 1 minute after
you log in. It only changes the wallpaper when the period changes, so
running it often costs nothing.

```bash
# Copy the files into place
cp dynamic-wallpaper.py ~/
cp dynamic-wallpaper.service dynamic-wallpaper.timer ~/.config/systemd/user/

# Edit the service file and put your real lat/lon in the ExecStart line
nano ~/.config/systemd/user/dynamic-wallpaper.service

# Turn the timer on
systemctl --user daemon-reload
systemctl --user enable --now dynamic-wallpaper.timer
```

Check it is running with `systemctl --user status dynamic-wallpaper.timer`.

## How to edit it

Everything you are likely to change is a command-line option. You do not
need to edit the Python code.

### Change your images

Point each period at a different file:

```bash
python3 dynamic-wallpaper.py --lat 40.71 --lon -74.00 \
  --day ~/Pictures/morning.png \
  --dawn ~/Pictures/sunrise.png \
  --dusk ~/Pictures/sunset.png \
  --night ~/Pictures/stars.png
```

If you only have three images, pass the same file for `--dawn` and `--dusk`:

```bash
python3 dynamic-wallpaper.py --lat 40.71 --lon -74.00 \
  --day ~/Pictures/morning.png \
  --dawn ~/Pictures/golden-hour.png \
  --dusk ~/Pictures/golden-hour.png \
  --night ~/Pictures/stars.png
```

If you use the systemd service, edit the `ExecStart` line in
`~/.config/systemd/user/dynamic-wallpaper.service` the same way, then run
`systemctl --user daemon-reload` and `systemctl --user restart dynamic-wallpaper.timer`.

### Change your location

Just change `--lat` and `--lon`. Find your numbers the same way as in the
quick start. No other changes needed, sunrise and sunset are recalculated
every run.

### Change how long dawn and dusk last

The dawn and dusk images each cover 30 minutes either side of sunrise and
sunset by default. To make them 45 minutes instead:

```bash
python3 dynamic-wallpaper.py --lat 40.71 --lon -74.00 --window 45
```

Set `--window 0` if you want it to switch straight from day to night with
no dawn or dusk period.

### Change how often it checks

Edit `dynamic-wallpaper.timer` and change `OnCalendar=*:0/5` to whatever
you want, for example `*:0/10` for every 10 minutes or `*:0/1` for every
minute. Then run:

```bash
systemctl --user daemon-reload
systemctl --user restart dynamic-wallpaper.timer
```

Five minutes is plenty. The script only changes the wallpaper when the
period changes, so checking more often does not cost anything except a
tiny bit of CPU every few minutes.

The timer uses a wall-clock schedule (`OnCalendar`) with `Persistent=true`,
so if the PC was asleep when a run was due, it fires immediately on wake
instead of waiting for the next interval. It also runs one minute after boot
(`OnBootSec=1min`).

### Use different images for dawn and dusk

That is the default now, four images with `--dawn` and `--dusk` as separate
options. If you only have one golden-hour image, pass the same file for both,
see "Change your images" above.

## How it works

- Sunrise and sunset are calculated with the NOAA solar approximation, a
  well-known formula that is accurate to about a minute. It needs only the
  date and your latitude and longitude, no network or location services.
- The script remembers the last image it set in a small state file
  (`~/.cache/dynamic-wallpaper.state` by default). If the image has not
  changed, it does nothing, so it is safe to run every few minutes.
- It sets the wallpaper with `plasma-apply-wallpaperimage`, the standard
  KDE Plasma command line tool.
- If your wallpaper does not update after a period change, run the script
  by hand once and check the output. It prints the current time, sunrise,
  sunset, and the image it picked.

## Files

| File | What it is |
| --- | --- |
| `dynamic-wallpaper.py` | The script. One file, standard library only. |
| `dynamic-wallpaper.service` | Systemd service that runs the script once. Edit the lat/lon in here. |
| `dynamic-wallpaper.timer` | Systemd timer that runs the service every 5 minutes. |

## License

MIT. Use it however you like.
