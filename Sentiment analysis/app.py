from flask import request, Flask, render_template
import requests
import os
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import numpy as np
# from textblob import TextBlob
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
app.app_context().push()

@app.route('/',methods=['GET'])
def Home():
    return render_template('index.html')


def final_sent_calc(spare_df):
    sentiment = SentimentIntensityAnalyzer()
    spare_df["Positive"] = [sentiment.polarity_scores(i)["pos"] for i in spare_df["text"]]
    spare_df["Negative"] = [sentiment.polarity_scores(i)["neg"] for i in spare_df["text"]]
    spare_df["Neutral"] = [sentiment.polarity_scores(i)["neu"] for i in spare_df["text"]]
    spare_df['Compound'] = [sentiment.polarity_scores(i)["compound"] for i in spare_df["text"]]
    score = spare_df["Compound"].values
    sentiment = []
    for i in score:
        if i >= 0.05 :
            sentiment.append('Positive')
        elif i <= -0.05 :
            sentiment.append('Negative')
        else:
            sentiment.append('Neutral')
    spare_df["Sentiment"] = sentiment
    final_sent = dict(spare_df["Sentiment"].value_counts())
    return final_sent
    # print(spare_df["Sentiment"].value_counts())

@app.route("/fetch_comments", methods=['POST'])
def fetch_comments():
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyBnKMjK_GlMK9ryRzRtNRgEnPKsnBhwmf0"
    comments = []
    if request.method == 'POST':
        try:
            link = request.form['url_name']
            if 'youtu.be' in link:
                v_id = link.split('youtu.be/')[-1]
            
            elif 'shorts' in link:
                v_id = link.split('shorts/')[-1].split('?')[0]
                
            else:
                v_id = link.split('?v=')[-1].split('&')[0]
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            youtube = googleapiclient.discovery.build(
                api_service_name, api_version, developerKey=DEVELOPER_KEY)

            yt_request =youtube.commentThreads().list(part="snippet", maxResults=200,  order="relevance",videoId= v_id)
            response = yt_request.execute()
       
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append([
                    comment['authorDisplayName'],
                    comment['publishedAt'],
                    comment['updatedAt'],
                    comment['likeCount'],
                    comment['textDisplay']
                ])
                    # Break the loop if there are no more pages
            df = pd.DataFrame(comments, columns=['author', 'published_at', 'updated_at', 'like_count', 'text'])
            spare_df = df.copy()
            final_sent = final_sent_calc(spare_df)
            return render_template('index.html',prediction_text=f"For top 100 relevant comments, <br> positive comments - {final_sent['Positive']},</br>  <br> negative comments - {final_sent['Negative']}, </br> <br>neutral comments - {final_sent['Neutral']}</br>")
        except:
            return render_template('index.html',prediction_text=f"Comments are Disabled or no comments found.")
    else:
        print('NO ENTRY')
        return render_template('index.html')

if __name__=="__main__":
    app.run()