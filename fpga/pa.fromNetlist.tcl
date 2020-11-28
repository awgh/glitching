
# PlanAhead Launch Script for Post-Synthesis pin planning, created by Project Navigator

create_project -name glitchcraft -dir "D:/fpga/glitchcraft/planAhead_run_2" -part xc6slx16csg324-2
set_property design_mode GateLvl [get_property srcset [current_run -impl]]
set_property edif_top_file "D:/fpga/glitchcraft/glitchcraft.ngc" [ get_property srcset [ current_run ] ]
add_files -norecurse { {D:/fpga/glitchcraft} }
set_param project.pinAheadLayout  yes
set_property target_constrs_file "glitchcraft.ucf" [current_fileset -constrset]
add_files [list {glitchcraft.ucf}] -fileset [get_property constrset [current_run]]
link_design
