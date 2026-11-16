`timescale 1ns / 1ps

// Synchronous weight ROM.
// Address order and file format are frozen in docs/PROJECT_CONTEXT.md.
module rom_weights (
    input  wire               clk,
    input  wire [14:0]        addr,
    output reg  signed [7:0]  data
);

    // 25,408 words, each containing one signed 8-bit weight.
    reg signed [7:0] mem [0:25407];

    // $readmemh is the only allowed initialization operation in rtl/.
    initial begin
        $readmemh("data/weights.hex", mem);
    end

    // A registered read gives the required one-clock BRAM latency.
    always @(posedge clk) begin
        data <= mem[addr];
    end

endmodule
