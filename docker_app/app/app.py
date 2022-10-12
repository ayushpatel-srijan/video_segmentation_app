from unicodedata import name
import streamlit as st
import os
from fun import get_chapters, group,pretty , convert ,split_video,abstractive_model_output,extract_chapters,add_phrases,get_phrases,extract_with_yake
import pickle
import shutil

from nltk.tokenize import word_tokenize, sent_tokenize
import nltk   
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'><u>Video Segmentation</u></h1>", unsafe_allow_html=True)


def show_vid(i):

    if len(vid_list) !=0:
        vid_path=vid_list[i][1]
    j=i

vf=""
chaps=[]
vid_path=""
show =False
f=1
col1, col2 ,col3 = st.columns((2,1,2))
j=-1
label=""
vid_list=None

with col1:
    st.header("Video")
    video_file = st.file_uploader('video', type = ['mp4'])
    if video_file:
      
        st.success('Done!')
        if not os.path.exists("videos"):
            os.mkdir("videos")
        with open(os.path.join("videos",f"{video_file.name}"),"wb") as f:
            f.write(video_file.getbuffer())         
            st.success("Saved File")

        if not os.path.exists(os.path.join("chapters",f'{video_file.name[:-4]}_chapters.pkl')):
            extract_chapters(video_file.name)
        old_chaps=group(get_chapters(video_file.name))
        
        if os.path.exists(os.path.join("phrases",f'{video_file.name[:-4]}_phrases.pkl')):
            phrases = get_phrases(video_file.name)
            chaps=add_phrases(old_chaps , phrases)
    
        vid_list =split_video(video_file.name,chaps)
        st.video(video_file)
        vf=video_file.name[:-4]
        #show = st.button("Show Chapters")


with col2:
    st.header("Chapters")
    for i in range(len(chaps)):
        v = st.button(on_click = show_vid(i),
                key=i,
                label=f"{pretty(chaps[i][2].split('>')[-1])} ➤")
        if v:
            j=i
            topic_full=chaps[i][2].split('>')
            label = " - ".join([pretty(i) for i in topic_full])
            if len(vid_list)!=0:
                    vid_path=vid_list[i][1]


with col3:
    if vid_path!="":
        st.header(label)
        print("-->",vid_path)
        st.video(vid_path)
        st.header(str("Summary ("+convert(chaps[j][0]/1000)+" - "+convert(chaps[j][1]/1000)+")"))
        if len(chaps[j][4])!=0 :
            phrase = " , ".join([i for i in sorted(chaps[j][4], key=len)[-2:]])
        else:
            phrase=extract_with_yake(chaps[j][3])
        
        st.subheader(f"Related to : {phrase.title()}")
        sentences = nltk.sent_tokenize(chaps[j][3])
        #for ind ,points in enumerate(chaps[j][3].split(".")[:-1]):
        for ind ,points in enumerate(sentences):
            st.markdown(str(str(ind+1) +". "+points))

        


        





        