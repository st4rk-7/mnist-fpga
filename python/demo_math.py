from common import hex_twos

pixel = 100
weight = -3
bias = 500

accumulator = bias + (pixel * weight)

print("MAC result:", accumulator)

print("Negative 3 in 8-bit hex:", hex_twos(-3, 8))
print("Negative 3 in 16-bit hex:", hex_twos(-3, 16))

acc = 100000

hidden = min(127, max(0, acc) >> 11)

print("Hidden neuron result:", hidden)