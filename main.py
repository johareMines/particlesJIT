from simulation import Simulation
import cProfile
import pstats
import asyncio


async def run_simulation():
    simulation = Simulation.get_instance()
    await simulation.run()

if __name__ == "__main__":
    # Initialize the profiler
    profiler = cProfile.Profile()

    # Start the profiler
    profiler.enable()

    # Run the async function
    asyncio.run(run_simulation())

    # Stop the profiler
    profiler.disable()

    # # Save and print stats
    # profiler.dump_stats("funcStats")
    # p = pstats.Stats("funcStats")
    # p.sort_stats("cumulative").print_stats(100)
