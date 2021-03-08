FROM alpine:3.11

# Basics
RUN apk update
RUN apk upgrade
RUN apk add g++ gcc git libffi-dev make python3 python3-dev py3-pip cmake libpng-dev libssh2-dev openssl-dev

# Service

WORKDIR /opt/glraw-service

ADD requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

# FastAPI, ASGI deployment
# RUN pip install fastapi uvicorn celery
# RUN pip install python-multipart aiofiles
# RUN pip3 freeze

# Deploy
# COPY bin bin
ADD . service

ENV USERNAME=glraw-service
ENV GLRAW_DIRECTORY=/opt/dependencies/glraw/build
ENV RESULT_DIR=/data/results

# CMD ["uvicorn", "--host=0.0.0.0", "main:app"]
CMD ["python3", "service/main.py"]
