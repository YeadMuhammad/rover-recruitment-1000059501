import csv
import math
import sys

earth_radius = 6371000.0
arrival_radius = 3.0
stopped_speed_limit = 0.5
green_duration = 5
max_speed = 20.0 


def get_distance(lat1, lon1, lat2, lon2):

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius * c


def to_float(s):

    try:
        v = float(str(s).strip())
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def valid_coord(lat, lon):

    return (lat is not None and lon is not None
            and -90 <= lat <= 90 and -180 <= lon <= 180)


def load_targets(filepath):
    waypoints = []
    try:
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if len(row) < 3:
                    continue
                lat, lon = to_float(row[-2]), to_float(row[-1])
                if valid_coord(lat, lon):          
                    waypoints.append((lat, lon))
    except OSError:
        pass
    return waypoints


def load_log(filepath):
    rows = {}
    with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            t = to_float(row[0])
            if t is None:
                continue
            t = int(round(t))
            mode = row[1].strip().upper()
            lat = to_float(row[2]) if len(row) > 2 else None
            lon = to_float(row[3]) if len(row) > 3 else None
            if not valid_coord(lat, lon):
                lat = lon = None
            rows[t] = (t, mode, lat, lon)
    return [rows[t] for t in sorted(rows)]



def main():

    if len(sys.argv) < 3:
        print("Usage: python light.py <log> <targets>", file=sys.stderr)
        sys.exit(1)


    waypoints = load_targets(sys.argv[2])
    log = load_log(sys.argv[1])


    target_idx = 0
    prev_time = prev_lat = prev_lon = None 
    green_until = None  
    last_mode = "MANUAL"


    for time_s, mode, lat, lon in log:
        if mode not in ("AUTO", "MANUAL"):
            mode = last_mode                
        last_mode = mode

        
        speed = None
        if lat is not None and prev_time is not None and time_s > prev_time:
            speed = get_distance(prev_lat, prev_lon, lat, lon) / (time_s - prev_time)
            if speed > max_speed:
                lat = lon = None
                speed = None
        if lat is not None:
            prev_time, prev_lat, prev_lon = time_s, lat, lon


        in_green = green_until is not None and time_s <= green_until
        if not in_green:
            green_until = None
            if (mode == "AUTO" and lat is not None and speed is not None
                    and target_idx < len(waypoints)):
                t_lat, t_lon = waypoints[target_idx]
                if (get_distance(lat, lon, t_lat, t_lon) <= arrival_radius
                        and speed < stopped_speed_limit):
                    green_until = time_s + green_duration - 1
                    target_idx += 1
                    in_green = True


        light = "green" if in_green else ("red" if mode == "AUTO" else "blue")
        print(f"{time_s},{light}")


if __name__ == "__main__":
    main()