`timescale 1ns / 1ps

module tb_controller;

    reg         clk;
    reg         rst_n;
    reg         start;
    reg  [3:0]  img_sel;

    wire        layer;
    wire [14:0] w_addr;
    wire [5:0]  b_addr;
    wire [13:0] px_addr;
    wire [4:0]  h_addr;
    wire        h_we;
    wire        load_bias;
    wire        acc_en;
    wire        score_valid;
    wire [3:0]  out_idx;
    wire        busy;
    wire        done;

    integer errors;
    integer cycles;
    integer acc_count;
    integer hidden_write_count;
    integer score_count;
    integer done_count;
    integer bias_load_count;
    integer expected_pixel_addr;

    reg [14:0] previous_w_addr;
    reg [13:0] previous_px_addr;
    reg [4:0]  previous_h_addr;

    controller dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .img_sel(img_sel),
        .layer(layer),
        .w_addr(w_addr),
        .b_addr(b_addr),
        .px_addr(px_addr),
        .h_addr(h_addr),
        .h_we(h_we),
        .load_bias(load_bias),
        .acc_en(acc_en),
        .score_valid(score_valid),
        .out_idx(out_idx),
        .busy(busy),
        .done(done)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    always @(posedge clk) begin
        if (rst_n) begin
            cycles = cycles + 1;

            if (acc_en) begin
                if (previous_w_addr != acc_count[14:0]) begin
                    $display("FAIL: weight address %0d, expected %0d",
                             previous_w_addr, acc_count);
                    errors = errors + 1;
                end

                if (acc_count < 25088) begin
                    expected_pixel_addr = (3 * 784) + (acc_count % 784);

                    if (previous_px_addr != expected_pixel_addr[13:0]) begin
                        $display("FAIL: pixel address %0d, expected %0d",
                                 previous_px_addr, expected_pixel_addr);
                        errors = errors + 1;
                    end
                end else begin
                    if (previous_h_addr != ((acc_count - 25088) % 32)) begin
                        $display("FAIL: hidden read address %0d at MAC %0d",
                                 previous_h_addr, acc_count);
                        errors = errors + 1;
                    end
                end

                acc_count = acc_count + 1;
            end

            if (h_we) begin
                if (h_addr != hidden_write_count[4:0]) begin
                    $display("FAIL: hidden write address %0d, expected %0d",
                             h_addr, hidden_write_count);
                    errors = errors + 1;
                end

                hidden_write_count = hidden_write_count + 1;
            end

            if (score_valid) begin
                if (out_idx != score_count[3:0]) begin
                    $display("FAIL: output index %0d, expected %0d",
                             out_idx, score_count);
                    errors = errors + 1;
                end

                score_count = score_count + 1;
            end

            if (done)
                done_count = done_count + 1;

            if (load_bias) begin
                if (b_addr != bias_load_count[5:0]) begin
                    $display("FAIL: bias address %0d, expected %0d",
                             b_addr, bias_load_count);
                    errors = errors + 1;
                end

                bias_load_count = bias_load_count + 1;
            end

            if (score_valid && out_idx > 4'd9) begin
                $display("FAIL: invalid output index %0d", out_idx);
                errors = errors + 1;
            end

            previous_w_addr  = w_addr;
            previous_px_addr = px_addr;
            previous_h_addr  = h_addr;
        end
    end

    task check_count;
        input [8*32-1:0] name;
        input integer actual;
        input integer expected;
        begin
            if (actual != expected) begin
                $display("FAIL: %0s = %0d, expected %0d", name, actual, expected);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        errors             = 0;
        cycles             = 0;
        acc_count          = 0;
        hidden_write_count = 0;
        score_count        = 0;
        done_count         = 0;
        bias_load_count    = 0;
        expected_pixel_addr = 0;
        previous_w_addr     = 15'd0;
        previous_px_addr    = 14'd0;
        previous_h_addr     = 5'd0;

        rst_n   = 1'b0;
        start   = 1'b0;
        img_sel = 4'd3;

        repeat (3) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        // The Board block promises a one-clock start pulse.
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        // A switch change while busy must not change the selected image.
        img_sel = 4'd9;

        // A correct one-MAC controller should finish well before this limit.
        // Waiting for a fixed limit keeps this testbench Verilog-2001 compatible.
        repeat (30000) @(posedge clk);

        if (done_count == 0) begin
            $display("FAIL: controller timed out");
            errors = errors + 1;
        end

        check_count("acc_en pulses", acc_count, 25408);
        check_count("hidden writes", hidden_write_count, 32);
        check_count("valid scores", score_count, 10);
        check_count("bias loads", bias_load_count, 42);
        check_count("done pulses", done_count, 1);

        if (errors == 0)
            $display("PASS: controller event counts are correct");
        else
            $display("FAIL: controller has %0d error(s)", errors);

        $finish;
    end

endmodule
