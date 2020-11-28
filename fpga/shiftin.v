/*
reg_in_data:  	data clocked in by the client
t_data: 			data bit
t_clk:  			data clock (controlled by client)
enable:   		enable (hi) / reset (low)
ready:  			output signal that data has been clocked in
*/

module data_shiftin( reg_in_data, t_data, t_clk, enable, ready, led3);

parameter REGISTER_WIDTH = 129;  //2 64bit counters and 1 1bit polarity

output [REGISTER_WIDTH-1:0]reg_in_data;
reg [REGISTER_WIDTH-1:0]reg_in_data;

input t_data;
wire t_data;

input t_clk;
wire t_clk;

input enable;
wire enable;

output ready;
reg ready;

output led3;
reg led3 = 0;

reg [7:0] bit_cntr;

always @ (posedge t_clk)
begin
   led3 <= 1;
	if (enable)
	begin
		if((bit_cntr < REGISTER_WIDTH))
		begin
			reg_in_data <= reg_in_data << 1;
			reg_in_data[0] <= t_data;
			bit_cntr <= bit_cntr + 1'b1;
		end 
		else 
		begin
			ready <= 1;
		end
	end
	else
	begin
		bit_cntr <= 0;
		ready <= 0;
	end
end

endmodule
