import math
import time

import numpy as np
import matplotlib.pyplot as plt
import serial
from mpl_toolkits.mplot3d import Axes3D
from random import randint

# make numpy raise errors instead of warn so can be caught by try except blocks
np.seterr(all="raise")
arduino = serial.Serial(port='COM3', baudrate=9600, timeout=.1)

# plot axis origins onto point with rotation
def plotOrigin(tx, ty, tz, rx, ry, rz, length):
    # transform origin
    rotall = np.matmul(np.matmul(Rz(rz), Ry(rx)), Rz(rx))
    xplots = np.matmul(rotall, ((0, length), (0, 0), (0, 0)))
    yplots = np.matmul(rotall, ((0, 0), (0, length), (0, 0)))
    zplots = np.matmul(rotall, ((0, 0), (0, 0), (0, length)))
    xplots[0] += tx
    xplots[1] += ty
    xplots[2] += tz
    yplots[0] += tx
    yplots[1] += ty
    yplots[2] += tz
    zplots[0] += tx
    zplots[1] += ty
    zplots[2] += tz

    # plot origin
    ax.plot(*xplots, c="#ff0000")
    ax.plot(*yplots, c="#00ff00")
    ax.plot(*zplots, c="#0000ff")


def findEndEffector(tx, ty, tz, rx, ry, rz, length):
    # transform line
    rotall = np.matmul(np.matmul(Rz(rz), Ry(ry)), Rx(rx))
    plots = list(np.matmul(rotall, (0, 0, length)))
    plots[0] += tx
    plots[1] += ty
    plots[2] += tz
    return plots


# define rotation matrices
def Rx(a):
    return (
        (1, 0, 0),
        (0, np.cos(a), -np.sin(a)),
        (0, np.sin(a), np.cos(a))
    )


def Ry(a):
    return (
        (np.cos(a), 0, np.sin(a)),
        (0, 1, 0),
        (-np.sin(a), 0, np.cos(a))
    )


def Rz(a):
    return (
        (np.cos(a), -np.sin(a), 0),
        (np.sin(a), np.cos(a), 0),
        (0, 0, 1)
    )


# functions to find angle between two vectors
def getAngle(vect1, vect2):
    unitvect1 = vect1 / np.linalg.norm(vect1)
    unitvect2 = vect2 / np.linalg.norm(vect2)
    theta = np.arccos(
        np.clip(
            np.dot(unitvect1, unitvect2),
            -1.0,
            1.0
        )
    )
    return theta


# project a 3d point onto a 3d plane
def pointToPlane(point, origin, normal):
    unitnormal = normal / np.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)
    vector = point - origin
    distance = np.dot(vector, unitnormal)
    projectedpoint = point - distance * unitnormal
    return projectedpoint


# linear interpolation
def lerp(a, b, t):
    return (a * (1 - t)) + (b * t)


def invKin(lengths, destination):
    # define parameters
    length1 = lengths[0]
    length2 = lengths[1]
    length3 = lengths[2]
    length4 = lengths[3]
    length5 = lengths[4]
    length6 = lengths[5]

    # define other
    error = False

    xplots = [0, 0]
    yplots = [0, 0]
    zplots = [0, length1]

    length2 = length2
    length34 = length3 + length4
    length56 = length5 + length6

    desttx = destination[0]
    destty = destination[1]
    desttz = destination[2]
    destrx = destination[3]
    destry = destination[4]
    destrz = destination[5]

    # create one large rotation matrix
    rall = np.matmul(
        np.matmul(
            Rz(destrz),
            Ry(destry)
        ),
        Rx(destrx)
    )

    # define points to be transformed
    act5pos = [[0.0, float(-length56)], [0.0, 0.0], [0.0, 0.0]]

    # rotate position
    act5newpos = np.matmul(rall, act5pos)

    # translate potitions
    act5pos[0][0] += desttx
    act5pos[0][1] += desttx
    act5pos[1][0] += destty
    act5pos[1][1] += destty
    act5pos[2][0] += desttz
    act5pos[2][1] += desttz
    act5newpos[0][0] += desttx
    act5newpos[0][1] += desttx
    act5newpos[1][0] += destty
    act5newpos[1][1] += destty
    act5newpos[2][0] += desttz
    act5newpos[2][1] += desttz

    # find angle between act5newpos and the xz plane
    joint5toorigin = (
        (0.0, act5newpos[0][1]),
        (0.0, act5newpos[1][1]),
        (act5newpos[2][1], act5newpos[2][1]),
    )

    # cannot divide by zero so catch and replace with real value
    try:
        angle = np.arctan(
            (joint5toorigin[1][1] - joint5toorigin[1][0])
            / (joint5toorigin[0][1] - joint5toorigin[0][0])
        )
    except FloatingPointError:
        angle = np.pi / 2

    # rotate act5newpos to the xz plane
    act5xzpos = list(map(list, np.matmul(Rz(-angle), joint5toorigin)))

    # define target position for 2D inverse kinematics (xz (z-up) plane now referred as xy (y-up) plane)
    targetpos = [act5xzpos[0][1], act5xzpos[2][1]]

    # perform inverse kinematics on the target position
    if targetpos[0] < 0:
        targetpos[0] *= -1
        angle += np.pi

    # inverse kinematics for angles 1, 2, and 3
    try:
        theta1 = np.arccos(
            (
                    length2 ** 2
                    + targetpos[0] ** 2
                    + (targetpos[1] - length1) ** 2
                    - length34 ** 2
            )
            / (2 * length2 * np.sqrt(targetpos[0] ** 2 + (targetpos[1] - length1) ** 2))
        )
        theta2 = np.pi - np.arccos(
            (
                    length2 ** 2
                    + length34 ** 2
                    - (targetpos[0] ** 2 + (targetpos[1] - length1) ** 2)
            )
            / (2 * length2 * length34)
        )
        theta3 = np.arctan((targetpos[1] - length1) / targetpos[0])
    except FloatingPointError:
        return None

    # angles saved to sensible variables
    angle1 = -angle if angle <= np.pi else (np.pi * 2) - angle
    angle2 = theta1 + theta3 - np.pi / 2
    angle3 = theta2

    # get plot positions from calculated angles
    xplots.append(-np.sin(angle2) * length2)
    yplots.append(0)
    zplots.append((np.cos(angle2) * length2) + length1)
    xplots.append(lerp(xplots[-1], targetpos[0], length3 / length34))
    yplots.append(0)
    zplots.append(lerp(zplots[-1], targetpos[1], length3 / length34))
    xplots.append(targetpos[0])
    yplots.append(0)
    zplots.append(targetpos[1])

    allplots = list(map(list, np.matmul(Rz(angle), [xplots, yplots, zplots])))
    xplots = allplots[0]
    yplots = allplots[1]
    zplots = allplots[2]
    xplots.append(lerp(act5newpos[0][1], desttx, length5 / length56))
    yplots.append(lerp(act5newpos[1][1], destty, length5 / length56))
    zplots.append(lerp(act5newpos[2][1], desttz, length5 / length56))
    xplots.append(desttx)
    yplots.append(destty)
    zplots.append(desttz)

    # angle 4 calculated by projecting plots between arm 2 and arm 5-6 onto plane with origin and normal of the forearm
    origin4 = np.array([xplots[2], yplots[2], zplots[2]])
    normal4 = np.array([xplots[4], yplots[4], zplots[4]]) - origin4
    point41 = pointToPlane(
        np.array([xplots[1], yplots[1], zplots[1]]), origin4, normal4
    )
    point42 = pointToPlane(
        np.array([xplots[6], yplots[6], zplots[6]]), origin4, normal4
    )
    vector41 = point41 - origin4
    vector42 = point42 - origin4
    point42direction = -1 if np.matmul(Rz(angle1), point42)[1] >= 0 else 1
    try:
        angle4 = (np.pi - getAngle(vector41, vector42)) * point42direction
    except:
        angle4 = 0

    # angle 5 calculated by taking plots 2, 4, and 6
    vector51 = (xplots[2] - xplots[4], yplots[2] - yplots[4], zplots[2] - zplots[4])
    vector52 = (xplots[6] - xplots[4], yplots[6] - yplots[4], zplots[6] - zplots[4])
    angle5 = np.pi - getAngle(vector51, vector52)

    # angle 6 calculated by projecting plots between arm 3 and end effector onto plane with origin and normal of the wrist
    origin6 = np.array([xplots[4], yplots[4], zplots[4]])
    normal6 = np.array([xplots[6], yplots[6], zplots[6]]) - origin6
    point61 = pointToPlane(
        np.array([xplots[2], yplots[2], zplots[2]]), origin6, normal6
    )
    point62 = pointToPlane(
        findEndEffector(desttx, destty, desttz, destrx, destry, destrz, 50),
        origin6,
        normal6,
    )
    vector61 = point61 - origin6
    vector62 = point62 - origin6
    point62direction = 1 if np.matmul(Rz(angle1), point42)[1] >= 0 else -1
    try:
        angle6 = getAngle(vector61, vector62) * point62direction
    except:
        angle6 = 0

    return (
        (-angle1, -angle2, angle3, angle4, angle5, angle6),
        tuple(xplots),
        tuple(yplots),
        tuple(zplots),
    )
def write_read(x):
    arduino.write(x.encode('utf-8'))

def upd(dest):
    lengths = [76.165, 173, 119.5, 45.31, 25.313, 0]
    raw = invKin(lengths, dest)
    angle1 = raw[0][0]
    angle2 = raw[0][1]
    angle3 = raw[0][2]
    angle4 = raw[0][3]
    angle5 = raw[0][4]
    angle6 = raw[0][5]
    a1 = round(np.degrees(angle1))
    a2 = round(np.degrees(angle2))
    a3 = round(np.degrees(angle3))
    a4 = round(np.degrees(angle4))
    a5 = round(np.degrees(angle5))
    a6 = round(np.degrees(angle6))

    t1 = 37 + 360
    t2 = 222
    t3 = 95
    t4 = 90
    t5 = 90
    t6 = 92


    write_read(str(1000 + a1 + t1))
    write_read(str(2000 + 90 - a2 + t2))
    write_read(str(3000 - a3 + t3))
    write_read(str(4000 + a4 + t4))
    write_read(str(5000 + a5 + t5))
    write_read(str(6000 + a6 + t6))


    print(f"destination = {dest}")
    print(f"A1 = {str(1000 + a1 + t1)} deg")
    print(f"A2 = {str(2000+90 - a2 + t2)} deg")
    print(f"A3 = {str(3000 - a3 + t3)} deg")
    print(f"A4 = {str(4000 + a4 + t4)} deg")
    print(f"A5 = {str(5000 + a5 + t5)} deg")
    print(f"A6 = {str(6000 + a6 + t6)} deg")

def p1 ():
    a1 = 0
    a2 = 52
    a3 = 38
    a4 = 0;
    a5 = -90
    a6 = 0

    t1 = 37 + 360
    t2 = 222
    t3 = 95
    t4 = 90
    t5 = 90
    t6 = 0


    write_read(str(1000 + a1 + t1))
    write_read(str(2000 + 90 - a2 + t2))
    write_read(str(3000 - a3 + t3))
    write_read(str(4000 + a4 + t4))
    write_read(str(5000 + a5 + t5))
    write_read(str(6000 + a6 + t6))
    print(f"A1 = {str(1000 + a1 + t1)} deg")
    print(f"A2 = {str(2000+90 - a2 + t2)} deg")
    print(f"A3 = {str(3000 - a3 + t3)} deg")
    print(f"A4 = {str(4000 + a4 + t4)} deg")
    print(f"A5 = {str(5000 + a5 + t5)} deg")
    print(f"A6 = {str(6000 + a6 + t6)} deg")

def p2 ():
    a1 = 0
    a2 = 56
    a3 = 52
    a4 = 0;
    a5 = -73
    a6 = 0

    t1 = 37 + 360
    t2 = 222
    t3 = 95
    t4 = 90
    t5 = 90
    t6 = 0


    write_read(str(1000 + a1 + t1))
    write_read(str(2000 + 90 - a2 + t2))
    write_read(str(3000 - a3 + t3))
    write_read(str(4000 + a4 + t4))
    write_read(str(5000 + a5 + t5))
    write_read(str(6000 + a6 + t6))
    print(f"A1 = {str(1000 + a1 + t1)} deg")
    print(f"A2 = {str(2000+90 - a2 + t2)} deg")
    print(f"A3 = {str(3000 - a3 + t3)} deg")
    print(f"A4 = {str(4000 + a4 + t4)} deg")
    print(f"A5 = {str(5000 + a5 + t5)} deg")
    print(f"A6 = {str(6000 + a6 + t6)} deg")

def main():
    global fig
    global ax

    lengths = [76.165, 173, 119.5, 45.31, 25.313, 0]

    Reset = [250, 0, 140, 0, 0, 0]
    AD  = [180, -120, 230, 0,0, -math.pi/2]

    Feed  = [300, 0, 90, 0,math.pi/2, 0]
    # output calculated angles

    # show plotted data
    # plt.show()


    while True:
        command = input()
        if (command == "R"):
            upd(Reset)

        if (command == "A"): #do not run, DOESN'T WORK
            p1()
        if (command == "B"): #do not run, DOESN'T WORK
            p2()
        if(command == "F"):
            upd(AD)






if __name__ == "__main__":
    main()
