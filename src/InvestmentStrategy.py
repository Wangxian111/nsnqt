# coding: utf-8

# In[25]:

import numpy as np
import pandas as pd
import tushare as ts
import matplotlib.pyplot as plt
#import seaborn as sns
get_ipython().magic('matplotlib inline')
import time,datetime

window_short = 20
window_long = 120
SD = 0.05

# 获取指定股票对应的数据并按日期升序排序
def import_data( stock, start, end ):
    #df = ts.get_h_data(stock, start=start, end=end).sort_index(ascending=True)
    df = pd.read_csv('d:/Trade/DB/' + str(stock) + '.csv', parse_dates=['date'])
    #df = stock_data[['code', 'date', 'open', 'close', 'change']]
    #df = stock_data[['Date', 'Open', 'High', 'Low', 'Close','Volumn', 'Adj Close']]
    
    #df.head(10);
    df['change'] = (df['close'] - df['close'].shift(1))/df['close'].shift(1)
    df['code'] = stock
    #print(df.head(10));
    print(df.tail());
    return df;

# 判断交易天数,如果不满足就不运行程序
def stock_trading_days(stock_data, trading_days=500):
    """
    :param stock_data: 股票数据集
    :param trading_days: 交易天数下限，默认为500
    :return: 判断股票的交易天数是否大于trading_days,如果不满足就退出程序
    """
    if len(stock_data) < trading_days:
        print ('股票上市时间过短,不运行策略')
        exit(1)
        
# 简单均线策略,输出每天的仓位
def analyze_data( df ):
    df['short_window'] = pd.rolling_mean(df.close,window_short)
    df['long_window'] = pd.rolling_mean(df.close,window_long)
    df['s-l'] = df['short_window'] - df['long_window']
    
    #df['Regime'] = np.where(df['s-l'] > df['long_window'] * SD, 1, 0)
    #df['Regime'].value_counts()
    
    df['position'] = np.where(df['s-l'] > df['long_window'] * SD, 1, 0)
    df['position'].value_counts()
    
    #df.ix[df['Regime'] > df['Regime'].shift(1), 'position'] = 1
    #df.ix[df['Regime'] < df['Regime'].shift(1), 'position'] = 0
    
    df['position'].fillna(method='ffill', inplace=True)
    df['position'].fillna(0, inplace=True)
                
    #print(df['Regime'].value_counts());
    print(df.tail());
    #df['Regime'].plot(grid=False, lw=1.5, figsize=(12,8))
    #plt.ylim((-0.1,1.1))
    return;

def trade_result( df ):
    df['Market'] = np.log(df['close'] / df['close'].shift(1))
    df['Strategy'] = df['Regime'].shift(1) * df['Market']
    print(df[['Market', 'Strategy', 'Regime']].tail())
    df[['Market', 'Strategy']].cumsum().apply(np.exp).plot(grid=False, figsize=(12,8))
    return;
        
# 根据每日仓位计算总资产的日收益率
def account(df, slippage=1.0 / 1000, commision_rate=2.0 / 1000):
    """
    :param df: 股票账户数据集
    :param slippage: 买卖滑点 默认为1.0 / 1000
    :param commision_rate: 手续费 默认为2.0 / 1000
    :return: 返回账户资产的日收益率和日累计收益率的数据集
    """
    df.ix[0, 'capital_rtn'] = 0
    # 当加仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 昨天的position在今天涨幅 + 今天开盘新买入的position在今天的涨幅(扣除手续费)
    df.ix[df['position'] > df['position'].shift(1), 'capital_rtn'] = (df['close'] / df['open'] - 1) * (
        1 - slippage - commision_rate) * (df['position'] - df['position'].shift(1)) + df['change'] * df[
        'position'].shift(1)
    # 当减仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 今天开盘卖出的positipn在今天的涨幅(扣除手续费) + 还剩的position在今天的涨幅
    df.ix[df['position'] < df['position'].shift(1), 'capital_rtn'] = (df['open'] / df['close'].shift(1) - 1) * (
        1 - slippage - commision_rate) * (df['position'].shift(1) - df['position']) + df['change'] * df['position']
    # 当仓位不变时,当天的capital_rtn是当天的change * position
    df.ix[df['position'] == df['position'].shift(1), 'capital_rtn'] = df['change'] * df['position']

    print(df.tail())
    return df

# 选取时间段,来计算资金曲线.
def select_date_range(stock_data, start_date=pd.to_datetime('20060101'), trading_days=250):
    """
    :param stock_data:
    :param start_date:
    :param trading_days:
    :return: 对于一个指定的股票,计算它回测资金曲线的时候,从它上市交易了trading_days天之后才开始计算,并且最早不早于start_date.
    """
    stock_data = stock_data[trading_days:]
    #stock_data = stock_data[datetime.datetime.strptime(stock_data['date'], '%Y%m%d') >= start_date]
    #stock_data.reset_index(inplace=True, drop=True)
    return stock_data

# 计算最近250天的股票,策略累计涨跌幅.以及每年（月，周）股票和策略收益
def period_return(stock_data, days=250, if_print=False):
    """
    :param stock_data: 包含日期、股票涨跌幅和总资产涨跌幅的数据集
    :param days: 最近250天
    :return: 输出最近250天的股票和策略累计涨跌幅以及每年的股票收益和策略收益
    """
    df = stock_data[['code', 'date', 'change', 'capital_rtn']]

    # 计算每一年(月,周)股票,资金曲线的收益
    year_rtn = df.set_index('date')[['change', 'capital_rtn']].resample('A', how=lambda x: (x + 1.0).prod() - 1.0)
    month_rtn = df.set_index('date')[['change', 'capital_rtn']].resample('M', how=lambda x: (x + 1.0).prod() - 1.0)
    week_rtn = df.set_index('date')[['change', 'capital_rtn']].resample('W', how=lambda x: (x + 1.0).prod() - 1.0)

    year_rtn.dropna(inplace=True)
    month_rtn.dropna(inplace=True)
    week_rtn.dropna(inplace=True)

    # 计算策略的年（月，周）胜率
    yearly_win_rate = len(year_rtn[year_rtn['capital_rtn'] > 0]) / len(year_rtn[year_rtn['capital_rtn'] != 0])
    monthly_win_rate = len(month_rtn[month_rtn['capital_rtn'] > 0]) / len(month_rtn[month_rtn['capital_rtn'] != 0])
    weekly_win_rate = len(week_rtn[week_rtn['capital_rtn'] > 0]) / len(week_rtn[week_rtn['capital_rtn'] != 0])

    # 计算股票的年（月，周）胜率
    yearly_win_rates = len(year_rtn[year_rtn['change'] > 0]) / len(year_rtn[year_rtn['change'] != 0])
    monthly_win_rates = len(month_rtn[month_rtn['change'] > 0]) / len(month_rtn[month_rtn['change'] != 0])
    weekly_win_rates = len(week_rtn[week_rtn['change'] > 0]) / len(week_rtn[week_rtn['change'] != 0])

    # 计算最近days的累计涨幅
    df = df.iloc[-days:]
    recent_rtn_line = df[['date']]
    recent_rtn_line['stock_rtn_line'] = (df['change'] + 1).cumprod() - 1
    recent_rtn_line['strategy_rtn_line'] = (df['capital_rtn'] + 1).cumprod() - 1
    recent_rtn_line.reset_index(drop=True, inplace=True)

    # 输出
    if if_print:
        print ('\n最近' + str(days) + '天股票和策略的累计涨幅:')
        print (recent_rtn_line)
        print ('\n过去每一年股票和策略的收益:')
        print (year_rtn)
        print ('策略年胜率为：%f' % yearly_win_rate)
        print ('股票年胜率为：%f' % yearly_win_rates)
        print ('\n过去每一月股票和策略的收益:')
        print (month_rtn)
        print ('策略月胜率为：%f' % monthly_win_rate)
        print ('股票月胜率为：%f' % monthly_win_rates)
        print ('\n过去每一周股票和策略的收益:')
        print (week_rtn)
        print ('策略周胜率为：%f' % weekly_win_rate)
        print ('股票周胜率为：%f' % weekly_win_rates)

    return year_rtn, month_rtn, week_rtn, recent_rtn_line


# 根据每次买入的结果,计算相关指标
def trade_describe(df):
    """
    :param df: 包含日期、仓位和总资产的数据集
    :return: 输出账户交易各项指标
    """
    # 计算资金曲线
    df['capital'] = (df['capital_rtn'] + 1).cumprod()
    # 记录买入或者加仓时的日期和初始资产
    df.ix[df['position'] > df['position'].shift(1), 'start_date'] = df['date']
    df.ix[df['position'] > df['position'].shift(1), 'start_capital'] = df['capital'].shift(1)
    df.ix[df['position'] > df['position'].shift(1), 'start_stock'] = df['close'].shift(1)
    # 记录卖出时的日期和当天的资产
    df.ix[df['position'] < df['position'].shift(1), 'end_date'] = df['date']
    df.ix[df['position'] < df['position'].shift(1), 'end_capital'] = df['capital']
    df.ix[df['position'] < df['position'].shift(1), 'end_stock'] = df['close']
    # 将买卖当天的信息合并成一个dataframe
    df_temp = df[df['start_date'].notnull() | df['end_date'].notnull()]

    df_temp['end_date'] = df_temp['end_date'].shift(-1)
    df_temp['end_capital'] = df_temp['end_capital'].shift(-1)
    df_temp['end_stock'] = df_temp['end_stock'].shift(-1)

    # 构建账户交易情况dataframe：'hold_time'持有天数，'trade_return'该次交易盈亏,'stock_return'同期股票涨跌幅
    trade = df_temp.ix[df_temp['end_date'].notnull(), ['start_date', 'start_capital', 'start_stock',
                                                       'end_date', 'end_capital', 'end_stock']]
    trade.reset_index(drop=True, inplace=True)
    trade['hold_time'] = (trade['end_date'] - trade['start_date']).dt.days
    trade['trade_return'] = trade['end_capital'] / trade['start_capital'] - 1
    trade['stock_return'] = trade['end_stock'] / trade['start_stock'] - 1

    trade_num = len(trade)  # 计算交易次数
    max_holdtime = trade['hold_time'].max()  # 计算最长持有天数
    average_change = trade['trade_return'].mean()  # 计算每次平均涨幅
    max_gain = trade['trade_return'].max()  # 计算单笔最大盈利
    max_loss = trade['trade_return'].min()  # 计算单笔最大亏损
    total_years = (trade['end_date'].iloc[-1] - trade['start_date'].iloc[0]).days / 365
    trade_per_year = trade_num / total_years  # 计算年均买卖次数

    # 计算连续盈利亏损的次数
    trade.ix[trade['trade_return'] > 0, 'gain'] = 1
    trade.ix[trade['trade_return'] < 0, 'gain'] = 0
    trade['gain'].fillna(method='ffill', inplace=True)
    # 根据gain这一列计算连续盈利亏损的次数
    rtn_list = list(trade['gain'])
    successive_gain_list = []
    num = 1
    for i in range(len(rtn_list)):
        if i == 0:
            successive_gain_list.append(num)
        else:
            if (rtn_list[i] == rtn_list[i - 1] == 1) or (rtn_list[i] == rtn_list[i - 1] == 0):
                num += 1
            else:
                num = 1
            successive_gain_list.append(num)
    # 将计算结果赋给新的一列'successive_gain'
    trade['successive_gain'] = successive_gain_list
    # 分别在盈利和亏损的两个dataframe里按照'successive_gain'的值排序并取最大值
    max_successive_gain =         trade[trade['gain'] == 1].sort_values(by='successive_gain', ascending=False)['successive_gain'].iloc[0]
    max_successive_loss =         trade[trade['gain'] == 0].sort_values(by='successive_gain', ascending=False)['successive_gain'].iloc[0]

    #  输出账户交易各项指标
    print ('\n==============每笔交易收益率及同期股票涨跌幅===============')
    print (trade[['start_date', 'end_date', 'trade_return', 'stock_return']])
    print ('\n====================账户交易的各项指标=====================')
    print ('交易次数为：%d   最长持有天数为：%d' % (trade_num, max_holdtime))
    print ('每次平均涨幅为：%f' % average_change)
    print ('单次最大盈利为：%f  单次最大亏损为：%f' % (max_gain, max_loss))
    print ('年均买卖次数为：%f' % trade_per_year)
    print ('最大连续盈利次数为：%d  最大连续亏损次数为：%d' % (max_successive_gain, max_successive_loss))
    return trade


# 计算年化收益率函数
def annual_return(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出在回测期间的年化收益率
    """
    # 将数据序列合并成dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})

    # 计算年化收益率
    annual = (df['capital'].iloc[-1] / df['capital'].iloc[0]) ** (250 / len(df)) - 1

    print (annual)


# 计算最大回撤函数
def max_drawdown(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出最大回撤及开始日期和结束日期
    """
    # 将数据序列合并为一个dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})

    df['max2here'] = pd.expanding_max(df['capital'])  # 计算当日之前的账户最大价值
    df['dd2here'] = df['capital'] / df['max2here'] - 1  # 计算当日的回撤
    #  计算最大回撤和结束时间
    temp = df.sort_values(by='dd2here').iloc[0][['date', 'dd2here']]
    max_dd = temp['dd2here']
    end_date = temp['date'].strftime('%Y-%m-%d')
    # 计算开始时间
    df = df[df['date'] <= end_date]
    start_date = df.sort_values(by='capital', ascending=False).iloc[0]['date'].strftime('%Y-%m-%d')

    print ('最大回撤为：%f, 开始日期：%s, 结束日期：%s' % (max_dd, start_date, end_date))

# =====读取数据
# 读取数据
#stock_data = get_stock_data('stocktest')
stock_data = import_data('stocktest','2010-01-01','2015-04-23')
# 判断交易天数是否满足要求
stock_trading_days(stock_data, trading_days=500)
# 简单均线策略,输出每天的仓位
analyze_data(stock_data)

# 根据每日仓位计算总资产的日收益率
account(stock_data)

# 选取时间段
return_data = select_date_range(stock_data, start_date=pd.to_datetime('20060101'), trading_days=250)
return_data['capital'] = (return_data['capital_rtn'] + 1).cumprod()

# =====根据策略结果,计算评价指标
# 计算最近250天的股票,策略累计涨跌幅.以及每年（月，周）股票和策略收益
period_return(return_data, days=250, if_print=True)

# 根据每次买卖的结果,计算相关指标
trade_describe(stock_data)

# =====根据资金曲线,计算相关评价指标
date_line = list(return_data['date'])
capital_line = list(return_data['capital'])
stock_line = list(return_data['close'])
print ('\n股票的年化收益为：')
annual_return(date_line, stock_line)
print ('策略的年化收益为：')
annual_return(date_line, capital_line)
print ('\n股票')
max_drawdown(date_line, stock_line)
print ('策略')
max_drawdown(date_line, capital_line)





# In[ ]:




# In[ ]:



