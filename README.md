# Intentional Walk Server

## Docker-based Development Setup

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop

   1. If you have Windows Home Edition, you will need to install Docker Toolbox instead.
   See the troubleshooting notes below.

2. Open a command-line shell, change into your repo directory, and execute this command:

   ```
   $ docker-compose up
   ```

   It will take a while the first time you run this command to download and
   build the images to run the web application code in a Docker "container".

3. Now you should be able to open the web app in your browser at: http://localhost:8000/

   1. If you had to install Docker Toolbox, then replace "localhost" with the IP
   address of the Docker Virtual Machine.

4. To stop the server, press CONTROL-C in the window with the running server.
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

## Docker Command Quick Reference

 * To start all the containers:

   ```
   $ docker-compose up
   ```

 * To log in to the running server container:

   ```
   $ docker-compose exec server bash -l
   ```

 * To stop all the containers, in case things didn't shutdown properly with CTRL-C:

   ```
   $ docker-compose stop
   ```

 * To run the server container without starting everything:

   ```
   $ docker-compose run --rm server bash -l
   ```

 * To re-build the server container:

   ```
   $ docker-compose build server
   ```

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
