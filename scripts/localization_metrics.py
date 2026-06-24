#!/usr/bin/env python
import csv
import math
import os

import rospy
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion


def yaw_from_quaternion(q):
    return euler_from_quaternion([q.x, q.y, q.z, q.w])[2]


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class LocalizationMetrics(object):
    def __init__(self):
        self.run_name = rospy.get_param("~run_name", "odom")
        self.output_dir = os.path.expanduser(rospy.get_param("~output_dir", "~/catkin_ws/src/Localiza-o-Robotica/results"))
        self.filtered_topic = rospy.get_param("~filtered_topic", "/odometry/filtered")
        self.gt_topic = rospy.get_param("~gt_topic", "/gt/odom")
        self.max_pair_dt = rospy.Duration(rospy.get_param("~max_pair_dt", 0.1))
        self.gt_offset_x = rospy.get_param("~gt_offset_x", 0.0)
        self.gt_offset_y = rospy.get_param("~gt_offset_y", 0.0)
        
        self.latest_gt = None
        self.rows = []
        self.sum_sq_pos = 0.0
        self.sum_sq_yaw = 0.0
        self.count = 0
        self.final_position_error = 0.0
        self.final_yaw_error = 0.0

        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        rospy.Subscriber(self.gt_topic, Odometry, self.gt_cb, queue_size=50)
        rospy.Subscriber(self.filtered_topic, Odometry, self.filtered_cb, queue_size=50)
        rospy.on_shutdown(self.write_results)

    def gt_cb(self, msg):
        self.latest_gt = msg

    def filtered_cb(self, msg):
        if self.latest_gt is None:
            return

        dt = abs(msg.header.stamp - self.latest_gt.header.stamp)
        if msg.header.stamp != rospy.Time() and self.latest_gt.header.stamp != rospy.Time() and dt > self.max_pair_dt:
            return

        fx = msg.pose.pose.position.x
        fy = msg.pose.pose.position.y
        gx = self.latest_gt.pose.pose.position.x + self.gt_offset_x
        gy = self.latest_gt.pose.pose.position.y + self.gt_offset_y

        pos_error = math.hypot(fx - gx, fy - gy)
        yaw_error = wrap_angle(yaw_from_quaternion(msg.pose.pose.orientation) -
                               yaw_from_quaternion(self.latest_gt.pose.pose.orientation))

        stamp = msg.header.stamp.to_sec() if msg.header.stamp else rospy.Time.now().to_sec()
        self.rows.append([stamp, fx, fy, gx, gy, pos_error, yaw_error])
        self.sum_sq_pos += pos_error ** 2
        self.sum_sq_yaw += yaw_error ** 2
        self.count += 1
        self.final_position_error = pos_error
        self.final_yaw_error = yaw_error

    def write_results(self):
        if not self.rows:
            rospy.logwarn("No metric samples collected for run '%s'", self.run_name)
            return

        csv_path = os.path.join(self.output_dir, "%s_metrics.csv" % self.run_name)
        summary_path = os.path.join(self.output_dir, "%s_summary.txt" % self.run_name)
        plot_path = os.path.join(self.output_dir, "%s_plot.png" % self.run_name)

        with open(csv_path, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["time", "filtered_x", "filtered_y", "gt_x", "gt_y", "position_error", "yaw_error_rad"])
            writer.writerows(self.rows)

        rmse_pos = math.sqrt(self.sum_sq_pos / self.count)
        rmse_yaw = math.sqrt(self.sum_sq_yaw / self.count)
        with open(summary_path, "w") as summary:
            summary.write("run_name: %s\n" % self.run_name)
            summary.write("samples: %d\n" % self.count)
            summary.write("rmse_position_m: %.6f\n" % rmse_pos)
            summary.write("final_position_error_m: %.6f\n" % self.final_position_error)
            summary.write("rmse_yaw_rad: %.6f\n" % rmse_yaw)
            summary.write("final_yaw_error_rad: %.6f\n" % self.final_yaw_error)

        self.write_plot(plot_path)
        rospy.loginfo("Metrics saved to %s", self.output_dir)

    def write_plot(self, plot_path):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            rospy.logwarn("matplotlib not available; skipping PNG plot")
            return

        t0 = self.rows[0][0]
        times = [row[0] - t0 for row in self.rows]
        errors = [row[5] for row in self.rows]
        fx = [row[1] for row in self.rows]
        fy = [row[2] for row in self.rows]
        gx = [row[3] for row in self.rows]
        gy = [row[4] for row in self.rows]

        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        axes[0].plot(gx, gy, label="gt")
        axes[0].plot(fx, fy, label="filtered")
        axes[0].set_title("Trajetoria")
        axes[0].set_xlabel("x [m]")
        axes[0].set_ylabel("y [m]")
        axes[0].axis("equal")
        axes[0].legend()

        axes[1].plot(times, errors)
        axes[1].set_title("Erro de posicao")
        axes[1].set_xlabel("tempo [s]")
        axes[1].set_ylabel("erro [m]")
        fig.tight_layout()
        fig.savefig(plot_path, dpi=140)


if __name__ == "__main__":
    rospy.init_node("localization_metrics")
    LocalizationMetrics()
    rospy.spin()
