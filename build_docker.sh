docker image build -t flask_docker .
docker login
docker tag flask_docker jamesnguyendev30/flask-docker
docker push jamesnguyendev30/flask-docker