#!/bin/bash
BAG=~/catkin_ws/src/Localiza-o-Robotica/bags/husky_trajectory.bag

for MODE in odom odom_imu odom_imu_gps; do
    echo "=== Rodando modo: $MODE ==="
    roslaunch localiza_o_robotica replay_bag.launch mode:=$MODE bag:=$BAG
    sleep 3   # aguarda escrita dos arquivos de métricas
done