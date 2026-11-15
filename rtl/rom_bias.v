`timescale 1ns / 1ps

// Synchronous signed bias ROM.
module rom_bias (
    input  wire                clk,
    input  wire [5:0]          addr,
    output reg  signed [15:0]  data
);

    reg signed [15:0] mem [0:41];

    initial begin
        $readmemh("data/biases.hex", mem);
    end

    always @(posedge clk) begin
        data <= mem[addr];
    end

endmodule
