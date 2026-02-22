# MongoDB → Azure CosmosDB Migration Guide

CosmosDB for MongoDB uses the same wire protocol as MongoDB, so the migration
is mostly a **connection string swap**. Here's the complete process.

---

## Step 1 — Export from local MongoDB

```bash
# Export the submissions collection to a BSON dump
mongodump \
  --uri="mongodb://localhost:27017" \
  --db=json_submissions \
  --collection=submissions \
  --out=./dump
```

Or export to JSON (portable):
```bash
mongoexport \
  --uri="mongodb://localhost:27017" \
  --db=json_submissions \
  --collection=submissions \
  --out=submissions.json
```

---

## Step 2 — Get your CosmosDB connection string

```bash
az cosmosdb keys list \
  --name cosmos-json-to-email \
  --resource-group rg-json-to-email \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" -o tsv
```

The string looks like:
```
mongodb://<account>:<key>@<account>.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@<account>@
```

---

## Step 3 — Import into CosmosDB

```bash
# Import BSON dump
mongorestore \
  --uri="<COSMOSDB_CONNECTION_STRING>" \
  --db=json_submissions \
  ./dump/json_submissions

# Or import from JSON
mongoimport \
  --uri="<COSMOSDB_CONNECTION_STRING>" \
  --db=json_submissions \
  --collection=submissions \
  --file=submissions.json
```

---

## Step 4 — Swap the connection string in your app

**Local `.env`:**
```env
MONGO_URI=mongodb://localhost:27017
```

**Production (Azure Container App env var):**
```env
MONGO_URI=mongodb://<account>:<key>@<account>.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@<account>@
```

The app code (`database.py`) does not change at all — Motor/PyMongo use the
same driver for both.

---

## CosmosDB Compatibility Notes

| Feature              | Local MongoDB | CosmosDB for MongoDB |
|----------------------|:---:|:---:|
| CRUD operations      | ✅  | ✅  |
| Async Motor driver   | ✅  | ✅  |
| Aggregation pipeline | ✅  | ✅ (subset) |
| Transactions         | ✅  | ✅ (4.0+)  |
| `$lookup` joins      | ✅  | ⚠️ Limited |
| Full-text search     | ✅  | ⚠️ Use Cognitive Search |

---

## Verify the migration

```bash
# Count documents in CosmosDB
mongosh "<COSMOSDB_CONNECTION_STRING>" \
  --eval "db.getSiblingDB('json_submissions').submissions.countDocuments()"
```
