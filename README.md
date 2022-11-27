# co:rise Data Engineering with Dagster

This repo contains the code to complete my co:rise Data Engineering with Dagster course 
(https://corise.com/course/dagster). 

Instructions and content is contained within the co:rise course itself.

## Week 1 Project
* config_schema={"s3_key": str}: this gets defined in the week_1/project/config.yaml file.
the key "s3_key" is defined in there, with the value for the key
* the data type of the function returns can be set using `out={"stocks": Out(dagster_type=List[Stock])}` key in 
@op decorator or by specific function type hint
* the "tag" key in @op(decorator) specifies the green value under config column
* The docstrings or use @op(description="xxx") to show the description of the operation

By specify all these values would help to provide more details info about the operations
for the pipeline.