`timescale 1ns / 1ps

// Synchronous label ROM for the 16 demonstration images.
module rom_label (
    input  wire        clk,
    input  wire [3:0]  addr,
    output reg  [3:0]  data
);

    reg [3:0] mem [0:15];

    initial begin
        $readmemh("data/labels.hex", mem);
    end

    always @(posedge clk) begin
        data <= mem[addr];
    end

endmodule
