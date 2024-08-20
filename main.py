from simulation import Simulation
import cProfile
import pstats

def runSimulation():
    simulation = Simulation.get_instance()
    
    simulation.run()
    

    
if __name__ == "__main__":
    cProfile.run('runSimulation()', "funcStats")
    
    # p = pstats.Stats("funcStats")
    # p.sort_stats("cumulative").print_stats(100)