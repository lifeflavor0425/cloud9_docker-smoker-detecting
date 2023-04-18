FROM python:3.9.16

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y update && apt-get -y install libgl1-mesa-glx
RUN apt-get -y update && apt-get -y install libglib2.0-0
# RUN apt-get -y update && python -m pip install --upgrade pip

ENV yolo /YOLO
WORKDIR $yolo/

COPY app.py /YOLO/app.py
COPY requirements.txt /YOLO/requirements.txt
COPY . /YOLO/

RUN pip install -r requirements.txt

CMD [ "python3","app.py" ]