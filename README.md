# Hanabi Web UI

This repo contains a web application that allows clients to connect and play Hanabi with an AI through a web browser. The purpose of this repo is to support research in Instructive AI, so this application facilicates the AI studying the human play style and recommending changes (in the form of instructions) that would theoretically lead to better play.

## Running the server application

To run the server application, first ensure you have all the necessary prerequisites.

### Dependencies

1. If you do not already have Python 3, you will need to install it (https://www.python.org/downloads/).
1. Install NodeJS (https://nodejs.org/en/download/). This application is being developed for support with version 12.13.1, but other versions will likely work too.

### Launching the server application

Once all dependencies are setup, the server application can be launched from the command line by navigating to the root of this repository and entering the command
```
node HanabiServer.js
```
The command line window will freeze (since hosting the server is a blocking operation), but the server will be running. Debug messages may print to the command line window during client interaction.

### Connecting with the web UI

Once the server application is running, you can launch the web UI by opening any browser (_except_ Internet Explorer, please) and entering
```
localhost:8090
```
if the server is running on the same machine that's running the web browser, otherwise
```
[server.ip.address.here]:8090
```
where `[server.ip.address.here]` is the IP address of the computer running the server application.