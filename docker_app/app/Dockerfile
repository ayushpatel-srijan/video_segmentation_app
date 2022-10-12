FROM python:3.10

RUN apt-get update -y
RUN apt install python3-pip -y

COPY requirements.txt ./requirements.txt
COPY  app /opt/

RUN pip3 install -r requirements.txt

WORKDIR /opt/

EEXPOSE 8502
CMD ["streamlit", "run", "app.py", "--server.port=8502"]
