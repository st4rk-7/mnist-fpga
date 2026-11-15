# Memory interfaces: team approval proposal

Status: **APPROVED BY THE TEAM - FROZEN**

These interfaces follow the frozen memory map in `docs/PROJECT_CONTEXT.md`.
Python's current files have the correct line counts and widths.

## 1. Weight ROM

```verilog
module rom_weights (
    input  wire               clk,
    input  wire [14:0]        addr,
    output reg  signed [7:0]  data
);
```

- Depth: 25,408 words.
- Contents: `data/weights.hex`.
- Read latency: one clock.
- `data` is signed because weights can be negative.

## 2. Bias ROM

```verilog
module rom_bias (
    input  wire                clk,
    input  wire [5:0]          addr,
    output reg  signed [15:0]  data
);
```

- Depth: 42 words.
- Contents: `data/biases.hex`.
- Read latency: one clock.
- `data` is signed because biases can be negative.

## 3. Dual-port image ROM

```verilog
module rom_image (
    input  wire         clk,
    input  wire [13:0]  addr_a,
    output reg  [7:0]   data_a,
    input  wire [13:0]  addr_b,
    output reg  [7:0]   data_b
);
```

- Depth: 12,544 words.
- Contents: `data/images.hex`.
- Both ports read the same memory.
- Port A belongs to the neural-network controller.
- Port B belongs to the VGA controller.
- Both outputs have one-clock latency.
- Pixel data is unsigned, 0 to 127.

The two ports allow VGA display and inference to read the selected image without
sharing an address wire.

## 4. Label ROM

```verilog
module rom_label (
    input  wire        clk,
    input  wire [3:0]  addr,
    output reg  [3:0]  data
);
```

- Depth: 16 words.
- Contents: `data/labels.hex`.
- Read latency: one clock.
- Labels are unsigned digits from 0 to 9.

## 5. Hidden buffer

```verilog
module hidden_buf (
    input  wire        clk,
    input  wire        we,
    input  wire [4:0]  addr,
    input  wire [7:0]  write_data,
    output reg  [7:0]  read_data
);
```

- Depth: 32 words.
- Layer 1 writes ReLU results using `we`.
- Layer 2 reads them using the same address port.
- Read latency: one clock.
- No initial file is required.

Layer 1 and layer 2 do not access the buffer at the same time, so one shared
read/write address is sufficient.

## 6. Top-level connections

| Producer | Signal | Memory port |
|---|---|---|
| Controller | `w_addr` | Weight ROM `addr` |
| Controller | `b_addr` | Bias ROM `addr` |
| Controller | `px_addr` | Image ROM `addr_a` |
| VGA | `pix_addr` | Image ROM `addr_b` |
| Controller | `h_addr` | Hidden buffer `addr` |
| Controller | `h_we` | Hidden buffer `we` |
| ReLU block | `out` | Hidden buffer `write_data` |
| Hidden buffer | `read_data` | Layer input mux |

## 7. Test plan

Each testbench will check:

1. The output changes one clock after the address.
2. Address 0 and the final legal address.
3. Important boundaries: weight 25,087/25,088, bias 31/32, and image 783/784.
4. Both image-ROM ports can read different addresses on the same clock.
5. The hidden buffer can write all 32 values and read them back.
6. The testbench prints `PASS` or `FAIL` by itself.

## 8. Hardware produced

| Module | Expected FPGA hardware |
|---|---|
| Weight ROM | Block RAM |
| Bias ROM | Block RAM or distributed ROM because it is small |
| Image ROM | Dual-port block RAM |
| Label ROM | LUT ROM or registers because it is very small |
| Hidden buffer | Distributed RAM or registers because it is only 256 bits |
| Registered outputs | Flip-flops inside or beside the memory block |

Vivado decides the exact implementation. The synchronous read style is important
for block-RAM inference.

## 9. Approved decisions

- [x] Python approved filenames, widths, and address order.
- [x] Compute approved signed weight and bias outputs.
- [x] Board approved image-ROM port B for VGA.
- [x] Control approved one-clock latency and hidden-buffer interface.
- [x] The approved interfaces are copied into `docs/PROJECT_CONTEXT.md` section 9.

## 10. Viva questions

1. Why is the image ROM dual-port?
2. Why are weight and bias outputs signed but image outputs unsigned?
3. Why does synchronous read style help Vivado infer block RAM?
