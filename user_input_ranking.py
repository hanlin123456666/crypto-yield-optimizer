import json
import couchdb

# CouchDB configuration
COUCHDB_URL = 'http://admin:password@couchdb-service:5984/' #updated
COUCHDB_DB = 'defillama_pools'

# Investment types and weights
investment_types = {
    'Yield maximize': {'apy_mean_30d': 0.7, 'apy_change_30d': 0.2, 'tvlUsd': 0.1},
    'Balanced investor': {'apy_mean_30d': 0.5, 'apy_change_30d': 0.3, 'tvlUsd': 0.2},
    'Conservative investor': {'apy_mean_30d': 0.4, 'apy_change_30d': 0.4, 'tvlUsd': 0.2}
}

# Only the 4 allowed (protocol, token) pairs
combinations = [
    ('aave-v3', 'USDC'),
    ('aave-v3', 'USDT'),
    ('aave-v3', 'DAI'),
    ('compound-v3', 'USDC')
]
# Connect to CouchDB
couch = couchdb.Server(COUCHDB_URL)
db = couch[COUCHDB_DB]

# Function to calculate weighted average
def weighted_average(data, weights):
    return sum(data.get(key, 0) * weight for key, weight in weights.items())

# User input for investment type
investment_type = input("Enter investment type (Yield maximize, Balanced investor, Conservative investor): ")

# Validate investment type
if investment_type not in investment_types:
    print("Invalid investment type. Choose from: Yield maximize, Balanced investor, Conservative investor.")
    exit()

weights = investment_types[investment_type]
results = []

# Query and score
for protocol, token in combinations:
    query = {'selector': {'symbol': token, 'project': protocol}}
    docs = list(db.find(query))
    if docs:
        latest = docs[-1]  # Assume latest is last
        score = weighted_average(latest, weights)
        results.append({
            'protocol': protocol,
            'token': token,
            'score': round(score, 4)
        })

# Sort by score descending
sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

# Output JSON
print(json.dumps(sorted_results, indent=2))