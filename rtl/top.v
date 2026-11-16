`timescale 1ns / 1ps

// top.v - top-level of the MNIST accelerator.
// NO math here. Only wires + module instances. The chassis that bolts
// Control's controller/memories to Compute's mac/relu_clip/argmax.
module top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [3:0]  img_sel,     // which test image (0..15)
    output wire [3:0]  digit,       // the predicted digit (from argmax)
    output wire        busy,
    output wire        done
);

    // ---------------------------------------------------------------
    // WIRES (the cables between modules)
    // ---------------------------------------------------------------
    wire        layer;              // 0 = layer 1, 1 = layer 2
    wire [14:0] w_addr;
    wire [5:0]  b_addr;
    wire [13:0] px_addr;
    wire [4:0]  h_addr;
    wire        h_we;
    wire        load_bias;
    wire        acc_en;
    wire        score_valid;
    wire [3:0]  out_idx;

    wire signed [7:0]  weight;      // from rom_weights
    wire signed [15:0] bias;        // from rom_bias
    wire [7:0]  image_px;           // from rom_image (layer 1 input)
    wire [7:0]  hidden_rd;          // from hidden_buf (layer 2 input)

    wire signed [23:0] acc;         // mac result
    wire [7:0]  relu_out;           // relu_clip result (goes to hidden_buf)

    wire [7:0]  mac_pixel;          // the MUX output -> mac.pixel

    // ---------------------------------------------------------------
    // CONTROL + MEMORY (Control's modules - plumbing, wired for you)
    // ---------------------------------------------------------------
    controller u_ctrl (
        .clk(clk), .rst_n(rst_n), .start(start), .img_sel(img_sel),
        .layer(layer), .w_addr(w_addr), .b_addr(b_addr), .px_addr(px_addr),
        .h_addr(h_addr), .h_we(h_we), .load_bias(load_bias), .acc_en(acc_en),
        .score_valid(score_valid), .out_idx(out_idx), .busy(busy), .done(done)
    );

    rom_weights u_w  (.clk(clk), .addr(w_addr), .data(weight));
    rom_bias    u_b  (.clk(clk), .addr(b_addr), .data(bias));
    rom_image   u_im (.clk(clk), .addr_a(px_addr), .data_a(image_px),
                      .addr_b(14'd0), .data_b());   // port b unused here

    hidden_buf  u_hb (
        .clk(clk), .we(h_we), .addr(h_addr),
        .write_data(relu_out),   // layer 1 writes relu result in
        .read_data(hidden_rd)    // layer 2 reads hidden value out
    );

    // ===============================================================
    // COMPUTE PART (mac / relu_clip / argmax) + input mux
    // ===============================================================

    // Input mux: layer 1 feeds image pixels, layer 2 feeds hidden values.
    // Becomes a 2-to-1 multiplexer, 8 bits wide.
    assign mac_pixel = layer ? hidden_rd : image_px;

    // Multiply-accumulate. Becomes a DSP48 slice + 24-bit register.
    mac u_mac (
        .clk(clk), .rst_n(rst_n),
        .load_bias(load_bias), .acc_en(acc_en),
        .bias(bias), .pixel(mac_pixel), .weight(weight),
        .acc(acc)
    );

    // ReLU + shift + clip. Combinational: comparators + mux.
    relu_clip u_relu (
        .acc(acc),
        .out(relu_out)
    );

    // Pick the biggest of the 10 layer-2 scores. Comparator + registers.
    argmax u_arg (
        .clk(clk), .rst_n(rst_n),
        .valid(score_valid), .score(acc), .out_idx(out_idx),
        .max_idx(digit)
    );

endmodule
