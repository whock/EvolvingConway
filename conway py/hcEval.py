

# Evaluation parameters:
evalTime = 10000; # plenty of time.
evalReplicates = 64; # plenty of reps.

# Other issue:
# Constructing a hillClimb object makes it's own pattern so modifying size or init density is bad.
# We want some defaults and to be able to modify them.

# Have reproducable seeds.
   # randomly generate a seed when hill-climbing.
   # perfectly reproducible.
   # One global seed gives a list of all random numbers.
   # Store seeds.

# Time taken for the entire algorythim.
start_time = time.time()
# your code
elapsed_time = time.time() - start_time