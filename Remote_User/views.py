from django.db.models import Count
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
import datetime
import openpyxl
import pandas as pd

# Create your views here.
from Remote_User.models import ClientRegister_Model,Election_model,Election_prediction_model,detection_ratio_model

def login(request):


    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            enter = ClientRegister_Model.objects.get(username=username, password=password)
            request.session["userid"] = enter.id

            return redirect('Add_DataSet_Details')
        except Exception as e:
            print(f"Login failed: {e}")
            pass
    
    return render(request, 'RUser/login.html')

def Add_DataSet_Details(request):
    if "GET" == request.method:
        return render(request, 'RUser/Add_DataSet_Details.html', {})
    else:
        try:
            excel_file = request.FILES["excel_file"]
            file_name = excel_file.name.lower()
            excel_data = list()
            
            # Clear existing data BEFORE the loop
            Election_model.objects.all().delete()
            
            if file_name.endswith('.csv'):
                # Read CSV file
                # Use io.StringIO or bytes to read uploaded file
                df = pd.read_csv(excel_file)
                # Ensure we handle NaN values
                df = df.fillna('')
                
                # Assuming standard column order: tweeter, total_tweet_Time, tweet
                # Or check by column names if possible. For now, assuming index based.
                for index, row in df.iterrows():
                    tweeter = str(row.iloc[0])
                    total_tweet_Time = str(row.iloc[1])
                    tweet = str(row.iloc[2])
                    
                    if tweeter or tweet:
                        Election_model.objects.create(
                            tweeter=tweeter,
                            total_tweet_Time=total_tweet_Time,
                            tweet=tweet
                        )
                        row_data = [tweeter, total_tweet_Time, tweet]
                        excel_data.append(row_data)

            elif file_name.endswith('.xlsx'):
                # Handle Excel file
                wb = openpyxl.load_workbook(excel_file)
                active_sheet = wb.active
                
                for row in active_sheet.iter_rows(min_row=2, values_only=True):
                    if not row:
                        continue
                        
                    tweeter = row[0]
                    total_tweet_Time = row[1]
                    tweet = row[2]
                    
                    if tweeter or tweet:
                        Election_model.objects.create(
                            tweeter=tweeter,
                            total_tweet_Time=total_tweet_Time,
                            tweet=tweet
                        )
                        row_data = [str(cell) for cell in row if cell is not None]
                        excel_data.append(row_data)
            elif file_name.endswith('.xls'):
                # Handle old Excel file with pandas
                df = pd.read_excel(excel_file)
                df = df.fillna('')
                for index, row in df.iterrows():
                    tweeter = str(row.iloc[0])
                    total_tweet_Time = str(row.iloc[1])
                    tweet = str(row.iloc[2])
                    
                    if tweeter or tweet:
                        Election_model.objects.create(
                            tweeter=tweeter,
                            total_tweet_Time=total_tweet_Time,
                            tweet=tweet
                        )
                        row_data = [tweeter, total_tweet_Time, tweet]
                        excel_data.append(row_data)

            else:
                 return render(request, 'RUser/Add_DataSet_Details.html', {"error": "Unsupported file format. Please upload .csv, .xls, or .xlsx"})

            return render(request, 'RUser/Add_DataSet_Details.html', {"excel_data": excel_data})

        except Exception as e:
            print(f"Error processing file: {e}")
            import traceback
            traceback.print_exc()
            return render(request, 'RUser/Add_DataSet_Details.html', {"error": str(e)})


def Register1(request):

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phoneno = request.POST.get('phoneno')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        ClientRegister_Model.objects.create(username=username, email=email, password=password, phoneno=phoneno,
                                            country=country, state=state, city=city)

        return render(request, 'RUser/Register1.html')
    else:
        return render(request,'RUser/Register1.html')

def ViewYourProfile(request):
    userid = request.session['userid']
    obj = ClientRegister_Model.objects.get(id= userid)
    return render(request,'RUser/ViewYourProfile.html',{'object':obj})


def Search_DataSets(request):
    obj = None
    if request.method == "POST":
        kword = request.POST.get('keyword')
        print(kword)
        try:
            # Assuming the intent is to search PREDICTIONS based on the keyword
            # Using Election_prediction_model because it has the 'prediction' field
            obj = Election_prediction_model.objects.filter(prediction__contains=kword)
        except Exception as e:
            print(e)
            obj = []

        return render(request, 'RUser/Search_DataSets.html', {'objs': obj})
    return render(request, 'RUser/Search_DataSets.html')



