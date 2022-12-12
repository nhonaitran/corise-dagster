## Directories

* workspaces: Contains the code for our Dagster workspace this include separate directories for the content, project and challenge.

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

* restart_content: Restart the Docker container running the content workspace. This can be helpful when your Docker compose is ru

nning, and you've made a change to the content workspace that you would like to be applied.

* restart_project: Restart the Docker container running the project workspace.

* restart_challenge: Restart the Docker container running the project workspace.