import json, random, os

path = "data/testing-input-output/flow_data.json"
if not os.path.exists(path):
    print("❌ flow_data.json not found. Skipping injection.")
    exit(1)

with open(path) as f:
    data = json.load(f)

data["fluid_properties"]["density"] = round(random.uniform(0.8, 1.2), 3)
data["fluid_properties"]["viscosity"] = round(random.uniform(0.05, 0.15), 3)
data["initial_conditions"]["initial_velocity"] = [round(random.uniform(-1, 1), 6) for _ in range(3)]
data["initial_conditions"]["initial_pressure"] = round(random.uniform(100, 200), 3)

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Injection complete. New values:")
print(json.dumps(data["fluid_properties"], indent=2))
print(json.dumps(data["initial_conditions"], indent=2))



