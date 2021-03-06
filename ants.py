#!/usr/bin/env python

import sys
import math
import random
from collections import Counter
import shortpath
from utils import tour
from utils import LOG,LOGN

def euclidian_distance( ci, cj, graph = None):
    return math.sqrt( float(ci[0] - cj[0])**2 + float(ci[1] - cj[1])**2 )

def graph_distance( ci, cj, graph ):
    p,c = shortpath.astar( graph, ci, cj )
    return c 


def cost( permutation, cost_func, cities ):
    dist = 0
    for ci,cj in tour(permutation):
        dist += cost_func( ci, cj, cities )
    return dist


def look( cities, last, exclude, pheromones, w_heuristic, w_history, cost_func = graph_distance ):
    choices = []
    # gather informations about possible moves
    for current in cities:
        if current in exclude:
            # This is faster than "if current not in exclude"
            continue
        c = {"city" : current}
        c["history"]   = pheromones[last][current] ** w_history
        c["distance"]  = cost_func( last, current, cities )
        c["heuristic"] = (1.0 / c["distance"]) ** w_heuristic
        c["proba"] = c["history"] * c["heuristic"]
        choices.append(c)
    return choices


def proba_choose( choices ):
    s = float(sum( c["proba"] for c in choices ))
    if s == 0.0:
        return random.choice(choices)["city"]

    v = random.random()
    for i,c in enumerate(choices):
        v -= c["proba"] / s
        if v <= 0.0:
            return c["city"]

    return c[-1]["city"]


def greedy_choose( choices ):
    c = max( choices, key = lambda c : c["proba"] )
    return c["city"]


def walk( cities, pheromones, w_heuristic, w_history, c_greedy, cost_func = graph_distance ):
    assert( len(cities) > 0 )
    # permutations are indices
    # randomly draw the first city index
    permutation = [ random.choice( cities.keys() ) ]
    # then choose the next ones to build the permutation
    while len(permutation) < len(cities):
        choices = look( cities, permutation[-1], permutation, pheromones, w_heuristic, w_history, cost_func )
        do_greedy = ( random.random() <= c_greedy )
        if do_greedy:
            next_city = greedy_choose( choices )
        else:
            next_city = proba_choose( choices )
        permutation.append( next_city )

    # assert no duplicates
    assert( max(Counter(permutation).values()) == 1 )
    return permutation


def initialize_pheromones_whole( cities, init_value ):
    rows = {}
    for i in cities:
        cols = {}
        for j in cities:
            cols[j] = init_value
        rows[i] = cols
    return rows


def update_global_whole( pheromones, candidate, graph, decay ):
    for i,j in tour(candidate["permutation"]):
        value = ((1.0 - decay) * pheromones[i][j]) + (decay * (1.0/candidate["cost"]))
        pheromones[i][j] = value
        pheromones[j][i] = value


def update_local_whole( pheromones, candidate, graph, w_pheromone, init_pheromone ):
    for i,j in tour(candidate["permutation"]):
        value = ((1.0 - w_pheromone) * pheromones[i][j]) + (w_pheromone * init_pheromone)
        pheromones[i][j] = value
        pheromones[j][i] = value


def initialize_pheromones_neighbors( cities, init_value ):
    rows = {}
    for i in cities:
        cols = {}
        for j in cities:
            # set an init value for neighbors only
            if j in cities[i]:
                cols[j] = init_value
            else: # else, there should be no edge
                cols[j] = 0
        rows[i] = cols
    return rows


def update_global_neighbors( pheromones, candidate, graph, decay ):
    for ci,cj in tour(candidate["permutation"]):
        # subpath between ci and cj
        p,c = path.astar( graph, ci, cj )
        # deposit pheromones on each edges of the subpath
        for i,j in zip(p,p[1:]):
            value = ((1.0 - decay) * pheromones[i][j]) + (decay * (1.0/candidate["cost"]))
            pheromones[i][j] = value
            pheromones[j][i] = value


def update_local_neighbors( pheromones, candidate, graph, w_pheromone, init_pheromone ):
    for ci,cj in tour(candidate["permutation"]):
        p,c = path.astar( graph, ci, cj )
        for i,j in zip(p,p[1:]):
            value = ((1.0 - w_pheromone) * pheromones[i][j]) + (w_pheromone * init_pheromone)
            pheromones[i][j] = value
            pheromones[j][i] = value


def search( cities, max_iterations, nb_ants, decay, w_heuristic, w_pheromone, w_history, c_greedy, cost_func = graph_distance ):
    # like random.shuffle(cities) but on a copy
    best = { "permutation" : sorted( cities, key=lambda i: random.random()) }
    best["cost"] = cost( best["permutation"], cost_func, cities )

    init_pheromone = 1.0 / float(len(cities)) * best["cost"]
    pheromones = initialize_pheromones_whole( cities, init_pheromone )

    for i in range(max_iterations):
        LOG( i )
        solutions = []
        for j in range(nb_ants):
            LOG( "." )
            candidate = {}
            candidate["permutation"] = walk( cities, pheromones, w_heuristic, w_history, c_greedy, cost_func )
            candidate["cost"] = cost( candidate["permutation"], cost_func, cities )
            if candidate["cost"] < best["cost"]:
                best = candidate
            update_local_whole( pheromones, candidate, cities, w_pheromone, init_pheromone )
        update_global_whole( pheromones, best, cities, decay )
        LOGN( best["cost"] )

    return best,pheromones


if __name__ == "__main__":
    max_it = 40
    num_ants = 10
    decay = 0.1
    w_heur = 2.5
    w_local_phero = 0.1
    c_greed = 0.9
    w_history = 1.0

    print """Graph TSP:
       -1  0     2 : x
      1 o  o-----o
        |  |     |
      0 o--o-----o
           |     |
           |     |
     -2 o--o-----o
      :
      y
      """
    G = {
            ( 0, 0) : [(-1, 0),( 0, 1),( 2, 0),( 0,-2)],
            ( 0, 1) : [( 0, 0),( 2, 1)],
            ( 0,-2) : [( 0, 0),( 2,-2),(-1,-2)],
            (-1, 0) : [(-1, 1),( 0, 0)],
            (-1, 1) : [(-1, 0)],
            (-1,-2) : [( 0,-2)],
            ( 2, 0) : [( 2, 1),( 2,-2),( 0, 0)],
            ( 2, 1) : [( 0, 1),( 2, 0)],
            ( 2,-2) : [( 2, 0),( 0,-2)],
    }

    best,phero = search( G, max_it, num_ants, decay, w_heur, w_local_phero, w_history, c_greed, cost_func = graph_distance )
    print best["cost"], best["permutation"]
