FROM python:3.10

RUN apt-get update -y
RUN apt install python3-pip -y

COPY requirements.txt ./requirements.txt
COPY  app /opt/

RUN pip3 install -r requirements.txt
RUN pip3 install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.5/en_core_web_sm-2.2.5.tar.gz --user
RUN python3 -m nltk.downloader punkt
WORKDIR /opt/

EXPOSE 8502
CMD ["streamlit", "run", "app.py", "--server.port=8502"]
