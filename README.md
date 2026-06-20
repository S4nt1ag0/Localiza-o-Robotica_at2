# Localiza-o-Robotica

Pacote ROS para comparar tres configuracoes de localizacao do Clearpath Husky no Gazebo usando o `ekf_localization_node` do pacote `robot_localization`:

- odometria;
- odometria + IMU;
- odometria + IMU + GPS convertido para odometria local.

O topico `/gt/odom` e publicado apenas para avaliacao e nunca e usado como entrada do filtro.

## Topicos

Entradas esperadas:

- `/wheel/odom` (`nav_msgs/Odometry`)
- `/imu/data` (`sensor_msgs/Imu`)
- `/fix` (`sensor_msgs/NavSatFix`)
- `/gt/odom` (`nav_msgs/Odometry`, gerado a partir do Gazebo)

Saidas principais:

- `/gps/odom` (`nav_msgs/Odometry`)
- `/odometry/filtered` (`nav_msgs/Odometry`)
- `results/<modo>_metrics.csv`
- `results/<modo>_summary.txt`
- `results/<modo>_plot.png`

## Como executar

Compile o workspace:

```bash
cd ~/catkin_ws
catkin build localiza_o_robotica
source devel/setup.bash
```

Este workspace ja foi criado com `catkin build`. Nao misture com
`catkin_make`, porque ele vai recusar o build space existente e o pacote novo
nao sera registrado no `devel/setup.bash`.

Abra o mundo simulado do LaR/Gazebo com o Husky em outro terminal. Depois execute uma configuracao por vez:

```bash
roslaunch localiza_o_robotica localization.launch mode:=odom
roslaunch localiza_o_robotica localization.launch mode:=odom_imu
roslaunch localiza_o_robotica localization.launch mode:=odom_imu_gps
```

Se os topicos do simulador tiverem nomes diferentes, passe-os como argumentos:

```bash
roslaunch localiza_o_robotica localization.launch \
  mode:=odom_imu_gps \
  wheel_odom_topic:=/husky_velocity_controller/odom \
  imu_topic:=/imu/data \
  fix_topic:=/fix
```

Finalize o launch com `Ctrl+C` para gravar automaticamente os arquivos em `results/`.


## Gravando uma trajetoria para comparar

Com o `roscore` e o Gazebo rodando, grave uma trajetoria uma unica vez:

```bash
cd ~/catkin_ws
source devel/setup.bash
roslaunch localiza_o_robotica record_trajectory.launch \
  bag:=$(rospack find localiza_o_robotica)/bags/husky_trajectory.bag
```

Enquanto esse launch estiver rodando, mova o Husky pelo mapa. Quando terminar, use
`Ctrl+C`. O bag vai conter os topicos normalizados `/wheel/odom`, `/imu/data`,
`/fix` e `/gt/odom`.

Depois compare os tres metodos usando exatamente a mesma gravacao:

```bash
roslaunch localiza_o_robotica replay_bag.launch mode:=odom
roslaunch localiza_o_robotica replay_bag.launch mode:=odom_imu
roslaunch localiza_o_robotica replay_bag.launch mode:=odom_imu_gps
```

Cada replay termina sozinho quando o bag acaba e grava os arquivos em `results/`:

```bash
cat $(rospack find localiza_o_robotica)/results/odom_summary.txt
cat $(rospack find localiza_o_robotica)/results/odom_imu_summary.txt
cat $(rospack find localiza_o_robotica)/results/odom_imu_gps_summary.txt
```

Ou gere uma tabela direta:

```bash
rosrun localiza_o_robotica compare_results.py
```

## Metricas geradas

O no `localization_metrics.py` compara `/odometry/filtered` com `/gt/odom` e calcula:

- erro instantaneo de posicao;
- RMSE de posicao;
- erro final de posicao;
- RMSE de orientacao em yaw;
- erro final de orientacao em yaw.

## Discussao esperada dos resultados

A configuracao apenas com odometria tende a acumular deriva ao longo do tempo. Com IMU, a estimativa de orientacao melhora e a trajetoria costuma ficar mais estavel em curvas. Com GPS, a posicao absoluta ajuda a reduzir o erro acumulado, principalmente em trajetorias longas, mas a qualidade final depende do ruido e da taxa do sensor GPS.
