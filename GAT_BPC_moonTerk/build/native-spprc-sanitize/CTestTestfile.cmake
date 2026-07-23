# CMake generated Testfile for 
# Source directory: /home/kai/work/GAT_BPC_moonTerk/native/lunar_spprc
# Build directory: /home/kai/work/GAT_BPC_moonTerk/build/native-spprc-sanitize
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[lunar_spprc_native_tests]=] "/home/kai/work/GAT_BPC_moonTerk/build/native-spprc-sanitize/lunar_spprc_native_tests")
set_tests_properties([=[lunar_spprc_native_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/kai/work/GAT_BPC_moonTerk/native/lunar_spprc/CMakeLists.txt;60;add_test;/home/kai/work/GAT_BPC_moonTerk/native/lunar_spprc/CMakeLists.txt;0;")
add_test([=[lunar_spprc_patch_queue_check]=] "/home/kai/miniconda3/bin/python" "/home/kai/work/GAT_BPC_moonTerk/native/lunar_spprc/../../scripts/check_rcspp_patch_queue.py" "--source" "/home/kai/work/GAT_BPC_moonTerk/build/native-spprc-sanitize/_deps/rcspp-src")
set_tests_properties([=[lunar_spprc_patch_queue_check]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/kai/work/GAT_BPC_moonTerk/native/lunar_spprc/CMakeLists.txt;61;add_test;/home/kai/work/GAT_BPC_moonTerk/native/lunar_spprc/CMakeLists.txt;0;")
subdirs("_deps/rcspp-build")
