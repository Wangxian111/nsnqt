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



#��������ָ��
#wind_code/sec_code     , wind���� 0
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
print ("start to query HSCEI.HI")

wset_listed_stocks = w.wsd("HSCEI.HI", "pre_close,open,high,low,close,volume,amt,turn,pe_ttm,pb_lf", "1994-09-01", "2016-09-17", "TradingCalendar=HKEX;Currency=CNY")

print("query data done")

print("start to save to database")
client = MongoClient("localhost", 27017)    #�������ݿ������
db = client.hk_index               			#��ȡ���ݿ�����

#db.hscei_hi.insert_one({"date":wset_listed_stocks.Times[0]}) 
print(wset_listed_stocks)
#####################################################################################################


for j in range(len(wset_listed_stocks.Data[0])):
    db.hscei_hi.update_one({"date":wset_listed_stocks.Times[j]},
        {"$set":{ 
            "pre_close":wset_listed_stocks.Data[0][j],
            "open":wset_listed_stocks.Data[1][j],
            "high":wset_listed_stocks.Data[2][j],
            "low":wset_listed_stocks.Data[3][j],
            "close":wset_listed_stocks.Data[4][j],
            "volume":wset_listed_stocks.Data[5][j],
            "amt":wset_listed_stocks.Data[6][j],
            "turn":wset_listed_stocks.Data[7][j],
            "pe_ttm":wset_listed_stocks.Data[8][j],
            "pb_lf":wset_listed_stocks.Data[9][j] }})   



print ("save to database done")