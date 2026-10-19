# MNIST Accelerator: project context

Course: EC5202 Digital System Design with HDL. Group of 4. Board: Digilent Nexys A7-100T (Artix-7). Language: Verilog + Python (NumPy).
Dates: work from 12 Oct 2026, **working version tagged in Git by 29 Nov 2026**, report and viva by mid-December. Spare week 7–13 Dec.
Time budget: about 2 h per person per week (about 72 team hours, 62 planned).
Status: topic still needs **lecturer approval**. Backup topic if rejected: an 8-bit single-cycle CPU.

## 1. What the demo does
- Switches **SW3–SW0** pick one of **16 test images** stored on the FPGA.
- **Centre button** starts recognition. **CPU_RESETN** (active-low) resets.
- **VGA** (640×480) shows the chosen image 8× larger.
- **Seven-segment** shows: image number, true label, predicted digit.
- **LED0** = done, **LED1** = prediction is correct.
- Expected result on the 16 images: 15 of 16 correct. **One image of a 5 is read as a 6, and the hardware must make exactly the same mistake** (it must match Python bit for bit, not be "better").

## 2. The network (frozen)
- Fully connected **784 → 32 → 10**.
- Input pixels: MNIST 0–255 shifted right by 1 → **0–127** (unsigned, 8 bits).
- Weights: **8-bit signed, −127…127**.
- Biases: **16-bit signed**, sign-extended to 24 bits when loaded into the accumulator.
- Accumulator: **24-bit signed**.
- Layer 1 neuron n: `acc = bias1[n] + Σ w1[n][i] * pixel[i]` (i = 0..783)
  `hidden[n] = clip( relu(acc) >> 11, 0, 127 )` (relu: negative → 0; then arithmetic shift right 11; then saturate at 127)
- Layer 2 output m: `score[m] = bias2[m] + Σ w2[m][j] * hidden[j]` (j = 0..31). No ReLU on the scores.
- Prediction = **argmax** of the 10 scores (on a tie, keep the lower index, unless the team decides otherwise in Python and Verilog together).
- An 8-bit model trained this way scored about **96.6%** on the 10,000 MNIST test images (same as floating point). Target: above 95%.

## 3. Memory map (frozen)
| Memory | Size | Contents / address |
|---|---|---|
| Weight ROM | 25,408 × 8 bit | layer 1 at `n*784 + i` (0..25,087), then layer 2 at `25,088 + m*32 + j` |
| Bias ROM | 42 × 16 bit | layer 1 biases at 0..31, layer 2 biases at 32..41 |
| Image ROM | 16 × 784 × 8 bit = 12,544 | image k pixel i at `k*784 + i`, row by row (28×28) |
| Label ROM | 16 × 4 bit | true digit of each test image |
| Hidden buffer | 32 × 8 bit | layer-1 results, read by layer 2 |

All memories are block RAM loaded with `$readmemh` from `data/*.hex`. Total about 38 KB, about 6% of the board's BRAM.
**Block RAM data arrives one clock after the address**, so the accumulate-enable must be delayed by one clock.

## 4. Hardware blocks
- **MAC unit**: signed 8×8 multiply, 24-bit accumulator, can be loaded with a bias.
- **ReLU + shift + clip**: acc → 0..127.
- **Input select mux**: layer 1 takes pixels, layer 2 takes hidden values (both 0–127).
- **Argmax**: keeps the largest of the 10 scores and its index.
- **Controller FSM** (Moore, 8 states + counters):
  `IDLE → L1_BIAS → L1_MAC (784×) → L1_STORE → (next neuron, 32×) → L2_BIAS → L2_MAC (32×) → ARGMAX → (next output, 10×) → DONE → IDLE`
- **Memories**: weight, bias, image, label ROMs + hidden buffer.
- **Board I/O**: button debounce, seven-segment driver, LEDs, VGA controller (640×480, 25 MHz pixel tick).
- **Top module**: only instances and wires.
- Speed: one MAC → 25,408 multiply-adds ≈ **254 µs per image at 100 MHz**. Stretch goal: 8 MACs in parallel (≈ 32 µs).

## 5. Testing strategy
Python is the referee. The hardware must match it **exactly**, at every step.
1. Each block alone: MAC, ReLU+shift+clip, argmax → testbench prints PASS/FAIL.
2. Full design, image 0: all 32 hidden values and 10 scores match Python.
3. All 16 images in simulation match.
4. Board shows the same digits as simulation.
Python exports expected hidden values, scores and digits as `.hex`; testbenches read them with `$readmemh` and compare.

## 6. Phases and gates
| Phase | Dates | Work | Gate |
|---|---|---|---|
| 1 Get ready | before 12 Oct | approval, roles, Git repo, Vivado + Icarus + Python installed | topic approved, roles agreed |
| 2 Python model + design | 12–25 Oct | train, 8-bit convert, golden model, export .hex; freeze ports; blink an LED | model > 95%, .hex in Git, LED blinks |
| 3 Build the blocks | 26 Oct – 8 Nov | MAC, ReLU/clip, argmax, memories, counters, FSM; VGA fixed image | all testbenches PASS; image 0 matches Python |
| 4 Simulation check | 9–15 Nov (light: CircuitBreak due 14 Nov) | all 16 images, compare every value | all 16 match exactly |
| 5 Board | 16–29 Nov | constraints, buttons, 7-seg, LEDs, VGA; record LUT/FF/DSP/BRAM/slack/cycles | board = simulation; Git tag 29 Nov |
| 6 Report + viva | 30 Nov – 6 Dec | write-up, practice explaining | everyone can explain every block |

## 7. Roles
- **Python and testing**: training, 8-bit conversion, golden model, .hex export, compare testbenches.
- **Compute**: MAC unit, ReLU+shift+clip, argmax (later the 8-MAC version).
- **Control and memories**: controller FSM, address counters, all memories, top module, Git repo.
- **Board and display**: constraints, debounce, seven-segment, LEDs, VGA.
Everyone must be able to explain the whole design (individual viva). 15-minute walkthrough every Friday.

## 8. Seven bugs to avoid
1. BRAM read latency is 1 clock: delay the accumulate signal.
2. Mark MAC inputs and the accumulator `signed`; mixing makes everything unsigned. Pixels/hidden are 0–127, so extend them with a 0 bit before multiplying as signed.
3. Sign-extend the 16-bit bias to 24 bits.
4. Weight address is `n*784 + i` in **both** Python and Verilog.
5. Python must shift right by 11 and clip to 127 exactly like the hardware.
6. Add every `.hex` file to the Vivado project, or the memory is silently empty.
7. `CPU_RESETN` is active-low.

## 9. Frozen phase-2 interface decisions

The team approved these decisions before RTL implementation. Do not change them
without agreement from all four roles.

### Controller port list

```verilog
module controller (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [3:0]  img_sel,
    output reg         layer,
    output reg  [14:0] w_addr,
    output reg  [5:0]  b_addr,
    output reg  [13:0] px_addr,
    output reg  [4:0]  h_addr,
    output reg         h_we,
    output reg         load_bias,
    output reg         acc_en,
    output reg         score_valid,
    output reg  [3:0]  out_idx,
    output reg         busy,
    output reg         done
);
```

The controller uses one shared 10-bit input counter. It counts 0 to 783 in
layer 1 and 0 to 31 in layer 2. `done` is a one-clock pulse.

### Memory files

Each file contains one hexadecimal value per line, in address order. Negative
weights and biases use two's complement.

| File | Lines | Width | Address order |
|---|---:|---:|---|
| `data/weights.hex` | 25,408 | 8 bits | Layer 1, then layer 2, as defined in section 3 |
| `data/biases.hex` | 42 | 16 bits | Layer 1 biases, then layer 2 biases |
| `data/images.hex` | 12,544 | 8 bits | Image 0 to 15, each image row by row |
| `data/labels.hex` | 16 | 4 bits | One true digit for each image |

All ROM reads have one-clock synchronous latency.

### Argmax tie rule

On equal scores, keep the lower output index. The comparison therefore updates
the best result only when the new score is strictly greater (`>`), not greater
than or equal (`>=`). Python and Verilog must use this same rule.

### Still to freeze

- Port lists for the Compute, memory, and Board modules.
