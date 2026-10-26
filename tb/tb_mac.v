`timescale 1ns / 1ps

module tb_mac;

    reg         clk;
    reg         rst_n;
    reg         load_bias;
    reg         acc_en;
    reg  signed [15:0] bias;
    reg         [7:0]  pixel;
    reg  signed [7:0]  weight;
    wire signed [23:0] acc;

    integer errors = 0;
    integer file, r;
    integer b, w, p, exp_acc;

    mac dut (
        .clk(clk),
        .rst_n(rst_n),
        .load_bias(load_bias),
        .acc_en(acc_en),
        .bias(bias),
        .pixel(pixel),
        .weight(weight),
        .acc(acc)
    );

    always #5 clk = ~clk; // 100 MHz clock

    reg [1023:0] dummy_str;

    initial begin
        clk = 0;
        rst_n = 0;
        load_bias = 0;
        acc_en = 0;
        bias = 0;
        pixel = 0;
        weight = 0;

        #20 rst_n = 1;
        #10;

        // Test 1: Vector-by-vector check from data/mac_vectors.csv
        file = $fopen("data/mac_vectors.csv", "r");
        if (file == 0) begin
            $display("[FAIL] Could not open data/mac_vectors.csv");
            $finish;
        end

        // Skip header
        r = $fgets(dummy_str, file);

        while (!$feof(file)) begin
            r = $fscanf(file, "%d,%d,%d,%d\n", b, w, p, exp_acc);
            if (r == 4) begin
                // Step 1: Set bias and assert load_bias before clock edge
                @(negedge clk);
                bias = b;
                load_bias = 1;
                acc_en = 0;

                // Step 2: Set inputs for accumulation
                @(negedge clk);
                load_bias = 0;
                weight = w;
                pixel = p;
                acc_en = 1;

                // Step 3: Deassert acc_en
                @(negedge clk);
                acc_en = 0;

                // Check output after accumulation is registered
                @(posedge clk);
                #1;
                if (acc !== exp_acc) begin
                    $display("[FAIL] bias=%d w=%d p=%d => got acc=%d, expected=%d", b, w, p, acc, exp_acc);
                    errors = errors + 1;
                end
            end
        end
        $fclose(file);

        if (errors == 0) begin
            $display("========================================");
            $display("  tb_mac: ALL TESTS PASSED");
            $display("========================================");
        end else begin
            $display("========================================");
            $display("  tb_mac: FAILED WITH %0d ERRORS", errors);
            $display("========================================");
        end
        $finish;
    end

endmodule
