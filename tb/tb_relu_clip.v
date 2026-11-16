`timescale 1ns / 1ps

module tb_relu_clip;

    reg  signed [23:0] acc;
    wire        [7:0]  out;

    integer errors = 0;
    integer file, r;
    integer a, exp_out;

    relu_clip dut (
        .acc(acc),
        .out(out)
    );

    reg [1023:0] dummy_str;

    initial begin
        file = $fopen("data/relu_vectors.csv", "r");
        if (file == 0) begin
            $display("[FAIL] Could not open data/relu_vectors.csv");
            $finish;
        end

        // Skip header
        r = $fgets(dummy_str, file);

        while (!$feof(file)) begin
            r = $fscanf(file, "%d,%d\n", a, exp_out);
            if (r == 2) begin
                acc = a;
                #5; // combinational settle
                if (out !== exp_out[7:0]) begin
                    $display("[FAIL] acc=%d => got out=%d, expected=%d", a, out, exp_out);
                    errors = errors + 1;
                end
            end
        end
        $fclose(file);

        if (errors == 0) begin
            $display("========================================");
            $display("  tb_relu_clip: ALL TESTS PASSED");
            $display("========================================");
        end else begin
            $display("========================================");
            $display("  tb_relu_clip: FAILED WITH %0d ERRORS", errors);
            $display("========================================");
        end
        $finish;
    end

endmodule
