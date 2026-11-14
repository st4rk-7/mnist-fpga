`timescale 1ns / 1ps

// Controller for the 784 -> 32 -> 10 MNIST accelerator.
// The frozen interface is in docs/PROJECT_CONTEXT.md section 9.
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

    localparam [3:0] IDLE     = 4'd0;
    localparam [3:0] L1_BIAS  = 4'd1;
    localparam [3:0] L1_MAC   = 4'd2;
    localparam [3:0] L1_STORE = 4'd3;
    localparam [3:0] L2_BIAS  = 4'd4;
    localparam [3:0] L2_MAC   = 4'd5;
    localparam [3:0] ARGMAX   = 4'd6;
    localparam [3:0] DONE     = 4'd7;

    reg [3:0] state;
    reg [3:0] next_state;

    // input_count is the next input address to issue.
    // It reaches 784 or 32 for one drain clock after the final address.
    reg [9:0] input_count;
    reg [4:0] hidden_count;
    reg [3:0] output_count;

    // weight_count runs through the frozen ROM order from 0 to 25,407.
    reg [14:0] weight_count;

    reg [13:0] image_base;

    // One-clock valid pipeline for synchronous BRAM data.
    reg data_valid_d;

    // Constant multiply by 784 = 512 + 256 + 16.
    // Synthesis implements the shifts as wires and the sums as adders.
    wire [13:0] selected_image_base;
    assign selected_image_base = ({10'd0, img_sel} << 9)
                               + ({10'd0, img_sel} << 8)
                               + ({10'd0, img_sel} << 4);

    // State, counters, and address-tracking registers.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state           <= IDLE;
            input_count     <= 10'd0;
            hidden_count    <= 5'd0;
            output_count    <= 4'd0;
            weight_count    <= 15'd0;
            image_base      <= 14'd0;
            data_valid_d    <= 1'b0;
        end else begin
            state <= next_state;

            case (state)
                IDLE: begin
                    data_valid_d <= 1'b0;

                    if (start) begin
                        input_count     <= 10'd0;
                        hidden_count    <= 5'd0;
                        output_count    <= 4'd0;
                        weight_count    <= 15'd0;
                        image_base      <= selected_image_base;
                    end
                end

                L1_BIAS: begin
                    // Address 0 is issued during this state.
                    input_count  <= 10'd1;
                    weight_count <= weight_count + 1'b1;
                    data_valid_d <= 1'b1;
                end

                L1_MAC: begin
                    if (input_count <= 10'd783) begin
                        input_count  <= input_count + 1'b1;
                        weight_count <= weight_count + 1'b1;
                        data_valid_d <= 1'b1;
                    end else begin
                        // No new request. Consume the previous final request.
                        data_valid_d <= 1'b0;
                    end
                end

                L1_STORE: begin
                    input_count  <= 10'd0;
                    data_valid_d <= 1'b0;

                    if (hidden_count < 5'd31)
                        hidden_count <= hidden_count + 1'b1;
                    else
                        output_count <= 4'd0;
                end

                L2_BIAS: begin
                    // Hidden address 0 is issued during this state.
                    input_count  <= 10'd1;
                    weight_count <= weight_count + 1'b1;
                    data_valid_d <= 1'b1;
                end

                L2_MAC: begin
                    if (input_count <= 10'd31) begin
                        input_count  <= input_count + 1'b1;
                        weight_count <= weight_count + 1'b1;
                        data_valid_d <= 1'b1;
                    end else begin
                        data_valid_d <= 1'b0;
                    end
                end

                ARGMAX: begin
                    input_count  <= 10'd0;
                    data_valid_d <= 1'b0;

                    if (output_count < 4'd9)
                        output_count <= output_count + 1'b1;
                end

                DONE: begin
                    data_valid_d <= 1'b0;
                end

                default: begin
                    input_count     <= 10'd0;
                    hidden_count    <= 5'd0;
                    output_count    <= 4'd0;
                    weight_count    <= 15'd0;
                    image_base      <= 14'd0;
                    data_valid_d    <= 1'b0;
                end
            endcase
        end
    end

    // Next-state logic.
    always @(*) begin
        next_state = state;

        case (state)
            IDLE: begin
                if (start)
                    next_state = L1_BIAS;
            end

            L1_BIAS: begin
                next_state = L1_MAC;
            end

            L1_MAC: begin
                if (input_count == 10'd784 && data_valid_d)
                    next_state = L1_STORE;
            end

            L1_STORE: begin
                if (hidden_count == 5'd31)
                    next_state = L2_BIAS;
                else
                    next_state = L1_BIAS;
            end

            L2_BIAS: begin
                next_state = L2_MAC;
            end

            L2_MAC: begin
                if (input_count == 10'd32 && data_valid_d)
                    next_state = ARGMAX;
            end

            ARGMAX: begin
                if (output_count == 4'd9)
                    next_state = DONE;
                else
                    next_state = L2_BIAS;
            end

            DONE: begin
                next_state = IDLE;
            end

            default: begin
                next_state = IDLE;
            end
        endcase
    end

    // Moore output and address logic. Every output has a default value.
    always @(*) begin
        layer       = 1'b0;
        w_addr      = weight_count;
        b_addr      = 6'd0;
        px_addr     = image_base;
        h_addr      = 5'd0;
        h_we        = 1'b0;
        load_bias   = 1'b0;
        acc_en      = 1'b0;
        score_valid = 1'b0;
        out_idx     = output_count;
        busy        = 1'b1;
        done        = 1'b0;

        case (state)
            IDLE: begin
                busy    = 1'b0;
                w_addr  = 15'd0;
                b_addr  = 6'd0;
                px_addr = selected_image_base;
            end

            L1_BIAS: begin
                b_addr    = {1'b0, hidden_count};
                px_addr   = image_base;
                load_bias = 1'b1;
            end

            L1_MAC: begin
                acc_en = data_valid_d;

                if (input_count <= 10'd783) begin
                    w_addr  = weight_count;
                    px_addr = image_base + input_count;
                end else begin
                    // Hold legal addresses during the drain clock.
                    w_addr  = weight_count - 1'b1;
                    px_addr = image_base + 14'd783;
                end
            end

            L1_STORE: begin
                h_addr = hidden_count;
                h_we   = 1'b1;

                // Present the next bias one clock before load_bias.
                if (hidden_count == 5'd31)
                    b_addr = 6'd32;
                else
                    b_addr = {1'b0, hidden_count} + 1'b1;
            end

            L2_BIAS: begin
                layer     = 1'b1;
                b_addr    = 6'd32 + output_count;
                h_addr    = 5'd0;
                load_bias = 1'b1;
            end

            L2_MAC: begin
                layer  = 1'b1;
                acc_en = data_valid_d;

                if (input_count <= 10'd31) begin
                    w_addr = weight_count;
                    h_addr = input_count[4:0];
                end else begin
                    w_addr = weight_count - 1'b1;
                    h_addr = 5'd31;
                end
            end

            ARGMAX: begin
                layer       = 1'b1;
                score_valid = 1'b1;

                // Preload the following layer-2 bias during ARGMAX.
                if (output_count < 4'd9)
                    b_addr = 6'd33 + output_count;
                else
                    b_addr = 6'd41;
            end

            DONE: begin
                busy = 1'b0;
                done = 1'b1;
            end

            default: begin
                busy = 1'b0;
            end
        endcase
    end

endmodule
