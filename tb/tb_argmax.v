`timescale 1ns / 1ps

module tb_argmax;

    reg         clk;
    reg         rst_n;
    reg         valid;
    reg  signed [23:0] score;
    reg         [3:0]  out_idx;
    wire        [3:0]  max_idx;

    integer errors = 0;
    integer file, r;
    integer s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, exp_digit;
    integer scores[0:9];
    integer i;

    argmax dut (
        .clk(clk),
        .rst_n(rst_n),
        .valid(valid),
        .score(score),
        .out_idx(out_idx),
        .max_idx(max_idx)
    );

    reg [1023:0] dummy_str;

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst_n = 0;
        valid = 0;
        score = 0;
        out_idx = 0;

        #20 rst_n = 1;
        #10;

        file = $fopen("data/argmax_vectors.csv", "r");
        if (file == 0) begin
            $display("[FAIL] Could not open data/argmax_vectors.csv");
            $finish;
        end

        // Skip header
        r = $fgets(dummy_str, file);

        while (!$feof(file)) begin
            r = $fscanf(file, "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                        s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, exp_digit);
            if (r == 11) begin
                scores[0] = s0; scores[1] = s1; scores[2] = s2; scores[3] = s3; scores[4] = s4;
                scores[5] = s5; scores[6] = s6; scores[7] = s7; scores[8] = s8; scores[9] = s9;

                // Reset before each test case
                @(posedge clk);
                rst_n = 0;
                @(posedge clk);
                rst_n = 1;

                // Stream 10 scores
                for (i = 0; i < 10; i = i + 1) begin
                    @(posedge clk);
                    valid   = 1;
                    out_idx = i[3:0];
                    score   = scores[i];
                end

                @(posedge clk);
                valid = 0;
                #1;

                if (max_idx !== exp_digit[3:0]) begin
                    $display("[FAIL] Expected digit %0d, got %0d", exp_digit, max_idx);
                    errors = errors + 1;
                end
            end
        end
        $fclose(file);

        if (errors == 0) begin
            $display("========================================");
            $display("  tb_argmax: ALL TESTS PASSED");
            $display("========================================");
        end else begin
            $display("========================================");
            $display("  tb_argmax: FAILED WITH %0d ERRORS", errors);
            $display("========================================");
        end
        $finish;
    end

endmodule
