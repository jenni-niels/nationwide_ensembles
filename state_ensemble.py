
from gerrychain.random import random
random.seed(0)
from gerrychain import (GeographicPartition, Partition, Graph, MarkovChain,
                        proposals, updaters, constraints, accept, Election, tree)
from gerrychain.proposals import recom
from gerrychain.updaters import Tally

import math
from functools import (partial, reduce)
import numpy as np
import random
import requests
import json
from networkx.readwrite import json_graph
import warnings
import tqdm

URL = "https://people.csail.mit.edu/ddeford/{0}/{0}_{1}.json"
URL_UNITS = {"blocks": "BLOCK",
             "blockgroups": "BG",
             "tracts": "TRACT",
             "counties": "COUNTY"}
DEFAULT_COLS = [
    # pop
    "TOTPOP", "NH_WHITE", "NH_BLACK", "NH_AMIN", "NH_ASIAN", "NH_NHPI", "NH_OTHER", "NH_2MORE",
    "HISP", "H_WHITE", "H_BLACK", "H_AMIN", "H_ASIAN", "H_NHPI", "H_OTHER", "H_2MORE",
    # vap
    "VAP", "HVAP", "WVAP", "BVAP", "AMINVAP", "ASIANVAP", "NHPIVAP", "OTHERVAP", "2MOREVAP",
]

class DualGraph:
    """
        Class representing the a Dual Graph object.
    """
    def __init__(self, state_fips, geoid_col="GEOID10", units="blockgroups", additional_data=None):
        """
        DualGraph class constructor

        Args:
            state_fips (string): which state to generate the dual graph for.
            pop_col (str, optional): [description]. Defaults to "TOTPOP".
            units (str, optional): [description]. Defaults to "blockgroups".
            additional_data (DataFrame, optional): [description]. Defaults to None.
        """
        self.st_fips = state_fips
        self.units = units
        self.graph = self.retrieve_dual_graph()
        self.tot_pop = lambda pop_col: sum([self.graph.nodes()[n][pop_col] for n in self.graph.nodes()])
        self.geoid_col = geoid_col
        if additional_data is not None:
            self.graph.add_data(additional_data)

    def retrieve_dual_graph(self):
        response = json.loads(requests.get(URL.format(URL_UNITS[self.units], self.st_fips)).text)
        return Graph(json_graph.adjacency_graph(response))

    def init_partition(self, num_districts, epsilon, pop_col, updaters=None):
        ideal_pop = self.tot_pop(pop_col) / num_districts
        distdict =  tree.recursive_tree_part(self.graph, range(num_districts), ideal_pop, pop_col, epsilon)
        part = Partition(self.graph, distdict, {"population": Tally(pop_col, alias="population")})
        if updaters is not None: part.updaters.update(updaters)
        return part

    def save_graph(self):
        """ TODO:: 
        """
        pass


class StateEnsemble:
    def __init__(self, dual_graph, num_districts, epsilon, pop_col="TOTPOP",
                 verbose=False, initital_partition=None, custom_updaters=None,
                 plan_scores=[], district_scores=[], track_census_cols=False):
        self.graph = dual_graph
        self.pop_col = pop_col
        self.num_districts = num_districts
        self.epsilon = epsilon
        self.init_partition = initital_partition
        self.custom_updaters = custom_updaters
        self.plan_scores = plan_scores
        self.district_scores = district_scores
        self.track_census_cols = track_census_cols

        if self.init_partition is None:
            self.init_partition = self.graph.init_partition(num_districts, epsilon, pop_col,
                                                            updaters=custom_updaters)
        
        if self.track_census_cols:
            census_updaters = {k: Tally(k) for k in DEFAULT_COLS}
            self.init_partition.updaters.update(census_updaters)
            self.district_scores += DEFAULT_COLS



    def save_partition(self, assignment, plan_number, saving_file_dir_path):
        partition_json = []
        for key, dist in assignment.items():
            node_info = {"node_id": key, "dist_id": dist, 
                         "geoid": self.graph.graph.nodes()[key][self.graph.geoid_col]}
            partition_json.append(node_info)

        fout_str = "{}/plan_{}_assignment.json".format(saving_file_dir_path, plan_number)
        with open(fout_str, "w") as fout:
            json.dump(partition_json, fout, indent=2)
        return fout_str
    
    def set_up_chain(self, num_steps, init_part, compactness=True, accept_func=None):
        ideal_population = self.graph.tot_pop(self.pop_col) / self.num_districts

        proposal = partial(recom,
                           pop_col=self.pop_col,
                           pop_target=ideal_population,
                           epsilon=self.epsilon,
                           node_repeats=1)

        if compactness:
            compactness_bound = constraints.UpperBound(lambda p: len(p["cut_edges"]),
                                    2*len(init_part["cut_edges"]))
            cs = [constraints.within_percent_of_ideal_population(init_part, self.epsilon),
                compactness_bound]
        else:
            cs = [constraints.within_percent_of_ideal_population(init_part, self.epsilon)]

        if accept_func == None: accept_func = accept.always_accept

        return MarkovChain(proposal=proposal, constraints=cs,
                           accept=accept_func, initial_state=init_part,
                           total_steps=num_steps)
    
    def run_chain(self, total_steps, saving_interval, compactness=True, accept_fun=None, 
                  saving_file_dir_path="", verbose=False):
        num_saves = math.ceil(total_steps / saving_interval)

        if total_steps % saving_interval != 0:
            warnings.warn("saving_interval is non a divisor of total_steps. Running chain with {} steps.".format(num_saves*saving_interval))

        part = self.init_partition
        
        for i in range(num_saves):
            ensemble_record = {"rng_seed": i, 
                               "initial_plan": self.save_partition(part.assignment, i*saving_interval, 
                                                                   saving_file_dir_path),
                               "ensemble_stats": []}
            random.seed(i)
            chain = self.set_up_chain(saving_interval, part, compactness=compactness, 
                                      accept_func=accept_fun)
            
            for j,part in enumerate(chain):
                plan_scores = {s: part[s] for s in self.plan_scores}
                district_scores = {s: part[s] for s in self.district_scores}

                plan_scores["num_cut_edges"] = len(part["cut_edges"])

                part_record = {"id": i*saving_interval + j,
                               "plan_scores": plan_scores,
                               "district_scores": district_scores}
                
                ensemble_record["ensemble_stats"].append(part_record)

            fout_str = "{}/plans_{}_{}.json".format(saving_file_dir_path, i*saving_interval, i*saving_interval+j)
            with open(fout_str, "w") as fout:
                json.dump(ensemble_record, fout, indent=2)
            if verbose: print("Saving interval {}".format(i), flush=True)