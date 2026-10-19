# Control and memories: design proposal

Status: **PROPOSAL - NOT FROZEN**

The team must approve the ports and file formats below. After approval, copy the
final decisions into `docs/PROJECT_CONTEXT.md` section 9.

## 1. Controller job

The controller runs one complete MNIST inference. It:

1. Loads each bias into the MAC.
2. Sends the correct memory addresses.
3. Enables the MAC only when ROM data is valid.
4. Stores 32 hidden results.
5. Sends 10 output scores to the argmax block.
6. Produces `busy` and `done` signals.

## 2. Proposed controller ports

```text
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

This is an interface proposal, not completed RTL.

### Port meanings

| Port | Direction | Meaning | Hardware |
|---|---|---|---|
| `clk` | input | 100 MHz system clock | Global clock network |
| `rst_n` | input | Active-low internal reset | Reset wiring |
| `start` | input | One-clock start pulse | Control input |
| `img_sel[3:0]` | input | Selects one of 16 images | Four input bits |
| `layer` | output | `0`: layer 1, `1`: layer 2 | One flip-flop or state decode |
| `w_addr[14:0]` | output | Weight ROM address | 15-bit counter/register |
| `b_addr[5:0]` | output | Bias ROM address | 6-bit register |
| `px_addr[13:0]` | output | Image ROM address | 14-bit counter/register |
| `h_addr[4:0]` | output | Hidden-buffer address | 5-bit counter/register |
| `h_we` | output | Hidden-buffer write enable | State decode logic |
| `load_bias` | output | Load the selected bias into the MAC | State decode logic |
| `acc_en` | output | Accumulate one valid product | Flip-flop plus state logic |
| `score_valid` | output | One completed score is ready | State decode logic |
| `out_idx[3:0]` | output | Output digit index, 0 to 9 | 4-bit counter/register |
| `busy` | output | Inference is running | State decode logic |
| `done` | output | One-clock completion pulse | State decode logic |

## 3. Eight-state Moore FSM

```text
                         n < 31
                    +--------------+
                    |              |
                    v              |
IDLE --> L1_BIAS --> L1_MAC --> L1_STORE
  ^                                  |
  |                                  | n = 31
  |                                  v
 DONE <-- ARGMAX <-- L2_MAC <-- L2_BIAS
           |                         ^
           +-------------------------+
                    m < 9

ARGMAX --> DONE when m = 9
DONE   --> IDLE on the next clock
```

The two loops are:

- Layer 1: 784 inputs for each of 32 hidden neurons.
- Layer 2: 32 hidden inputs for each of 10 output neurons.

## 4. State table

| State | Work | Counter action | Main outputs |
|---|---|---|---|
| `IDLE` | Wait for `start` | Clear all loop counters | `busy=0` |
| `L1_BIAS` | Load bias for hidden neuron `n` | Prepare input index `i=0` | `load_bias=1`, `layer=0` |
| `L1_MAC` | Process pixels 0 to 783 | Increment `i` for each issued address | `layer=0`, delayed `acc_en` |
| `L1_STORE` | Store one hidden result | Increment `n`, or start layer 2 | `h_we=1` |
| `L2_BIAS` | Load bias for output `m` | Prepare hidden index `j=0` | `load_bias=1`, `layer=1` |
| `L2_MAC` | Process hidden values 0 to 31 | Increment `j` for each issued address | `layer=1`, delayed `acc_en` |
| `ARGMAX` | Send one score to argmax | Increment `m`, or finish | `score_valid=1`, `out_idx=m` |
| `DONE` | Report completion | No loop operation | `done=1`, `busy=0` |

## 5. Counters

| Name | Range | Width | Purpose |
|---|---:|---:|---|
| `i` | 0 to 783 | 10 bits | Pixel within one hidden neuron |
| `n` | 0 to 31 | 5 bits | Hidden neuron number |
| `j` | 0 to 31 | 5 bits | Hidden input for layer 2 |
| `m` | 0 to 9 | 4 bits | Output neuron/digit number |
| `w_addr` | 0 to 25,407 | 15 bits | Address of every network weight |

The controller may share `i` and `j` as one 10-bit input counter because only one
layer runs at a time. The team should choose between separate counters and one shared
counter before RTL is written.

## 6. BRAM timing

Block RAM data arrives one clock after its address.

```text
Clock edge       1          2          3          4
Address issued   0          1          2          3
ROM output       old        data[0]    data[1]    data[2]
Data valid       0          1          1          1
MAC action       none       use 0      use 1      use 2
```

The controller needs a one-bit valid pipeline register. The final input must also be
allowed to reach the MAC before leaving the MAC operation.

## 7. Address order

These formulas come from the frozen memory map:

```text
Layer-1 weight: n * 784 + i
Layer-2 weight: 25088 + m * 32 + j
Image pixel:    img_sel * 784 + i
Layer-1 bias:   n
Layer-2 bias:   32 + m
```

Because the weights are stored in the exact processing order, `w_addr` can count from
0 through 25,407. This avoids a hardware multiplier for weight addresses.

## 8. Expected events for one image

| Event | Expected count |
|---|---:|
| Layer-1 accumulations | 25,088 |
| Layer-2 accumulations | 320 |
| Total `acc_en` pulses | 25,408 |
| Hidden writes | 32 |
| Valid scores | 10 |
| `done` pulses | 1 |

The controller testbench must count these events and print `PASS` or `FAIL`.

## 9. Memory-file proposal

| File | Lines | Bits per line | Example |
|---|---:|---:|---|
| `data/weights.hex` | 25,408 | 8 | `FD` means -3 |
| `data/biases.hex` | 42 | 16 | `FFFD` means -3 |
| `data/images.hex` | 12,544 | 8 | `3F` means 63 |
| `data/labels.hex` | 16 | 4 | `7` means digit 7 |

Use one hexadecimal value per line. Negative values use two's complement. Python and
Control must agree on this format before creating the ROM modules.

## 10. Decisions the team must approve

- [ ] Approve or change the proposed controller ports.
- [ ] Decide whether the controller uses one shared input counter or separate `i` and `j` counters.
- [ ] Approve the four `.hex` filenames and formats.
- [ ] Confirm argmax ties keep the lower index by using `>` rather than `>=`.
- [ ] Confirm all ROM reads have one-clock synchronous latency.
- [ ] Confirm `done` is a one-clock pulse.
- [ ] Record the final decisions in `docs/PROJECT_CONTEXT.md` section 9.

## 11. Hardware summary

| Design item | FPGA hardware |
|---|---|
| FSM state | Flip-flops |
| Counters and address registers | Flip-flops plus adders |
| Final-count checks | Comparators |
| Next-state choice | Muxes and logic gates |
| Delayed data-valid signal | One flip-flop |
| ROM arrays | Block RAM |
| Hidden buffer | RAM |

## 12. Viva practice

1. Why must `acc_en` be delayed by one clock?
2. Why does `w_addr` need 15 bits?
3. Why can the weight address count continuously instead of calculating `n * 784 + i` in hardware?
