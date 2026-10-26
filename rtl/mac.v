`timescale 1ns / 1ps

module mac (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               load_bias,
    input  wire               acc_en,
    input  wire signed [15:0] bias,
    input  wire        [7:0]  pixel,   // unsigned 0..127
    input  wire signed [7:0]  weight,  // signed -127..127
    output reg  signed [23:0] acc
);

    // Hardware detail: Convert pixel (0..127) to 9-bit signed so Verilog
    // does a SIGNED multiplication with weight.
    wire signed [16:0] product;
    assign product = $signed({1'b0, pixel}) * weight;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // TODO 1: Reset acc to 0
            acc <= 24'sd0;
        end else if (load_bias) begin
            // Sign-extend 16-bit bias to 24 bits
            acc <= {{8{bias[15]}}, bias};
        end else if (acc_en) begin
            // Accumulate signed product
            acc <= acc + product;
        end
    end

endmodule
