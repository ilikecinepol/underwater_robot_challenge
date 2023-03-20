import matplotlib.pyplot as plt
import pymurapi as mur
from auv_moving import *
import time

auv = mur.mur_init()
t0 = round(time.time() * 1000)
h1, = plt.plot([], [])
x = []
y1 = []
y = []
t0 = 0


def timer(t0):
    step = 0.1
    time.sleep(step)
    return t0 + step


def get_data(action, value, setpoint):
    global x, y, t0
    t0 = timer(t0)
    action
    x.append(t0)
    y.append(value)
    y1.append(setpoint)


def update_line(h1):
    global x, y
    h1.set_xdata(x)
    h1.set_ydata(y)
    plt.autoscale(enable=True, axis='x', tight=True)
    plt.plot(x, y)
    plt.plot(x, y1)
    plt.draw()
    plt.pause(0.0001)


goal_value = 2.5
while True:
    current_depth = auv.get_depth()
    power = pid_controller(current_depth, goal_value,p=-35, i=50, d=10)
    get_data(moving(linear_z=power), current_depth, goal_value)
    update_line(h1)

