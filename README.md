# swimsuite
Swimming Pool Computer and web-app


## Introduction

Swimsuite is a raspberry pi pool computer capable of controlling the main pump and a solar valve by driving two solid state relays, and by sensing water and roof temperatures through a dual channel A/D converter. Python code for the raspberry pi and the init script (raspbian) can be found in /rpi.

The raspberry pi pool computer periodically logs data to a mongodb database.

A web application for smart phones is serving from the mongo database content, and shows current temperatures and pump and valve status, and can draw graphs for the day and the week.

## Run the Web App serving container

Start as docker container:

    docker-compose up
  
or:

    docker run --name mongo -v /root/mongo:/data/db -p 27017:27017 mongo

    docker build andreblum/swimsuite .
    docker run --name swimsuite --link mongo:swimsuite_mongo -p 8080:80 -d andreblum/swimsuite

## Run the Web App

Point a browser at <your docker host ip>:8080/status
