# Google Cloud Platform: Strava data in Cloud Storage to BigQuery

This repository contains example Python code to populate Strava data in Cloud Storage
to be loaded to  BigQuery. It is designed to be deployed to a Cloud Function.

It is expected to be triggered by a Cloud Storage event which will provide it with
the bucketId and objectId of the file it should process.

The function will load the  object from Cloud Storage, parse it as JSON, and transform the data
into a modified structure, before loading into Google BigQuery.

##Initialisation
### Environment Variables

This Cloud Function requires the following environment variables:

| Environment Variable Name|Explanation|
|---|---|
| GOOGLE_APPLICATION_CREDENTIALS|A path to a JSON credentials file. Within GCP this is set automatically.|
| STORAGE_BUCKET_NAME| The name (not path) of the Cloud Storage bucket to where the function should save each activity.|
| BIGQUERY_TABLE | The table name where the function should save the data. E.g. `my-project.dataset.table`|

## BigQuery Schema
To use the code out of the box, your BigQuery table should have the following schema:
```json
[
  {
    "name": "source",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "The origin of the data. E.g. 'strava'."
  },
  {
    "name": "source_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "An Id for the source, E.g. strava Activity Id."
  },
  {
    "name": "type",
    "type": "STRING",
    "description": "The type of activity. E.g. 'run'."
  },
  {
    "name": "timestamp_utc",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "latitude",
    "type": "FLOAT"
  },
  {
    "name": "longitude",
    "type": "FLOAT"
  },
  {
    "name": "point",
    "type": "GEOGRAPHY"
  },
  {
    "name": "elevation",
    "type": "FLOAT"
  },
  {
    "name": "velocity",
    "type": "FLOAT"
  },
  {
    "name": "heartrate",
    "type": "FLOAT"
  },
  {
    "name": "updated_utc",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "When this record was last updated. This field is used to deduplicate as the function is designed to write only."
  }
]
```