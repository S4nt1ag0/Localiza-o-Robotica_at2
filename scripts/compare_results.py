#!/usr/bin/env python
import argparse
import os


DEFAULT_MODES = ["odom", "odom_imu", "odom_imu_gps"]
METRICS = [
    ("samples", "samples"),
    ("rmse_position_m", "rmse_pos_m"),
    ("final_position_error_m", "final_pos_m"),
    ("rmse_yaw_rad", "rmse_yaw_rad"),
    ("final_yaw_error_rad", "final_yaw_rad"),
]


def read_summary(path):
    data = {}
    with open(path) as summary:
        for line in summary:
            if ":" not in line:
                continue
            key, value = line.strip().split(":", 1)
            data[key.strip()] = value.strip()
    return data


def fmt(value):
    try:
        return "%.6f" % float(value)
    except (TypeError, ValueError):
        return value or "-"


def main():
    parser = argparse.ArgumentParser(description="Compare localization summary files.")
    parser.add_argument("--results-dir", default=os.path.expanduser("~/catkin_ws/src/Localiza-o-Robotica/results"))
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES)
    args = parser.parse_args()

    rows = []
    missing = []
    for mode in args.modes:
        path = os.path.join(args.results_dir, "%s_summary.txt" % mode)
        if not os.path.exists(path):
            missing.append(path)
            continue
        data = read_summary(path)
        rows.append([mode] + [fmt(data.get(key)) for key, _ in METRICS])

    if missing:
        print("Missing summary files:")
        for path in missing:
            print("  %s" % path)

    if not rows:
        return 1

    headers = ["mode"] + [label for _, label in METRICS]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    def print_row(values):
        print("  ".join(value.ljust(width) for value, width in zip(values, widths)))

    print_row(headers)
    print_row(["-" * width for width in widths])
    for row in rows:
        print_row(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
