# syntax=docker/dockerfile:1.4
# 베이스 이미지
# --platform=$BUILDPLATFORM : 필요한 경우 대상 플랫폼을 표시하는 옵션
# 알파인 리눅스
# -> 가볍고 간단한, 보안성 목적으로 개발한 리눅스 배포판
# builder는 여러 옵션으로 기술된 베이스 이미지의 별칭 or 스테이지(단계)
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

# 작업 디렉토리 지정, 없음녀 생성한다.
WORKDIR /was_app


COPY requirements.txt /was_app
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -r requirements.txt
COPY . /was_app

# 환경변수, 앱의 이름은 flask run 명령시 자동 인식이므로 생략
ENV FLASK_RUN_PORT 8000
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_APP app.py
ENV FLASK_ENV development

# 포트 설정
EXPOSE 8000

# 구동 명령
ENTRYPOINT [ "flask" ]
# 옵션
CMD [ "run" ]


# builder를 기반으로 추가 기술
# 리눅스 관련 작업
# 패키지 업데이트, 계정 추가, 권한 부여 등등

FROM builder AS flask-env

# os 상 작업 추가(실습상 추가)
# 여러줄 명령 수행을 위해서 EOF 옵션 사용
# 알파인 리눅스의 패키지 관리자 => apk
# 더미 작업
RUN <<EOF
apk update
apk add git
EOF

# 앞스테이지 실행 명령 동일하게 기술
CMD ["flask", "run"]