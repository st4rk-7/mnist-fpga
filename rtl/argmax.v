`timescale 1ns / 1ps

module argmax (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               valid,       // 1-clock pulse when a score is ready
    input  wire signed [23:0] score,       // score for class out_idx
    input  wire        [3:0]  out_idx,     // index 0..9
    output reg         [3:0]  max_idx      // predicted digit
);

    reg signed [23:0] max_score;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // TODO 1: Reset max_idx to 0 and max_score to lowest possible 24-bit signed number (24'sh800000)
            max_idx   <= 4'd0;
            max_score <= 24'sh800000;
        end else if (valid) begin
            // Tie-break rule (PROJECT_CONTEXT.md Section 9):
            // Use strict greater-than (>) to keep the lower index on a tie.
            // When out_idx == 0, unconditionally take the first score.
            if (out_idx == 4'd0 || score > max_score) begin
                max_score <= score;
                max_idx   <= out_idx;
            end
        end
    end

endmodule
