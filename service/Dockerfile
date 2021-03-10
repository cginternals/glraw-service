FROM utensils/opengl:19.0.8

#
# Basics
#

RUN apk update
RUN apk upgrade
RUN apk add g++ gcc make

#
# Service API Dependencies
#

RUN apk add python3 python3-dev py3-pip libffi-dev

WORKDIR /opt/glraw-service

ADD requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

# FastAPI, ASGI deployment
# RUN pip install fastapi uvicorn celery
# RUN pip install python-multipart aiofiles
# RUN pip3 freeze

#
# Service Internals and Dependencies
#

RUN apk add git cmake qt5-qtbase-dev mesa-demos

WORKDIR /opt/dependencies

RUN git clone --depth 1 https://github.com/cginternals/glraw.git

WORKDIR /opt/dependencies/glraw
RUN mkdir build
WORKDIR /opt/dependencies/glraw/build
RUN cmake .. -DCMAKE_BUILD_TYPE=Release -DOPTION_BUILD_TESTS=Off
RUN make

#
# Service
#

# Deploy
# COPY bin bin
ADD . service

ENV USERNAME=glraw-service
ENV GLRAW_DIRECTORY=/opt/dependencies/glraw/build
ENV RESULT_DIR=/data/share

#
# TEST
#

# CMD ["uvicorn", "--host=0.0.0.0", "main:app"]
CMD ["python3", "service/main.py"]
