from gerrychain import (GeographicPartition, Partition, Graph, MarkovChain,
                        proposals, updaters, constraints, accept, Election, tree)
from gerrychain.proposals import recom, propose_random_flip
from functools import (partial, reduce)
import numpy as np
import random
import requests
import json
from networkx.readwrite import json_graph

URL = "https://people.csail.mit.edu/ddeford/{0}/{0}_{1}.json"
URL_UNITS = {"blocks": "BLOCK",
             "blockgroups": "BG",
             "tracts": "TRACT",
             "counties": "COUNTY"}
DEFAULT_COLS = [
    # pop
    "TOTPOP", "NH_WHITE", "NH_BLACK", "NH_AMIN ", "NH_ASIAN", "NH_NHPI", "NH_OTHER", "NH_2MORE",
    "HISP", "H_WHITE", "H_BLACK", "H_AMIN", "H_ASIAN", "H_NHPI", "H_OTHER", "H_2MORE",
    # vap
    "VAP", "HVAP", "WVAP", "BVAP", "AMINVAP", "ASIANVAP", "NHPIVAP", "OTHERVAP", "2MOREVAP",
]

class DualGraph:
    """
        Class representing the a Dual Graph object.
    """
    def __init__(self, state_fips, pop_col="TOTPOP", units="blockgroups", additional_data=None):
        self.st_fips = state_fips
        self.units = units
        self.pop_col = pop_col
        self.graph = self.retrieve_dual_graph()
        if additional_data:
            self.graph.add_data(additional_data)

    def retrieve_dual_graph(self):
        response = json.loads(requests.get(URL.format(URL_UNITS[self.units], self.st_fips)).text)
        return Graph(json_graph.adjacency_graph(response))

    def init_partition(self, num_districts, epsilon):
        totpop = sum([self.graph.nodes()[n][self.pop_col] for n in self.graph.nodes()])
        ideal_pop = totpop / num_districts
        return tree.recursive_tree_part(self.graph, range(num_districts), ideal_pop, self.pop_col, epsilon)

    def save_graph(self):
        """ TODO:: 
        """
        pass


class StateEnsemble:
    def __init__(self, dual_graph, num_districts, epsilon, 
                 verbose=False, initital_partition=None, custom_updaters=None):
        self.graph = dual_graph
        self.num_districts = num_districts
        self.epsilon = epsilon
        self.init_partition = initital_partition

        if self.init_partition is None:
            self.init_partition = self.graph.init_partition(num_districts, epsilon)