# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.9.16 

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install libglib2.0-0
RUN apt-get update && apt-get -y install libgl1-mesa-glx
WORKDIR /detection

COPY dlib_face_recognition_resnet_model_v1.dat /detection/
COPY dlib_face_recognition_resnet_model_v1.dat.bz2 /detection/
COPY shape_predictor_5_face_landmarks.dat /detection/
COPY shape_predictor_5_face_landmarks.dat.bz2 /detection/
COPY detect.py /detection/


COPY dataset_img /detection/dataset_img/
COPY detecting_img /detection/detecting_img/
COPY success /detection/success/
COPY . /detection/


# WORKDIR /app


COPY requirements.txt /detection/requirements.txt

RUN pip install --upgrade pip

RUN pip3 install cmake

# 체크 부분
RUN apt-get install -y libpq-dev
RUN apt-get -y update && apt-get -y install libboost-all-dev
# RUN pip install dlib==19.24.1

# RUN apt-get update -y && apt-get install build-essential cmake pkg-config -y

RUN pip install dlib==19.24.1

RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt


# ENTRYPOINT [ "home" ]
# 옵션
CMD ["python3", "detect.py"]