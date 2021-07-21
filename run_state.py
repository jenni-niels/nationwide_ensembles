import argparse
import pandas as pd
from states import STATES
from state_ensemble import *
from gerrychain.updaters import Tally
import sys

ACS_COLS = ['HCVAP19','NHCVAP19','2MORECVAP19','AMINCVAP19','ASIANCVAP19','BCVAP19','NHPICVAP19',
            'WCVAP19','CVAP19','HCPOP19','NHCPOP19','2MORECPOP19','AMINCPOP19','ASIANCPOP19',
            'BCPOP19','NHPICPOP19','WCPOP19','CPOP19','TOTPOP19','NH_WHITE19','NH_BLACK19',
            'NH_AMIN19','NH_ASIAN19','NH_NHPI19','NH_OTHER19','NH_2MORE19','HISP19','H_WHITE19',
            'H_BLACK19','H_AMIN19','H_ASIAN19','H_NHPI19','H_OTHER19','H_2MORE19']

## Read in 
parser = argparse.ArgumentParser(description="State Ensemble", 
                                 prog="sb_runs.py")
parser.add_argument("state", metavar="postal_code", type=str,
                    help="postal code of state to run the ensemble for")
parser.add_argument("iters", metavar="chain_length", type=int,
                    help="how long to run each chain")
parser.add_argument("saving_interval", metavar="saving_interval", type=int,
                    help="How often to save plans/plan stats")
parser.add_argument("map", metavar="district_type", type=str,
                    help="What kind of districts to draw?",
                    choices=["congress10", "congress20", "state_senate"])
args = parser.parse_args()

fips_code = STATES[args.state]["STFIPS"]

eps = 0.02 if args.map in ["congress10", "congress20"] else 0.05

pop_col = "TOTPOP" if args.map == "congress10" else "TOTPOP19"

try:
    num_dists = STATES[args.state]["Districts"][args.map]
except:
    print("District type ({}) not found for state {}.".format(args.state, args.map))
    sys.exit()

try: 
    df = pd.read_csv("acs19_by_state/{}_acs_19_data.csv".format(args.state))
    df = df.rename(columns={"GEOID": "GEOID10"})
except:
    print("ACS data not available for {}".format(args.state))
    sys.exit()

graph = DualGraph(fips_code, additional_data=df)

updaters = {k: Tally(k) for k in ACS_COLS}
ensemble = StateEnsemble(graph, num_dists, eps, pop_col=pop_col,custom_updaters=updaters,
                         track_census_cols=True, district_scores=ACS_COLS)

ensemble.run_chain(args.iters, args.saving_interval, verbose=True,
                   saving_file_dir_path="/cluster/tufts/mggg/jmatth03/national_ensembles_data/{}/{}".format(args.state, args.map))