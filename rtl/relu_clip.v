`timescale 1ns / 1ps

module relu_clip (
    input  wire signed [23:0] acc,
    output reg         [7:0]  out   // unsigned 0..127
);

    // Step 1: ReLU - if acc < 0, clamped to 0
    // Step 2: Arithmetic right shift by 11 (acc >>> 11)
    // Step 3: Clip/Saturate - if shifted > 127, clamp to 127, else take [6:0]

    wire signed [23:0] shifted;
    assign shifted = acc >>> 11;

    always @(*) begin
        if (acc < 0) begin
            // ReLU: negative numbers become 0
            out = 8'd0;
        end else if (shifted > 24'sd127) begin
            // Clip: saturate at 127
            out = 8'd127;
        end else begin
            // Normal range: 0..127
            out = shifted[7:0];
        end
    end

endmodule
