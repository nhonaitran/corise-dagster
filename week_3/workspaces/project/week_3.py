from typing import List

from dagster import (
    In,
    Nothing,
    Out,
    ResourceDefinition,
    RetryPolicy,
    RunRequest,
    ScheduleDefinition,
    SkipReason,
    graph,
    op,
    schedule,
    sensor,
    static_partitioned_config,
)
from workspaces.project.sensors import get_s3_keys
from workspaces.resources import mock_s3_resource, redis_resource, s3_resource
from workspaces.types import Aggregation, Stock


@op(
    config_schema={"s3_key": str},
    required_resource_keys={"s3"},
    out={"stocks": Out(dagster_type=List[Stock])},
    tags={"kind": "s3"}
)
def get_s3_data(context) -> List[Stock]:
    """Get a list of stocks from an S3 file"""
    data = context.resources.s3.get_data(context.op_config["s3_key"])
    return [Stock.from_list(item) for item in data]


@op(
    ins={"stocks": In(dagster_type=List[Stock], description="A list of stocks")},
    out={"aggregation": Out(dagster_type=Aggregation, description="Aggregation of stock data")},
)
def process_data(context, stocks: List[Stock]) -> Aggregation:
    """Given a list of stocks return the Aggregation of the greatest stock high"""
    stock_greatest_high: Stock = max(stocks, key=lambda x: x.high)
    context.log.debug(stock_greatest_high)
    return Aggregation(date=stock_greatest_high.date, high=stock_greatest_high.high)


@op(
    required_resource_keys={"redis"},
    ins={"aggregation": In(dagster_type=Aggregation, description="Aggregation of stock data")},
    tags={"kind": "redis"},
)
def put_redis_data(context, aggregation: Aggregation) -> Nothing:
    """Upload an Aggregation to Redis"""
    key = aggregation.date.isoformat()
    value = str(aggregation.high)
    context.resources.redis.put_data(key, value)


@op(
    required_resource_keys={"s3"},
    ins={"aggregation": In(dagster_type=Aggregation, description="Aggregation of stock data")},
    tags={"kind": "s3"},
)
def put_s3_data(context, aggregation: Aggregation) -> Nothing:
    """Upload an Aggregation to S3 file"""
    key = aggregation.date.isoformat()
    context.resources.s3.put_data(key, aggregation)


@graph
def week_3_pipeline():
    stocks = get_s3_data()
    aggregation = process_data(stocks)
    put_s3_data(aggregation)
    put_redis_data(aggregation)


local = {
    "ops": {"get_s3_data": {"config": {"s3_key": "prefix/stock_9.csv"}}},
}


resources_config = {
    "resources": {
        "s3": {
            "config": {
                "bucket": "dagster",
                "access_key": "test",
                "secret_key": "test",
                "endpoint_url": "http://localstack:4566",
            }
        },
        "redis": {
            "config": {
                "host": "redis",
                "port": 6379,
            }
        },
    },
}

docker = {
    **resources_config,
    "ops": {"get_s3_data": {"config": {"s3_key": "prefix/stock_9.csv"}}},
}


@static_partitioned_config(partition_keys=[str(i) for i in range(1, 11)])
def docker_config(partition: str):
    key = f"prefix/stock_{partition}.csv"
    return {
        **resources_config,
        "ops": {"get_s3_data": {"config": {"s3_key": key}}},
    }


week_3_pipeline_local = week_3_pipeline.to_job(
    name="week_3_pipeline_local",
    config=local,
    resource_defs={
        "s3": mock_s3_resource,
        "redis": ResourceDefinition.mock_resource()
    },
)

week_3_pipeline_docker = week_3_pipeline.to_job(
    name="week_3_pipeline_docker",
    config=docker,
    resource_defs={
        "s3": s3_resource,
        "redis": redis_resource
    },
    op_retry_policy=RetryPolicy(max_retries=10, delay=1)
)


week_3_schedule_local = ScheduleDefinition(job=week_3_pipeline_local, cron_schedule="*/15 * * * *")


@schedule(
    job=week_3_pipeline_docker,
    cron_schedule="0 * * * *"
)
def week_3_schedule_docker():
    """"""
    return RunRequest(run_config=docker_config)


@sensor(
    job=week_3_pipeline_docker,
    minimum_interval_seconds=30
)
def week_3_sensor_docker(context):
    """"""
    # Here context argument is required; without it unit tests will fail.  Why?
    # Could these value provided for get_s3_keys read from a configuration file instead?
    new_files = get_s3_keys(bucket="dagster", prefix="prefix", endpoint_url="http://localstack:4566")
    if not new_files:
        yield SkipReason("No new s3 files found in bucket.")
        return

    for new_file in new_files:
        yield RunRequest(
            run_key=new_file,
            run_config={
                **resources_config,
                "ops": {"get_s3_data": {"config": {"s3_key": new_file}}},
            },
        )
