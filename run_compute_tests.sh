#!/bin/bash
set -e

mkdir -p build

echo "=== Running tb_mac ==="
iverilog -g2005 -Wall -o build/sim_mac tb/tb_mac.v rtl/mac.v
vvp build/sim_mac

echo ""
echo "=== Running tb_relu_clip ==="
iverilog -g2005 -Wall -o build/sim_relu tb/tb_relu_clip.v rtl/relu_clip.v
vvp build/sim_relu

echo ""
echo "=== Running tb_argmax ==="
iverilog -g2005 -Wall -o build/sim_argmax tb/tb_argmax.v rtl/argmax.v
vvp build/sim_argmax

echo ""
echo ">>> ALL COMPUTE MODULE TESTS PASSED <<<"
