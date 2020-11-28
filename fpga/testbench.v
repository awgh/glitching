//`include "glitch.v"
`timescale 1 ns/1 ns

module testme();

	reg enable = 0;
	reg go = 0;
	reg t_data = 0;

	wire done;
	wire glitch;
	wire armed;
	wire targetreset;
	
	wire led2;
	wire led3;
	reg SYSCLK_P = 0;
	reg SYSCLK_N = 0;
	
	initial
	begin
		$dumpfile("test.vcd");    
		$dumpvars(0,glitchcraft_inst);

		// Initialize Inputs
		SYSCLK_P = 0;
		SYSCLK_N = 1;

      enable   	= 0;
		
		//as soon as we enable the shifter starts taking in data
		#4 enable	= 1;

		//make last 2 bits of first counter 1
		#124 t_data	= 1;
		#4  t_data	= 0;

		//make last 2 bits of second counter 1
		#124 t_data	= 1;
		#4	  t_data = 0;	//comment out this line to leave t_data high which sets polarity to 1

		//armed should be high now, tell the module to perform glitch
		#15 go 		= 1;
		//#17 go 		= 0;

      #100;
      #4 enable = 0;  // do a pseudo-reset 
		#4 enable = 1;
		
		#100 $finish;
	end

	glitchcraft glitchcraft_inst(go, armed, enable, done, glitch, targetreset, t_data, SYSCLK_P, led2, led3, SYSCLK_P, SYSCLK_N);	
             
   always 
	begin	 
     #1 SYSCLK_P <= ~SYSCLK_P; SYSCLK_N <= SYSCLK_P;
   end  

endmodule

