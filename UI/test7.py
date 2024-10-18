# import numpy as np

# from vispy.plot import Fig
# fig = Fig()

# ax_left = fig[0, 0]
# ax_right = fig[0, 1]


# data = np.random.randn(2, 10)
# ax_left.plot(data)
# ax_right.histogram(data[1])


# from vispy.plot import Fig
# fig = Fig()
# ax = fig[0, 0]  # this creates a PlotWidget
# ax.plot([[0, 1], [0, 1]])


import numpy as np

from vispy import plot as vp

fig = vp.Fig(size=(600, 500), show=False)

# Plot the target square wave shape
x = np.linspace(0, 10, 1000)
y = np.zeros(1000)
y[1:500] = 1
y[500:-1] = -1
line = fig[0, 0].plot((x, y), width=3, color='k',
                      title='Square Wave Fourier Expansion', xlabel='x',
                      ylabel='4/π Σ[ 1/n sin(nπx/L) | n=1,3,5,...]')



if __name__ == '__main__':
    vcanvas = fig.show(run=True)