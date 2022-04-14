# %% [markdown]
# # Fetch data from mongodb

# %%
import pandas as pd
import numpy as np
import pymongo
from pymongo import MongoClient
from pymongo import ReplaceOne, InsertOne
import re
import sys
client = MongoClient(host="localhost", port=27017)
from datetime import datetime,timezone,timedelta


# %% [markdown]
# # Score weight

# %%
weight_item = ['overall_status','phase','intervention_type','has_single_facility','Molecule Type']
score_file = '.\score_weight.xlsx'
score_overall_status = pd.read_excel(score_file, sheet_name= 'overall_status')
score_phase = pd.read_excel(score_file, sheet_name= 'phase')
score_intervention_type = pd.read_excel(score_file, sheet_name= 'intervention_type')
score_has_single_facility = pd.read_excel(score_file, sheet_name= 'has_single_facility')
score_molecule_type = pd.read_excel(score_file, sheet_name= 'Molecule Type')

# %% [markdown]
# # Today

# %%
# dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
# dt2 = dt1.astimezone(timezone(timedelta(hours=8)))
# next_year = dt2 + timedelta(days=365)
# now = dt2.strftime("%Y-%m-%d %H:%M")

next_year = datetime.now() + timedelta(days=365)

# %%
# all_indications = ['AML', 'NSCLC','AD']
indica = sys.argv[1]
#indica = 'COVID-19'

# %% [markdown]
# # Fetch CTs from mongodb

# %% [markdown]
# ## Sponsor

# %%
db = client[f"clinicaltrial_aact_{indica}"]
# db = client[f"clinicaltrial_aact_AML"]
collection = db['sponsors']
sponsor_df = pd.DataFrame()

myresult  = collection.find({},{'item.name':1, 'item.lead_or_collaborator':1,'item.agency_class':1})
for m in myresult:
    nct = m['_id']
    item = m['item']
    for it in item:
        df = pd.DataFrame(it, index=[0])
        df['_id'] = nct
        sponsor_df = sponsor_df.append(df)
            

# %%
sponsor_df.rename(columns={'name':'sponsors'}, inplace = True)
sponsor_df = sponsor_df[sponsor_df['lead_or_collaborator'] == 'lead']
sponsor_df = sponsor_df[(sponsor_df['agency_class'] == 'Industry') | (sponsor_df['agency_class'] == 'INDUSTRY')]

# %%
studies_nctid = sponsor_df['_id'].unique().tolist()

# %% [markdown]
# ## Studies

# %%
#db = client[f"clinicaltrial_aact_{indica}"]
# db = client[f"clinicaltrial_aact_AML"]
collection = db['studies']
studies_df = pd.DataFrame()
# for drug in drug_list:
for nid in studies_nctid:
    myresult  = collection.find({'_id':nid},{'_id':1,'start_date':1,'start_date_type':1,'completion_date':1,'completion_date_type':1,'brief_title':1,'official_title':1,'overall_status':1,'phase':1,'enrollment':1,'enrollment_type':1,'url':1,'last_update_posted_date':1})
    for m in myresult:
        # nct = m['_id']
        # item = m['item']
        # for it in item:
        # df['_id'] = nct
        df = pd.DataFrame(m, index=[0])
        studies_df = studies_df.append(df)

# %% [markdown]
# ## Interventions

# %%
intervention_df = pd.DataFrame()
# for drug in drug_list:
# drug = 'Tipifarnib'
# db = client[f"clinicaltrial_aact_AML"]
collection = db['interventions']
for nid in studies_nctid:
# nid = 'NCT00074737'
    # myresult  = collection.find({'_id':nid},{'_id':1 ,'item.name':1,'item.other_name':1,'item.intervention_type':1})
    myresult  = collection.find({'_id':nid},{'_id':1 ,'item.name':1,'item.intervention_type':1})
    for m in myresult:
        nct = m['_id']
        item = m['item']
        for it in item:
            df = pd.DataFrame(it, index=[0])
            df['_id'] = nct
            intervention_df = intervention_df.append(df)

# %%
intervention_df.rename(columns={'name':'intervention'}, inplace = True)

# %%
intervention_df = intervention_df[(intervention_df['intervention_type'] == 'Drug')|(intervention_df['intervention_type'] == 'Biological')]
# intervention_df = intervention_df[intervention_df['intervention_type'] == 'Drug']

# %%
intervention_df.reset_index(drop = True, inplace = True )

# %%
for i, inter in enumerate(intervention_df['intervention'].tolist()):
    if "(" in inter:
        inter = re.sub(r"\ *\(.*\)",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if "[" in inter:
        inter = re.sub(r"\ *\[.*\]",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if "®" in inter:
        inter = re.sub(r"\®",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if "™" in inter:
        inter = re.sub(r"\™",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if "sodium" in inter:
        inter = re.sub(r"\ *sodium",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("dose" in inter)|("Dose" in inter):
        inter = re.sub(r"(High|Low)* *[Dd]ose ?[0-9]*",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("phase" in inter)|("Phase" in inter):
        inter = re.sub(r"[Pp]hase [a-zA-Z0-9]*",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("Besylate" in inter)|("besylate" in inter):
        inter = re.sub(r"\ *[Bb]esylate",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("mcg/kg/day" in inter):
        inter = re.sub(r" \d+\.?\d* mcg\/kg\/day",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("Day" in inter)|("day" in inter):
        inter = re.sub(r" \+ [dD]ay ?\d* Food",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("mg/kg" in inter):
        inter = re.sub(r" \d+\.?\d* mg\/kg",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("mg/day" in inter):
        inter = re.sub(r" \d+\.?\d* mg\/day",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" alone" in inter):
        inter = re.sub(r" alone",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" IR" in inter):
        inter = re.sub(r" IR",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("Tablet" in inter)|("tablet" in inter):
        inter = re.sub(r" ?[tT]ablet",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" Arm" in inter):
        inter = re.sub(r" \- \w* *Arm",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" mg" in inter):
        inter = re.sub(r" ?\d+\.?\d* *mg ?",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" MG" in inter):
        inter = re.sub(r" ?\d+\.?\d* *MG ?",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" μg" in inter):
        inter = re.sub(r" \d+ μg",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" SR" in inter):
        inter = re.sub(r" SR",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" MR" in inter):
        inter = re.sub(r" MR\d",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" Transdermal" in inter):
        inter = re.sub(r" Transdermal",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" po TID" in inter):
        inter = re.sub(r" po TID",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("TDS" in inter):
        inter = re.sub(r" TDS",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("Version" in inter):
        inter = re.sub(r" Version \w",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("Drug: " in inter):
        inter = re.sub(r"Drug\: ",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("/" in inter):
        inter = re.sub(r" ?\/ ?",' + ',inter)
        intervention_df.loc[i,'intervention'] = inter
    if re.search(r"[^ ]\+[^ ]",inter):
        inter = re.sub(r"\+",' + ',inter)
        intervention_df.loc[i,'intervention'] = inter
    if re.search(r"[^ ]\+ ", inter):
        inter = re.sub(r"\+ ",' + ',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" level" in inter):
        inter = re.sub(r" level \d",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if re.search(r" \dx", inter):
        inter = re.sub(r" \dx",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("TID" in inter):
        inter = re.sub(r" TID",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if (" PET Scan" in inter):
        inter = re.sub(r" PET Scan",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("SC" in inter):
        inter = re.sub(r" ?\- ?SC",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("IV" in inter):
        inter = re.sub(r" ?\- ?IV",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("OL" in inter):
        inter = re.sub(r" ?OL",'',inter)
        intervention_df.loc[i,'intervention'] = inter
    if ("COVID-19" in inter):
        inter = re.sub(r" ?COVID-19",'',inter)
        intervention_df.loc[i,'intervention'] = inter

# %%
intervention_df[intervention_df['_id'] == 'NCT00998764']

# %%
intervention_df.drop_duplicates(inplace = True, ignore_index=True)

# %% [markdown]
# ## Calculate Value

# %%
calculatedvalue_df = pd.DataFrame()
# for drug in drug_list:
# drug = 'Tipifarnib'
# db = client[f"clinicaltrial_aact_AML"]
collection = db['calculated_values']
for nid in studies_nctid:
# nid = 'NCT00074737'
    # myresult  = collection.find({'_id':nid},{'_id':1 ,'item.name':1,'item.other_name':1,'item.intervention_type':1})
    myresult  = collection.find({'_id':nid},{'_id':1 ,'item.has_us_facility':1,'item.has_single_facility':1, 'item.number_of_facilities':1})
    for m in myresult:
        nct = m['_id']
        item = m['item']
        for it in item:
            df = pd.DataFrame(it, index=[0])
            df['_id'] = nct
            calculatedvalue_df = calculatedvalue_df.append(df)

# %% [markdown]
# # Design Group

# %%
#db = client[f"clinicaltrial_aact_{indica}"]
# db = client[f"clinicaltrial_aact"]
collection = db['design_groups']
design_group_df = pd.DataFrame()

for nid in studies_nctid:
    # myresult  = collection.find({'_id':nid},{'item.group_type':1, 'item.title':1,'item.description':1})
    myresult  = collection.find({'_id':nid},{'item.group_type':1})
    for m in myresult:
        nct = m['_id']
        item = m['item']
        for it in item:
            df = pd.DataFrame(it, index=[0])
            df['_id'] = nct
            design_group_df = design_group_df.append(df)

# %%
design_group_df = design_group_df[design_group_df['group_type'] == 'Experimental']

# %% [markdown]
# # Combine above tables

# %%
ct_df = studies_df.merge(sponsor_df, on = '_id', how = 'left')
ct_df = ct_df.merge(intervention_df, on = '_id', how = 'left')
ct_df = ct_df.merge(design_group_df, on = '_id', how = 'left')
ct_df = ct_df.merge(calculatedvalue_df, on = '_id', how = 'left')

# %%
ct_df.drop_duplicates(inplace=True)
ct_df.shape

# %%
# ct_df = ct_df[ct_df['intervention'].str.contains(" Care") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r" [Cc]are") == False]
# ct_df = ct_df[ct_df['intervention'].str.contains("placebo") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r"[Pp]lacebo") == False]
# ct_df = ct_df[ct_df['intervention'].str.contains("Choice") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r"[Cc]hoice") == False]
# ct_df = ct_df[ct_df['intervention'].str.contains("therapy") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r"[Tt]herapy") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r"[Ss]aline") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r"[Cc]ontrol") == False]
ct_df = ct_df[ct_df['intervention'].str.contains(r"[Cc]ell") == False]

# %%
ct_df.reset_index(drop=True, inplace=True)


# %% [markdown]
# # SOC drug

# %%
chemotherapy_file = '.\SOC.xlsx'
chemotherapy_df = pd.read_excel(chemotherapy_file, sheet_name = 'chemotherapy')

drug = chemotherapy_df['Drug'].dropna().tolist()
alias = chemotherapy_df['Alias'].dropna().tolist()
chemotherapy_alisa_list = list()
for a in alias:
    alist = a.split('; ')
    chemotherapy_alisa_list = chemotherapy_alisa_list +alist
chemotherapy = drug+chemotherapy_alisa_list
# chemotherapy

# %%
drop_list = list()
for c in chemotherapy:
    for i, ct in enumerate(ct_df['intervention']):
        if re.search(c, ct, flags=re.IGNORECASE):
            drop_list.append(i)

# %%
socdrug_df = pd.read_excel(chemotherapy_file, sheet_name = 'soc_drug')
for c in socdrug_df.index:
    drug = socdrug_df.loc[c,'Drug']
    sponsor = socdrug_df.loc[c,'Sponsor']
    for i in ct_df.index:
        if (ct_df.loc[i,'intervention'] == drug) and (ct_df.loc[i,'sponsors'] != sponsor):
            drop_list.append(i)

# %%
ct_df_new = ct_df.drop(drop_list)

# %% [markdown]
# # Remove 7+3

# %%
ct_df_new = ct_df_new[(ct_df_new['intervention']=='7+3')==False]

# %%
ct_df_new.drop_duplicates(inplace=True)

# %% [markdown]
# # Fetch intervention detail

# %% [markdown]
# ## Fetch drug id

# %%
intervention = ct_df_new['intervention'].tolist()
db_drug = client[f"drug_{indica}"]
collection = db_drug['drug_name']
drug_name_df = pd.DataFrame()

for int in intervention:
    myresult  = collection.find({'Alias Name':{'$regex':int, '$options':'i'}},{'_id':1})
    # myresult  = collection.find({'Drug Name':int},{'_id':1})
    for m in myresult:
        df = pd.DataFrame(m, index=[0])
        df['intervention'] = int
        drug_name_df = drug_name_df.append(df)

for int in intervention:
    myresult  = collection.find({'Drug Name':{'$regex':int, '$options':'i'}},{'_id':1})
    # myresult  = collection.find({'Drug Name':int},{'_id':1})
    for m in myresult:
        df = pd.DataFrame(m, index=[0])
        df['intervention'] = int
        drug_name_df = drug_name_df.append(df)

# %% [markdown]
# ## Fetch drug details

# %%
drugid = drug_name_df['_id'].tolist()
collection = db_drug['drug_detail']
drug_detail_df = pd.DataFrame()

for id in drugid:
    myresult  = collection.find({'_id':id},{'_id':1, 'Target':1,'Mechanism of Action':1,'Molecule Type':1,'Drug Descriptor':1,'Drug Descriptor Group':1})
    # myresult  = collection.find({'Drug Name':int},{'_id':1})
    for m in myresult:
        df = pd.DataFrame(m, index=[0])
        # df['intervention'] = int
        drug_detail_df = drug_detail_df.append(df)

# %%
drug_df = drug_name_df.merge(drug_detail_df, on = '_id', how = 'left')

# %%
del drug_df['_id']

# %%
drug_df.drop_duplicates(inplace=True,ignore_index=True)

# %%
ct_df_new = ct_df_new.merge(drug_df, on = 'intervention', how = 'left')

# %%
ct_df_new.reset_index(inplace = True, drop = True)

# %%
ct_df_new.drop_duplicates(inplace=True,ignore_index=True)

# %%
ct_df_new = ct_df_new[ct_df_new['has_us_facility'] == True]

# %% [markdown]
# # Add unique_intervention

# %%
inter_spon_temp = list(ct_df_new['intervention'] + ct_df_new['sponsors'])
unique_drug = list(set(inter_spon_temp))
ct_df_new['temp'] = inter_spon_temp

# %%
unique_drug_df = pd.DataFrame()
for u in unique_drug:
    u_count = inter_spon_temp.count(u)
    d = {'temp':u, 'count': u_count}
    df = pd.DataFrame(data=d, index = [0])
    unique_drug_df = unique_drug_df.append(df)

# %%
unique_drug_df['unique_intervention'] = 1/unique_drug_df['count']
del unique_drug_df['count']

# %%
ct_df_new_merge = ct_df_new.merge(unique_drug_df, on = 'temp', how = 'left')


# %%
ct_df_new = ct_df_new_merge[['unique_intervention','intervention','phase','overall_status','enrollment','sponsors','completion_date','start_date','brief_title','official_title','_id','url','last_update_posted_date','start_date_type','completion_date_type','enrollment_type','agency_class','lead_or_collaborator','intervention_type','group_type','number_of_facilities','has_us_facility','has_single_facility','Target','Mechanism of Action','Molecule Type','Drug Descriptor','Drug Descriptor Group']]

# %% [markdown]
# # Add weighted score

# %%
ct_df_new.reset_index(inplace = True, drop = True)

# %% [markdown]
# ## Add unmeighted score

# %%
ct_df_new = ct_df_new.merge(score_overall_status, on = 'overall_status', how = 'left')
ct_df_new = ct_df_new.merge(score_phase, on = 'phase', how = 'left')
ct_df_new = ct_df_new.merge(score_intervention_type, on = 'intervention_type', how = 'left')
ct_df_new = ct_df_new.merge(score_has_single_facility, on = 'has_single_facility', how = 'left')
ct_df_new = ct_df_new.merge(score_molecule_type, on = 'Molecule Type', how = 'left')

# %%
df_index = ct_df_new.index
for d in df_index:
    ## unweighted score
    complete_time = ct_df_new.loc[d, 'completion_date']
    if complete_time is None:
        ct_df_new.loc[d, 'CT_Score_unweighted (completion date in one year)'] = 5
    else:
        if complete_time <= next_year:
            ct_df_new.loc[d, 'CT_Score_unweighted (completion date in one year)'] = 10
        else:
            ct_df_new.loc[d, 'CT_Score_unweighted (completion date in one year)'] = 5
            
    ## weighted score
    raw = ct_df_new.loc[d, 'CT_Score_unweighted (completion date in one year)'] 
    o = ct_df_new.loc[d, 'overall_status_weight']
    p = ct_df_new.loc[d, 'phase_weight']
    i = ct_df_new.loc[d, 'intervention_type_weight']
    h = ct_df_new.loc[d, 'has_single_facility_weight']
    m = ct_df_new.loc[d, 'Molecule Type weight']
    CT_Score_weight = raw*o*p*i*h*m
    ct_df_new.loc[d, 'CT_Score_weight'] = CT_Score_weight

# %% [markdown]
# # Print out

# %%
# some_value = ['Active, not recruiting','Recruiting','Not yet recruiting','Enrolling by invitation']
# ct_df_new['overall_status_weight'] = 1.5
# ct_df_new = ct_df_new[ct_df_new['overall_status'].isin(some_value)]

ct_df_new.to_excel(f'.\{indica}_CT.xlsx', index = False, sheet_name = indica)
