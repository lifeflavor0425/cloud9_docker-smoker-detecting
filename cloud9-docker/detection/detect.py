# 모듈
import dlib
from glob import glob
import numpy as np
import matplotlib.pyplot as plt
import boto3
from botocore.client import Config
import json
from urllib import request
from PIL import Image
from botocore.exceptions import ClientError
from urllib.error import HTTPError, URLError
import os
import time

detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor("shape_predictor_5_face_landmarks.dat")
facerec = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")


def plotPairs(img1, img2):
    fig = plt.figure()

    ax1 = fig.add_subplot(1, 2, 1)
    plt.imshow(img1)
    plt.axis("off")

    ax1 = fig.add_subplot(1, 2, 2)
    plt.imshow(img2)
    plt.axis("off")

    # plt.savefig('./test.jpg')


threshold = (
    0.5  # distance threshold declared in dlib docs for 99.38% confidence score on LFW data set
)


def findEuclideanDistance(source_representation, test_representation):
    euclidean_distance = source_representation - test_representation
    euclidean_distance = np.sum(np.multiply(euclidean_distance, euclidean_distance))
    euclidean_distance = np.sqrt(euclidean_distance)
    return euclidean_distance


def verify(img1_path, img2_path):
    img1 = dlib.load_rgb_image(img1_path)
    img2 = dlib.load_rgb_image(img2_path)

    """
    print("Raw images: ")
    plotPairs(img1, img2)
    """

    # ------------------------------------
    # face detection and alignment

    img1_detection = detector(img1, 1)
    img2_detection = detector(img2, 1)

    if len(img1_detection) == 0:
        return 0

    if len(img2_detection) == 0:
        return 0

    img1_shape = sp(img1, img1_detection[0])
    img2_shape = sp(img2, img2_detection[0])

    img1_aligned = dlib.get_face_chip(img1, img1_shape)
    img2_aligned = dlib.get_face_chip(img2, img2_shape)

    img1_representation = facerec.compute_face_descriptor(img1_aligned)
    img2_representation = facerec.compute_face_descriptor(img2_aligned)

    img1_representation = np.array(img1_representation)
    img2_representation = np.array(img2_representation)

    # -----------------------------------
    # verification

    distance = findEuclideanDistance(img1_representation, img2_representation)

    # print("Distance is ", distance," whereas threshold is ", threshold)

    if distance < threshold:
        print(img1_path, " and ", img2_path, " are same person")
        verified = True
        plotPairs(img1_aligned, img2_aligned)
    else:
        verified = False

    return verified


# TODO s3 에서 이미지 다운로드 추가
# 아마존 생태계 바깥쪽에서 아마존 access 처리 사용할 코드
# with open("./key.json") as f:
#     keys = json.load(f)
CLOUD_FLONT_CDN = "https://d2nh0kpre7014e.cloudfront.net"
# s3 서비스 객체 생성
bk = "ai-public-bk-00950707"
with open('./key.json') as f:
    keys = json.load(f)

s3 = boto3.resource(
    "s3", 
    aws_access_key_id=keys["ACCESS_KEY_ID"],
    aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="ap-northeast-2",
    )
s3_client = boto3.client(
    "s3", 
    aws_access_key_id=keys["ACCESS_KEY_ID"],
    aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="ap-northeast-2",
    )
sqs = boto3.client(
    "sqs", 
    aws_access_key_id=keys["ACCESS_KEY_ID"],
    aws_secret_access_key=keys["ACCESS_SECRET_KEY"],
    config=Config(signature_version="s3v4"),
    region_name="ap-northeast-2",
    )


def decodeImage(data, shape):
    # Gives us 1d array
    decoded = np.frombuffer(data, dtype=np.uint8)
    # We have to convert it into (270, 480,3) in order to see as an image
    decoded = decoded.reshape(shape)
    return decoded


def dataset_img(bk):
    i = 0
    while True:
        try:
            s3_client.download_file(bk, f"dataset_img/{i}.jpg", f"dataset_img/dataset_{i}.jpg")
            i += 1
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                break
            else:
                print("An error occurred while downloading the dataset. Please try again later.")
                break
    dataset_img_list = glob("dataset_img/*.jpg")
    return dataset_img_list


def detecting_img():
    # SQS : 메시지 획득 -> key 획득 -> 예측수행
    # s3_client.download_file(bk, 'detecting_img/', 'detecting_img')
    i = 0
    while True:
        try:
            req = request.Request(
                CLOUD_FLONT_CDN + f"/yolo_detected/(720,-1280,-3)_{i}", headers={"orgin": "*"}
            )
            frame = request.urlopen(req).read()
            tmp_sqs = f"/yolo_detected/(720,-1280,-3)_{i}"
            shape_str = tmp_sqs.split("(")[-1].split(")")[0].replace("-", " ")
            shape = tuple(map(int, shape_str.split(", ")))
            de = decodeImage(frame, shape)
            img = Image.fromarray(de)
            img.save(f"./detecting_img/detecting_{i}.jpg")
            i += 1
        except HTTPError as e:
            break
        except URLError as e:
            break
        except Exception as e:
            break

    detecting_img_list = glob("detecting_img/*.jpg")
    return detecting_img_list


def upload(bk, key):
    with open(key, "rb") as f:
        img = f.read()
    # 업로드 -> 버킷 선택
    s3.Bucket(bk).put_object(Key=key, Body=img)


def determine(bk):
    dataset_img_list = dataset_img(bk)
    detecting_img_list = detecting_img()
    for i in range(len(dataset_img_list)):
        for j in range(len(detecting_img_list)):
            verified = verify(detecting_img_list[j], dataset_img_list[i])
            if verified:
                key = f"success/detection{i}.jpg"
                if not os.path.exists(key):
                    plt.savefig(key)
                    # TODO s3 에 이미지 업로드 추가
                    upload(bk, key)
                else:
                    break


def remove():
    os.system("rm -r dataset_img/*.jpg")
    os.system("rm -r detecting_img/*.jpg")
    os.system("rm -r success/*.jpg")


def sqs_message_check():
    # 대기열 큐를 특정 주기로 체크, 모니터링
    q_name = "dlib_queue"
    res = sqs.receive_message(
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
        msg = res["Messages"][0]["Body"]
        sqs.delete_message(
            QueueUrl=q_name,
            ReceiptHandle=receipt_handle,
        )
        return msg
    else:
        print("No message")
        return 0


if __name__ == "__main__":
    while True:
        msg = sqs_message_check()
        time.sleep(5)
        if msg:
            print("start !!")
            determine(bk)
            time.sleep(5)
            print("end !!")
            remove()
