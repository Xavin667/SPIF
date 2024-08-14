import threading
from dobot_api import DobotApiDashboard, DobotApi, DobotApiMove, MyType,alarmAlarmJsonFile
from time import sleep
import numpy as np
import re
import matplotlib.pyplot as plt
import math

def Spiral(step, diameter):
        """
        Returns trajectory points in the form of spiral
        :return:
        list x, y
        """
        iterations = int(diameter / step)
        points_count = 20000
        points_factor = points_count/10000
        dia_factor = diameter/60
        step_div = 0.58 * dia_factor / step 

        theta = np.radians(np.linspace(0, 360*100*step_div, int(points_count*step_div*points_factor)))
        r = (diameter/10)/80000*theta**2/(step_div*step_div)

        x_2 = r*np.cos(theta)
        y_2 = r*np.sin(theta)
        x_2_rev = np.flip(x_2)
        y_2_rev = np.flip(y_2)
        x = []
        y = []
        
        iter_point_count = int(100*points_factor**2)
        for i in range(1, iterations+1):
            x.append(x_2_rev[iter_point_count*i-iter_point_count:iter_point_count*i+1])
            y.append(y_2_rev[iter_point_count*i-iter_point_count:iter_point_count*i+1])
        return x, y, iterations  

def Square(step, diameter):
        """
        Returns trajectory points in the form of square, max edge size = 
        :return:
        list x, y
        """
        iterations = int((diameter * (math.sqrt(2) / 4) / step))
        edge_size = (diameter / math.sqrt(2)) / 2
        x1 = np.array([-edge_size, -edge_size, edge_size, edge_size, -edge_size])
        y1 = np.array([-edge_size, edge_size, edge_size, -edge_size, -edge_size])
        x = [[] for i in range(iterations)]
        y = [[] for i in range(iterations)]
        offset = 0
        for i in range(0,iterations):
            for j in range(0, len(x1)):
                x[i].append(x1[j]) if x1[j] == 0 else x[i].append(x1[j] - offset) if x1[j] > 0 else x[i].append(x1[j] + offset)
                y[i].append(y1[j] + offset) if x1[j] == 0 else y[i].append(y1[j] - offset) if y1[j] > 0 else y[i].append(y1[j] + offset)
            offset += step
        return x, y, iterations

def Triangle(step, diameter):
    """
    Returns trajectory points in the form of traingle
    :param step:
    :return:
    """
    iterations = int((diameter * (math.sqrt(3) / 4) / step))
    h = diameter*3/4    
    a = h / math.sqrt(3)
    x1 = np.array([0, -a, a, 0])
    y1 = np.array([h * 2/3, -1/3 * h, -1/3 * h, h * 2/3])
    x = [[] for i in range(iterations)]
    y = [[] for i in range(iterations)]
    for i in range(0, iterations):
        for j in range(0, len(x1)):
            x[i].append(x1[j] - step * i) if x1[j] > 0  else x[i].append(x1[j] + step * i) if x1[j] < 0 else x[i].append(x1[j])
            y[i].append(y1[j] - step * i) if y1[j] > 0 else y[i].append(y1[j] + step / math.sqrt(2) * i) if y1[j] < 0 else y[i].append(y1[j])
    return x, y, iterations

def GenerateCoordinates(x, y, depth):
    file = open("coordinates.txt", "w")
    z_step = depth / len(x)
    for i in range(len(x)):
        for j in range(len(x[i])):
            try:
                if i == 0 and j == 0:
                    file.write(f"{x[i][j]} {y[i][j]} {35 - z_step * (i - 1)}\n")
                    file.write(f"{x[i][j]} {y[i][j]} { - z_step * (i - 1)}\n")
                else:
                    file.write(f"{x[i][j] } {y[i][j]} { - z_step * (i - 1)}\n")
            except IndexError:
                pass

def ShowPlot(step, diameter, depth, type):
        if type == "Triangle":
            x, y, iterations = Triangle(step, diameter)
        elif type == "Square":
            x, y, iterations = Square(step, diameter)
        elif type == "Circle":
            x, y, iterations = Spiral(step, diameter)
        z_step = depth/len(x)
        ax = plt.figure(figsize=(8,8), num="Planned Trajectory").add_subplot(projection='3d')
        N = 5 * 0.1 / z_step  
        ax.set_box_aspect((N, N, 1))  
        for i in range(0, len(x)):
            ax.plot(x[i], y[i], -z_step*i)
        plt.show()

x, y, iterations = Square(0.25, 75)
GenerateCoordinates(x, y, 30)
ShowPlot(0.25, 75, 30, "Square")