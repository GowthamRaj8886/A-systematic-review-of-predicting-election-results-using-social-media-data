from django.shortcuts import render, redirect
from django.db.models import Count, Avg, Q
from django.http import HttpResponse
import xlwt
import pandas as pd
import os

from nltk import bigrams
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter

# Machine Learning Imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

from Remote_User.models import (
    ClientRegister_Model,
    Election_model,
    Election_prediction_model,
    detection_ratio_model
)

# ---------------- SERVICE PROVIDER LOGIN ---------------- #

def serviceproviderlogin(request):
    if request.method == "POST":
        admin = request.POST.get('username')
        password = request.POST.get('password')

        if admin == "Admin" and password == "Admin":
            return redirect('View_Remote_Users')
        else:
            return render(
                request,
                'SProvider/serviceproviderlogin.html',
                {'error': 'Invalid credentials'}
            )

    return render(request, 'SProvider/serviceproviderlogin.html')




# ---------------- VIEW REMOTE USERS ---------------- #

def View_Remote_Users(request):
    obj = ClientRegister_Model.objects.all()
    return render(request, 'SProvider/View_Remote_Users.html', {'objects': obj})


# ---------------- TRENDING TOPICS ---------------- #

def ViewTrendings(request):
    topic = Election_prediction_model.objects.values(
        'prediction'
    ).annotate(dcount=Count('prediction')).order_by('-dcount')

    return render(request, 'SProvider/ViewTrendings.html', {'objects': topic})


# ---------------- CHARTS ---------------- #

def charts(request, chart_type):
    chart1 = detection_ratio_model.objects.values(
        'names'
    ).annotate(dcount=Avg('ratio'))

    return render(request, "SProvider/charts.html", {
        'form': chart1,
        'chart_type': chart_type
    })


def charts1(request, chart_type):
    chart1 = detection_ratio_model.objects.values(
        'names'
    ).annotate(dcount=Avg('ratio'))

    return render(request, "SProvider/charts1.html", {
        'form': chart1,
        'chart_type': chart_type
    })


def likeschart(request, like_chart):
    charts = detection_ratio_model.objects.values(
        'names'
    ).annotate(dcount=Avg('ratio'))

    return render(request, "SProvider/likeschart.html", {
        'form': charts,
        'like_chart': like_chart
    })


# ---------------- PREDICTION RESULT ---------------- #

def View_Election_Tweet_Predicted_Type(request):
    obj = Election_prediction_model.objects.all()
    return render(
        request,
        'SProvider/View_Election_Tweet_Predicted_Type.html',
        {'list_objects': obj}
    )


# ---------------- DOWNLOAD EXCEL ---------------- #

def Download_Trained_DataSets(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Election_Predictions_Results.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Predictions")

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    headers = ['Tweeter', 'Total Tweet Time', 'Tweet', 'Prediction']
    for col, header in enumerate(headers):
        ws.write(0, col, header, font_style)

    row = 1
    for obj in Election_prediction_model.objects.all():
        ws.write(row, 0, obj.tweeter)
        ws.write(row, 1, obj.total_tweet_Time)
        ws.write(row, 2, obj.tweet)
        ws.write(row, 3, obj.prediction)
        row += 1

    wb.save(response)
    return response


# ---------------- TRAIN MODEL ---------------- #

def train_model(request):
    detection_ratio_model.objects.all().delete()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(BASE_DIR, 'US_election_2020_Tweets.csv')

    df = pd.read_csv(csv_path)

    # Simple logic for rendering legacy sentiment scores (Optional but kept for compatibility)
    df_CW = df[df.Tweeted_about == 'Chris Wallace']
    df_JB = df[df.Tweeted_about == 'Vice President Joe Biden']
    df_DT = df[df.Tweeted_about == 'President Donald J. Trump']

    text_CW = " ".join(df_CW.text.astype(str))
    text_JB = " ".join(df_JB.text.astype(str))
    text_DT = " ".join(df_DT.text.astype(str))

    sia = SentimentIntensityAnalyzer()

    sent_CW = sia.polarity_scores(text_CW)
    sent_DT = sia.polarity_scores(text_DT)
    sent_JB = sia.polarity_scores(text_JB)

    Election_prediction_model.objects.all().delete()

    # Step 1: Assign initial labels using VADER and save to DB
    all_tweets = Election_model.objects.all()
    tweets_list = []
    labels_list = []

    for t in all_tweets:
        sentiment = sia.polarity_scores(t.tweet)['compound']
        if sentiment >= 0.05:
            result = "Positive"
        elif sentiment <= -0.05:
            result = "Negative"
        else:
            result = "Neutral"

        tweets_list.append(t.tweet)
        labels_list.append(result)

        Election_prediction_model.objects.create(
            tweeter=t.tweeter,
            total_tweet_Time=t.total_tweet_Time,
            tweet=t.tweet,
            prediction=result
        )

    # Step 2: Machine Learning Preprocessing
    if len(tweets_list) > 10: # Ensure we have enough data to train
        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        X = vectorizer.fit_transform(tweets_list)
        y = labels_list

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Step 3: Define Models
        models = {
            'Naive Bayes': MultinomialNB(),
            'Logistic Regression': LogisticRegression(max_iter=1000),
            'SVM': SVC(kernel='linear'),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'KNN': KNeighborsClassifier(n_neighbors=5)
        }

        # Step 4: Train, evaluate, and save accuracies to DB
        for name, model in models.items():
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            acc = accuracy_score(y_test, predictions) * 100
            # Store accuracy in the ratio model instead of sentiment ratios
            detection_ratio_model.objects.create(names=name, ratio=round(acc, 2))
    else:
        # Fallback if no tweets
        for name in ['Naive Bayes', 'Logistic Regression', 'SVM', 'Decision Tree', 'Random Forest', 'KNN']:
            detection_ratio_model.objects.create(names=name, ratio=0)

    obj = detection_ratio_model.objects.all()

    return render(request, 'SProvider/train_model.html', {
        'objs': obj,
        'CW': sent_CW,
        'DT': sent_DT,
        'JB': sent_JB
    })
