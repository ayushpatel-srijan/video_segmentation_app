FROM python:3.10

RUN apt-get update -y
RUN apt install python3-pip -y

COPY requirements.txt ./requirements.txt
COPY  app app

RUN pip3 install -r requirements.txt
RUN python3 -m nltk.downloader punkt
WORKDIR app

EXPOSE 8502
CMD ["streamlit", "run", "app.py", "--server.port=8502"]
