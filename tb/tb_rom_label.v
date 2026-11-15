`timescale 1ns / 1ps

module tb_rom_label;

    reg        clk;
    reg  [3:0] addr;
    wire [3:0] data;

    reg [3:0] expected [0:15];
    integer errors;
    integer i;

    rom_label dut (
        .clk(clk),
        .addr(addr),
        .data(data)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        errors = 0;
        addr   = 4'd0;
        $readmemh("data/labels.hex", expected);

        for (i = 0; i < 16; i = i + 1) begin
            @(negedge clk);
            addr = i[3:0];
            @(posedge clk);
            #1;

            if (data !== expected[i]) begin
                $display("FAIL: label addr %0d gave %h, expected %h",
                         i, data, expected[i]);
                errors = errors + 1;
            end
        end

        if (errors == 0)
            $display("PASS: all rom_label entries are correct");
        else
            $display("FAIL: rom_label has %0d error(s)", errors);

        $finish;
    end

endmodule
