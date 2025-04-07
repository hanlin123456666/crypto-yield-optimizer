import json
import couchdb

# CouchDB configuration
COUCHDB_URL = 'http://admin:password@localhost:5984/' #need to update
COUCHDB_DB = 'defillama_pools'

# Investment types and weights
investment_types = {
    'Yield maximize': {'apy_mean_30d': 0.7, 'apy_change_30d': 0.2, 'tvlUsd': 0.1},
    'Balanced investor': {'apy_mean_30d': 0.5, 'apy_change_30d': 0.3, 'tvlUsd': 0.2},
    'Conservative investor': {'apy_mean_30d': 0.4, 'apy_change_30d': 0.4, 'tvlUsd': 0.2}
}

# Connect to CouchDB
couch = couchdb.Server(COUCHDB_URL)
db = couch[COUCHDB_DB]

# Function to calculate weighted average
def weighted_average(data, weights):
    return sum(data.get(key, 0) * weight for key, weight in weights.items())

# User input for multiple values
protocols = input("Enter protocols (comma-separated, e.g., aave-v3, compound-v3, lendle): ").split(',')
tokens = input("Enter tokens (comma-separated, e.g., USDT, USDC, ETH): ").split(',')
investment_type = input("Enter investment type (Yield maximize, Balanced investor, Conservative investor): ")

# Validate investment type
if investment_type not in investment_types:
    print("Invalid investment type. Choose from: Yield maximize, Balanced investor, Conservative investor.")
    exit()

results = []

# Fetch data for all combinations
for protocol in protocols:
    for token in tokens:
        protocol = protocol.strip()
        token = token.strip()
        query = {'selector': {'symbol': token, 'project': protocol}}
        result = list(db.find(query))
        if result:
            latest_data = result[-1]  # Assuming the latest entry is the most recent
            weights = investment_types[investment_type]
            score = weighted_average(latest_data, weights)
            results.append((protocol, token, score))

# Sort results by score in descending order
sorted_results = sorted(results, key=lambda x: x[2], reverse=True)

# Display sorted recommendations
print("\nRecommendations (sorted from highest to lowest score):")
for protocol, token, score in sorted_results:
    print(f"{protocol} - {token}: {score:.4f}")
