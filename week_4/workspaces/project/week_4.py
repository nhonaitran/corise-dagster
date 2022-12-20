from typing import List

from dagster import Nothing, String, asset, with_resources, AssetIn, OpExecutionContext
from workspaces.resources import redis_resource, s3_resource
from workspaces.types import Aggregation, Stock


@asset(
    config_schema={"s3_key": String},
    required_resource_keys={"s3"},
    op_tags={"kind": "s3"},
    group_name="corise",
)
def get_s3_data(context: OpExecutionContext) -> List[Stock]:
    """Get a list of stocks from an S3 file"""
    data = context.resources.s3.get_data(context.op_config["s3_key"])
    return [Stock.from_list(item) for item in data]


@asset(
    ins={"stocks": AssetIn(key="get_s3_data")},
    group_name="corise",
)
def process_data(stocks: List[Stock]) -> Aggregation:
    """Given a list of stocks return the Aggregation of the greatest stock high"""
    stock_greatest_high: Stock = max(stocks, key=lambda x: x.high)
    return Aggregation(date=stock_greatest_high.date, high=stock_greatest_high.high)


@asset(
    required_resource_keys={"redis"},
    ins={"aggregation": AssetIn(key="process_data")},
    op_tags={"kind": "redis"},
    group_name="corise",
)
def put_redis_data(context: OpExecutionContext, aggregation: Aggregation) -> Nothing:
    """Upload an Aggregation to Redis"""
    key = aggregation.date.isoformat()
    value = str(aggregation.high)
    context.resources.redis.put_data(key, value)


@asset(
    required_resource_keys={"s3"},
    ins={"aggregation": AssetIn(key="process_data")},
    op_tags={"kind": "s3"},
    group_name="corise",
)
def put_s3_data(context: OpExecutionContext, aggregation: Aggregation) -> Nothing:
    """Upload the Aggregation to S3."""
    key = aggregation.date.isoformat()
    context.resources.s3.put_data(key=key, data=aggregation)


get_s3_data_docker, process_data_docker, put_redis_data_docker, put_s3_data_docker = with_resources(
    definitions=[get_s3_data, process_data, put_redis_data, put_s3_data],
    resource_defs={"s3": s3_resource, "redis": redis_resource},
    resource_config_by_key={
        's3': {
            'config': {
                'bucket': 'dagster',
                'access_key': 'test',
                'secret_key': 'test',
                'endpoint_url': 'http://localhost:4566',
            }
        },
        'redis': {
            'config': {
                'host': 'redis',
                'port': 6379,
            }
        },
    },
)
