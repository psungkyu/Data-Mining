#-*- coding: utf-8 -*-

#**************************** Libraries **************************** 
import datetime
import time
import sys
import MeCab
import operator
from pymongo import MongoClient
from bson import ObjectId
from itertools import combinations
#*******************************************************************


#************************* MongoDB Account ************************* 
DBname = "**********"#ID
conn = MongoClient('********.******.**.**')#url
db = conn[DBname]
db.authenticate(DBname, DBname)
#*******************************************************************


#**************************** Variables **************************** 
stop_word = {}
transaction = db.news.count()
min_sup = transaction * 0.1
#*******************************************************************


# Print the menu script
def printMenu() :
    print "0. CopyData"
    print "1. Morph"
    print "2. print morphs"
    print "3. print wordset"
    print "4. frequent item set"
    print "5. association rule"
    print "6. strong association rule"


# Make stop word
def make_stop_word() :
    f = open("wordList.txt", 'r')
    while True :
        line = f.readline()
        if not line : break
        stop_word[line.strip('\n')] = line.strip('\n')
    f.close()


# Find the morph which is a word composing news article 
def morphing(content) :
    t = MeCab.Tagger('-d/usr/local/lib/mecab/dic/mecab-ko-dic')#use MeCab library
    nodes = t.parseToNode(content.encode('utf-8'))
    MorpList = []
    while nodes :
        if nodes.feature[0] == 'N' and nodes.feature[1] == 'N' :
            w = nodes.surface
            if not w in stop_word :
                try :
                    w = w.encode('utf-8')
                    MorpList.append(w)
                except :
                    pass
        nodes = nodes.next
    return MorpList


# Make 'news_freq' which contains key
def p0() :
    col1 = db['news']
    col2 = db['news_freq']
    col2.drop()
    for doc in col1.find() :
        contentDic = {}
        for key in doc.keys() :
            if key != "_id" :
                contentDic[key] = doc[key] 
        col2.insert(contentDic)


# Store the data into MongoDB
def p1() :
    for doc in db['news_freq'].find() :
        doc['morph'] = morphing(doc['content'])
        db['news_freq'].update({"_id":doc['_id']}, doc)


# Print morphs using url
def p2(url) :
    theString = []
    for doc in db['news_freq'].find() :
        if doc['url'] == url :               
            for thing in doc['morph'] :
                thing = thing.encode('utf-8')
                print thing


# Make the wordset in which there's no same elements 
def p3() :
    col1 = db['news_freq']
    col2 = db['news_wordset']
    col2.drop()
    
    for doc in col1.find() :
        new_doc = {}
        new_set = set()
        for w in doc['morph'] :
            new_set.add(w.encode('utf-8'))
        new_doc['word_set'] = list(new_set)
        new_doc['url'] = doc['url']
        col2.insert(new_doc)


# Print elements of wordset
def p4(url) :
    theString = []
    for doc in db['news_wordset'].find() :
        if doc['url'] == url :
            for thing in doc['word_set'] :
                thing = thing.encode('utf-8')
                print thing


# Find the 1 frequent itemset whose the value of numbers is beyond min_sup 
def find_frequent_1_itemset() :
    
    col1 = db['news_freq']
    col2 = db['candidate_L1']
    col3 = db['news_wordset']
    col2.drop()

    #make C1
    new_dic = {}
    new_wordset = set()
    L = list()
    for doc in col3.find() :
        for w in doc['word_set'] :
            w = w.encode('utf-8')
            new_wordset.add(w)

            #count numbers
            if w in new_dic : 
                new_dic[w] += 1
            else :
                new_dic[w] = int(1)
    
    #make L1 set without count
    new_wordlist = list(new_wordset)

    for w in new_wordlist :
            
        if new_dic[w] > min_sup or new_dic[w] == min_sup :
            new_doc = {}
            new_doc['item_set'] = w
            L.append(w)
            new_doc['support'] = new_dic[w]
            col2.insert(new_doc)
                 
    return L


# Find the 2 frequent itemset whose the value of numbers is beyond min_sup 
def find_frequent_2_itemset(Ck) :

    col2 = db['candidate_L2']
    col3 = db['news_wordset']
    col2.drop()

    #make C2
    new_dic = {}
    new_wordset = set()
    L = list()
   
    for i in range(len(Ck)) :
        cnt = 0
        val1 = Ck[i][0]
        val2 = Ck[i][1] 
        
        for doc in col3.find() :
            
            if val1 in doc['word_set'] :
                if val2 in doc['word_set'] :
                    cnt += 1

        if cnt > min_sup or cnt == min_sup :
            tmp = list()
            tmp.append(val1)
            tmp.append(val2)
            
            new_doc = {}
            new_doc['item_set'] = tmp
            new_doc['support'] = cnt
            col2.insert(new_doc)
            L.append(tmp)

    return L


# Find the 3 frequent itemset whose the value of numbers is beyond min_sup 
def find_frequent_3_itemset(Ck) :

    col1 = db['candidate_L3']
    col2 = db['news_wordset']
    col1.drop()

    #make C3
    new_dic = {}
    new_wordset = set()
    L = list()

    for i in range(len(Ck)) :
        val1 = Ck[i][0]
        val2 = Ck[i][1]
        val3 = Ck[i][2]

        for doc in col2.find() :
            if val1 in doc['word_set'] :
                if val2 in doc['word_set'] :
                    if val3 in doc['word_set'] :
                        cnt += 1
       
        if cnt > min_sup or cnt == min_sup :
            tmp = list()
            tmp.append(val1)
            tmp.append(val2)
            tmp.append(val3)
 
            new_doc = {}
            new_doc['item_set'] = tmp
            new_doc['support'] = cnt
            col1.insert(new_doc)


# remove the key whose value is lower than min_sup
def has_infrequent_subset(c, L_prior) :
    
    l = list(c)
    
    #make subset of c
    for val in l :
        
        if len(l) == 2 :
            if not val in L_prior :
                return True
            else :
                continue

        else : 
            tmp = list(l)
            tmp.remove(val)
            
            if not tmp in L_prior :
                return True
            else : 
                continue
    
    return False


# apply apriori alg
def apriori_gen(L_prior, length) :
    
    Ck = list()
    L = list(L_prior)
    cnt = 0
    for i in range(0, len(L) - 1) :
        s1 = set()

        if length == 2 :
            s1.add(L[i])
        else :
            s1 = set(L[i])

        for j in range(i+1, len(L)) :
            s2 = set()

            if length == 2 :
                s2.add(L[j])
            else :
                s2 = set(L[j])
                
            if len(s1 - s2) == 1 : 
                c = s1 | s2
                
                if list(c) in Ck :
                    continue 

                else :
                    if len(c) == length :
                        if has_infrequent_subset(c, L_prior) :
                            continue
                        else : 
                            Ck.append(list(c))
    return Ck


# Make the dataset
def p5(length) :
    
    if length == 1 :
        find_frequent_1_itemset()
    
    elif length == 2 :
        L_prior = find_frequent_1_itemset()
        Ck = apriori_gen(L_prior, 2)
        find_frequent_2_itemset(Ck)

    elif length == 3 :
        L_prior = find_frequent_1_itemset()
        Ck = apriori_gen(L_prior, 2)
        L_prior = find_frequent_2_itemset(Ck)
        Ck = apriori_gen(L_prior, 3)
        find_frequent_3_itemset(Ck)


# Print the wordset
def p6(length) :

    if length == 1 :
        print('cannot do this')
        
    elif length == 2 :
        col1 = db['candidate_L1']
        col2 = db['candidate_L2']
        
        for doc in col2.find() :
            s_cnt = doc['support']
            val1 = doc['item_set'][0]
            val2 = doc['item_set'][1]

            if col1.find({'item_set' : val1}) :
                doc2 = col1.find_one({'item_set' : val1})
                m_cnt = doc2['support']
                
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s =>%s\t%f' %(val1, val2, conf))
               
            if col1.find({'item_set' : val2}) :
                doc2 = col1.find_one({'item_set' : val2})
                m_cnt = doc2['support']

                conf = s_cnt / m_cnt
                if conf >= 0.5 :
                    print('%s =>%s\t%f' %(val1, val2, conf))
                    
    elif length == 3 :
        col1 = db['candidate_L2']
        col2 = db['candidate_L3']
        col3 = db['candidate_L1']

        for doc in col2.find() :
        
            s_cnt = doc['support']
            val1 = doc['item_set'][0]
            val2 = doc['item_set'][1]
            val3 = doc['item_set'][2]
            val4 = [doc['item_set'][0], doc['item_set'][1]]
            val5 = [doc['item_set'][1], doc['item_set'][2]]
            val6 = [doc['item_set'][2], doc['item_set'][0]]
            
            
            if col3.find({'item_set' : val1}) :
                doc2 = col3.find_one({'item_set' : val1})
                m_cnt = doc2['support']
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s =>%s, %s\t%f' %(val1, val2, val3, conf))

            if col3.find({'item_set' : val2}) :
                doc2 = col3.find_one({'item_set' : val2})
                m_cnt = doc2['support']
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s =>%s, %s\t%f' %(val2, val1, val3, conf))

            if col3.find({'item_set' : val3}) :
                doc2 = col3.find_one({'item_set' : val3})
                m_cnt = doc2['support']
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s =>%s, %s\t%f' %(val3, val2, val1, conf))
            
            if col1.find({'item_set' : val4}) :
                doc2 = col1.find_one({'item_set' : val4})
                m_cnt = doc2['support']
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s, %s =>%s\t%f' %(val1, val2, val3, conf))

            if col1.find({'item_set' : val5}) :
                doc2 = col1.find_one({'item_set' : val5})
                m_cnt = doc2['support']
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s, %s =>%s\t%f' %(val2, val3, val1, conf))
            
            if col1.find({'item_set' : val6}) :
                doc2 = col1.find_one({'item_set' : [val1, val3]})
                m_cnt = doc2['support']
                conf = float(s_cnt)/float(m_cnt)
                if conf >= 0.5 :
                    print('%s, %s =>%s\t%f' %(val1, val3, val2, conf))


# main
if __name__ == "__main__" :
    make_stop_word()
    printMenu()
    selector = input()

    print(transaction)

    if selector == 0:
        p0()

    elif selector == 1:
        p1()
        p3()

    elif selector == 2:
        url = str(raw_input("input news url:"))
        p2(url)
    
    elif selector == 3:
        url = str(raw_input("input news url:"))
        p4(url)
    
    elif selector == 4:
        length = int(raw_input("input length of the frequent item:"))
        p5(length)
    
    elif selector == 5:
        length = int(raw_input("input length of the frequent item:"))
        p5(length)
    
    elif selector == 6:
        length = int(raw_input("input length of the frequent item:"))
        p6(length)

        
