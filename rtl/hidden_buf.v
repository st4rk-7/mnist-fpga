`timescale 1ns / 1ps

// Single-port hidden-value buffer.
// Layer 1 writes 32 ReLU results. Layer 2 reads the same 32 values.
module hidden_buf (
    input  wire        clk,
    input  wire        we,
    input  wire [4:0]  addr,
    input  wire [7:0]  write_data,
    output reg  [7:0]  read_data
);

    reg [7:0] mem [0:31];

    always @(posedge clk) begin
        if (we)
            mem[addr] <= write_data;

        // This is a synchronous, read-first RAM style.
        read_data <= mem[addr];
    end

endmodule
