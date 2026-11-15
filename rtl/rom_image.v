`timescale 1ns / 1ps

// Dual-port synchronous image ROM.
// Port A is used by inference. Port B is used by VGA.
module rom_image (
    input  wire         clk,
    input  wire [13:0]  addr_a,
    output reg  [7:0]   data_a,
    input  wire [13:0]  addr_b,
    output reg  [7:0]   data_b
);

    reg [7:0] mem [0:12543];

    initial begin
        $readmemh("data/images.hex", mem);
    end

    always @(posedge clk) begin
        data_a <= mem[addr_a];
    end

    always @(posedge clk) begin
        data_b <= mem[addr_b];
    end

endmodule
