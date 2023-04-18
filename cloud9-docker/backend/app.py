from flask import Flask, render_template, url_for, redirect, request, make_response, session
import sys
import time
from datetime import datetime
from flask_socketio import SocketIO
import os
import boto3
from botocore.client import Config
import json
from db import db_init, db_select

# Flask & socket 세팅
app = Flask(__name__)
app.config["SECRET_KEY"] = "smoker"
socketio = SocketIO(app)
# DB 초기화
db_init()
with open("./key.json") as f:
    keys = json.load(f)

# sqs 초기
SQS = boto3.client(
    "sqs",
    aws_access_key_id=keys["ACCESS_KEY_ID"],
    aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="ap-northeast-2",
)
S3 = boto3.resource(
    "s3",
    aws_access_key_id=keys["ACCESS_KEY_ID"],
    aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="ap-northeast-2",
)

BUCKET_NAME = "ai-public-bk-00950707"

# sqs 메시지 전송
def send_sqs_msg(msg):
    queue_url = "https://sqs.ap-northeast-2.amazonaws.com/792797522079/dlib_queue"
    try:
        SQS.send_message(QueueUrl=queue_url, MessageBody=msg)
    except Exception as e:
        print("메세지 전송 오류", e)


# dlib -> sqs 메시지 전송
@socketio.on("get_recidivist")
def get_recidivist():
    print("send msg")
    send_sqs_msg("click")


# Home(index) 페이지
@app.route("/")
def index():
    return render_template("index.html")


# PPT 발표용 페이지
@app.route("/ppt")
def ppt():
    return render_template("pages/ppt.html")


# # 로그인 페이지
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if db_select(username, password):
            session["username"] = username
            session["password"] = password
            print(session)
            return redirect(url_for("index"))
        else:
            return render_template("pages/login.html", error=True)
    else:
        return render_template("pages/login.html", error=False)


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("password", None)
    return render_template("pages/login.html")


@socketio.on("video_upload")
def video_upload():
    with open('./static/video/video_org.mp4', 'rb') as f :
        data = f.read()
    print("video upload ~ !!!")
    S3.Bucket(BUCKET_NAME).put_object(
        Key= "video/video_org.mp4",
        Body= data,
    )


# video 페이지
@app.route("/video")
def video():
    if session.get("username") and session.get("password"):
        return render_template("pages/video.html")
    # 아니면 다시 로그인
    else:
        return redirect(url_for("login"))


# 검출 페이지
@app.route("/recidivist")
def recidivist():
    if session.get("username") and session.get("password"):
        return render_template("pages/recidivist.html")
    # 아니면 다시 로그인
    else:
        return redirect(url_for("login"))


# 실행
# if __name__ == "__main__":
#     socketio.run(app, debug=True, port=3333)
