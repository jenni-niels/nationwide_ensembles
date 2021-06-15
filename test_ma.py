from state_ensemble import *

graph = DualGraph("25")

ensemble = StateEnsemble(graph, 3, 0.02)

ensemble.run_chain(100, 50, saving_file_dir_path="data")