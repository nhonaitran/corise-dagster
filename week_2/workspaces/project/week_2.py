from typing import List

from dagster import In, Nothing, Out, ResourceDefinition, String, graph, op
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
def process_data(context, stocks: list[Stock]) -> Aggregation:
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
def week_2_pipeline():
    stocks = get_s3_data()
    aggregation = process_data(stocks)
    put_s3_data(aggregation)
    put_redis_data(aggregation)


local = {
    "ops": {"get_s3_data": {"config": {"s3_key": "prefix/stock.csv"}}},
}

docker = {
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
    "ops": {"get_s3_data": {"config": {"s3_key": "prefix/stock.csv"}}},
}

week_2_pipeline_local = week_2_pipeline.to_job(
    name="week_2_pipeline_local",
    config=local,
    resource_defs={
        "s3": mock_s3_resource,
        "redis": ResourceDefinition.mock_resource()
    },
)

week_2_pipeline_docker = week_2_pipeline.to_job(
    name="week_2_pipeline_docker",
    config=docker,
    resource_defs={
        "s3": s3_resource,
        "redis": redis_resource
    },
)
