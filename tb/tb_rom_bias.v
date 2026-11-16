`timescale 1ns / 1ps

module tb_rom_bias;

    reg                 clk;
    reg  [5:0]          addr;
    wire signed [15:0]  data;

    reg signed [15:0] expected [0:41];
    integer errors;

    rom_bias dut (
        .clk(clk),
        .addr(addr),
        .data(data)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task check_address;
        input [5:0] test_addr;
        begin
            @(negedge clk);
            addr = test_addr;
            @(posedge clk);
            #1;

            if (data !== expected[test_addr]) begin
                $display("FAIL: bias addr %0d gave %h, expected %h",
                         test_addr, data, expected[test_addr]);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        errors = 0;
        addr   = 6'd0;
        $readmemh("data/biases.hex", expected);

        check_address(6'd0);
        check_address(6'd1);
        check_address(6'd31);
        check_address(6'd32);
        check_address(6'd40);
        check_address(6'd41);

        if (errors == 0)
            $display("PASS: rom_bias synchronous reads are correct");
        else
            $display("FAIL: rom_bias has %0d error(s)", errors);

        $finish;
    end

endmodule
