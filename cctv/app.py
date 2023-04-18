import cv2
import boto3
from botocore.client import Config
import time
from datetime import datetime
import sys
import json
import os

capture = None
S3 = None
BUCKET_NAME = "ai-public-bk-00950707"

# 웹 캠 초기화
def init():
    capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    time.sleep(2)
    if not capture.isOpened():
        sys.exit("카메라 연결 오류")

    return capture


# 웹캠 활성화, 및 녹화 --> 10초
def cctv_main():
    capture = init()
    video = None
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    # 시작 지점
    start = datetime.now().timestamp()
    # 오늘 날짜 반환
    today = str(datetime.now().strftime("%d_%H-%M-%S")).split("_")[0]

    while True:
        res, frame = capture.read()
        end = datetime.now().timestamp()
        # 현재 seconds
        now = int(end) - int(start)
        if not res:
            sys.exit("프레임 정보 획득 오류, 여기서는 종료처리")
        # 녹화 시작
        if now < 1:
            video = cv2.VideoWriter(
                "./video/" + today + ".mp4", fourcc, 20.0, (frame.shape[1], frame.shape[0])
            )
        else:
            if video:
                # 각 프레임 녹화에 저장
                video.write(frame)
            # 10 초후 종료
            if now == 10:
                break

    capture.release()
    cv2.destroyAllWindows()
    return today


# S3 초기화
def s3_init():
    global S3
    with open("./key.json") as f:
        keys = json.load(f)
    S3 = boto3.resource(
        "s3",
        aws_access_key_id=keys["ACCESS_KEY_ID"],
        aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="ap-northeast-2",
    )


# 비디오 업로드
def upload_video(today):
    print("upload !!!")
    with open(f"./video/{today}.mp4", "rb") as f:
        data = f.read()
    S3.Bucket(BUCKET_NAME).put_object(
        Key=f"video/{today}.mp4",
        Body=data,
    )


# video 폴더 비우기
def remove_video(today):
    print("remove !!")
    os.remove(f"./video/{today}.mp4")


# 전체 실행
def main():
    today = cctv_main()
    s3_init()
    upload_video(today)
    remove_video(today)


main()
