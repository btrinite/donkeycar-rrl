# DIYRobocarsFr Hat

DIYRobocarsFr Hat is a daughter board (Hat) for Raspberry Pi or Nvidia Jeston Nano or any other SBC with Raspberry compatible GPIO to ease the built of autonomous small scale RC-style car like the Donkey car. You can find more about DIYRobocarsFr Hat here :
- [software](https://github.com/btrinite/robocars_hat)
- [hardware](https://github.com/btrinite/robocars_hat_hw)

## Main changes to integrate RobocarsHat :
- new part : [robocars_hat_ctrl.py](./donkeycar/parts/robocars_hat_ctrl.py) with new Class RobocarsHatInCtrl, which is both a part to add support for receiving throttle and steering command from an RC Receiver and also act as low level driver between raspberry pi/jetson nano and the hat (to control the serial port). The controler part is enabled by setting USE_ROBOCARSHAT_AS_CONTROLLER configuation key to True.
- updated [actuator.py](./donkeycar/parts/actuator.py) with a new Class RobocarsHat that is used to send throttle and steering orders to the hat, enabled by setting DRIVE_TRAIN_TYPE configuration key to ROBOCARSHAT.
- new set of config parameters (search ROBOCARSHAT)
- update [complete.py](./donkeycar/templates/complete.py) with instantiation of RobocarsHatInCtrl and RobocarsHat accordingly to configuration.

Warning : for Raspberry pi 3, you have to get rid of 'miniuart' and resplace it by the true UART device known as PL011.
You will most likely lose Bluetooth. You can check [here](https://www.circuits.dk/setup-raspberry-pi-3-gpio-uart/)

## Configuration options

### set serial port to use to connect RobocarsHat

The following configuration item is used to define the UART device to use to connect to the Hat (depends on SBC hardware and linux distro):
```
ROBOCARSHAT_SERIAL_PORT = '/dev/ttyTHS1'
``` 

### Enable RobocarsHat as the train driver

To use the RobocarsHat as the driver for ESC and Servo, set the following configuration :
```
DRIVE_TRAIN_TYPE = "ROBOCARSHAT"
```

The following configuration items can be used to calibrate the signal output.
It can be usefull to ensure ;in and ;ax does not exceed capacity of the hardware
```
ROBOCARSHAT_PWM_OUT_THROTTLE_MIN    =   1000
ROBOCARSHAT_PWM_OUT_THROTTLE_IDLE   =   1500
ROBOCARSHAT_PWM_OUT_THROTTLE_MAX    =   2000
ROBOCARSHAT_PWM_OUT_STEERING_MIN    =   1000
ROBOCARSHAT_PWM_OUT_STEERING_IDLE   =   1500
ROBOCARSHAT_PWM_OUT_STEERING_MAX    =   2000
```

### Enable RobocarsHat as the main controller

The following configuration item allow to enable RobocarsHat as main controller (receiving RC Channels from Hat) :
```
USE_ROBOCARSHAT_AS_CONTROLLER  = True
```

The following configuration items can be used to calibrate the signal input. See chapter Qualibration below.
```
ROBOCARSHAT_PWM_IN_THROTTLE_MIN    =   1000
ROBOCARSHAT_PWM_IN_THROTTLE_IDLE   =   1500
ROBOCARSHAT_PWM_IN_THROTTLE_MAX    =   2000
ROBOCARSHAT_PWM_IN_STEERING_MIN    =   1000
ROBOCARSHAT_PWM_IN_STEERING_IDLE   =   1500
ROBOCARSHAT_PWM_IN_STEERING_MAX    =   2000
ROBOCARSHAT_PWM_IN_AUX_MIN    =   1000
ROBOCARSHAT_PWM_IN_AUX_IDLE   =   1500
ROBOCARSHAT_PWM_IN_AUX_MAX    =   2000
```

Autocalibration of input idle (When Hat detect PWM activity on its input, first samples are considered as the actual idle value and transmitted to Donkey to adjust mapping):
```
ROBOCARSHAT_USE_AUTOCALIBRATION = True
```

discret throttling (instead of progressive throttling, cam be used to ease manual driving at 2 speed for example):
```
ROBOCARSHAT_THROTTLE_DISCRET = None 
```

prevent car from driving too fast / lose control:
```
ROBOCARSHAT_THROTTLE_FLANGER = [-0.2,0.2] 
```

### Brake and automatic brake
Reverse throttle to apply to brake when pilot is disengaged :
```
ROBOCARSHAT_BRAKE_ON_IDLE_THROTTLE = 0.2
```

Disable filter on double throttle reverse sequance to engage reverse gear (depends on ESC behavior) :
```
THROTTLE_BRAKE_REV_FILTER = False
```

### Autononous mode
Autonomous mode when triggered from RC (ussualy either 'local' or 'local_angle'):
```
ROBOCARSHAT_PILOT_MODE = 'local'
```

Fix throttle to use when local_angle is engaged :
```
ROBOCARSHAT_LOCAL_ANGLE_FIX_THROTTLE = 0.2
```

# automatic record on throttle

to enable automatic record  when trottle is positive, use the following configuration :
```
ROBOCARSHAT_AUTORECORD_ON_THROTTLE = False 
```

### Enable Odometry
To use Odometry, configure the followin items :
```
HAVE_ODOM = True
ENCODER_TYPE = 'ROBOCARSHAT'
```     

Odometry sensor raw max value (used to map Odometry raw value from [0:max value] to [0:1]:
```
ROBOCARSHAT_ODOM_IN_MAX = 20000
```

### Localizer and drive on lane
To enable Drive on lane :
```
ROBOCARS_LOCALIZER_DRIVE_ON_LANE=True
ROBOCARS_LOCALIZER_STEERING_ADJUST_STEPS=[0,0.2,0.4]
TRAIN_LOCALIZER = True
NUM_LOCATIONS = 3
```

### Fixed steering
The following configuration items allows to fix input steering value.
This is usefull to control steering qualibration to ensure the car is going straight forward 
```
ROBOCARSHAT_STEERING_FIX = None 
```

## Special Festures
Some special mode/command can be associated to aux rc channels through the following configuration parameters :
- ROBOCARSHAT_AUX1_FEATURE
- ROBOCARSHAT_AUX2_FEATURE

Possible values are (as string) :
- 'none' : means aux ch is not used 
- 'record/pilot' means aux ch is used to control either data recording (lower position), either to enable pilot mode (upper position)
- 'record' means aux ch is used to control data recording 
- 'pilot' means aux ch is used to control pilot mode
- 'throttle_exploration' means special mode where aux ch is used to increment/decrement a fixed throttle value in user mode 
- 'steering_exploration' means special mode where aux ch is used to increment/decrement a fixed steering value in user mode 
- 'output_steering_trim' means special mode where aux ch is used to increment/decrement a steering idle output for triming direction in user mode, resulting value must be reported in  ROBOCARSHAT_PWM_OUT_STEERING_IDLE
- 'output_steering_exp' means special mode where aux ch is used to increment/decrement a fixed steering output to calibrate direction in user mode, resulting values must be reported in  ROBOCARSHAT_PWM_IN_STEERING_MIN and ROBOCARSHAT_PWM_IN_STEERING_MAX
- 'lane_annotation' means special mode where aux ch is used to annotate on which lane the car is driving (as a 3 positions switch)
- 'drive_on_lane' means special mode where channel value (as a 3 positions switch) is used to control on which lane the car must drive 

### record, pilot, record/pilot
In this node, the aux channel is used to trigger pilot and/or recording.

### throttle_exploration
In this mode, input throttle is set to a fix value which can be incresed or decreasd with the selected aux channel.
Increment step is configured with the following configuration item : 
```
ROBOCARSHAT_THROTTLE_EXP_INC = 0.05 
```
This mode can be used to determine the maximum speed that can be used before the car start drifting for exemple.

### steering_exploration
In this mode, input steering is set to a fix value which can be incresed or decreasd with the selected aux channel.
Increment step is configured with the following configuration item : 
```
ROBOCARSHAT_STEERING_EXP_INC = 0.05 
```
### output_steering_trim
In this mode, the current steering output can be trimmed with the aux channel. 
Steering Trim increment cab be control with the following configuration :
```
ROBOCARSHAT_OUTPUT_STEERING_TRIM_INC = 10 
```
This mode is usefull to determine the best steering idle value ensuring the car is driving straight on idle steering
Once the correct value has been found, report it to ROBOCARSHAT_PWM_OUT_STEERING_IDLE

### output_steering_exp
In this mode, output steering is set to a fix value which can be incresed or decreasd with the selected aux channel.
Increment step is configured with the following configuration item : 
```
ROBOCARSHAT_OUTPUT_STEERING_TRIM_INC = 10
```
This mode is usefull to determine the qualibrate steering output and determine min and max value that for a well balance turning radius
Once the correct value has been found, report it to ROBOCARSHAT_PWM_OUT_STEERING_MIN and ROBOCARSHAT_PWM_OUT_STEERING_MAX

### lane_annotation
In this mode, the aux channel can be used to annotate recorded images with 3 possible values (0,1 and 2), representing the side of the road the car is driving. 
THis is usefull to train a model that will estimate on which side of the road the car is actually driving,

### drive_on_lane
In this mode, the aux channel can be used to instruct on which side of the road the car must drive (in pilot mode).


## Calibration of input:
PWM signal is supposed to be square signal with positive pulse duration from 1ms to 2ms
This pulse width represents the 'value' carried.
For example, talking about steering, 1ms could mean to turn to the most left, and 2ms to turn to the most right
Pulse width at 1.5ms is then the theoritical idle position for the steering. This is more os less the same for the control of throttle as long as we are talking about cat (1ms means full reverse, 1.5 means idle and 2ms means full forward).
Now, a real Tx/RX signal would not stick strictly on those values. This is why qualibration is needed.

The simple way to qualibrate :
- Make sure your remote control is on idle position
- Make sure your car is on a stand, wheels being free to move in case of
- Connect the Rx Receiver to the Hat
- Connect the ESC control line to the Hat (3 Wire, neede because ESC is in charge to provide power supply to the RX Receiver)
- Power the Hat+Host
- Note the idle, minimum and maximum values reported by the Hat when actioning the remote control
- Update the following configuration items accordingly :
    - ROBOCARSHAT_PWM_IN_THROTTLE_MIN : value reported by Hat when moving remote control to the lowest throttle value
    - ROBOCARSHAT_PWM_IN_THROTTLE_IDLE : value reported by Hat when moving remote control to the default/idle throttle value
    - ROBOCARSHAT_PWM_IN_THROTTLE_MAX : value reported by Hat when moving remote control to the highest throttle value
    - ROBOCARSHAT_PWM_IN_STEERING_MIN : value reported by Hat when moving remote control to the maximum steering postion of one of the direction (the one that provides the minimum value)
    - ROBOCARSHAT_PWM_IN_STEERING_IDLE : value reported by Hat when moving remote control to the default steering postion 
    - ROBOCARSHAT_PWM_IN_STEERING_MAX : value reported by Hat when moving remote control to the maximum steering postion of the other direction (the one that provides the maximum value)

To visualize easely value reported by the Hat, 2 possibilities according to the firmware you use :
- With ROS :
    Dump incoming messages related to radio channes :  

    ``rostopic echo /radio_channels`` 

    Messages contains an array of 4 ints : 

    ``
        ...
        data: [xxxx yyyy, aaaa, bbbb]
    ``
    
- With Simple Serial Protocol (Text Protocol) :  
    Dump incoming messages : 

    `` stty -F /dev/serial0 1000000 raw `` 

    `` cat /dev/serial0 | grep "^1," `` 
 
    Messages like ``1,xxxx,yyyy,aaaa,bbbb`` are the Radio channel messages

Throttle is the first value out of four (xxxx) 
Steering is the second value out of four (yyyy)

If you see only 1500 as value, it means that Rx Receiver PWM signal has not been detected (you should see also status LED blinking either RED or BLUE).

