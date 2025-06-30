from economy import Market

# Create a market with a handful of agents
market = Market(num_agents=20)

# Run the simulation for five days
market.simulate(10)