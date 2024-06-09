# Intentional Walk Server

[![Coverage Status](https://coveralls.io/repos/github/sfbrigade/intentional-walk-server/badge.svg?branch=master)](https://coveralls.io/github/sfbrigade/intentional-walk-server?branch=master)

## API

See [Wiki](https://github.com/sfbrigade/intentional-walk-server/wiki)

## Docker-based Development Setup

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop

   1. If you have Windows Home Edition, you will need to install Docker Toolbox instead.
   See the troubleshooting notes below.

2. Copy `example.env` to `.env` and edit the Docker environment variables as needed.

3. Open a command-line shell, change into your repo directory, and execute this command:

   ```
   $ docker-compose up
   ```

   It will take a while the first time you run this command to download and
   build the images to run the web application code in a Docker "container".
   In addition, random database data is generated during this process.

4. Now you should be able to open the web app in your browser at: http://localhost:8000/

   1. If you had to install Docker Toolbox, then replace "localhost" with the IP
   address of the Docker Virtual Machine.

5. To stop the server, press CONTROL-C in the window with the running server.
   If it is successful, you will see something like this:

   ```
   Killing intentional-walk-server_db_1           ... done
   Killing intentional-walk-server_server_1       ... done
   ```

   If it is not successful, you may see something like this:

   ```
   ERROR: Aborting.
   ```

   If you get an error, the server may still be running on your computer. To force it to stop,
   run the following command and wait for the output to report DONE:

   ```
   $ docker-compose stop
   Stopping intentional-walk-server_db_1          ... done
   Stopping intentional-walk-server_server_1      ... done
   ```

## Server management commands

Note: see the instructions in the next quick reference section to start/log in to a running
server container and perform the following actions within the container CLI.

 * To create an admin user that can log in to the web views:

   ```
   # python manage.py createsuperuser
   ```

 * To run the test suite:

   ```
   # pytest
   ```

 * To run database migrations:

   ```
   # python manage.py migrate
   ```

 * To collect staticfiles (required for admin interface):

   ```
   # python manage.py collectstatic
   ```
### Seeding the database 
For seeding the database for development you have two options:

1) (Recommended) - Grabbing a scrubbed replica of a deployed database from test/staging or prod:
This needs to be run inside the docker integrated terminal (e.g. docker exec -it <id> /bin/bash)
```sh
python manage.py herokudump iwalk-prod
```

2) (Older) - A randomized database dump. 
```
# python scripts/dummydata.py --help
# python scripts/dummydata.py > data.dump
```

## Testing

This project uses `pytest` for testing. Tests are located in the `tests` directory.

To run tests, invoke the following command in a docker terminal connected to the container:

```bash
make test
```

To generate a code coverage report to see which parts of the code are covered by the tests. This is done with the following command:

```bash
make coverage
```

This runs the tests, generates a coverage report and displays a nice HTML direcotry `htmlcov`. You can view this report
on `http://localhost:8001/`.
Be sure to manually refresh the page each time you run `make coverage`.

## Heroku deployment info

 * Register a free Heroku account here: https://signup.heroku.com/

   Set up your ssh keys with your account for authentication. Then contact an existing team member for access to the Heroku deployment instance(s).

 * Add the git remote repository corresponding to the Heroku deployment environment you wish to access. For example, the staging environment:

   ```
   # git remote add staging https://git.heroku.com/iwalk-test.git
   ```

 * Log in with the Heroku client:

   ```
   # heroku login
   ```

 * Perform a manual database backup:

   ```
   # heroku pg:backups:capture
   ```

 * Download the latest database backup:

   ```
   # heroku pg:backups:download
   ```

 * Deploy to Heroku:

   ```
   # git push <remote name, i.e. staging> <branch to deploy, i.e. master>
   ```

 * Execute a management command in the Heroku deployment environment:

   ```
   # heroku run --remote <remote name, i.e. staging> <command to execute, i.e. python manage.py migrate>
   ```

## Docker Command Quick Reference

 * To start all the containers:

   ```
   $ docker-compose up
   ```

 * To run commands within the server container, use the Docker Desktop UI to open a shell inside the running server container. Alternatively, with the containers running, open a new terminal window, change directory (`cd`) to the root directory of this project, and run:

   ```
   $ docker-compose exec server bash -l
   ```

   If you are missing modules, re-build the server (see below).


 * To stop all the containers, in case things didn't shutdown properly with CTRL-C:

   ```
   $ docker-compose stop
   ```

 * To run the server container without starting everything:

   ```
   $ docker-compose run --rm server bash -l
   ```

 * To re-build the server container (e.g., when you are missing a new modules):

   ```
   $ docker-compose build server
   ```

   Alternatively, you can use to Docker Desktop UI to re-build the server or db container.


## Docker Troubleshooting

* On some PC laptops, a hardware CPU feature called virtualization is disabled by default, which is required by Docker. To enable it, reboot your computer into its BIOS interface (typically by pressing a key like DELETE or F1 during the boot process), and look for an option to enable it. It may be called something like *Intel Virtualization Technology*, *Intel VT*, *AMD-V*, or some similar variation.

* On Windows, Docker Desktop cannot run on Windows Home edition. Install Docker Toolbox instead:

  https://docs.docker.com/toolbox/overview/

  https://github.com/docker/toolbox/releases

  Use the *Docker QuickStart shell* installed with Docker Toolbox to open a command-line shell that launches Docker for you when it starts. On Windows, right-click on the shotcut and Run as Administrator. Note: this can take a long time to start, depending upon your computer, as it needs to start a virtual machine running Linux.

  The virtual machine will have its own, separate IP address on your computer. In the ```.env``` file (see step 4 in Getting Started), replace *localhost* with *192.168.99.100* in the BASE_HOST and BASE_URL variables. To confirm that this is the correct IP address, run this command in the command-line shell:

  ```
  $ docker-machine ip
  ```

## Requirements
The Heroku buildpack for python requires the existence of a `requirements.txt` file. However, we use `poetry` (and its associated requirements file, `pyproject.toml`) to run coverage tests in TravisCI. Keeping the two package lists in sync is difficult to manage manually; instead we export a `requirements.txt` file from poetry with:

```
poetry add {NEW_PACKAGE}
poetry export -f requirements.txt --without-hashes > requirements.txt
```
