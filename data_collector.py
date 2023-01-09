#!/usr/bin/env python
# coding: utf-8

# In[6]:


import requests
import xmltodict
import pandas as pd

NUMBER_OF_HOUSE_SPEAKERS = 434


# In[99]:


def pp_dict(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pp_dict(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))

def get_names_and_vote(alist):
    """
    Prints name of house rep and their casted vote in alist

    Parameter alist: list of house reps with their vote
    Precondition: 
        - alist is a list of dicts
        - each dict has
            legislator: {
                @unaccented-name: str
                @party: str
                @state: str
            }
            vote: str
    """
    
    for rep in alist:
        assert 'legislator' in rep.keys()
        assert 'vote' in rep.keys()
        legislator = rep['legislator']
        vote = rep['vote']
        print(f"({legislator['@party']}) {legislator['@unaccented-name']} of {legislator['@state']} votes {vote}")
    
def check_data(data):
    """
    Raises ValueError if data does not pass tests.
    Tests:
        Number of House of Representatives is NUMBER_OF_HOUSE_SPEAKERS
        Votes in vote-metadata and vote-data agree
    """
#     assert len(alist) == NUMBER_OF_HOUSE_SPEAKERS
    
def preprocess_votes(votes, rollcall_num):
    """
    Returns votes preprocessed:
        - unpacks legislator dict
    
    Parameter votes: list of house reps with their vote
    Precondition: 
        - votes is a list of dicts
        - each dict has
            legislator: dict
            vote: str

    Parameter rollcall_num: rollcall-num for this election
    Precondition: rollcall_num is an int
    """
    assert type(votes) == list
    assert type(rollcall_num) == int
    out = []
    for rep in votes:
        assert 'legislator' in rep.keys()
        assert 'vote' in rep.keys()
        adict = {}
        adict['vote'] = rep['vote']
        for k, v in rep['legislator'].items():
            adict[k] = v
        adict['rollcall-num'] = rollcall_num
        out.append(adict)
    return out

def preprocess_vote_metadata(vote_metadata):
    """
    Returns vote_metadata, vote_totals preprocessed
    vote_metadata preprocessed:
        - omits @time-etz in action-time
        - remove vote-totals 
        - change rollcall-num value to int
    vote-totals
        - unpacks totals-by-candidate
        - each candidate will be at top level as candidate_name : candidate-total
        
    Parameter vote_metadata: voting metadata
    Precondition: 
    vote_metadata is a dict with schema:
    {
        vote-totals : {
            totals-by-candidate: list
        },
        action-time : {
            @time-etz: str,
            #text: str,
        }
        rollcall-num: str,
        ...
    }
    """
    metadata = {}
    assert type(vote_metadata) == dict
    assert 'vote-totals' in vote_metadata.keys()
    assert 'action-time' in vote_metadata.keys()
    assert 'rollcall-num' in vote_metadata.keys()
    for k, v in vote_metadata.items():
        if k == 'vote-totals':
            assert 'totals-by-candidate' in v.keys()
            assert type(v['totals-by-candidate']) == list
            rollcall_num = vote_metadata['rollcall-num']
            assert type(rollcall_num) == str and rollcall_num.isnumeric()
            vote_totals = preprocess_vote_metadata_aux(v['totals-by-candidate'], int(rollcall_num))
        elif k == 'action-time':
            assert type(v) == dict
            assert '@time-etz' in v.keys()
            assert type(v['@time-etz']) == str
            metadata[k] = v['@time-etz']
        elif k == 'rollcall-num':
            assert type(v) == str and v.isnumeric()
            metadata[k] = int(v)
        else:
            metadata[k] = v
    return [metadata], vote_totals
    
def preprocess_vote_metadata_aux(vote_totals, rollcall_num):
    """
    Returns list representing vote_totals
    Schema
    vote_totals = [{
        rollcall-num: int,
        candidate-total: int,
        ...
    }]
    
    Parameter vote_totals: vote totals of all candidates
    Precondition: vote_totals is a list of dicts
    Schema
    vote_totals = [{
        candidate-total: str,
        ...
    }]
    
    Parameter rollcall_num: rollcall-num for this election
    Precondition: rollcall_num is an int
    """
    assert type(vote_totals) == list
    assert type(rollcall_num) == int
    out = []
    for c in vote_totals:
        d = dict()
        assert 'candidate-total' in c.keys()
        for k, v in c.items():
            if k == 'candidate-total':
                assert type(v) == str and v.isnumeric()
                d[k] = int(v)
            else:
                d[k] = v
        d['rollcall-num'] = rollcall_num
        out.append(d)
    return out


# In[100]:


url = "https://clerk.house.gov/evs/2023/roll012.xml"
response = requests.get(url)
data = xmltodict.parse(response.content)


# In[101]:


pp_dict(data)


# In[102]:


metadata, vote_totals = preprocess_vote_metadata(data['rollcall-vote']['vote-metadata'])


# In[103]:


metadata_df = pd.DataFrame(metadata)
metadata_df


# In[104]:


vote_totals_df = pd.DataFrame(vote_totals)
vote_totals_df


# In[111]:


votes = preprocess_votes(data['rollcall-vote']['vote-data']['recorded-vote'], metadata_df['rollcall-num'].item())
votes_df = pd.DataFrame(votes)
votes_df


# In[112]:


votes_df.groupby(['vote'])['vote'].count()


# In[114]:



ROLLCALL_NUMS = ['002', '003', '004', '005',
                 '006', '007', '009', '010', 
                 '011', '012', '013', '015',
                 '016', '018', '020']
# assert len(rollcall_nums) == 15
def data_collect_df(rollcall_num):
    """
    Returns metadata, vote_summary, and vote records from 
    "https://clerk.house.gov/evs/2023/<rollcall_num>.xml" as DataFrames.
    
    Parameter rollcall_num: Voting session number
    Precondition: rollcall_num is a str in ROLLCALL_NUMS
    """
    assert type(rollcall_num) == str and rollcall_num in ROLLCALL_NUMS
    url = f"https://clerk.house.gov/evs/2023/roll{rollcall_num}.xml"
    response = requests.get(url)
    data = xmltodict.parse(response.content)
    metadata, vote_totals = preprocess_vote_metadata(data['rollcall-vote']['vote-metadata'])
    metadata_df = pd.DataFrame(metadata)
    vote_totals_df = pd.DataFrame(vote_totals)
    votes = preprocess_votes(data['rollcall-vote']['vote-data']['recorded-vote'], metadata_df['rollcall-num'].item())
    votes_df = pd.DataFrame(votes)
    return (metadata_df, vote_totals_df, votes_df)


# In[115]:


import random
(metadata_df, vote_totals_df, votes_df) = data_collect_df(random.choice(ROLLCALL_NUMS))
display(metadata_df)
display(vote_totals_df)
display(votes_df)
print(votes_df.groupby(['vote'])['vote'].count())


# In[132]:


import os
import time
paths = {'metadata': './data/metadata', 'vote-totals': './data/vote-totals', 'votes': './data/votes'}
def data_to_csv(rollcall_num):
    """
    Writes data collected from data_collect_df to CSVs.
    
    Parameter rollcall_num: Voting session number
    Precondition: rollcall_num is a str in ROLLCALL_NUMS
    """
    assert type(rollcall_num) == str and rollcall_num in ROLLCALL_NUMS
    (metadata_df, vote_totals_df, votes_df) = data_collect_df(rollcall_num)
    metadata_df.to_csv(os.path.join(paths['metadata'], rollcall_num + '.csv'), index=False)
    vote_totals_df.to_csv(os.path.join(paths['vote-totals'], rollcall_num + '.csv'), index=False)
    votes_df.to_csv(os.path.join(paths['votes'], rollcall_num + '.csv'), index=False)

# data_to_csv(random.choice(ROLLCALL_NUMS))
t0 = time.time_ns()
for n in ROLLCALL_NUMS:
    data_to_csv(n)
print(f"Wrote data in {(time.time_ns() - t0) * 10**-6 : .3f} ms")


# In[133]:


def read_data(rollcall_num):
    """
    Returns DataFrames of metadata, vote-totals, and votes of rollcall_num
    
    Parameter rollcall_num: Voting session number
    Precondition: rollcall_num is a str in ROLLCALL_NUMS
    """
    assert type(rollcall_num) == str and rollcall_num in ROLLCALL_NUMS
    metadata_df = pd.read_csv(os.path.join(paths['metadata'], rollcall_num + '.csv'))
    vote_totals_df = pd.read_csv(os.path.join(paths['vote-totals'], rollcall_num + '.csv'))
    votes_df = pd.read_csv(os.path.join(paths['votes'], rollcall_num + '.csv'))
    return (metadata_df, vote_totals_df, votes_df)

t0 = time.time_ns()
for n in ROLLCALL_NUMS:
    (metadata_df, vote_totals_df, votes_df) = read_data(n)
    display(metadata_df)
    display(vote_totals_df)
print(f"Read data in {(time.time_ns() - t0) * 10**-6 : .3f} ms")


# In[ ]:




