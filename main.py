import streamlit as st
import streamlit.components.v1 as components
import spacy
import pytextrank
from youtube_transcript_api import YouTubeTranscriptApi
from urllib import parse
import re
import numpy as np
import pytube
from pytube import YouTube
import pandas as pd
from gensim.summarization.summarizer import summarize
import datetime

def transcripts_load(url):
        url_data = parse.urlparse(url)
        query = parse.parse_qs(url_data.query)
        video_id = query["v"][0]
        try:
            transcripts = YouTubeTranscriptApi.get_transcript(video_id,languages=['en'])
        except:
            raise
        return transcripts

def transcripts_sum(transcripts):
    # Combine transcript by sentence unit
    new_transcripts = []
    temp_text = ''
    temp_start = 0
    temp_duration = 0

    for transcript in transcripts:
        if ('.'==transcript['text'][-1])|('?'==transcript['text'][-1])|('!'==transcript['text'][-1]):
            if temp_text:
                temp_text = temp_text + transcript['text'] + ' '
                temp_duration += transcript['duration']
                new_transcript = {'text':temp_text, 'start':temp_start, 'duration':temp_duration}
                new_transcripts.append(new_transcript)
                temp_text = ''
                temp_start = 0
                temp_duration = 0
            else:
                new_transcripts.append(transcript)
                temp_text = ''
                temp_start = 0
                temp_duration = 0
        else:
            temp_text = temp_text + transcript['text'] + ' '
            temp_duration += transcript['duration']
            temp_start = transcript['start']
            
    return new_transcripts

def transcripts_remove_stopwords(transcripts, stopwords):
    for transcript in transcripts:
        transcript['text'] = transcript['text'].lower()
        transcript['text'] = re.sub(r"\[([A-Za-z0-9_]+)\] ", '', transcript['text']).strip()
        transcript['text'] = re.sub(r"\[([A-Za-z0-9_]+)\]", '', transcript['text']).strip()
        transcript['text'] = re.sub(r"[\(\[].*?[\)\]]", "", transcript['text']).strip()
        transcript['text'] = transcript['text'].replace('\n', ' ').strip()
        
        for word in stopwords:
            transcript['text'] = transcript['text'].replace(word, '').strip()
            
    return transcripts

class Transcripts:
    def __init__(self, url, stopwords=['um, ', 'um,' , 'um', 'uh, ', 'uh,', 'uh', 'you know, ', 'you know,']):
        try:
            self.transcripts = transcripts_load(url)
        except:
            raise
        self.stopwords = stopwords
        
    def transcripts_preprocess(self):
        
        # Combine transcript by sentence unit
        #new_transcripts = transcripts_sum(new_transcripts)
        new_transcripts = transcripts_sum(self.transcripts)
        
        # Erase meaningless exclamations in sentences
        new_transcripts = transcripts_remove_stopwords(new_transcripts, self.stopwords)
        self.transcripts = new_transcripts
        
        
        return self.transcripts


def downloadVideo(video_url):  
    youtube = pytube.YouTube(video_url)  
    video = youtube.streams.get_highest_resolution()
    return video.download()


def textRank(text):
    nlp = spacy.load('en_core_web_md')
    
    #tr = pytextrank.TextRank()
    #nlp.add_pipe(tr.PipelineComponent, name='textrank', last=True)
    nlp.add_pipe("textrank")
    doc = nlp(text)
    
    return doc._.textrank.summary(limit_phrases=15, limit_sentences=5)
        
def textRank1(text):
    return summarize(text,ratio=0.02,split=True)

def run():

    #global c1,c2,d1,d2

    st.set_page_config(page_title="Design Project",initial_sidebar_state="expanded",layout="wide")
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.sidebar.title("Automatic Video Chapter Creator")
    st.sidebar.title("Design Project")
    st.sidebar.text("Vaibhav Singhal")
    st.sidebar.text("CED17I040")
    st.sidebar.text("Dr. B Sivaselvan")
    st.sidebar.text("Mercy Ma'am")
    
    c1,c2= st.columns((4,1))

    yt_link = c1.text_input('Enter the YouTube link') 
    c2.markdown('#')
    if(c2.button("Upload video to server and create video chapters")):
        try:
            print("c2 button pressed")
            transcripts = Transcripts(yt_link)
            video_path = downloadVideo(yt_link)
            #_,_,d1,_,_ = st.columns(5)
            #if(d1.button("Create video chapters")):
            #    print("d1 button pressed")
            print("check 1")
            processed_transcripts=transcripts.transcripts_preprocess()
            df=pd.DataFrame(processed_transcripts)
            
            transcript_text=""
            for t in processed_transcripts:
                transcript_text+=t['text']
                transcript_text+="\n"
            
            print(transcript_text[:50])

            try:
                sentences = textRank1(transcript_text)
    
                #print("open file")
                file_chapter = open("chapter.vtt", "w")
                L = ["WEBVTT \n\n"]
                
                #print(df.info())
                for s in sentences:
                    #print(s)
                    index = df.index[(df['text'] == s)].tolist()[0]
                    #print(index)
                    line=""
                    line+=str(datetime.timedelta(seconds=int(df.iloc[index]['start'])))
                    #print(line)
                    line+=" --> "
                    line+=str(datetime.timedelta(seconds=int(df.iloc[index]['start']))+datetime.timedelta(seconds=int(df.iloc[index]['duration'])))
                    #print(line)
                    line+="\n"
                    #print(line)
                    L.append(line)
                    line=s+"\n\n"
                    L.append(line)


                file_chapter.writelines(L)
                file_chapter.close()

                chapter_path="chapter.vtt"
                #print("close file")

                video_html = """
        <!DOCTYPE html>
        <html>
            <head>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js"> </script>
                <script type="text/javascript">
                    $(function() 
                    {
                        var $videoWrapper = $('.video-wrapper');
                        $videoWrapper.each(function() 
                        {
                            var $video = $(this).find('video');
                            var $transcript = $(this).find('.transcript');
                            $video.find('track[kind="chapters"]').on("load", function(evt) 
                            {
                                var $video  = $(this).closest('video');
                                var transcriptHtml = '';
                                var cues = $video[0].textTracks[0].cues;
                                for (var i=0; i<cues.length; i++) 
                                {
                                    transcriptHtml += '<li role="button" tabindex="0" class="cuepoint" data-id="'+cues[i].id+'" data-start-time="'+cues[i].startTime+'" data-end-time="'+cues[i].endTime+'">' + cues[i].text + '</li>';
                                }
                                $transcript.html(transcriptHtml);
                                var $cuepoints = $transcript.find('.cuepoint');
                                console.log('$cuepoints: ', $cuepoints);
                                $cuepoints.click(function() 
                                {
                                    var $cuepoint = $(this);
                                    var $videoWrapper = $cuepoint.closest('.video-wrapper');
                                    var $transcript = $cuepoint.closest('.transcript');
                                    var $video = $videoWrapper.find('video');
                                    var $cuepoints = $transcript.find('.cuepoint');
                                    $video[0].currentTime = $cuepoint.data('startTime');
                                    $cuepoints.each(function() {
                                        $(this).removeClass('active');
                                    });
                                    $cuepoint.addClass('active');
                                });
                            });
                        });
                    });
                </script>
                <style>
                    body
                    {
                        display: flex;
                        justify-content: center;
                    }
                    .video-wrapper {
                        font-size: 0; 
                        position: relative; 
                        margin: 0; 
                        width: 75%;
                        display: flex;
                        justify-content: center;
                    }

                    .vid {
                        width: 75%;
                        height: auto;
                    
                    }

                    .transcript-wrapper {
                        
                        background: #31333F; 
                        width: 25%; 
                        font-size: .8rem; 
                        color: #666; 
                        height: 100%; 
                        overflow-y: scroll; 
                        -moz-scrollbars-vertical;
                    }

                    .transcript{
                        position: relative;
                        list-style-type: none;
                        margin: 5px; 
                        padding: 0; 
                    }



                    .cuepoint {
                        font-family: sans-serif;
                        font-size: medium;
                        cursor: pointer;
                        color: #FAFAFA;
                        padding-left: 5px;
                        padding-top: 5px;
                        padding-bottom: 5px;
                    }

                    li.cuepoint:hover,li.cuepoint:active {
                        color: #F63366;
                    }

                    #chapter-title{
                        text-align: center;
                        color: #F63366;
                    }
                </style>
            </head>
            <body>
                <div class="video-wrapper">
                    <video class="vid" controls crossorigin="anonymous">
                        <source src='"""+video_path+"""' type="video/mp4">
                        <track id="chaptersTrack01" class="chaptersTrack" src='"""+chapter_path+"""' srclang="en" kind="chapters" default>
                            
                    </video>
                    <div class="transcript-wrapper"><h2 id="chapter-title">Chapters</h2> <div class="transcript"></div></div>
                </div>
                
                
            
            </body>
        </html>
            """
                components.html(video_html, height=800)
            
            except:
                st.error("Internal issue")

        except:
            st.error("Enter a valid youtube link which has english subtitles")
        
    

run()