from state_ensemble import *

graph = DualGraph("25")

ensemble = StateEnsemble(graph, 3, 0.02, tract_census_cols=True)

ensemble.run_chain(10, 5, saving_file_dir_path="data")