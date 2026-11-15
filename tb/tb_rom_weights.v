`timescale 1ns / 1ps

module tb_rom_weights;

    reg                clk;
    reg  [14:0]        addr;
    wire signed [7:0]  data;

    reg signed [7:0] expected [0:25407];
    integer errors;

    rom_weights dut (
        .clk(clk),
        .addr(addr),
        .data(data)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task check_address;
        input [14:0] test_addr;
        begin
            // Change the address away from the active clock edge.
            @(negedge clk);
            addr = test_addr;

            // The synchronous ROM updates data at the following rising edge.
            @(posedge clk);
            #1;

            if (data !== expected[test_addr]) begin
                $display("FAIL: addr %0d gave %h, expected %h",
                         test_addr, data, expected[test_addr]);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        errors = 0;
        addr   = 15'd0;

        $readmemh("data/weights.hex", expected);

        // Start, layer boundary, and end of the frozen weight map.
        check_address(15'd0);
        check_address(15'd1);
        check_address(15'd25087);
        check_address(15'd25088);
        check_address(15'd25406);
        check_address(15'd25407);

        if (errors == 0)
            $display("PASS: rom_weights synchronous reads are correct");
        else
            $display("FAIL: rom_weights has %0d error(s)", errors);

        $finish;
    end

endmodule
