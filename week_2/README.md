## Directories

* workspaces: Contains the code for our Dagster workspace this include separate directories for the content, project and
challenge.

* data: Any data files we use for the project

* tests: The tests for the project that we will use to determine if things are working as expected

## Files

* local_stack.sh: Contains configuration settings for our localstack AWS instance.

* workspace.yaml and dagster.yaml: Dagster specific configuration settings for our Dagster project

## Makefile Commands

This week you can run the following commands in the command line using the Makefile to help:

* week_2_tests: Run the tests associated with week two

* week_2_start: Start the Docker compose project detached in the background

* week_2_down: Stop all the containers for the Docker compose project

* restart_content: Restart the Docker container running the content workspace. This can be helpful when your Docker 
compose is running, and you've made a change to the content workspace that you would like to be applied.

* restart_project: Restart the Docker container running the project workspace.

* restart_challenge: Restart the Docker container running the project workspace.

## Docker

Last week we ran everything within a virtual environment (or Gitpod). This helped manage our python dependencies such as
Dagster, but this week we will want to run the full Dagster instance, which will require some additional resources. This
time around, we will use Docker to run the full service.

### Docker Environment

From the root of the repo run the following to ensure Docker is up and running.

```
> docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

Assuming you are not currently using Docker for anything else, we should not see any containers running.

To start the Dagster Docker project, you can use the Makefile included in root of the repo. This Makefile has some 
simple commands to make interacting with the project as easy as possible. To run our Docker project, run the following 
command.

```
> make week_2_start
```

This will start the Docker compose project in the background. If this is the first time you are starting the project, 
it may take a little while for all the images to download and build (in the future Docker will not need to rebuild 
anything so it should be much faster).

```
Do not worry too much about the command itself, but if you are curious, the Makefile is running.

docker compose --env-file=week_2/.course_week --profile dagster up -d --build

This is the basic docker compose up command with a few extra flags set.

docker compose: The base Docker compose command

--env-file=week_2/.course_week: Pass in the environment variables associated with week 2

--profile dagster: Enable the Dagster services in the compose

-d: Run detached.

--build: Build the associated images if they do not exist.
```

Eventually the terminal should show all the containers have started.

```
[+] Running 9/9
 ⠿ Network dagster_network   Created                                                                                                                                                                                                                                                  0.1s
 ⠿ Container postgresql      Started                                                                                                                                                                                                                                                  3.0s
 ⠿ Container redis           Started                                                                                                                                                                                                                                                  2.9s
 ⠿ Container localstack      Started                                                                                                                                                                                                                                                  2.7s
 ⠿ Container dagster-daemon  Started                                                                                                                                                                                                                                                  9.9s
 ⠿ Container dagit           Started                                                                                                                                                                                                                                                 10.0s
 ⠿ Container content         Started                                                                                                                                                                                                                                                  8.7s
 ⠿ Container project         Started                                                                                                                                                                                                                                                  7.0s
 ⠿ Container challenge       Started
```

You can rerun the docker ps command from above to make sure all the containers are running successfully.

```
> docker ps
CONTAINER ID   IMAGE                                      COMMAND                  CREATED          STATUS                             PORTS                                             NAMES
63822fc1f93f   corise-dagster-answer-key_challenge        "dagster api grpc -h…"   33 seconds ago   Up 24 seconds                      4002/tcp                                          challenge
1936006e3c32   corise-dagster-answer-key_project          "dagster api grpc -h…"   33 seconds ago   Up 26 seconds                      4001/tcp                                          project
bd3240905181   corise-dagster-answer-key_content          "dagster api grpc -h…"   33 seconds ago   Up 24 seconds                      4000/tcp                                          content
a995913b678c   corise-dagster-answer-key_dagit            "dagit -h 0.0.0.0 --…"   33 seconds ago   Up 23 seconds                      0.0.0.0:3000->3000/tcp                            dagit
333a07e9771e   corise-dagster-answer-key_dagster-daemon   "dagster-daemon run"     33 seconds ago   Up 23 seconds                                                                        dagster-daemon
cfa71d4ea727   localstack/localstack                      "docker-entrypoint.sh"   34 seconds ago   Up 31 seconds (health: starting)   4510-4559/tcp, 5678/tcp, 0.0.0.0:4566->4566/tcp   localstack
5fcb42ce8a01   postgres:11                                "docker-entrypoint.s…"   34 seconds ago   Up 31 seconds                      5432/tcp                                          postgresql
e5a4393a4448   redis:6.2-alpine                           "docker-entrypoint.s…"   34 seconds ago   Up 31 seconds                      6379/tcp                                          redis
```

If you have Docker Desktop up you can also see a visual representation of all your containers running.

### Confirmation
After all the containers are running for the Dagster project, you can go to http://localhost:3000/, where Dagit is 
hosted. This will be the interface for your fully running Dagster Docker project.

If you want to stop your Dagster Docker project, you can use the Makefile to stop the containers by running make 
week_2_down. It is a good practice to stop the containers when you are not using Docker or working on the Dagster 
project.

### Dagster Docker Deployment

Now that we have talked about Docker, let's talk about how this relates to our week two project. There is a single 
graph for week two, but you will see two different jobs for it. One is local_week_2_pipeline and the other is 
docker_week_2_pipeline. The jobs have noticeable differences between them in terms of configs and resources used. 
Let's talk about each individually.

* local_week_2_pipeline
The config for the local job is very similar to week one. The only setting we are providing is the config schema value 
required for the process_data op:

```
local = {
    "ops": {"get_s3_data": {"config": {"s3_key": "prefix/stock.csv"}}},
}
```

Looking at the job configuration, we are using that config and setting our resource definitions to use the mock 
versions of the resources. For testing, Dagster supplies a useful helper in ResourceDefinition.mock_resource() which 
can be used to mock a resource we need to work with. This is very helpful for local runs and writing tests.

```
local_week_2_pipeline = week_2_pipeline.to_job(
    name="local_week_2_pipeline",
    config=local,
    resource_defs={"s3": mock_s3_resource, "redis": ResourceDefinition.mock_resource()},
)
```

You might notice that for the local configuration the S3 resource is mock_s3_resource rather than the more general 
ResourceDefinition.mock_resource() used by Redis. The reason for this is that the S3 mocked resource needs a return 
value (stocks) in order to execute successfully. The Redis resource mocks interacting with Redis but does not need a 
return value to provide further down the pipeline, so it can use the more generalized mock.

* docker_week_2_pipeline

The Docker job configuration is slightly more complicated. Let's look at the config:

```
docker = {
    "resources": {
        "s3": {
            "config": {
                "bucket": "dagster",
                "access_key": "test",
                "secret_key": "test",
                "endpoint_url": "http://host.docker.internal:4566",
            }
        },
        "redis": {
            "config": {
                "host": "redis",
                "port": 6379,
            }
        },
    },
    "ops": {"get_s3_data": {"config": {"s3_key": "preifx/stock.csv"}}},
}
```
There is a lot more here compared to the local config. We can still see the op level config for process_data, but we 
now also have resources in the configuration for both S3 and Redis. This makes sense. Before in our local 
configuration we were not interacting with other systems, so we did not need to pass in connection information. In 
Docker, however, we actually need to connect to S3 and Redis and provide things like the host and any authentication 
information we might need. In our job configuration we will need to supply the config and resource_defs. When you're 
in Dagit if you bring up launch pad for the docker_week_2_pipeline you will see your configuration value set.

You will want to ensure that the configuration is set when you execute a run of the pipeline.

If you run the Docker pipeline and it fails with the error.

```
botocore.errorfactory.NoSuchKey: An error occurred (NoSuchKey) when calling the GetObject operation: The specified key
does not exist.
```
Make sure you have the config schema set for your run. If this isn't set the pipeline will not know where to look for 
the S3 file.

## Summary
While in the Docker environment, if you run the jobs for local_week_2_pipeline or docker_week_2_pipeline, they will 
seem to execute the same. This is extremely powerful and will make more sense as we talk more about making our Dagster 
project production-ready later in the class. Being able to run our pipeline on two entirely different infrastructures 
without changing the actual pipeline code is very exciting and opens up a lot of possibilities when designing data 
applications! 




* 
