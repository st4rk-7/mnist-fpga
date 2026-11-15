`timescale 1ns / 1ps

module tb_rom_image;

    reg         clk;
    reg  [13:0] addr_a;
    wire [7:0]  data_a;
    reg  [13:0] addr_b;
    wire [7:0]  data_b;

    reg [7:0] expected [0:12543];
    integer errors;

    rom_image dut (
        .clk(clk),
        .addr_a(addr_a),
        .data_a(data_a),
        .addr_b(addr_b),
        .data_b(data_b)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task check_pair;
        input [13:0] test_addr_a;
        input [13:0] test_addr_b;
        begin
            @(negedge clk);
            addr_a = test_addr_a;
            addr_b = test_addr_b;
            @(posedge clk);
            #1;

            if (data_a !== expected[test_addr_a]) begin
                $display("FAIL: image port A addr %0d gave %h, expected %h",
                         test_addr_a, data_a, expected[test_addr_a]);
                errors = errors + 1;
            end

            if (data_b !== expected[test_addr_b]) begin
                $display("FAIL: image port B addr %0d gave %h, expected %h",
                         test_addr_b, data_b, expected[test_addr_b]);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        errors = 0;
        addr_a = 14'd0;
        addr_b = 14'd0;
        $readmemh("data/images.hex", expected);

        check_pair(14'd0,     14'd12543);
        check_pair(14'd1,     14'd12542);
        check_pair(14'd783,   14'd784);
        check_pair(14'd784,   14'd783);
        check_pair(14'd11760, 14'd2352);

        if (errors == 0)
            $display("PASS: both rom_image ports read correctly");
        else
            $display("FAIL: rom_image has %0d error(s)", errors);

        $finish;
    end

endmodule
