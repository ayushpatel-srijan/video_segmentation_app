FROM python:3.10

RUN apt-get update -y
RUN apt install python3-pip -y

COPY requirements.txt ./requirements.txt
COPY  app /opt/

RUN pip3 install -r requirements.txt

WORKDIR /opt/

ENTRYPOINT [ "streamlit", "run" ]
CMD ["app.py"]
