# -*- coding:utf-8 -*-
# Author:harry
# Editdate:2016-09-1
# example to show how to get history data from wind
from WindPy import *
from datetime import *
import csv
from pymongo import MongoClient

#start wind
w.start()
print(w.isconnected())



#ȡȫ��A �ɹ�Ʊ���롢������Ϣ
#wind_code              , wind���� 0
#sec_name               , ��Ʊ������ 1
#close_price            , �������̼� 2
#total_market_value	    , ����ֵ 3
#mkt_cap_float			, ������ֵ 4
#trade_status			, ����״̬ 5
#last_trade_day			, �������̼����� 6
#ipo_day				, �������� 7
#province				, ʡ�� 8
#sec_type				, ֤ȯ���� 9
#listing_board			, ���а� 10
#exchange				, ���н����� 11				
print ("start to query all mainland stock list")

wset_listed_stocks=w.wset("listedsecuritygeneralview","sectorid=a001010100000000")
print(wset_listed_stocks)
with open("win_code.csv","w",newline="") as datacsv:
    csvwriter = csv.writer(datacsv,dialect = ("excel"))
    csvwriter.writerow(wset_listed_stocks.Data[0])
    
with open("sec_name.csv","w",newline="") as datacsv:
    csvwriter = csv.writer(datacsv,dialect = ("excel"))
    csvwriter.writerow(wset_listed_stocks.Data[1])    
    
with open("ipo_day.csv","w",newline="") as datacsv:
    csvwriter = csv.writer(datacsv,dialect = ("excel"))
    csvwriter.writerow(wset_listed_stocks.Data[7])  
    
client = MongoClient("localhost", 27017)    #�������ݿ������
client.ml_security_table                    #test���ݿ��û�����������֤
db = client.ml_security_table               #��ȡtest���ݿ�����

#####################################################################################################
for item in wset_listed_stocks.Data[0]:
    db.stock.insert_one({"sec_code":item})       #��test���ݿ��µ�stock��collection������һ����¼   
   

print ("query data from win done")