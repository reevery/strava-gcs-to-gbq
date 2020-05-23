from google.cloud import storage
from google.cloud import bigquery
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def main(event, context=None):
    # Get bucket name and object_id from the Bucket event message.
    bucket_name = event['attributes']['bucketId']
    logger.info('Bucket ID: %s', bucket_name)
    object_id = event['attributes']['objectId']
    logger.info('Object ID: %s', object_id)

    # Initialise Cloud Storage.
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Initialise BigQuery.
    bigquery_client = bigquery.Client()
    table = bigquery_client.get_table(os.getenv('BIGQUERY_TABLE'))

    # Read the file from Cloud Storage.
    blob = bucket.get_blob(object_id)
    activity = json.loads(blob.download_as_string())
    logger.debug(activity)

    # Set the updated time so that all points in BigQuery get the same value.
    updated_utc = datetime.now()

    # My output saves each point as a different row. These points are contained
    # within the activity stream lists.
    streams = activity['streams']
    stream_types = streams.keys()
    logger.debug('Stream keys: %s', stream_types)

    # Get the number of points.
    number_of_points = None
    for k, v in streams.items():
        if not number_of_points:
            number_of_points = len(v['data'])
        else:
            assert number_of_points == len(v['data'])
    logger.info('%s points', number_of_points)

    # Initialise the list to save points to.
    output = []

    for i in range(0, number_of_points):
        # The timestamp is number of seconds from activity start.
        point = dict(
            source='strava',
            source_id=os.path.splitext(object_id)[0],
            type=activity['type'],
            timestamp_utc=(
                    datetime.fromisoformat(activity['start_date'])
                    + timedelta(
                seconds=streams['time']['data'][i])).timestamp(),
            updated_utc=updated_utc
        )
        # Split out latlng into two objects.
        if 'latlng' in stream_types:
            point['latitude'] = streams['latlng']['data'][i][0]
            point['longitude'] = streams['latlng']['data'][i][1]
            # And add a point
            point['point'] = f"POINT({point['longitude']} " \
                             f"{point['latitude']})"

        # Velocity and Altitude I want renamed.
        if 'velocity_smooth' in stream_types:
            point['velocity'] = streams['velocity_smooth']['data'][i]
        if 'altitude' in stream_types:
            point['elevation'] = streams['altitude']['data'][i]

        # Now streams I do not need to manipulate, but may not be recorded.
        for stream in [s for s in stream_types if s in [
            'heartrate']]:
            point[stream] = streams[stream]['data'][i]

        logger.debug(point)
        output.append(point)

    # Write to BigQuery in chunks of  10,000 rows.
    # BigQuery API will time out if you try to write too many rows at once.
    for i in range(0, len(output), 10000):
        errors = bigquery_client.insert_rows(table, output[i:i+10000])
        try:
            assert errors == []
        except AssertionError:
            logger.error(errors)
