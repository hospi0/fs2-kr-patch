@echo off
rem FS2 Korean mod - FSO 26.0.1 FASTDBG launch (writes fs2_open.log)
rem log: %APPDATA%\HardLightProductions\FreeSpaceOpen\data\fs2_open.log
cd /d "C:\Program Files (x86)\GOG Galaxy\Games\Freespace 2\Knossos.NET\FS2"
"C:\Program Files (x86)\GOG Galaxy\Games\Freespace 2\Knossos.NET\bin\FSO-26.0.1\windows\x64_avx\fs2_open_26_0_1_x64_AVX-FASTDBG.exe" -mod FS2KR-0.2,MVPS-5.0.2,GOTYMissions-1.0.3,MjnMHs-1.7.3,SCPUI-1.1.2 -soft_particles -enable_shadows -dualscanlines -targetinfo -rearm_timer -3dwarp -warp_flash -aa -ship_choice_3d -weapon_choice_3d -ambient_factor 80 -spec_point 0.3 -spec_static 1.2 -spec_tube 0.3 -bloom_intensity 15 -fov 0.6
