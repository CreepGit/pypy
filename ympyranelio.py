from numpy import random

arg_loops = 10**8

hits = 0
misses = 0

# for x,y in random.random((arg_loops,2))*2-1:
#     dist2 = x*x + y*y
#     if dist2 <= 1:
#         hits += 1
#     else:
#         misses += 1

array = random.random((arg_loops,2))*2-1
result = array[:,0]*array[:,0] + array[:,1]*array[:,1]
print(4*(result<1).sum()/result.size)

#ratio = hits/(hits+misses)
#print(4*ratio)
