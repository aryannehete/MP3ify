from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
from youtubesearchpython import VideosSearch
import youtube_dl
import os
import zipfile
import re

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template("site.html")

newFolder=""
path = "C:/Users/nehet/Desktop/desktop/CS/" #EDIT THIS VARIABLE FOR YOUR OWN SYSTEM

@app.route("/result", methods = ['POST', "GET"])
def result():
    output = request.form.to_dict()
    link = output['link']

    def zip_directory(folder_path, zip_path):
        #zip da folder
        with zipfile.ZipFile(zip_path, mode='w') as zipf:
            len_dir_path = len(folder_path)
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path[len_dir_path:])

    def findTitle(songLink):
        #webscrape
        src = requests.get(songLink).content
        soup = BeautifulSoup(src, 'lxml')
        title = soup.find('title').text
        title = str(title)

        #format the title correctly
        titleContent = title.split()
        titleF = []
        append = True
        for i in range(len(titleContent)):
            if titleContent[i] == '-': append = False
            if titleContent[i] == '|': break
            if append: titleF.append(titleContent[i])
            if titleContent[i] == 'by': append = True
        
        return titleF

    def findSongLink(songTitle):
        #get first result when song is searched on youtube
        videosSearch = VideosSearch(" ".join(songTitle)+" audio", limit = 1)
        return videosSearch.result()['result'][0]['link']

    def download(songUrl, songTitle, playlistTitle):
        
        #download youtube video as mp3
        options = {'format':'bestaudio/best', 
                'keepvideo':False, 
                'outtmpl':path + playlistTitle + '/' + " ".join(songTitle)+".mp3"}
                
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([songUrl])

    matched = re.match(r"https://open.spotify.com/playlist/[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]\?si=[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]", link)
    if not bool(matched):
        return render_template("site.html", error=True)

    #webscrape
    url = link
    playlistPage = requests.get(url)
    src = playlistPage.content
    playlistSoup = BeautifulSoup(src, 'lxml')
    meta = playlistSoup.find_all('meta')

    #get title of playlsit
    title = playlistSoup.find("title").text
    title = str(title)
    playlistTitle = " ".join(i for i in title.split() if i != '|' and i != "Spotify")

    #get links of all songs in playlsit
    songLinks = []
    for info in meta:    
        try: 
            if info.attrs['property'] == "music:song": 
                songLinks.append(str(info.attrs['content']))
        except: 
            pass

    #get title of each song and download it
    for link in songLinks:
        title = findTitle(link)
        try: 
            download(findSongLink(title), title, playlistTitle)
        except:
            print("An error occured with " + " ".join(title))
            pass
    
    #zip folder
    global newFolder
    newFolder = playlistTitle+".zip"
    zip_directory(path + playlistTitle, path+newFolder)

    #return dat
    return render_template("site.html", link=link, folder=newFolder)

@app.route('/download', methods = ['POST', "GET"])
def downloadFile():
    path2 = path + newFolder
    return send_file(path2, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)