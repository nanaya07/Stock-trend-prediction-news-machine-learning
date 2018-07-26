import json
from collections import OrderedDict
import newspaper
from datetime import datetime

newscom = "cnn"
url = 'https://www.cnn.com'

#memoize_articles=False
papers = newspaper.build(url, language='en', memoize_articles=False)
print("newspaper size: "+ str(papers.size()))

data = {}  
data['news'] = []
id = 0

for article in papers.articles:
    #process each article
    try:
        article.download()
        article.parse()
        #article.nlp()
    except:
        continue
    #print(article.keywords)
    #print(article.publish_date)
    print("process news: "+str(id))
    #construct data
    file_data = OrderedDict()
    file_data["id"] = id
    file_data["source"] = newscom
    #file_data["keywords"] = article.keywords
    if (article.publish_date is None):
        file_data["date"] = "1000-01-01 00:00:00"
    else:
        file_data["date"] = datetime.strftime(article.publish_date,'%Y-%m-%d %H:%M:%S')
    file_data["text"] = article.text
    data['news'].append(file_data)
    #print(json.dumps(file_data, indent="\t"))
    id += 1

#write data to file
with open(newscom+'_data.json', 'a') as make_file:
    json.dump(data, make_file, indent="\t")

