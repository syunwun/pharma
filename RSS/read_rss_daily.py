# %% [markdown]
# # Set Parameter
email_address = sys.argv[1]
email_password = sys.argv[2]

# %%
import feedparser
import pandas as pd
import re
# import datetime
import numpy as np
import pytz
from datetime import datetime,timezone,timedelta

# %%
from pymongo import MongoClient
from pymongo import ReplaceOne, InsertOne
client = MongoClient(host="localhost", port=27017)
db = client['rss']
news_id_max_dict = db['news'].find({}, {"_id":1}).sort([("_id",-1)]).limit(1)
news_id_max = news_id_max_dict[0]['_id']
news_count = news_id_max+1
# news_count = 1
select_new_score = 24

# %%
# # Date&Time
# tz_utc = pytz.timezone("UTC")
# now = datetime.datetime.now()
# now = now.strftime("%Y-%m-%d %H:%M")
# today = datetime.datetime.now().replace(tzinfo=tz_utc)
dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
dt2 = dt1.astimezone(timezone(timedelta(hours=8)))

# Set patemeter
# dev_stage = ['Marketed','Pre-Registration','Phase III','Phase II','Phase I','Phase 0']
# today = datetime.now()
week_ago = dt2 - timedelta(hours=24)
anq_id = 244152

now = dt2.strftime("%Y-%m-%d %H:%M")

# %% [markdown]
# ## Score Parameter

# %%
## score
limit_times = 2
indi_score = 2
comp_score = 2
drug_score = 20
deal_score = 20
score_file = '.\score.xlsx'
trial_score_df = pd.read_excel(score_file, index_col = 0, sheet_name = 'development')
trial_score = (trial_score_df.to_dict(orient = 'dict'))['Score']
description_score_df = pd.read_excel(score_file, index_col = 0, sheet_name= 'description')
description_score = (description_score_df.to_dict(orient = 'dict'))['Score']
designation_df = pd.read_excel(score_file, index_col = 0, sheet_name = 'designation')
designation = (designation_df.to_dict(orient = 'dict'))['Alias']
designation_score = (designation_df.to_dict(orient = 'dict'))['Score']
deal_df = pd.read_excel(score_file, index_col = 0, sheet_name = 'deal')
deal = (deal_df.to_dict(orient = 'dict'))['Alias']

# %% [markdown]
# # Read RSS feed WebLink

# %%
## readin rss feed
website_file = '.\website.xlsx'
website_sheet = 'website'
website_df = pd.read_excel(website_file, sheet_name = website_sheet)
urllist = website_df['RSS'].values.tolist()
weblist = website_df['Website'].values.tolist()
imalist = website_df['Image'].values.tolist()
#print(urllist)


# %%
## assign list Variables
tit = []
lin = []
pub = []
des = []
web = []
sou = []
lan = []
dic = {}

# %% [markdown]
# # Fetch RSS feed News

# %%

## fetch RSS data and store as dic
for webname, url in zip(weblist, urllist):
    feed = feedparser.parse(url)
    entrie = feed.entries
    #print(webname, ', Number of RSS posts:', len(entrie))
#    print('keys:', entrie[0].keys())
    for i in range(len(entrie)):
        #print(webname)
        entry = entrie[i]
        
        ## website
        web.append(webname)
        
        ## title
        if(entrie[i].has_key('title')):
            title_raw = entry.title
            title_raw = title_raw.replace('\n\u200b','')
            tit.append(title_raw)
        else:
            tit.append('')
            
        ## link
        if(entrie[i].has_key('link')):
            lin.append(entry.link)
        else:
            lin.append('')
        
        ## description
        if(entrie[i].has_key('summary')):
            des.append(entry.summary)
        else:
            des.append('')
            
        ## pulication date
        if(entrie[i].has_key('published')):
            pub.append(entry.published)
        elif(entrie[i].has_key('updated')):
            pub.append(entry.updated)
        else:
            pub.append('')
            
        ## source
        if(entrie[i].has_key('source')):
            sou.append(entry.source['title'])
        else:
            sou.append('')
            
        ## language
        if(entrie[i].has_key('language')):
            lan.append(entry.language)
        else:
            lan.append('')
            
    ## store data in the dictionary        
    dic = {'Website': web,
           'Title': tit,
           'Link': lin,
           'PubDate': pub,
           'Description': des,
           'Language': lan,
           'Source': sou
           }


# %% [markdown]
# # Store RSS News into Dictionary

# %%
## convert rss dic into the dataframe
rss_df = pd.DataFrame.from_dict(dic)
rss_df['update'] = now
#rss_df


# %% [markdown]
# # Store Raw data in the database

# %%
#new_rss_df = df_all
rss_df = rss_df.astype(object).where(pd.notnull(rss_df),None)
rss_df_dict = rss_df.to_dict('records')

collections = db['news_raw']

##check if title exsits in the db
title_list = list()
for x in collections.find({},{'Title':1}):
    title_list.append(x['Title'])

## insert

for f in rss_df_dict:
    if not f['Title'] in title_list: 
        collections.insert_one(f)
        #collections.replace_one({'Title': f['Title']}, f, upsert=True)
        #collections.update({'Title': f['Title']}, f, upsert=True)


# %% [markdown]
# # Parse RSS Raw news

# %%
pub_formation = []
for p in pub:
    p = re.sub(',',', ',p)
    p = re.sub(' {2,}',' ',p)
    
    if(p == '')|(p == 'Invalid Date'):
        pub_formation.append(None)
        continue
    
    # convert timezone name
    if re.search(r'[A-Z]{2,3}$',p):
        # GMT' in p:
        p = re.sub(r'GMT$',r'+0000',p)
        p = re.sub(r'EST$',r'-0500',p)
        p = re.sub(r'EDT$',r'-0500',p)
        p = re.sub(r'UT$',r'+0000',p)
        p = re.sub(r'PST$',r'-0800',p)
        p = re.sub(r'PDT$',r'-0700',p)
        
        count = len(re.findall(r':', p))
        if count == 2 and ',' in p:
        # if re.find(r'\:[0-9]*\:',p):
            date_formatter = "%a, %d %b %Y %H:%M:%S %z"
        if ',' not in p:
            date_formatter = "%d %b %Y %H:%M:%S %z"
        if count == 1:
            date_formatter = "%a, %d %b %Y %H:%M %z"
        p_formation = datetime.strptime(p, date_formatter)
        pub_formation.append(p_formation)
        continue
       
    # 2021-11-19T00:05:31Z
    # 2019-06-26 12:00:00 -0400
    # 2021-10-25T01:03:21-07:00
    # 2021-11T00:00:00 +0000
    # 2021-11
    # 2021-11-23T15:00:00.000Z
    
    if re.search(r'\d\-\d',p):
        count = len(re.findall(r'\d\-', p))
        if count == 1:
            if 'T' not in p:
                p = p +'T00:00:00 +0000'
            date_formatter1 = "%Y-%mT%H:%M:%S %z"
        elif 'T' not in p and re.search(':',p):
            date_formatter1 = "%Y-%m-%d %H:%M:%S %z"
        elif 'T' not in p and not re.search(':',p):
            p = p + 'T00:00:00 +0000'
            date_formatter1 = "%Y-%m-%dT%H:%M:%S %z"
        elif '.' in p:
            p = re.sub(r'\..*',' +0000',p)
            date_formatter1 = "%Y-%m-%dT%H:%M:%S %z"
        elif 'T' in p:
            date_formatter1 = "%Y-%m-%dT%H:%M:%S%z"

        else:
            p = re.sub('Z$',' +0000',p)
            date_formatter1 = "%Y-%m-%dT%H:%M:%S %z"
            
        p_formation1 = datetime.strptime(p, date_formatter1)
        pub_formation.append(p_formation1)
        continue

    
    # 13 Nov 2021 21:53:18 EST
    if ',' not in p:
        date_formatter2 = "%d %b %Y %H:%M:%S %z"
        p_formation2 = datetime.strptime(p, date_formatter2)
        pub_formation.append(p_formation2)
        continue
    
    # Oct 26, 2021
    # Tue, 23 Nov 2021
    # October 27, 2021
    
    if ':' not in p:
        p = p + ' +0000'
        catch = re.search(r'^(\w*)',p).group()
        if re.search(r'[A-Za-z]\,', p):
            date_formatter3 = "%a, %d %b %Y %z"
        elif len(catch) >3:
            date_formatter3 = "%B %d, %Y %z"
        else:
            date_formatter3 = "%b %d, %Y %z"
        p_formation3 = datetime.strptime(p, date_formatter3)
        pub_formation.append(p_formation3)
        continue
    # 'Mon, 30 Nov -0001 00:00:00 +0000'
    # Wednesday, July 11, 2018 - 01:00
    if '+' in p or ' -' in p:
        count1 = len(re.findall(r':', p))
        count2 = len(re.findall(r',', p))
        if ('+' in p) and (' -' in p):
            pub_formation.append(None)
            continue
        elif count1 == 2 and ',' in p:
            date_formatter4 = "%a, %d %b %Y %H:%M:%S %z"
        elif count1 == 1:
            if count2 == 1:
                date_formatter4 = "%a, %d %b %Y %H:%M %z"
            elif count2 == 2:
                p = re.sub(r':','',p)
                p = re.sub(r'- ','-',p)
                date_formatter4 = "%A, %B %d, %Y %z"

        # date_formatter4 = "%a, %d %b %Y %H:%M:%S %z"
        p_formation4 = datetime.strptime(p, date_formatter4)
        pub_formation.append(p_formation4)
        continue    
        
    # 2021-11-19 09:00:00
    else:
    # if '+' not in p and '-0' not in p and 'EST' not in p:
        p = re.sub(' Z$','',p)
        p = p + ' +0000'
        if '-' in p:
            date_formatter5 = "%Y-%m-%d %H:%M:%S %z"
        if re.search('[a-zA-Z]{4,}',p):
            date_formatter5 = "%a, %d %B %Y %H:%M:%S %z"
        else:
            date_formatter5 = "%a, %d %b %Y %H:%M:%S %z"
        p_formation5 = datetime.strptime(p, date_formatter5)
        pub_formation.append(p_formation5)
        continue

# %% [markdown]
# ## Add formated date to rss_df

# %%
# replace date (pubdate) as new format
#rss_df['PubDate_ori'] = rss_df['PubDate']
rss_df['PubDate'] = pub_formation

# %% [markdown]
# # Indication
# ## Input indication file

# %%
## read & parse indication file (file from excel file)
### store company in the dic, the format is "indication: [alias list]"

indication_dic = {}
indication_file = '.\Indication.xlsx'
indication_df = pd.read_excel(indication_file)
indication = indication_df['Indication'].tolist()
alias = indication_df['Alias'].tolist()
for i, a in zip(indication, alias):
    a = list(a.split("; "))
    if i in indication_dic.keys():
        indication_dic[i].append(a)
    else:
        indication_dic[i] = a
indi_uniqu = indication_dic.keys()

# %% [markdown]
# # Company
# ## Defined unnecessary company name

# %%
## abbre for company short name => need to replace
drop_abbre = [' Co., Ltd.', ' AG & Co', ' & Co Ltd',  ' , Inc', ' Co Ltd', ' Corp', ' SA De CV', ' & Co KG',
              ' LLC', ' LLP', ' Pvt Ltd',
              ' Inc', ' SAS',
              ', Inc.',
              ' AG', ' AS', ' ASA', ' A/S', ' AB',
              ' and Co', ' Co Ltd', ' Corp', ' Co',
              ' Plc', ' Pvt', ' Pty',
              ' KK',
              ' GmbH',
              ' SA',  ' SAS', ' Srl', ' SpA', ' SE', ' SL',
              ' BV',
              ' KGaA',
              ' NV',
              ' Ltd', ' Tbk', ' (Group)',
              ' Pharmaceuticals',
              ' Scientific'
            #   ' Pharmaceutical', ' Pharmaceuticals', 'Therapeutics', ' Holdings',
            #   ' Industries', ' Pharma', ' International', ' Group', ' Laboratories', ',',
              ]

# %% [markdown]
# ## Input company file

# %%
## read & parse company file (file from tsv file)
## store company in the dic, the format is "company: parant company"
company_dic = {}
company_list = '.\Company.csv'
company_df = pd.read_csv(company_list,encoding = "ISO-8859-1")
#company_df = pd.read_csv(company_list)

## clean company name, remove abbreviation type in the name  
company = company_df['Company Name'].tolist()
for i, c in enumerate(company):
    if c == 'Merck & Co Inc':
        next
    else:
        c = str(c)
        for a in drop_abbre:
            if(re.search(a,c)):
                c = re.sub(a,'', c)
        company[i] = c
        #next
marketcap = company_df['Annual Revenue (US$ m)'].tolist()

## biuld dictionary
for c, p in zip(company, marketcap):
    company_dic[c] = p
comp_uniqu = company_dic.keys()


# %% [markdown]
# # Drug
# ## Input drug file

# %%
drug_list = '.\CT_drug.xlsx'
drug_df = pd.read_excel(drug_list)
name_group_df_ori = drug_df[['drug','_id']]
name_group_df = name_group_df_ori.rename(columns={'drug':'name'})
name_group_df.drop_duplicates(inplace = True, ignore_index = True)

# %% [markdown]
# ## Define drug dev. rank
# %%
dev_rank={
            "Unknown": 1,
            "Archived": 2,
            "Archived (Marketed)": 3,
            "Inactive": 4,
            "Discontinued": 5,
            "Withdrawn": 6,
            "Filing rejected/Withdrawn": 7,
            "Withdrawn (Marketed)": 8,
            "Discovery": 9,
            "IND/CTA Filed": 10,
            "Preclinical": 11,
            "Phase 0": 12,
            "Early Phase 1":13,
            "Phase 1":14,
            "Phase 1/Phase 2":15,
            "Phase 2":16,
            "Phase 2/Phase 3":17,
            "Phase 3":18,
            "Pre-Registration":19,
            "Phase 4":20,
            "Marketed":21
}

# %% [markdown]
# ## Select the advanced dev. status for each drug & stroe in dic: drug_dev_dic

# %%
## drug : dev stage
## read & parse drug file (file from tsv file)
## store company in the dic, the format is "drug name: dev stage"

drug_dev_dic = {}
drug = drug_df['_id'].tolist()
dev_stage = drug_df['Highest Development Stage'].tolist()

for d, ds in zip(drug, dev_stage):
    d = str(d)
    if d != 'nan':
        if d in drug_dev_dic.keys():
            current_ds = drug_dev_dic[d]
            if dev_rank[current_ds] <=  dev_rank[ds]:
                drug_dev_dic[d] = ds
            else:
                next
        else:
            drug_dev_dic[d] = ds
            #drug_dic[d].append(b)

# %% [markdown]
# ## Define drug description rank

# %%
description_rank = {"IO": 3,
                    "Target": 2,
                    "Chemo": 1,
                    "Others":0,
                    "Unknown":0}

# %% [markdown]
# ## Find the MOA type for each drug & stroe in dic: drug_descriptor_dic

# %%
## drug : drug descriptor
## read & parse drug file (file from tsv file)
## store company in the dic, the format is "drug name: drug descriptor"

drug_descriptor_dic = {}
drug = drug_df['_id'].tolist()
drug_descriptor = drug_df['Drug Descriptor Group'].tolist()
drug_descriptor = list(np.nan_to_num(drug_descriptor,nan = 'Others'))

for d, dd in zip(drug, drug_descriptor):
    d = str(d)
    if d != 'nan':
        if d in drug_descriptor_dic.keys():
            current_dd = drug_descriptor_dic[d]
            if description_rank[current_dd] <=  description_rank[dd]:
                drug_descriptor_dic[d] = dd
            else:
                next
        else:
            drug_descriptor_dic[d] = dd
            #drug_dic[d].append(b)

# %% [markdown]
# # Filter undesired indications related news

# %%
rss_df['Language'] = rss_df['Language'].fillna('en')

# %%
## drop duplicated news
rss_df = rss_df[rss_df['PubDate'] >= week_ago]
rss_df = rss_df[rss_df['Language'].str.contains('en')]
rss_df = rss_df[rss_df['Title'].str.contains('updadte') == False]
rss_df = rss_df[rss_df['Title'].str.contains('NBA')== False]
rss_df = rss_df[rss_df['Title'].str.contains('house')== False]
rss_df = rss_df[rss_df['Title'].str.contains('husband')== False]
# rss_df = rss_df.drop_duplicates(subset=['Title','Description'])
rss_df = rss_df.drop_duplicates(subset=['Title'])
# rss_df.reset_index(drop = True, inplace = True)
rss_df.reset_index(drop = True, inplace = True)

# %% [markdown]
# # Parse description

# %%
## parse Title
title_raw = rss_df['Title'].tolist()
#web = rss_df['Website'].tolist()
for i, item in enumerate(title_raw):
    item = str(item)
    #if re.search(r'\r', item, flags=re.IGNORECASE):
    title = item.splitlines()
    title = re.sub(r'\n','',item, count = 0)
    title = re.sub(r'\r','',title, count = 0)
    title = re.sub(r'\’','\'',title, count = 0)
    title = re.sub(r'\®','',title, count = 0)
    title = re.sub(r'\™','',title, count = 0)
    if rss_df.loc[i,'Website'] == 'Google News':
        title = re.sub("\ \-\ .*$",'',title)
    title_raw[i] = title
rss_df['Title'] = title_raw

# %%
rss_df = rss_df.drop_duplicates(subset=['Title'])
rss_df.reset_index(drop = True, inplace = True)

# %%
## parse description
desc_raw = rss_df['Description'].tolist()
#web = rss_df['Website'].tolist()
for i, item in enumerate(desc_raw):
    item = str(item)
    #disr = item.splitlines()
    disr = re.sub(r'\n','',item, count = 0)
    disr = re.sub(r'\<.*href\=.*\>','',disr,count = 0)
    disr = re.sub(r'\<img*\>','',disr,count = 0)
    disr = re.sub(r'\®','',disr, count = 0)
    disr = re.sub(r'\™','',disr, count = 0)
    if rss_df['Website'][i] == 'The bmj':
        disr_all = re.match(r'(.*)\<div class',item)
        if disr_all:
            disr = disr_all.group()
    if rss_df['Website'][i] == 'ClinicalTrial.gov':
        disr = re.sub(r'\xa0',' ',item,count = 0)
    # disr = re.sub('\xa0',' ',item)
    #disr = re.sub('\<a.*\"\>','',item)
    #disr = item.splitlines()
    #disr = re.sub('\n','',item)
    desc_raw[i] = disr
rss_df['Description'] = desc_raw

# %% [markdown]
# ## Combine title and description column

# %%
## create rss sub: combine "Title" & "Description"
rss_df['temp'] = rss_df.loc[:,'Title']+rss_df.loc[:,'Description']

# %% [markdown]
# ## Fetch description content

# %%
desc = rss_df['Description'].values.tolist()
tit_modi = rss_df['Title'].values.tolist()
temp_desc = rss_df['temp'].values.tolist()

# %%
## record which news is related to which indication
indication_news = {}
company_news = {}
drug_news = {}
designation_news = {}
deal_news = {}

# %% [markdown]
# ## Find which news is related to desired indication

# %%
## find which column hit the indication

non_hit_idx1 = list(range(len(rss_df)))
for ind in indi_uniqu:
    hit_idx1 = []
    for i, item in enumerate(temp_desc):
        item = str(item)
        #if re.search(r"\b{}\b".format(ind), item, flags=re.IGNORECASE):
        if re.search(ind, item, flags=re.IGNORECASE):
            hit_idx1.append(i)
            #print(i)
            if i in non_hit_idx1:
                non_hit_idx1.remove(i)
        else:
            other_ind = indication_dic[ind]
            for oi in other_ind:
                #if re.search(r"\b{}\b".format(oi), item, flags=re.IGNORECASE):
                if re.search(oi, item, flags=re.IGNORECASE):
                    hit_idx1.append(i)
                    #print(i)
                    if i in non_hit_idx1:
                        non_hit_idx1.remove(i) 
                    break

    indication_news[ind] = hit_idx1   
indication_news['Others'] = non_hit_idx1

# %%
indication_news.keys()

# %% [markdown]
# ## Keep news that are related to selected indications

# %%
## create a keyword list which will use as a column
keyword_list = ['']*len(rss_df)

# %%
## create score list to record hit result
## list size is same with df and filled with "0"
score = [0]*len(rss_df)

# %% [markdown]
# ## Color the indication with red

# %%
## find which column hit the indication
score_ind = [0]*len(rss_df)
# hit_indication_idx = []
non_hit_idx1 = list(range(len(rss_df)))
for ind in indi_uniqu:
#ind = 'COVID'
    hit_idx1 = []
    for i, item in enumerate(temp_desc):
        item = str(item)
        if re.search(ind, item):
        #if re.search(r"\b{}\b".format(ind), item, flags=re.IGNORECASE):
            hit_idx1.append(i)
            #print(i)
            if i in non_hit_idx1:
                non_hit_idx1.remove(i)
            # hit_indication_idx.append(i)
            desc[i] = re.sub(ind, '<font color="red"><b>'+ind+'</b></font color="red">',desc[i], count=0, flags=re.IGNORECASE)
            tit_modi[i] = re.sub(ind, '<font color="red"><b>'+ind+'</b></font color="red">',tit_modi[i], count=0, flags=re.IGNORECASE)
            if keyword_list[i] == '':
                #keyword_list[i] = [ind]
                keyword_list[i] = ['<font color="red"><b>'+ind+'</b></font color="red">']
            else:
                #keyword_list[i].append(ind)
                keyword_list[i].append('<font color="red"><b>'+ind+'</b></font color="red">')
        else:
            other_ind = indication_dic[ind]
            for oi in other_ind:
                # if re.search(r"\b{}\b".format(oi), item, flags=re.IGNORECASE):
                if re.search(oi, item, flags=re.IGNORECASE):
                    hit_idx1.append(i)
                    #print(i)
                    if i in non_hit_idx1:
                        non_hit_idx1.remove(i) 
                    # hit_indication_idx.append(i)
                    #desc[i] = re.sub(r"\b{}\b".format(oi), '<font color="red"><b>'+oi+'</b></font color="red">',item, count=0)
                    desc[i] = re.sub(oi, '<font color="red"><b>'+oi+'</b></font color="red">',desc[i], count=0)
                    tit_modi[i] = re.sub(oi, '<font color="red"><b>'+oi+'</b></font color="red">',tit_modi[i], count=0)
                    if keyword_list[i] == '':
                        #keyword_list[i] = [oi]
                        keyword_list[i] = ['<font color="red"><b>'+oi+'</b></font color="red">']
                    else:
                        #keyword_list[i].append(oi)
                        keyword_list[i].append('<font color="red"><b>'+oi+'</b></font color="red">')
                    break

    indication_news[ind] = hit_idx1
    
    ## add score to the column
    for h1 in hit_idx1:
        score_ind[h1] = score_ind[h1]+indi_score
        
indication_news['Others'] = non_hit_idx1

for i, s in enumerate(score_ind):
    if s > indi_score*limit_times:
        score_ind[i] = indi_score*limit_times
    score[i] = score[i] + score_ind[i]

# %% [markdown]
# ## Color the deal with blueviolet

# %%
## Deal
#desc_formation_idx2 = desc ##renew desc
## find which column hit the company
score_de = [0]*len(rss_df)
for de in deal.keys():
    hit_idx5 = []
    for i, item in enumerate(temp_desc):
        item = str(item)
        #if re.search(r"\b{}\b".format(de), item, flags=re.IGNORECASE):
        if re.search(de, item):
            hit_idx5.append(i)
            desc[i] = re.sub(r"(^|\s){}($|\s)".format(de), '<font color="blueviolet"><b>'+de+'</b></font color="blueviolet">',desc[i], count=0, flags=re.IGNORECASE)
            tit_modi[i] = re.sub(r"(^|\s){}($|\s)".format(de), '<font color="blueviolet"><b>'+de+'</b></font color="blueviolet">',tit_modi[i], count=0, flags=re.IGNORECASE)
            if keyword_list[i] == '':
                keyword_list[i] = ['<font color="blueviolet"><b>'+de+'</b></font color="blueviolet">']
            else:
                keyword_list[i].append('<font color="blueviolet"><b>'+de+'</b></font color="blueviolet">')
        else:
            if str(deal[de]) != 'nan':
                other_deal_str = deal[de]
                other_deal = other_deal_str.split('; ')
                for od in other_deal:
                    if re.search(od, item, flags=re.IGNORECASE):
                        hit_idx5.append(i)
                        desc[i] = re.sub(r"(^|\s){}($|\s)".format(od), '<font color="blueviolet"><b> '+od+' </b></font color="blueviolet">',desc[i], count=0, flags=re.IGNORECASE)
                        tit_modi[i] = re.sub(r"(^|\s){}($|\s)".format(od), '<font color="blueviolet"><b> '+od+' </b></font color="blueviolet">',tit_modi[i], count=0, flags=re.IGNORECASE)
                        if keyword_list[i] == '':
                            keyword_list[i] = ['<font color="blueviolet"><b>'+de+'</b></font color="blueviolet">']
                        else:
                            keyword_list[i].append('<font color="blueviolet"><b>'+de+'</b></font color="blueviolet">')                

    #print(hit_idx2)
    deal_news[de] = hit_idx5
    
    ## add score to the column
    for h5 in hit_idx5:
        score_de[h5] = score_de[h5]+ deal_score
        
for i, s in enumerate(score):
    score[i] = score[i] + score_de[i]

# %% [markdown]
# ## Color the designation with orange: Orphan drug, ...

# %%
## Designation
#desc_formation_idx2 = desc ##renew desc
## find which column hit the company
score_deg = [0]*len(rss_df)
for deg in designation.keys():
    hit_idx4 = []
    for i, item in enumerate(temp_desc):
        item = str(item)
        #if re.search(r"\b{}\b".format(deg), item, flags=re.IGNORECASE):
        if re.search(deg, item, flags=re.IGNORECASE):
            hit_idx4.append(i)
            desc[i] = re.sub(deg, '<font color="orange"><b>'+deg+'</b></font color="orange">',desc[i], count=0)
            tit_modi[i] = re.sub(deg, '<font color="orange"><b>'+deg+'</b></font color="orange">',tit_modi[i], count=0)
            if keyword_list[i] == '':
                keyword_list[i] = ['<font color="orange"><b>'+deg+'</b></font color="orange">']
            else:
                k = keyword_list[i]
                k = str(k)
                # if (deg == 'FDA') and (re.search('[EMA|Breakthrough|Priority Review|Fast Track|Accelerated Approve]',k, flags=re.IGNORECASE)):
                #     continue
                # elif (deg == 'EMA') and (re.search('CMA',k, flags=re.IGNORECASE)):
                #     continue
                # else:
                #     keyword_list[i].append('<font color="orange"><b>'+deg+'</b></font color="orange">')
                keyword_list[i].append('<font color="orange"><b>'+deg+'</b></font color="orange">')
        else:
            other_deg_str = designation[deg]
            other_deg = other_deg_str.split('; ')
            for od in other_deg:
                if re.search(od, item, flags=re.IGNORECASE):
                    hit_idx5.append(i)
                    desc[i] = re.sub(od, '<font color="orange"><b>'+od+'</b></font color="orange">',desc[i], count=0, flags=re.IGNORECASE)
                    tit_modi[i] = re.sub(od, '<font color="orange"><b>'+od+'</b></font color="orange">',tit_modi[i], count=0, flags=re.IGNORECASE)
                    if keyword_list[i] == '':
                        keyword_list[i] = ['<font color="orange"><b>'+deg+'</b></font color="orange">']
                    else:
                        keyword_list[i].append('<font color="orange"><b>'+deg+'</b></font color="orange">')                    
    
    #print(hit_idx2)
    designation_news[deg] = hit_idx4
    
    ## add score to the column
    for h4 in hit_idx4:
        score_deg[h4] = score_deg[h4]+designation_score[deg]
        
for i, s in enumerate(score):
    score[i] = score[i] + score_deg[i]

# %% [markdown]
# ## Color the drug with blue

# %%
# 2021.09.29: 399.7s
# 2021.11.03: 10m30s
#PF-07321332

#name_group_dict
# import codecs
## find which column hit the drug
temp = []
name_group_df_id = name_group_df['_id'].tolist()
name_group_df_name = name_group_df['name'].tolist()

count_drug = [0]*len(rss_df)
drug_done = [['']]*len(rss_df)

for drug_id, dru in zip(name_group_df_id,name_group_df_name):
    drug_id = str(drug_id)   
    #drulist = name_group_df[drug_id]
    if drug_id != 'nan':
        this_drug_score = 0
        if pd.notna(drug_dev_dic[drug_id]):  
            this_drug_score = trial_score[drug_dev_dic[drug_id]]
        hit_idx3 = []
        for i, item in enumerate(temp_desc):
            if drug_id in drug_done[i]:
                continue
            count_drug[i] = count_drug[i]+1
            item = str(item)
            temp.append(drug_id)
            # for dru_all in name_group_dict[drug_id]:
            # for dru in dru_all:
            # dru = re.sub('-','\-',dru)
            dru = re.sub(r"\[","",dru)
            dru = re.sub(r"\]","",dru)
            dru = re.sub(r"\(","",dru)
            dru = re.sub(r"\)",'',dru)
            #dru = re.sub(r"-",'',dru)
            #dru = re.sub(r" ",'',dru)
            # if re.search(r"\b{}\b".format(dru), item):
            if re.search(r"(^|\s){}($|\s)".format(dru), item, re.IGNORECASE) or re.search(r"{}\)".format(dru), item, re.IGNORECASE) :
                drug_done[i].append(drug_id)
                hit_idx3.append(i)
                subs_word = '<font color="blue"><b> '+dru+' </b></font color="blue">'
                desc[i] = re.sub(r"(^|\s){}($|\s)".format(dru), subs_word,desc[i], count=0)
                tit_modi[i] = re.sub(r"(^|\s){}($|\s)".format(dru), subs_word,tit_modi[i], count=0)
                if keyword_list[i] == '':
                    keyword_list[i] = [subs_word]
                else:
                    if not subs_word in keyword_list[i]:
                        keyword_list[i].append(subs_word)
                break
                    
        drug_news[drug_id] = hit_idx3
        
        # ## add score to the column
        # for h3 in hit_idx3:
        #     if drug_id == anq_id: ## antroquinonol
        #         score[h3] = score[h3]+drug_score + 45
        #     if count_drug[h3] >= 3:
        #         score[h3] = score[h3]+(drug_score+this_drug_score)*description_score[drug_descriptor_dic[drug_id]]/count_drug[h3]
        #     else:
        #         score[h3] = score[h3]+(drug_score+this_drug_score)*description_score[drug_descriptor_dic[drug_id]]
        ## add score to the column
        for h3 in hit_idx3:
            if drug_id == anq_id: ## antroquinonol
                score[h3] = score[h3]+drug_score + 60
            # if count_drug[h3] >= 5:
            #     score[h3] = score[h3]+(drug_score+this_drug_score)*description_score[drug_descriptor_dic[drug_id]]/count_drug[h3]
            # else:
            #     score[h3] = score[h3]+(drug_score+this_drug_score)*description_score[drug_descriptor_dic[drug_id]]
            
            score[h3] = score[h3]+(drug_score+this_drug_score)*description_score[drug_descriptor_dic[drug_id]]

# %% [markdown]
# ## Color the company with green

# %%
# 2021.09.29: 138s
# 2021.11.03: 8m24s

#desc_formation_idx2 = desc ##renew desc
## find which column hit the company
score_com = [0]*len(rss_df)
count_com = [0]*len(rss_df)
score_com_special = [0]*len(rss_df)
for com in comp_uniqu:
    hit_idx2 = []
    this_comp_score_add = 0
    if company_dic[com] >= 10000:
        this_comp_score_add = 1
    if com in gbc_candidate_df:
        this_comp_score_add = 15
    if re.search('Golden Biotechnology',com, flags=re.IGNORECASE):
        this_comp_score_add = 45
    for i, item in enumerate(temp_desc):
        item = str(item)
        #if re.search(r"\b{}\b".format(com), item, flags=re.IGNORECASE) or re.search(r"{}'s".format(com), item, flags=re.IGNORECASE):
        if re.search(r"(^|\s){}($|\s)".format(com), item):
            hit_idx2.append(i)
            # desc[i] = re.sub(r"\b{}\b".format(com), '<font color="green"><b>'+com+'</b></font color="green">',item, count=0, flags=re.IGNORECASE)
            # tit_modi[i] = re.sub(r"\b{}\b".format(com), '<b>'+com+'</b>',item, count=0, flags=re.IGNORECASE)
            # desc[i] = re.sub(r"(^|\s){}($|\s)".format(com), '<font color="green"><b>'+com+'</b></font color="green">',desc[i], count=0)
            # tit_modi[i] = re.sub(r"(^|\s){}($|\s)".format(com), '<font color="green"><b>'+com+'</b></font color="green">',tit_modi[i], count=0)
            desc[i] = re.sub(com, '<font color="green"><b>'+com+'</b></font color="green">',desc[i], count=0)
            tit_modi[i] = re.sub(com, '<font color="green"><b>'+com+'</b></font color="green">',tit_modi[i], count=0)
            if keyword_list[i] == '':
                keyword_list[i] = ['<font color="green"><b>'+com+'</b></font color="green">']
            else:
                keyword_list[i].append('<font color="green"><b>'+com+'</b></font color="green">')
    #print(hit_idx2)
    company_news[com] = hit_idx2
     
    ## add score to the column
    for h2 in hit_idx2:
        score_com[h2] = score_com[h2]+comp_score
        count_com[h2] = count_com[h2]+1
        score_com_special[h2] = this_comp_score_add
        
# ## the max of score
# for i, s in enumerate(score_com):
#     # if s > comp_score*limit_times:
#     if count_com[i] >= 3:
#         score_com[i] = (comp_score*limit_times)/count_com[i]
# for i, s in enumerate(score):
#     score[i] = score_ind[i] + score_com[i] + score_com_special[i]
# #rss_df['Description'] = desc_formation_idx2

for i, s in enumerate(score):
    if count_com[i] >= 3:
        score[i] = (score[i] + score_com[i] + score_com_special[i])/count_com[i]
    else:
        score[i] = score[i] + score_com[i] + score_com_special[i]

# %% [markdown]
# ## Update the description for each news

# %%
rss_df.loc[:,'Description'] = desc
rss_df.loc[:,'Title ori'] = rss_df.loc[:,'Title']
rss_df.loc[:,'Title'] = tit_modi

# %% [markdown]
# # Add keyword

# %%
k_new = []
s = ', '
for k in keyword_list:
    k = s.join(k)
    k_new.append(k)

# %%
## add score to rss_df
rss_df['Score'] = score
rss_df['Keyword'] = k_new

# %% [markdown]
# # If source is pharma or authority, add additional score: 10

# %%
website_source_df = website_df[['Website','Web Category']]
website_source_df.drop_duplicates(inplace=True)

# %%
rss_df = rss_df.merge(website_source_df,how = 'left', on = 'Website')

# %%
# sco = rss_df['Score'].to_list()
# webc = rss_df['Web Category'].to_list()
# webfrom = rss_df['Source'].to_list()
# for w_ind, w in enumerate(webc):
# #for wc_index, wc in enumerate(rss_df['Web Category'].to_list()):
#     # if (w == 'Pharma'):
#     #         #w[0] = w[0] +10
#     #         sco[w_ind] = sco[w_ind] +100
# # for w_ind, w in enumerate(webfrom):
# #     #for wc_index, wc in enumerate(rss_df['Web Category'].to_list()):
# #     if (w == 'CNN'):
# #             #w[0] = w[0] +10
# #             sco[w_ind] = sco[w_ind] +100
# rss_df['Score'] = sco

# %% [markdown]
# # Score
# ## if has special words

# %%
special_word = ['fail', 'failure', 'collapses', 'plunge']
# score_index = rss_df.columns.get_loc("Score")
## reduce the impact (score) of review article
for i, item in enumerate(rss_df['Title'].tolist()):
    if ('trial' in item) or ('phase' in item) or ('Phase' in item) or ('study' in item):
        for s in special_word:
            if re.search(r"(^|\s){}($|\s)".format(s), item,flags=re.IGNORECASE):
                # rss_df.iloc[i,score_index] = rss_df.iloc[i,score_index]+100
                rss_df.loc[i,'Score'] = rss_df.loc[i,'Score']+100
            else:
                continue
    else:
        continue

# %%
special_word = ['pill', 'oral']
score_index = rss_df.columns.get_loc("Score")
## reduce the impact (score) of review article
for i, item in enumerate(rss_df['Title'].tolist()):
    for s in special_word:
        if s in item:
            rss_df.iloc[i,score_index] = rss_df.iloc[i,score_index]+100

# %%
# discarded_special_word = ['ties up with']
# score_index = rss_df.columns.get_loc("Score")
# ## reduce the impact (score) of review article
# for i, item in enumerate(rss_df['temp'].tolist()):
#     for s in discarded_special_word:
#         if s in item:
#             rss_df.iloc[i,score_index] = rss_df.iloc[i,score_index] + 20

# %%
discarded_special_word = ['test','é','Test',';', 'Antibody', 'vaccine']
score_index = rss_df.columns.get_loc("Score")
## reduce the impact (score) of review article
for i, item in enumerate(rss_df['Title'].tolist()):
    for s in discarded_special_word:
        # if s in item:
        if re.search(s ,item , flags=re.IGNORECASE):
            rss_df.iloc[i,score_index] = 0

# %% [markdown]
# # Remove unnecesarry column

# %%
## remove unnecesarry column
rss_df = rss_df.drop(columns = 'temp')

# %% [markdown]
# # Parse Source

# %%
source_web = rss_df['Source']
for s_i, s in enumerate(source_web):
    if pd.isna(s):
        rss_df.loc[s_i,'Source'] = rss_df.loc[s_i,'Website']

# %% [markdown]
# # Output RSS daily News

# %%
# from pymongo import MongoClient
# from pymongo import ReplaceOne, InsertOne
# client = MongoClient(host="localhost", port=27017)
# db = client['rss']
# news_count = db['news'].estimated_document_count()

## output rss 
#rss_df.rename(columns={"Index": "News_id"})
rss_df.reset_index(inplace=True,drop = True)
rss_df = rss_df.drop_duplicates()
rss_df['_id'] = rss_df.index

## Title
old_title = rss_df['Title'].to_list()
new_title = old_title
for i, t in enumerate(old_title):
    t = str(t)
    t = re.sub('\n\r','',t)
    new_title[i] = t
rss_df['Title'] = new_title

## title_modi
old_title = rss_df['Title ori'].to_list()
new_title = old_title
for i, t in enumerate(old_title):
    t = str(t)
    t = re.sub('\n\r','',t)
    new_title[i] = t
rss_df['Title ori'] = new_title

rss_df['_id'] = rss_df['_id'] + news_count
rss_df.to_csv(r'.\daily_news.csv', header = True, index = False, encoding='utf-8-sig')

# %% [markdown]
# # Output Sub-table: Indication

# %%
## open a file: indication
fo_ind = open(r'.\indication_news.csv',"w+",encoding="utf-8")
fo_ind.write('Indication'+','+'News_id'+"\n")
indication_news_df = pd.DataFrame()

## news table: inidcate which indication related to the news
for k in indication_news.keys():
    if len(indication_news[k]) >= 1: 
        indication_news[k] = [x+news_count for x in indication_news[k]]
    for index_k in indication_news[k]:
        #index_k = index_k + news_count
        #indication_news[k] = index_k
        index_k_st = str(index_k)
        fo_ind.write(k+','+index_k_st+"\n")
        df = pd.DataFrame(np.array([[k,index_k_st]]),columns=['indication','news_id'])
        indication_news_df = indication_news_df.append(df)        
        

## close the file
fo_ind.close()

# %% [markdown]
# # Output Sub-table: Company

# %%
## open a file: company
fo_com = open(r'.\company_news.csv',"w+", encoding="utf-8")
fo_com.write('Company'+','+'News_id'+"\n")
company_news_df = pd.DataFrame()

## news table: inidcate which indication related to the news
for k in company_news.keys():
    if len(company_news[k]) >= 1: 
        company_news[k] = [x+news_count for x in company_news[k]]
    for index_k in company_news[k]:
        #index_k = index_k + news_count
        index_k_st = str(index_k)
        fo_com.write(k+","+index_k_st+"\n")
        df = pd.DataFrame(np.array([[k,index_k_st]]),columns=['company','news_id'])
        company_news_df = company_news_df.append(df)
        

## close the file
fo_com.close()

# %% [markdown]
# # Output Sub-table: Drug

# %%
drug_df_output = drug_df[['drug','_id']]

# %%
## open a file: drug
drug_news_df = pd.DataFrame()
mylist = list()

## news table: inidcate which indication related to the news
for k in drug_news.keys():
    #k = str(k)
    if len(drug_news[k]) >= 1: 
        drug_news[k] = [x+news_count for x in drug_news[k]]
        
    for index_k in drug_news[k]:
        #index_k = index_k + news_count
        index_k_st = str(index_k)
        k = str(k)
        # fo_drug.write(k+"\t"+index_k_st+"\n")
        df = pd.DataFrame(np.array([[k,index_k_st]]),columns=['drug','news_id'])
        drug_news_df = drug_news_df.append(df)
if len(drug_news_df) > 0:
    drug_news_df['drug'] = drug_news_df['drug'].astype(float)
    drug_df_output['_id'] = drug_df_output['_id'].astype(float)
    drug_news_df_out = drug_news_df.merge(drug_df_output,how = 'left', left_on = 'drug', right_on = '_id')
    drug_news_df_out = drug_news_df_out.drop_duplicates()
    drug_news_df_out.to_csv(r'.\drug_news.csv',index = False)

## close the file
# fo_drug.close()

# %% [markdown]
# # Output Sub-table: Designation

# %%
## open a file: designation
fo_desi = open(r'.\designation_news.csv',"w+", encoding="utf-8")
fo_desi.write('Designation'+','+'News_id'+"\n")
designation_news_df = pd.DataFrame()
## news table: inidcate which indication related to the news
for k in designation_news.keys():
    if len(designation_news[k]) >= 1: 
        designation_news[k] = [x+news_count for x in designation_news[k]]
    for index_k in designation_news[k]:
        #index_k = index_k + news_count
        index_k_st = str(index_k)
        fo_desi.write(k+","+index_k_st+"\n")
        df = pd.DataFrame(np.array([[k,index_k_st]]),columns=['designation','news_id'])
        designation_news_df = designation_news_df.append(df)
        

## close the file
fo_desi.close()

# %% [markdown]
# # Output Sub-table: Deal

# %%
## open a file: deal
fo_deal = open(r'.\deal_news.csv',"w+", encoding="utf-8")
fo_deal.write('Deal'+','+'News_id'+"\n")
deal_news_df = pd.DataFrame()

## news table: inidcate which indication related to the news
for k in deal_news.keys():
    if len(deal_news[k]) >= 1: 
        deal_news[k] = [x+news_count for x in deal_news[k]]    
    for index_k in deal_news[k]:
        #index_k = index_k + news_count
        index_k_st = str(index_k)
        fo_deal.write(k+","+index_k_st+"\n")
        df = pd.DataFrame(np.array([[k,index_k_st]]),columns=['deal','news_id'])
        deal_news_df = deal_news_df.append(df)

## close the file
fo_deal.close()

# %% [markdown]
# # Import to mongodb

# %% [markdown]
# # Merge all tables to one big table

# %%
all_collection = ['indication','company','drug','designation','deal']
all_df_sub = [indication_news_df,company_news_df,drug_news_df,designation_news_df,deal_news_df]
# all_collection = ['indication','company']
# all_df_sub = [indication_news_df,company_news_df]

# %%
df_all = pd.DataFrame()
new_rss_df = rss_df

for subcollection, subdf in zip(all_collection,all_df_sub):
    if len(subdf) > 0:
        df_this = pd.DataFrame()
        subdf['news_id'] = subdf['news_id'].astype(int)
        group = subdf.groupby('news_id')
        id = subdf['news_id'].unique().tolist()
        for i in id:
            df = group.get_group(i)
            fea = list()
            for item in df[subcollection].to_list():
                fea.append(item)
            d = {subcollection: [fea], '_id': i}
            df = pd.DataFrame(data=d)
            df_this = df_this.append(df)
        if len(df_all)==0:
            df_all =  df_this
        else:
            df_all = df_all.merge(df_this, how = 'left', on = '_id')    
new_rss_df = rss_df.merge(df_all, how = 'left', on = '_id')

# %% [markdown]
# # Import to mongodb

# %%
duplicate_news_id = list()
#new_rss_df = df_all
new_rss_df = new_rss_df.astype(object).where(pd.notnull(new_rss_df),None)
new_rss_df_dict = new_rss_df.to_dict('records')

collections = db['news']

##check if title exsits in the db
title_list = list()
for x in collections.find({},{'Title ori':1}):
    title_list.append(x['Title ori'])

## insert
for f_index, f in enumerate(new_rss_df_dict):
    if not f['Title ori'] in title_list: 
        collections.insert_one(f)
        #collections.replace_one({'Title': f['Title']}, f, upsert=True)
        #collections.update({'Title': f['Title']}, f, upsert=True)
    elif (f['Title ori'] in title_list) and (f['Website'] != 'Google News'):
        myresult = collections.find({'Title ori':f['Title ori']},{'_id':1})
        for m in myresult:
            news_id = m['_id']
            f['_id'] = news_id
            rss_df.loc[f_index,'_id'] = news_id
            collections.replace_one({"_id": m['_id']},f, upsert=True)
        duplicate_news_id.append(f['_id'])
    elif f['Title ori'] in title_list:
        duplicate_news_id.append(f['_id'])

# %% [markdown]
# # Del duplicates

# %%
rss_df = rss_df.loc[rss_df['_id'].isin(duplicate_news_id) == False]

# %% [markdown]
# # Select News

# %%
# select news
d = rss_df[(rss_df['Score'] >= select_new_score)]
select_source_d = rss_df[(rss_df['Source'] == 'MarketWatch')]
select_source_d = select_source_d[select_source_d['Keyword'].str.contains('\"green\"')]
# d = rss_df[(rss_df['Score'] >= 24)]
# d = d[d['Keyword'].str.contains('\"red\"|\"blue\"')]
d = d[d['Keyword'].str.contains('\"red\"')]
d = d[~d['Keyword'].str.contains('\"blueviolet\"')]
# d = d[(d['Keyword'].str.contains('"red"'))|(d['Keyword'].str.contains('"blue"'))]
d = d[d['Website'] != 'ClinicalTrial.gov']
# d.reset_index(inplace=True,drop = True)
d = d.append(select_source_d)

# %%
d_select = d[['Title ori','Link','Source','Keyword','Score','_id']]
d_select = d_select.merge(indication_news_df, left_on = '_id', right_on = 'news_id', how = 'left')

# %%
d_select['indication'] = d_select['indication'].fillna('Others')

# %%
del d_select['_id']
del d_select['news_id']
l = list()
for i, item in enumerate(d_select['Keyword'].to_list()):
    # <font color="red"><b>Oncology</b></font color="red">, 
    k = re.sub(r'\<font\ color\=\"red\"\>\<b\>.*\<\/b\>\<\/font color\=\"red\"\>\,\ ','',item)
    k = re.findall(r'\<b\>([a-zA-Z0-9- ]*)\<\/',k)
    k = ', '.join(k)
    l.append(k)
d_select['Keyword'] = l    

# %%
d_select = d_select.sort_values(by=['indication'])
d_select.reset_index(inplace = True, drop = True)

# %%
num = 1
mail_list = list()
d_select.sort_values(by = ['indication','Score'], inplace = True, ascending=False)
for i in d_select.index:
    title = d_select.iloc[i,0]
    link = d_select.iloc[i,1]
    source = d_select.iloc[i,2]
    keyword = d_select.iloc[i,3]
    score = d_select.iloc[i,4] 
    indication = d_select.iloc[i,5] 
    
    # m = f'{num}. {title}\n'+f'{score}/ {source}/ {keyword}\n'+ link
    m = '('+ indication+') '+keyword+'\n' + f'{num}. {title} ({source})\n'+ link
    mail_list.append(m)
    num = num+1

# %%
# len(mail_list)
mail_list_test = mail_list
mail_list_test_drop = mail_list_test.copy()

# %%
len_sum = 0
no = 0
noin = 0
mail_list_sub = list()

for m in mail_list_test:
    # print(len(m))
    len_sum = len_sum + len(m)
    str_here = str(len(m))+'/'+str(len_sum)+'/'+str(no)
    # print(str_here)
    # print(m)
    if len_sum > 1000:
        item = list()
        for c in range(noin):
            item.append(mail_list_test_drop.pop(0))
        mail_list_sub_item = '\n\n'.join(item)
        mail_list_sub.append(mail_list_sub_item)
        # print(mail_list_sub_item)
        # print(mail_list_test_drop)
        # print('......end')
        len_sum = len(m)
        no = no+1
        noin = 1
        # continue
    else:
        no = no+1
        noin = noin+1
        # continue
    
mail_list_sub_item = '\n\n'.join(mail_list_test_drop)
mail_list_sub.append(mail_list_sub_item)

# %% [markdown]
# # Send mail

%%
mail_body_all = '\n'.join(mail_list_sub)
# Send mail
import smtplib
from email.mime.text import MIMEText
from email.header import Header
# set up the SMTP server
smtpObj  = smtplib.SMTP('smtp.gmail.com', 587)
smtpObj .starttls()
smtpObj .login(email_address, email_password)
to = [email_address]


message = MIMEText(mail_body_all, 'plain', 'utf-8')


subject = f'News: {now}'
message['Subject'] = Header(subject, 'utf-8')

# msg = '123456789'
# subject = f'{rss_content} News: {now}'
# body = mail_body
smtpObj.sendmail(email_address, to, message.as_string())
smtpObj.quit()
