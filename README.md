# swimsuite
Swimming Pool Computer and web-app

Start as docker container:

    docker-compose up
  
or:

    docker run --name mongo -v /root/mongo:/data/db -p 27017:27017 mongo

    docker build andreblum/swimsuite .
    docker run --name swimsuite --link mongo:swimsuite_mongo -p 8080:80 -d andreblum/swimsuite
