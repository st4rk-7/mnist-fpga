`timescale 1ns / 1ps

// Full-system test. Runs all 16 images through the whole accelerator
// and checks the predicted digit against Python's golden answer.
module tb_top;

    reg        clk;
    reg        rst_n;
    reg        start;
    reg  [3:0] img_sel;
    wire [3:0] digit;
    wire       busy;
    wire       done;

    integer errors = 0;
    integer i;
    integer timeout;

    // Python's expected predicted digit for each of the 16 images.
    reg [3:0] exp_digit [0:15];

    top dut (
        .clk(clk), .rst_n(rst_n), .start(start), .img_sel(img_sel),
        .digit(digit), .busy(busy), .done(done)
    );

    always #5 clk = ~clk;   // 100 MHz

    initial begin
        $readmemh("data/exp_digit.hex", exp_digit);

        clk = 0; rst_n = 0; start = 0; img_sel = 0;
        #20 rst_n = 1;
        #10;

        for (i = 0; i < 16; i = i + 1) begin
            @(negedge clk);
            img_sel = i[3:0];
            start   = 1;
            @(negedge clk);
            start   = 0;

            // wait for done, with a safety timeout
            timeout = 0;
            while (!done && timeout < 100000) begin
                @(posedge clk);
                timeout = timeout + 1;
            end

            if (timeout >= 100000) begin
                $display("[FAIL] image %0d: timed out, done never asserted", i);
                errors = errors + 1;
            end else if (digit !== exp_digit[i]) begin
                $display("[FAIL] image %0d: got digit %0d, expected %0d",
                         i, digit, exp_digit[i]);
                errors = errors + 1;
            end else begin
                $display("[ok]   image %0d: digit %0d", i, digit);
            end

            // let the FSM return to IDLE before the next image
            @(negedge clk);
            repeat (3) @(posedge clk);
        end

        $display("========================================");
        if (errors == 0)
            $display("  tb_top: ALL 16 IMAGES PASSED");
        else
            $display("  tb_top: FAILED WITH %0d ERRORS", errors);
        $display("========================================");
        $finish;
    end

endmodule
