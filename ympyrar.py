import matplotlib.pyplot as plt
import math

# Configs :
cirle = 1.5
maxn = 1000000

pointsx = []
pointsy = []
for a in range(0, maxn+1):
    percentage = a/maxn
    angle = math.radians(cirle*360*percentage)
    r = percentage * 3 * math.pi

    pointsx.append(r * math.sin(angle))
    pointsy.append(r * -math.cos(angle))

plt.plot(pointsx, pointsy)

sumdist = 0
last = pointsx[0], pointsy[0]
for x, y in zip(pointsx[1:], pointsy[1:]):
    dx = last[0] - x
    dy = last[1] - y
    sumdist += math.sqrt(dx*dx + dy*dy)
    last = x,y
print("Computed {:0.30f}".format(sumdist))
wolfram_exact = 46.13216613068578400231134
print("Wolfram  {:0.30f}".format(wolfram_exact))

plt.show()
