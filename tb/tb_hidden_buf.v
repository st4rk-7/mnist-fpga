`timescale 1ns / 1ps

module tb_hidden_buf;

    reg        clk;
    reg        we;
    reg  [4:0] addr;
    reg  [7:0] write_data;
    wire [7:0] read_data;

    reg [7:0] expected [0:31];
    integer errors;
    integer i;

    hidden_buf dut (
        .clk(clk),
        .we(we),
        .addr(addr),
        .write_data(write_data),
        .read_data(read_data)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        errors     = 0;
        we         = 1'b0;
        addr       = 5'd0;
        write_data = 8'd0;

        // Write a different known value into every location.
        for (i = 0; i < 32; i = i + 1) begin
            expected[i] = (i * 7) + 3;
            @(negedge clk);
            we         = 1'b1;
            addr       = i[4:0];
            write_data = expected[i];
            @(posedge clk);
            #1;
        end

        // Read every location back with one-clock synchronous timing.
        @(negedge clk);
        we = 1'b0;

        for (i = 0; i < 32; i = i + 1) begin
            addr = i[4:0];
            @(posedge clk);
            #1;

            if (read_data !== expected[i]) begin
                $display("FAIL: hidden addr %0d gave %h, expected %h",
                         i, read_data, expected[i]);
                errors = errors + 1;
            end

            if (i < 31)
                @(negedge clk);
        end

        if (errors == 0)
            $display("PASS: hidden_buf wrote and read all 32 values");
        else
            $display("FAIL: hidden_buf has %0d error(s)", errors);

        $finish;
    end

endmodule
