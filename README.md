# Localiza-o-Robotica

Pacote ROS para comparar tres configuracoes de localizacao do Clearpath Husky no Gazebo usando o `ekf_localization_node` do pacote `robot_localization`:

- odometria;
- odometria + IMU;
- odometria + IMU + GPS convertido para odometria local.

O topico `/gt/odom` e publicado apenas para avaliacao e nunca e usado como entrada do filtro.

## Configuracao do ambiente

O projeto possui um `dockerfile` para preparar o ambiente ROS/Gazebo usado nos testes. Baixe esse arquivo individualmente, coloque-o em uma pasta de trabalho e gere a imagem Docker a partir dele:

```bash
docker build -t localiza_o_robotica_ros -f dockerfile .
```

Depois que a imagem for criada, inicie o container:

```bash
docker run -it \
  --env DISPLAY=$DISPLAY \
  --env QT_X11_NO_MITSHM=1 \
  --volume /tmp/.X11-unix:/tmp/.X11-unix:rw \
  --network host \
  --name ros_lar_run \
  <sua_imagem>
```

Substitua `<sua_imagem>` pelo nome da imagem gerada no passo anterior, por exemplo `localiza_o_robotica_ros`.

No host, antes de abrir interfaces graficas pelo Docker, libere o acesso ao X11:

```bash
xhost +local:docker
```

Dentro do container, clone este repositorio dentro de `~/catkin_ws/src/`:

```bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
git clone <link-do-repositorio> Localiza-o-Robotica
```

Somente depois disso compile o workspace:

```bash
cd ~/catkin_ws
catkin build localiza_o_robotica
source devel/setup.bash
```

Sempre que abrir um novo terminal no container, carregue o ambiente:

```bash
docker exec -it ros_lar_run bash
export LIBGL_ALWAYS_SOFTWARE=1
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
```

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

## Bag de teste

O repositorio ja inclui uma bag padrao em:

```bash
bags/husky_trajectory.bag
```

Voce pode usar essa bag diretamente para reproduzir os testes ou gravar sua propria trajetoria. Atencao: ao gravar uma nova bag no mesmo caminho, a bag padrao que vem no repositorio sera apagada/substituida.

## Gravando uma nova trajetoria

Abra quatro terminais dentro do container e carregue o ambiente em todos eles:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
```

Terminal 1:

```bash
roscore
```

Terminal 2:

```bash
roslaunch lar_gazebo lar_husky.launch
```

Terminal 3:

```bash
rosrun rqt_robot_steering rqt_robot_steering
```

Na interface do `rqt_robot_steering`, selecione o topico de comando do Husky, normalmente `/husky_velocity_controller/cmd_vel` ou `/cmd_vel`.

Terminal 4:

```bash
roslaunch localiza_o_robotica record_trajectory.launch \
  bag:=$(rospack find localiza_o_robotica)/bags/husky_trajectory.bag
```

Manipule o robo com o joystick gerado no Terminal 3. Depois de um tempo, pare a gravacao no Terminal 4 com `Ctrl+C`. O bag vai conter os topicos normalizados `/wheel/odom`, `/imu/data`, `/fix` e `/gt/odom`.

## Executando os testes

Para comparar os tres modos de localizacao, use o script:

```bash
cd ~/catkin_ws
source devel/setup.bash
rosrun localiza_o_robotica run_replay.sh
rosrun localiza_o_robotica compare_results.py
```

O script executa automaticamente os modos:

- `odom`
- `odom_imu`
- `odom_imu_gps`

Cada replay termina sozinho quando a bag acaba e grava os arquivos em `results/`:

```bash
results/<modo>_metrics.csv
results/<modo>_summary.txt
results/<modo>_plot.png
results/comparison_position_error.png
results/comparison_yaw_error.png
results/comparison_trajectories.png
```

## Metricas geradas

O script `localization_metrics.py` compara `/odometry/filtered` com `/gt/odom` e calcula:

- erro instantaneo de posicao;
- RMSE de posicao;
- erro final de posicao;
- RMSE de orientacao em yaw;
- erro final de orientacao em yaw.

## Resultados e discussao

Os resultados obtidos ficam versionados em `results/` e permitem comparar o desempenho dos tres modos. Em geral, a configuracao apenas com odometria tende a acumular mais erro ao longo do tempo. A configuracao com odometria + IMU melhora a estimativa de orientacao, enquanto a configuracao com odometria + IMU + GPS tende a reduzir o erro global de posicao por usar uma referencia absoluta convertida para odometria local.
