import json
from datetime import datetime, timedelta
from gensim.models import doc2vec
from collections import namedtuple
import math
import re

# define training data
from sklearn import svm
from sklearn.preprocessing import StandardScaler  

#these are source text files
keywordfiles = ['fox_data.json', 'nytimes_data.json', 'cnn_data.json', 'huffington_data.json'] #'cnn_data.json', 

#for not dated texts
mindate = "1000-01-01 00:00:00"

def getdatadate(x):
    if (x['date'] is None):
        return mindate
    elif (x['date'] == "None"):
        return mindate
    else:
        return x['date']
  
#start source processing
cleaned_data = []
reduced_data = []
record = {}
id = 0
jsons = []
data = []

#getting source text
for data_file in keywordfiles:
    with open(data_file) as json_file:  
        jsons.append(json.load(json_file))

for js in jsons:
    data += js['news']

#with open('sdata.json', 'w') as make_file:
#    json.dump(data, make_file, indent="\t")

#sort articles by dates
sorted_date = sorted(data, key=lambda x: datetime.strptime(getdatadate(x), '%Y-%m-%d %H:%M:%S'))
#print (sorted_date)

#cleaning just in case
for p in sorted_date:
    if (p['date'] is None):
        continue
    elif (p['date'] == "None"):
        continue
    else:
        cleaned_data.append(p)

#collide same date articles
record = cleaned_data[0]
text = record['text']
re.sub('[^A-Za-z0-9]+', ' ', text)
record['text'] = text

for r in cleaned_data:
    if (record['date'] == r['date']):
        record['text'] += ' '
        text = r['text']
        re.sub('[^A-Za-z0-9]+', ' ', text)
        record['text'] += text
    else:
        record["id"] = id
        id += 1
        reduced_data.append(record)
        record = r
record["id"] = id
reduced_data.append(record)


#write data to file
#with open('reduced_data.json', 'w') as make_file:
#    json.dump(reduced_data, make_file, indent="\t")

# Transform data (you can add more data preprocessing steps) 
docs = []
tag_dates = []
analyzedDocument = namedtuple('AnalyzedDocument', 'words tags')
for t in reduced_data:
    words = t['text'].lower().split()
    tags = []
    tags.append(t['date'])
    tag_dates.append(t['date'])
    #print(words)
    #print(tags)
    docs.append(analyzedDocument(words, tags))

print("number of docs:", len(docs))

# Train model (set min_count = 1, if you want the model to work with the provided example data set)
model = doc2vec.Doc2Vec(docs, vector_size = 100, window = 300, min_count = 1, workers = 4)
print(str(model))
#model.save('doc2vec.model')

print(len(model.docvecs))

#getting stock data
with open('query_IXIC.json') as stock_json_file:
    stock_data = json.load(stock_json_file)

daily_data = stock_data["Time Series (Daily)"]
    
labels = []

#print(tag_dates)

def avoidingdatenext(x):
    current_date = datetime.strptime(x, '%Y-%m-%d')
    next_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
    if (x in daily_data):
        #print("basecase", x)
        return x
    else:
        #print(next_date)
        return avoidingdatenext(next_date)

def avoidingdateprev(x):
    current_date = datetime.strptime(x, '%Y-%m-%d')
    prev_date = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
    if (x in daily_data):
        #print("basecase", x)
        return x
    else:
        #print(next_date)
        return avoidingdateprev(prev_date)

for t_date in tag_dates:
    c_datetime = datetime.strptime(t_date, '%Y-%m-%d %H:%M:%S')
    p_date = (c_datetime - timedelta(days=2)).strftime("%Y-%m-%d")
    c_date = c_datetime.strftime("%Y-%m-%d")
    
    if (t_date == mindate):
        labels.append(0)
    elif (t_date is mindate):
        labels.append(0)
    else:
        diff_val = float(daily_data[avoidingdatenext(c_date)]['4. close']) - float(daily_data[avoidingdateprev(p_date)]['4. close'])
        if (diff_val > 0.0):
            labels.append(1)
        elif (diff_val < 0.0):
            labels.append(0)
        else:
            labels.append(0)

#print(labels)
print(len(labels))

split_val = math.ceil(len(labels) * 0.75)

scaler = StandardScaler() 
X = []
for index in range(1, split_val):
    X.append(model.docvecs[index])

scaler.fit(X)
X = scaler.transform(X)
print("X",len(X))

y = labels[1:split_val]
print("y",len(y))

clf = svm.SVC(kernel='rbf', degree=7)
clf.fit(X, y)

test_set = []
for index in range(split_val, len(labels)):
    test_set.append(model.docvecs[index])

test_set = scaler.transform(test_set)
print("test_set",len(test_set))

real_y = labels[split_val:]

print("real_y", len(real_y))

predicted_y = clf.predict(test_set)

print("predicted_y", len(predicted_y))

error_counts = 0
predict_counts = 0

for index in range(len(real_y)):
    if (real_y[index] == predicted_y[index]):
        predict_counts += 1
    elif (real_y[index] != predicted_y[index]):
        error_counts += 1
    else:
        print("error in error count")

print("error_counts", error_counts)
print("predict_counts", predict_counts)

print("accuracy %", (predict_counts / len(real_y)) * 100)