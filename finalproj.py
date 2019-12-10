import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import pandas as pd
import sys
import sqlite3
import matplotlib.pyplot as plt
import chart_studio.plotly as py
import plotly.graph_objs as go
from plotly.graph_objs import *
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator


#----------Caching
CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}

def get_unique_key(url):
  return url

def make_request_using_cache(url):
    unique_ident = get_unique_key(url)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        return CACHE_DICTION[unique_ident]



    else:
        #print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]

class Health():
    def __init__(self, title, user, desc, view, superuser):
        self.title = title
        self.user = user
        self.description = desc
        self.view= view
        self.superuser= superuser

    def __str__(self):
        return "{};{};{}".format(self.title,self.user, self.description, self.view, self.superuser)

    def csv_row(self):
        lst_result = [self.title, self.user, self.description, self.view, self.superuser]
        return lst_result

def csv_header():
	return ["Title","User", "Description", "Views", "superuser"]

def get_health_data():
    baseurl= "https://www.nairaland.com"
    healthurl= "/health"
    counter=0
    current_url= baseurl+ healthurl
    nextpage=current_url
    health_list=[]
    while counter < 10:

        nairaland = make_request_using_cache(nextpage)
        soup = BeautifulSoup(nairaland, "html.parser")
        content_div = soup.find(class_ = "body")
        table_content = content_div.find_all('table', id= None)

        postlist=[]
        for tr in table_content:
            table_cells = tr.find_all('td')
            for t in table_cells:
                #represents all the information in the s class (span)
                pull= t.find(class_= 's').text.strip()
                # print(len(pull))
                #this is m
                #I am splitting the information by a period
                pullsplit= pull.split(".")
                #I am splitting the first element of the split data to obtain only the views
                views= pullsplit[1].split("&")
                #here is the user which should agree to the user group below
                superuser= pullsplit[0][3:]
                #print("this is superusername",superuser)
                # After splitting the information, this is me obtaining the views by users
                view_by_user= views[1][:-5]
                #print("this is userview", view_by_user)

                postlist.append(pullsplit)
                # print(type(post))
                # print(type(pull))
                # print(pull[0])

                inside= t.find('b')

                inner_url= inside.find('a')['href']

                detail_url = baseurl  + inner_url

                forum = make_request_using_cache(detail_url)
                soup = BeautifulSoup(forum, 'html.parser')
                info_div = soup.find_all(class_='body')

                for a in info_div:
                    title = a.find('h2').text
                    para = a.find(class_= 'narrow').text
                    summary= a.find_all('table', summary= "posts")

                    for it in summary:
                        user= it.find("a", class_="user")
                        if user is None:
                            user= "unknown"
                        else:
                            user= user.text.strip()
                    healthdet = Health(title, user, para, view_by_user, superuser)
                    health_list.append(healthdet.csv_row())
        # print("Here is the first elemennt in post", postlist[0], len(postlist[0]))
        # print("Here is the second element in post", postlist[1])
        # print("Here is the third element in post", postlist[2])
        counter = counter + 1
        nextpage= current_url+ "/" + str(counter)

    return health_list


# #----------Word Cloud
new_list= []
user_list= []
text= get_health_data()
for i in text:
    description_cloud= i[2]
    user_cloud= i[1]
    user_list.append(user_cloud)
    new_list.append(description_cloud)

# unique_string=(" ").join(new_list)
# #----------Word Cloud for description
# stopwords = set(STOPWORDS)
# stopwords.update(["will", "Nigeria", "symptom", "one", "help", "symptom", "disease", "need","day", "good", "treatment", "cause", "take", "time", "now", "make", "may", "problem", "body", "well", "use", "said", "first", "please", "way", "going", "called", "result", "many", "want", "find", "symptoms", "helps", "even", "know", "include", "test", "year", "come", "food", "people", "used", "new", "feel", "go", "us", "often", "product", "health", "great", "reason", "patient", "best", "thing", "without", "area", "condition", "results", "say"])
#
# # Generate a word cloud image
# wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(unique_string)
# plt.imshow(wordcloud, interpolation='bilinear')
# plt.axis("off")
# plt.savefig("507wc.png", bbox_inches='tight')
# #plt.show()
# plt.close()
#
# #----------Word Cloud for user
# user_string=(" ").join(user_list)
# #----------Word Cloud for description
# stopwords = set(STOPWORDS)
# # Generate a word cloud image
# wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(user_string)
# plt.imshow(wordcloud, interpolation='bilinear')
# plt.axis("off")
# plt.savefig("507wcuser.png", bbox_inches='tight')
# #plt.show()
# plt.close()



#------ CREATE Health CSV FILE USING CLASS
with open('health.csv', 'w', newline= '') as csvfile:
    writer = csv.writer(csvfile, delimiter=";",quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(csv_header())
    for item in text:
        writer.writerow(item)

# ----------INITIALIZE DATABASE
DBNAME= "health.db"


HEALTHCSV= pd.read_csv("health.csv", sep= ";", encoding= 'utf-8')
#----------FINDING KEY DISEASE

dia= pd.read_csv("diagnosis.csv", names=['ds'])
dia=dia['ds'].str.lower()
dia= dia.to_frame()
dia_list= dia["ds"].tolist()
dia_list= list(set(dia_list))
diareg=re.compile(r'\b(?:%s)\b' % '|'.join(dia_list))

HEALTHCSV["disease"]=HEALTHCSV['Description'].str.findall(diareg)
for index, item in enumerate(HEALTHCSV["disease"]):
    HEALTHCSV["disease"][index]= list(set(item))

HEALTHCSV.to_csv("health.csv")

def init_db():

    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

# Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'Posts';
    '''
    cur.execute(statement)
    statement = '''
        DROP TABLE IF EXISTS 'Disease';
    '''
    cur.execute(statement)
    statement = '''
        DROP TABLE IF EXISTS 'User';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
       CREATE TABLE 'Disease' (
               'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
               'Disease' TEXT,
               'User' TEXT,
               'UserId' INTEGER,
               FOREIGN KEY('UserID') REFERENCES 'User'('Id')
       );  '''
    cur.execute(statement)


    statement = '''
        CREATE TABLE 'Posts' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Title' TEXT ,
                'User' TEXT ,
                'Description' TEXT,
                "View" INTEGER,
                "Superuser" TEXT,
                'UserID' INTEGER,
                FOREIGN KEY('UserID') REFERENCES 'User'('Id'));
    '''
    cur.execute(statement)
    statement = '''
        CREATE TABLE 'User' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'User' TEXT UNIQUE
        );
    '''
    cur.execute(statement)
    conn.commit()
    conn.close()

if len(sys.argv) > 1 and sys.argv[1] == '--init':
    print('Deleting db and starting over from scratch.')
    init_db()
else:
    print('Leaving the DB alone.')

initializing = init_db()

def insert_stuff():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    Health = HEALTHCSV


    for index, row in Health.iterrows():
        insertion= row[1]
        for eachrow in row[5]:
            statement = 'INSERT INTO "Disease" (Disease, User,UserId)'
            statement += 'VALUES (?, ?, NULL)'
            cur.execute(statement, (eachrow, insertion))
        # statement = 'INSERT INTO "Disease" (User)'
        # statement += 'VALUES (?)'
        # cur.execute(statement, (insertion,))


    Health = HEALTHCSV


    for index, row in Health.iterrows():
        insertion = (row[0], row[1], row[2], row[3], row[4])
        statement = 'INSERT OR REPLACE INTO "Posts" (Title, User, Description, View, Superuser, UserID) '
        statement += 'VALUES (?, ?, ?,?,?, NULL)'
        cur.execute(statement, insertion)


    start_key = 1
    Health = HEALTHCSV
    foreign_key_dict = {}

    for index, row in Health.iterrows():
        insertion=row[1]
        user= row[1]
        statement = 'INSERT OR REPLACE INTO "User" (User) '
        statement += 'VALUES (?) '
        cur.execute(statement, (insertion,))
        foreign_key_dict[user] = start_key
        start_key +=1

    for user, foreign_key in foreign_key_dict.items():
        try:
            cur.execute('UPDATE Posts SET userID =' + str(foreign_key) + ' WHERE user =' + '"' + user  + '"')
            cur.execute('UPDATE Disease SET UserId =' + str(foreign_key) + ' WHERE user =' + '"' + user  + '"')
        except:
            pass


    conn.commit()
    conn.close()
insert = insert_stuff()


# def words_in_string(word_list, a_string):
#     return set(word_list).intersection(a_string.split())
#
# if words_in_string(my_word_list,a_string ):
#     print('One or more words found!')
#
# for word in words_in_string(my_word_list, a_string):
#     print(word)

# words_in_string(searchcleaned,unique_string)
#Function processes user commands
#PRE PROCESSING STEP ONE
def process_command(command):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    if command.split()[0] == 'user':
        user_select= "SELECT User, Count(*) FROM Posts"
        user_join = " "
        user_group = 'GROUP BY User'
        user_order1 = 'ORDER BY COUNT(*) '
        user_order2= 'ASC '
        user_limit= 'LIMIT 10 '


        command_split = command.split(' ')
        for item in command_split:
            if "bottom" in item:
                bottom = item.split('=')[1]
                user_order2= 'ASC '
                user_limit = 'LIMIT ' + bottom
            elif "top" in item:
                top= item.split('=')[1]
                user_order2= 'DESC '
                user_limit = 'LIMIT ' + top

        statement = user_select  + user_join + user_group +" " + user_order1 + user_order2 + user_limit
        result= cur.execute(statement)
        print(result)

        user_list = []
        count_list = []
        for tuple in result:
            user_list.append(tuple[0])
            count_list.append(tuple[1])

        data = [go.Bar(
                x = user_list,
                y = count_list
        )]

        layout = go.Layout(
            title = 'List of Users'
        )

        fig = go.Figure(data=data, layout=layout)
        fig.show()
        conn.commit()
        conn.close()
        #print(statement)
        # return statement


    elif command.split()[0]== "disease":
        disease_select= "SELECT Disease, Count(*) FROM Disease"
        disease_join = " "
        disease_group = 'GROUP BY Disease'
        disease_order1 = 'ORDER BY COUNT(*) '
        disease_order2= 'DESC '
        disease_limit= 'LIMIT 10 '


        command_split = command.split(' ')
        for item in command_split:
            if "bottom" in item:
                bottom = item.split('=')[1]
                disease_order2= 'ASC '
                disease_limit = 'LIMIT ' + bottom
            elif "top" in item:
                top= item.split('=')[1]
                disease_order2= 'DESC '
                disease_limit = 'LIMIT ' + top

        statement = disease_select  + disease_join + disease_group +" " + disease_order1 + disease_order2 + disease_limit
        #print(statement)
        result= cur.execute(statement)



        disease_list = []
        count_list = []
        for tuple in result:
            disease_list.append(tuple[0])
            count_list.append(tuple[1])

        data = [go.Bar(
                x = disease_list,
                y = count_list
        )]

        layout = go.Layout(
            title = 'List of Diseases'
        )

        fig = go.Figure(data=data, layout=layout)
        fig.show()
        conn.commit()
        conn.close()

    # return result


        unique_string=(" ").join(disease_list)
        #----------Word Cloud for description
        stopwords = set(STOPWORDS)
        stopwords.update(["will", "Nigeria", "symptom", "one", "help", "symptom", "disease", "need","day", "good", "treatment", "cause", "take", "time", "now", "make", "may", "problem", "body", "well", "use", "said", "first", "please", "way", "going", "called", "result", "many", "want", "find", "symptoms", "helps", "even", "know", "include", "test", "year", "come", "food", "people", "used", "new", "feel", "go", "us", "often", "product", "health", "great", "reason", "patient", "best", "thing", "without", "area", "condition", "results", "say"])
        wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(unique_string)

        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()


    elif command.split()[0]== "view":
        view_select= "SELECT User, View FROM Posts"
        view_join = " "
        view_group = 'GROUP BY View '
        view_order1 = 'ORDER BY View '
        view_order2= 'DESC '
        view_limit= 'LIMIT 30 '

        command_split = command.split(' ')
        for item in command_split:
            if "bottom" in item:
                bottom = item.split('=')[1]
                view_order2= 'ASC '
                view_limit = 'LIMIT ' + bottom
            elif "top" in item:
                top= item.split('=')[1]
                view_order2= 'DESC '
                view_limit = 'LIMIT ' + top

        statement = view_select  + view_join + view_group +" " + view_order1 + view_order2 + view_limit
        print(statement)
        result= cur.execute(statement)
        # print(result)


        view_list = []
        count_list = []
        for tuple in result:
            view_list.append(tuple[0])
            count_list.append(tuple[1])

        data = [go.Bar(
                x = view_list,
                y = count_list
        )]

        layout = go.Layout(
            title = 'List of Views'
        )

        fig = go.Figure(data=data, layout=layout)
        fig.show()
        conn.commit()
        conn.close()


        view_string=(" ").join(view_list)
        #----------Word Cloud for description
        stopwords = set(STOPWORDS)
        wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(view_string)

        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()


    elif command.split()[0]== "mention":
        mention_select= "SELECT User FROM Disease "
        mention_where= ' '

        command_split = command.split(' ')
        for item in command_split:
            if 'mention' in item:
                disease = item.split('=')[1]
                print(disease)
                mention_where = '''
                WHERE Disease.Disease="''' + disease + '" '


        statement = mention_select  + mention_where
        print(statement)
        result= cur.execute(statement)
        # print(result)

        mention_list = []
        count_list = []

        labels= mention_list
        values= count_list
        fig = {
            'data':[{'values': values, 'labels': labels, 'type': 'pie'}],
            'layout':{'title': 'Disease Distribtion'}
        }
        py.plot(fig, filename='pie_genre')
        # trace = go.Pie(labels=labels, values=values)
        # py.plot([trace], filename='genre_pie_chart')

        # for tuple in result:
        #     view_list.append(tuple[0])
        #     count_list.append(tuple[1])
        #
        # data = [go.Bar(
        #         x = view_list,
        #         y = count_list
        # )]
        #
        # layout = go.Layout(
        #     title = 'List of Views'
        # )
        #
        # fig = go.Figure(data=data, layout=layout)
        # fig.show()
        conn.commit()
        conn.close()


        # view_string=(" ").join(view_list)
        # #----------Word Cloud for description
        # stopwords = set(STOPWORDS)
        # wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(view_string)
        #
        # plt.imshow(wordcloud, interpolation='bilinear')
        # plt.axis("off")
        # plt.show()

    return result

# for u in users:
#     print(u)

## Part 3: Implement interactive prompt. We've started for you!
def load_help_text():
    with open('help.txt') as f:
        return f.read()

def interactive_prompt():
    help_text = load_help_text()
    response = ''
    cmds = ['user','disease', 'view', "mention"]
    second = ['top=', 'bottom=', "disease="]
    options = tuple(second)
    while response != 'exit':
        response = input('Enter a command (or type "help"): ')

        if response == 'help':
            print(help_text)
        elif response == 'exit':
            print('bye!')
        elif not response.split(' ')[0] in cmds:
            print("Command not recognized")
        # elif not (response.split(' ')[1]).startswith(options):
        #     print("Command not recognized")
        else:
            process_command(response)


## Make sure nothing runs or prints out when this file is run as a module
if __name__=="__main__":
    interactive_prompt()
