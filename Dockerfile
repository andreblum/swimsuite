FROM fedora:21
MAINTAINER andre@blums.nl

RUN yum install -y django pymongo python-matplotlib
ADD . /opt/swimsuite
WORKDIR /opt/swimsuite
EXPOSE 80
CMD [ "python", "manage.py", "runserver", "0.0.0.0:80" ]


