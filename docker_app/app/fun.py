from genericpath import exists
import moviepy.editor as mp
import requests
import os
import pickle
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import re 
import shutil
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import yake

checkpoint = "philschmid/distilbart-cnn-12-6-samsum"
tokenizer_samsum = AutoTokenizer.from_pretrained(checkpoint)
model_samsum = AutoModelForSeq2SeqLM.from_pretrained(checkpoint)


#KEY = "00469c8069664c64a1a4e391f36d34fe"
KEY = os.environ.get("ASSEMBLY_API_KEY", f'default_value')

def extract_with_yake(doc):
    print("Extracting with Yake")
    kw_extractor = yake.KeywordExtractor(top=15, stopwords=None)
    keywords = kw_extractor.extract_keywords(doc)
    #print(keywords[-2:])
    return keywords[0][0]

@st.cache
def add_phrases(chaps,phs):
    temp=[]
    for i in range(len(chaps)):
        for j in range(len(phs)):
            if ((phs[j][0]<chaps[i][1] and phs[j][0]>chaps[i][0]) or (phs[j][1]<chaps[i][1] and phs[j][1]>chaps[i][0])):
                #print(chaps[i][0],chaps[i][1],phs[j][0],phs[j][1])
                temp.append(phs[j][2])
        chaps[i].extend([temp])
        temp=[]
        print("[INFO] Phrases Added")
    return chaps

def abstractive_model_output(model  , tokenizer, chunks):
    print("[Processing] Summarizing text")
    input = tokenizer(chunks, return_tensors = "pt")
    output_list = []
    output_ = ''
    output = model.generate(**input, min_length = int(len(chunks)*0.1), max_length = int(len(chunks)*0.2), early_stopping = False)
    output_list.append(tokenizer.decode(*output, skip_special_tokens=True))
    output_ = ' '.join(output_list)
    return output_

pretty =lambda x:' '.join(re.findall('[A-Z][^A-Z]*', x))
extract_imp_phrases  = lambda d :[[d['results'][i]['timestamps'][0]['start'],d['results'][i]['timestamps'][0]['end'],d['results'][i]['text']] for i in range(len(d['results']))]

def save_phrases(filename,chapters):
    if not os.path.exists("phrases"):
        os.mkdir("phrases")
    with open(os.path.join("phrases",f"{filename[:-4]}_phrases.pkl"),'wb') as f:
        pickle.dump(chapters,f)

def get_phrases(filename):
    with open(os.path.join("phrases",f"{filename[:-4]}_phrases.pkl"), 'rb') as f:
        data = pickle.load(f)
    return data
     
def group(chaps):
    new_chaps=[]
    f=0
    sum=""

    for i in range(0,len(chaps)):
        s=chaps[f][0]
        e=chaps[i][1]
        if i!= len(chaps)-1 and chaps[i][2]==chaps[i+1][2]:
            e=chaps[i+1][1]
            sum=sum +" "+chaps[i][3]
            continue
        else:
            f=i+1
            #new_chaps.append([s,e,chaps[i][2],abstractive_model_output(model_samsum, tokenizer_samsum,chunks=sum+" "+str(chaps[i][3]))])
            new_chaps.append([s,e,chaps[i][2],sum+" "+str(chaps[i][3])])
            sum=""
    return new_chaps

@st.cache
def split_video(filename,data):
    print("[INFO] Splitting Video")
    vid_list=[]
    folder_name=filename[:-4]
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    if not os.path.exists("splitted_videos"):
        os.mkdir("splitted_videos")
    folder_name=os.path.join("splitted_videos",folder_name)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    print(data)
    for ind, i in enumerate(data):
        print("-->",os.path.join(folder_name,f"{ind}.mp4"))
        print("-->",f"{folder_name}\{ind}.mp4")
        video_name = pretty(i[2].split('>')[-1])
        print(convert(i[0]/1000), convert(i[1]/1000),video_name)
        ffmpeg_extract_subclip(os.path.join("videos",filename), 
                            i[0]//1000, 
                            i[1]//1000,
                            targetname=f"{folder_name}/{ind}.mp4")
        vid_list.append([ind,f"{folder_name}/{ind}.mp4"])
    print("[INFO] Video Splitted")
    return vid_list

def PlayAudioSegment(filepath, start, end,ind,folder_name):
    out=os.path.join(folder_name,f"{filepath[:-4]}_{ind}.mp3")
    audio_path = filepath
    sound = AudioSegment.from_mp3(filepath)
    spliced_audio = sound[start : end]
    spliced_audio.export(out, format="mp3")
    display(ipd.Audio(out))

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)

def read_file(filename):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read()
            if not data:
                break
            yield data
            
def local2url(filename):
    key =  KEY# your auth key
    headers = {'authorization': key}
    response = requests.post('https://api.assemblyai.com/v2/upload',
                            headers=headers,
                            data=read_file(filename))

    return response.json()['upload_url']

def post_response(upload_url):
    key=KEY
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json = { "audio_url": upload_url,
            "auto_chapters": True,
            "iab_categories": True,
            "auto_highlights": True
               }
    headers = {
        "authorization": key,
        "content-type": "application/json"
    }
    response = requests.post(endpoint, json=json, headers=headers)
    return response

def get_response(response):
    key=KEY
    endpoint = "https://api.assemblyai.com/v2/transcript/"+ response.json()['id']
    headers = {
        "authorization": key,
    }
    i='queued'
    #if loop doesn't work check response.json()['status'] 
    while i!='completed':
        response = requests.get(endpoint, headers=headers)
        i=response.json()['status']
    return response

def save_chapters(filename,chapters):
    if not os.path.exists("chapters"):
        os.mkdir("chapters")
    with open(os.path.join("chapters",f"{filename[:-4]}_chapters.pkl"),'wb') as f:
        pickle.dump(chapters,f)
        
def get_chapters(filename):
    with open(os.path.join("chapters",f"{filename[:-4]}_chapters.pkl"), 'rb') as f:
        data = pickle.load(f)
    return data

def save_video_summary(filename,video_summary):
    if not os.path.exists("Video summary"):
        os.mkdir("Video summary")
    with open(os.path.join("Video summary",f"{filename[:-4]}_video_summary.pkl"),'wb') as f:
        pickle.dump(video_summary,f)
        
def get_video_summary(filename):
    with open(os.path.join("Video summary",f"{filename[:-4]}_video_summary.pkl"), 'rb') as f:
        data = pickle.load(f)
    return data

def video2audio(filename):
    print("[INFO] Converting video to audio")
    audio_name=filename[:-1]+'3'
    my_clip = mp.VideoFileClip(os.path.join("videos",filename))
    if not os.path.exists("audios"):
        os.mkdir("audios")
    audio_path = os.path.join("audios",audio_name)
    my_clip.audio.write_audiofile(audio_path)
    return audio_path

def extract_chapters(filename):
    audio_path = video2audio(filename)
    upload_url=local2url(audio_path)
    print("[INFO] File uploaded")
    post_reponse = post_response(upload_url)
    print("[INFO] Post request sent")
    response = get_response(post_reponse)
    print("[INFO] Response received")
    topics= response.json()['iab_categories_result']
    imp_words= response.json()['auto_highlights_result']
    video_summary=response.json()['chapters']
    phrases = extract_imp_phrases(imp_words)
    chapters=[]
    for ind ,i in enumerate(topics['results']):
        folder_name = filename[:-4]
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        start = i['timestamp']['start']# in seconds
        end =i['timestamp']['end'] # in seconds
        print("Start:" ,convert(round(i['timestamp']['start']/1000)) ,"-","End:",convert(i['timestamp']['end']/1000),":- ",i['labels'][0]['label'])
        chapters.append([start,end ,i['labels'][0]['label'],abstractive_model_output(model_samsum ,tokenizer_samsum,i['text'])])
    save_chapters(filename,chapters)
    save_phrases(filename,phrases)
    save_video_summary(filename,video_summary)

    print("[INFO] Chapters Extracted")

    return response
    
