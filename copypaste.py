import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Create figure and axes
fig, ax = plt.subplots()

# Set figure properties
ax.set_xlim(-10, 10)
ax.set_ylim(-1, 1)

# Initialize line
line, = ax.plot(0, 0, lw=2)

# Function to update the plot
def update_line(num, data, line):
    line.set_data(data[..., :num])
    return line,

# Generate sin wave data
x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)
data = np.array([x, y])

# Set up the animation
ani = animation.FuncAnimation(fig, update_line, 100, fargs=(data, line),
                              interval=25, blit=True)
plt.show()
