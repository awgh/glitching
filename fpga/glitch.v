`include "shiftin.v"

module glitchcraft(go, armed, enable, done, glitch, targetreset, t_data, t_clk, led2, led3, SYSCLK_P, SYSCLK_N);

parameter CTR_WIDTH = 63;
parameter DUTY_REG_WIDTH = 3;

//inputs
input SYSCLK_P;
input SYSCLK_N;

//input clk;
input go;
input enable;
input t_data;
input t_clk;

//outputs
output armed;
reg armed = 0;
output done;
reg done = 0;
output glitch;
reg glitch = 0;
output targetreset;
reg targetreset = 0;

// Debug LEDs
output led2;
reg led2 = 0;
output led3;

//internal storage
reg [CTR_WIDTH:0]holdoff_ctr;
reg [CTR_WIDTH:0]hold_ctr;
reg [1:0]state = 0;
reg polarity = 0;
wire [128:0]configdata; //2 64bit counters and 1 1bit polarity

// Differential clock @ 200 Mhz
IBUFGDS #(
	.DIFF_TERM("TRUE"),     // Differential Termination
	.IOSTANDARD("LVDS_25")  // Specify the input I/O standard
) IBUFGDS_inst (
	.O  (CLK200M),   // Clock buffer output
	.I  (SYSCLK_P),  // Diff_p clock buffer input (connect directly to top-level port)
	.IB (SYSCLK_N)   // Diff_n clock buffer input (connect directly to top-level port)
);


data_shiftin data_in(configdata, t_data, t_clk, enable, ready, led3);

always @ (posedge CLK200M)//clk)
begin	
   led2 <= 1;
	if (enable)
	begin
		case(state)
		//STATE 0: reset/prep
			0:begin					
				done 		   <= 0;
				targetreset <= 0;
				
				if (ready)
				begin					
					{holdoff_ctr, hold_ctr, polarity} <= configdata;
					glitch 		<= polarity;
					armed 		<= 1;					
				end
				
				if (armed & go)
				begin
					state <= state + 1'b1;
				end
			end		
		//STATE 1: waiting for 'go' signal
			1:begin
				//armed <= 0;
				targetreset <= 1;		//release the target from reset
				holdoff_ctr <= holdoff_ctr-1;
				
				if (holdoff_ctr == 0)
				begin
					glitch <= !glitch;
					state <= state + 1'b1;
				end									
			end
		//STATE 2: wait t(hold), then stop glitching
			2:begin
				hold_ctr <= hold_ctr-1;
				
				if (hold_ctr == 0)
				begin
					glitch <= !glitch;
					state <= state + 1'b1;					
				end			
			end

		//STATE 3: indicate completion, wait for reset
			3:begin
				done <= 1;				
				armed <= 0;
			end
		endcase
	end
	else
	begin
		state <= 0;
	end
end

endmodule
