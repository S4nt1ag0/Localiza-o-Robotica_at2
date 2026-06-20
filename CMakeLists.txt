cmake_minimum_required(VERSION 3.0.2)
project(localiza_o_robotica)

find_package(catkin REQUIRED COMPONENTS
  rospy
  geometry_msgs
  nav_msgs
  sensor_msgs
  std_msgs
  tf
  gazebo_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/gps_to_odom.py
  scripts/gt_odom_publisher.py
  scripts/localization_metrics.py
  scripts/compare_results.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY bags config launch results
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
