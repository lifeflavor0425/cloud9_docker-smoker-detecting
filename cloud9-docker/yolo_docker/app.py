from ultralytics import YOLO
import boto3
import time
import json
from botocore.client import Config

import numpy as np
from urllib import request
import os

MODEL_CIGA = None
MODEL_SMOKE = None
MODEL_PERSON = None
BUCKET_NAME = "ai-public-bk-00950707"
CLOUD_FLONT_CDN = "https://d2nh0kpre7014e.cloudfront.net"

S3 = None
SQS = None

# 모델 로딩
def get_model():
    global MODEL_CIGA, MODEL_SMOKE, MODEL_PERSON

    if not os.path.exists("./ciga.pt"):
        request.urlretrieve(CLOUD_FLONT_CDN + "/models/ciga_v8s.pt", "./ciga.pt")
    if not os.path.exists("./smoke.pt"):
        request.urlretrieve(CLOUD_FLONT_CDN + "/models/maybe_n_smoke_best.pt", "./smoke.pt")
    if not os.path.exists("./person.pt"):
        request.urlretrieve(CLOUD_FLONT_CDN + "/models/person_v8s.pt", "./person.pt")

    MODEL_CIGA = YOLO("./ciga.pt")
    MODEL_SMOKE = YOLO("./smoke.pt")
    MODEL_PERSON = YOLO("./person.pt")


# 초기화
def init():
    global S3, SQS
    get_model()
    
    with open('./key.json') as f:
        keys = json.load(f)
    S3 = boto3.resource(
        "s3", 
        aws_access_key_id=keys["ACCESS_KEY_ID"],
        aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="ap-northeast-2",
        )
    SQS = boto3.client(
        "sqs", 
        aws_access_key_id=keys["ACCESS_KEY_ID"],
        aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="ap-northeast-2",
        )


# s3 업로드
def upload(detected_imgs, shape_arr):
    for idx, (img, shape) in enumerate(zip(detected_imgs, shape_arr)):
        S3.Bucket(BUCKET_NAME).put_object(
            Key=f"yolo_detected/{shape}_{idx}".replace(" ", "-"),
            Body=img,
        )


# 예측
def predict(url):
    ciga_img_arr = list()
    smoke_img_arr = list()
    person_img_arr = list()
    shape_arr = list()
    # 담배 모델 예측
    results_ciga = MODEL_CIGA.predict(url)
    for result_ciga in results_ciga:
        if not result_ciga.boxes.numpy():
            continue
        if result_ciga.boxes.data.numpy()[0][-2] < 0.2:
            continue

        ciga_img_arr.append(result_ciga.orig_img)

    # 연기 모델 예측
    for ciga_img in ciga_img_arr:
        results_smoke = MODEL_SMOKE.predict(ciga_img)[0]
        if not results_smoke.boxes.numpy():
            continue
        if results_smoke.boxes.data.numpy()[0][-2] < 0.2:
            continue
        smoke_img_arr.append(results_smoke.orig_img)

    # 사람 모델 예측
    for smoke_img in smoke_img_arr:
        results_person = MODEL_PERSON.predict(smoke_img)[0]
        if not results_person.boxes.numpy():
            continue
        if results_person.boxes.data.numpy()[0][-2] < 0.5:
            continue
        shape_arr.append(results_person.orig_img.shape)  # 예측된 이미지 형태 보관
        img_byte = results_person.orig_img.tobytes()  # 이미지 -> 바이너리 변환
        person_img_arr.append(img_byte)

    print(len(ciga_img_arr), len(smoke_img_arr), len(person_img_arr))
    # 업로드
    upload(person_img_arr, shape_arr)
    del ciga_img_arr
    del smoke_img_arr
    del person_img_arr
    del shape_arr


# sqs 메시지 체크
def sqs_message_check():
    # 대기열 큐를 특정 주기로 체크, 모니터링
    q_name = "yolo_test_queue"
    res = SQS.receive_message(
        QueueUrl=q_name,
        AttributeNames=["SentTimestamp"],
        MessageAttributeNames=["All"],
        MaxNumberOfMessages=1,
        VisibilityTimeout=0,
        WaitTimeSeconds=0,
    )
    if res and ("Messages" in res):
        # 수신한 값을 기준 => 메시지가 존재하는 여부 체크 -> 메시지 삭제(큐에서) -> 예측 처리 요청 처리
        receipt_handle = res["Messages"][0]["ReceiptHandle"]  # 메시지 고유값
        # cmd = json.loads(res["Messages"][0]["Body"])["cmd"]
        key = json.loads(res["Messages"][0]["Body"])["key"]
        SQS.delete_message(
            QueueUrl=q_name,
            ReceiptHandle=receipt_handle,
        )
        return key
    else:
        print("No message")
        return 0


def main():
    # 모델 및 aws 초기화
    init()
    # sqs 메시지 확인
    while True:
        key = sqs_message_check()
        time.sleep(5)
        if key:
            # 모델 예측
            predict(CLOUD_FLONT_CDN + f"/{key}")


if __name__ == "__main__":
    main()
