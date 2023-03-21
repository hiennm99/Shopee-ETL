import pandas as pd
import regex as re
import numpy as np
import requests
import json
import random
import time
from time import sleep
import concurrent.futures
from sqlalchemy import create_engine
import configparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def connect_MySQL():
    #MySQL connection information
    config=configparser.ConfigParser()
    config.read('config.ini')
    
    mysql_engine=create_engine(f"{config['MySQL']['driver']}://{config['MySQL']['username']}:{config['MySQL']['password']}@{config['MySQL']['host']}/{config['MySQL']['database']}") 
    return mysql_engine

def connect_AWSRedshift():
    #AWSRedshift connection information
    config=configparser.ConfigParser()
    config.read('config.ini')
  
    AWSRedshift_engine=create_engine(f"{config['AWSRedshift']['driver']}://{config['AWSRedshift']['username']}:{config['AWSRedshift']['password']}@{config['AWSRedshift']['host']}:{config['AWSRedshift']['port']}/{config['AWSRedshift']['database']}")
    return AWSRedshift_engine

def Open_Multi_Driver(drivers_1,n):
    for i in range(n):
        driver=webdriver.Chrome('chromedriver.exe',options=chrome_options)
        sleep(0.5)
        drivers_1.append(driver)
        
def Get_List_ID(driver,url):
    #Get list link of items
    print('-----Start crawl page-----')
    driver.get(url)
    sleep(random.randint(8,10))
    for i in range(28,49):
        item_elem=driver.find_element(By.XPATH,f'/html/head/script[{i}]')
        item=item_elem.get_attribute('innerHTML')
        y=item.split('"url":"')
        URL=y[1].split('","productID"')[0]
        product_URLs.append(URL)
    sleep(2)
    
def Get_Multi_Pages():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(Get_List_ID,drivers_1,page_urls)


def Get_API_Information(link):
    print(link)
    sleep(random.randint(2,4))
    #Retrieve productID and sellerID from link
    temp1=link.split('?')
    temp2=temp1[0].split('i.')
    temp=temp2[1].split('.')
    shopID=temp[0] #ShopID
    productID=temp[1] #ProductID
    product_data=[]
    api_URL= f'https://shopee.vn/api/v4/item/get?itemid={productID}&shopid={shopID}'
    payload={}
    headers = {
    'authority': 'shopee.vn',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
    'content-type': 'application/json',
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'iOS app iPhone Shopee appver=29030 language=vi app_type=1',
    'x-api-source': 'pc',
    'x-kl-ajax-request': 'Ajax_Request',
    'x-requested-with': 'XMLHttpRequest',
    'x-shopee-language': 'en'
    }  
    response = requests.get(api_URL, headers=headers, data=payload)
    item_raw=response.json()
    product_data=item_raw['data']

    ## Get master information
    master_={}
    name=product_data['name']                               #Name
    #Category
    category=''
    for cat in product_data['fe_categories']:
        category=category+cat['display_name']+' > '
        category=category[0:-2]
    location=product_data['shop_location']                  #Location
    brand=product_data['brand']                             #Brand
    
    master_={
        'Product_ID':productID,
        'Product_Name':name,
        'Brand':brand,
        'Category':category,
        'Location':location,
        'Shop_ID':shopID
    }
    Master_Product.append(master_)
    
    
    ## Get marketing information
    marketing_={}                                 
    averageScore=product_data['item_rating']['rating_star'] #Rating star
    countReviews=product_data['cmt_count']                  #Count reviews
    soldItems=product_data['historical_sold']               #Sold items
 
    marketing_={
        'Product_ID':productID,
        'Average_Score':averageScore,
        'Count_Reviews':countReviews,
        'Sold_Items':soldItems
    }
    Marketing.append(marketing_)
    ##Get detail information from API
    for i in range(len(product_data['models'])):
        detail_={}
        skuID=product_data['models'][i]['modelid']
        skuName=product_data['models'][i]['name']
        skuID=product_data['models'][i]['modelid']
        price=product_data['models'][i]['price']
        inStock=product_data['models'][i]['normal_stock']

        if inStock !=0:
            isActive=1
        else:
            isActive=0
        
        detail_={
            'Product_ID':productID,
            'SKU_ID':skuID,
            'SKU_Name':skuName,
            'Price':price,
            'In_Stock':inStock,
            'Is_Active':isActive,
        }
        DetailAPI.append(detail_)

def Get_Multi_Product_API():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(Get_API_Information,product_URLs)
        

def Create_DataFrame():
    
    df_MasterProduct=pd.DataFrame(data=Master_Product)
    df_Marketing=pd.DataFrame(data=Marketing)
    df_ProductDetail=pd.DataFrame(data=DetailAPI)
    # df_Seller=pd.DataFrame(data=Seller,columns=['Shop ID','Shop name','Item count','Rating star','Response rate','Cancel rate','Follower count'])
    print('-------Create DataFrame successfully-------')
    
    Clean_Master_Product(df_MasterProduct)
    Clean_Product_Details(df_ProductDetail)
    Clean_Marketing(df_Marketing)
    # Clean_Seller(df_Seller)
    print('-------Clean DataFrame successfully-------')
    
    # Dataframe to Excel 
    df_MasterProduct.to_excel('Master Product.xlsx')
    df_ProductDetail.to_excel('Product Detail.xlsx')
    df_Marketing.to_excel('Marketing.xlsx')
    # df_Seller.to_excel('Seller.xlsx')
    print('-------Insert data to excel file successfully-------')
    
    #DataFrame to MySQL
    mysql_engine=connect_MySQL()
    df_MasterProduct.to_sql('master product',con=mysql_engine,if_exists='append',index=False)
    df_ProductDetail.to_sql('product detail',con=mysql_engine,if_exists='append',index=False)
    df_Marketing.to_sql('marketing',con=mysql_engine,if_exists='append',index=False)
    print('-------Insert data to MySQL successfully-------')
    
    # #DataFrame to AWS Redshift
    # redshift_engine=connect_AWSRedshift()
    # df_MasterProduct.to_sql('master product',con=redshift_engine,if_exists='append',index=False)
    # df_ProductDetail.to_sql('product detail',con=redshift_engine,if_exists='append',index=False)
    # df_Marketing.to_sql('marketing',con=redshift_engine,if_exists='append',index=False)
    # print('-------Insert data to AWS Redshift successfully-------')
    

def Clean_Product_Details(df):
    df['Product_ID']=df['Product_ID'].astype(np.int64)
    df['SKU_ID']=df['SKU_ID'].astype(np.int64)
    df['Price']=df['Price'].astype(np.int64)
    df['Price']=df['Price']/100000
     
def Clean_Marketing(df):
    df['Average_Score']=df['Average_Score'].astype(np.float64)
    df['Average_Score']=round(df['Average_Score'],2)

def Clean_Master_Product(df):
    df['Product_ID']=df['Product_ID'].astype(np.int64)
    df['Shop_ID']=df['Shop_ID'].astype(np.int64)

def Clean_Seller(df):
    df['Shop_ID']=df['Shop_ID'].astype(np.int64)

if __name__ == "__main__":
    
    start_time=time.perf_counter()
    
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    product_URLs=[]
    Master_Product=list()
    Marketing=list()
    Seller=list()
    DetailAPI=[]
    
    page_urls=[]
    for i in range(1,2):
        url=f'https://shopee.vn/search?category=11036030&keyword=%C4%91i%E1%BB%87n%20tho%E1%BA%A1i%20di%20%C4%91%E1%BB%99ng&page={i}'
        page_urls.append(url)
        

    drivers_1=[]
    Open_Multi_Driver(drivers_1,n=2)
    Get_Multi_Pages()
    
    Get_Multi_Product_API()
    Create_DataFrame()

    end_time=time.perf_counter()
    print(f'Executive time {end_time-start_time}')