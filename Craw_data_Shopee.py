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
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

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

def Open_Multi_Driver2(drivers_2,n):
    for i in range(n):
        driver=webdriver.Chrome('chromedriver.exe',options=chrome_options)
        sleep(0.5)
        drivers_2.append(driver)
         
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
    payload={
    }
    headers = {
    'authority': 'shopee.vn',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
    'content-type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'x-kl-ajax-request': 'Ajax_Request',
    'x-requested-with': 'XMLHttpRequest',
    'x-shopee-language': 'vi'
    }   
    response = requests.get(api_URL, headers=headers, data=payload)
    item_raw=response.json()
    product_data=item_raw['data']

    ## Get master information
    master_=[]
    name=product_data['name']                               #Name
    #Category
    category=''
    for cat in product_data['fe_categories']:
        category=category+cat['display_name']+' > '
        category=category[0:-2]
    location=product_data['shop_location']                  #Location
    brand=product_data['brand']                             #Brand
    
    master_.append(productID)
    master_.append(name)
    master_.append(brand)
    master_.append(category)
    master_.append(location)
    master_.append(shopID)
    Master_Product.append(master_)
    
    
    ## Get marketing information
    marketing_=[]                                   
    averageScore=product_data['item_rating']['rating_star'] #Rating star
    countReviews=product_data['cmt_count']                  #Count reviews
    soldItems=product_data['historical_sold']               #Sold items

    marketing_.append(productID)
    marketing_.append(averageScore)
    marketing_.append(countReviews)
    marketing_.append(soldItems)
    Marketing.append(marketing_)
    
    ##Get detail information from API
    if len(product_data['models'])==1:
        detail_api=[]
        
        skuID=product_data['models'][0]['modelid']
        skuName="Default"
        
        detail_api.append(productID)
        detail_api.append(skuID)
        detail_api.append(skuName)
        DetailAPI.append(detail_api)
    elif len(product_data['models'])!=1:
        for i in range(len(product_data['models'])):
            detail_api=[]
            
            skuID=product_data['models'][i]['modelid']
            skuName=product_data['models'][i]['name']
            
            detail_api.append(productID)
            detail_api.append(skuID)
            detail_api.append(skuName)
            DetailAPI.append(detail_api)
    
def Get_Multi_Product_API():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(Get_API_Information,product_URLs)
             
def Get_Selenium_Information(driver,link):
    ##Get detail information by Selenium
    #Retrieve productID and sellerID from link
    temp1=link.split('?')
    temp2=temp1[0].split('i.')
    temp=temp2[1].split('.')
    productID=temp[1] #ProductID
    #Check count of option
    driver.get(link)
    sleep(8)

    #Get all option elements
    try:
        option_elems=driver.find_elements(By.CSS_SELECTOR,".bR6mEk")
    except NoSuchElementException as e:
        option_elems=None

    if len(option_elems)==0:
        sleep(0.5)
        #Product don't have option list
        detail_=[]
        skuName="Default"
        #Get price            
        try:
            price_elem=driver.find_element(By.CSS_SELECTOR,".pqTWkA")
            price_=price_elem.text
        except NoSuchElementException as e:
            price_=''
        price=price_[1:]
        #Get inStock
        try:
            inStock_elem=driver.find_element(By.CSS_SELECTOR,'._6lioXX')
            inStock_=inStock_elem.text 
        except Exception as e:
            inStock_=''
            
        inStock=re.findall('[0-9]+',inStock_)[0]
        
        isActive=1
        detail_.append(productID)
        detail_.append(skuName)
        detail_.append(price)
        detail_.append(inStock)
        detail_.append(isActive) 
        DetailSele.append(detail_)
    
    
    elif len(option_elems)==1:
        #Get option list
        try:
            option_list_elems=option_elems[0].find_elements(By.CSS_SELECTOR,'.product-variation')
            option_list=[elem.text for elem in option_list_elems]
        except NoSuchElementException as e:
            e
            
        action = ActionChains(driver)
        for i in range(len(option_list)):
            option_button=option_list_elems[i]
            detail_=[]
            #Check if option1_button is disabled ?
            if option_button.get_attribute("aria-disabled")=='false': 
                action.click(on_element=option_button)
                action.perform()
                sleep(0.5)
                skuName=f'{option_list[i]}'   
                    
                #Get price            
                try:
                    price_elem=driver.find_element(By.CSS_SELECTOR,".pqTWkA")
                    price_=price_elem.text
                except NoSuchElementException as e:
                    price_=''
                price=price_[1:]
        
                #Get inStock
                try:
                    inStock_elem=driver.find_element(By.CSS_SELECTOR,'._6lioXX')
                    inStock_=inStock_elem.text 
                except Exception as e:
                    inStock_=''
                    
                inStock=re.findall('[0-9]+',inStock_)[0]
                
                isActive=1
                detail_.append(productID)
                detail_.append(skuName)
                detail_.append(price)
                detail_.append(inStock)
                detail_.append(isActive) 
                DetailSele.append(detail_)
            else:
                skuName=f'{option_list[i]}'
                price=''
                inStock=''
                isActive=0
                detail_.append(productID)
                detail_.append(skuName)
                detail_.append(price)
                detail_.append(inStock)
                detail_.append(isActive)
                DetailSele.append(detail_)    
                    
    elif len(option_elems)==2: #Product have 2 option list
            
        option1_elems=option_elems[0]
        #Get option 1
        try:
            option1_list_elems=option1_elems.find_elements(By.CSS_SELECTOR,'.product-variation')
            option1_list=[elem.text for elem in option1_list_elems]
        except NoSuchElementException as e:
            e

        option2_elems=option_elems[1]
        #Get option 2
        try:
            option2_list_elems=option2_elems.find_elements(By.CSS_SELECTOR,'.product-variation')
            option2_list=[elem.text for elem in option2_list_elems]
        except NoSuchElementException as e:
            e
        
        action1 = ActionChains(driver)
        action2 = ActionChains(driver)

        for i in range(len(option1_list)):
            sleep(1)
            option1_button=option1_list_elems[i]
            
            #Check if option1_button is disabled ?
            if option1_button.get_attribute("aria-disabled")=='false': 
                action1.click(on_element=option1_button)
                action1.perform()
                sleep(0.5)
                
                for j in range(len(option2_list)):
                    detail_=[]
                    option2_button=option2_list_elems[j]
                    
                    #Check if option2_button is disabled ?
                    if option2_button.get_attribute("aria-disabled")=='false': 
                        action2.click(on_element=option2_button)
                        action2.perform()
                        sleep(0.5)
                        
                        skuName=f'{option1_list[i]},{option2_list[j]}'   
                        
                        #Get price            
                        try:
                            price_elem=driver.find_element(By.CSS_SELECTOR,".pqTWkA")
                            price_=price_elem.text
                        except NoSuchElementException as e:
                            price_=''
                        price=price_[1:]
                        
                        #Get inStock
                        try:
                            inStock_elem=driver.find_element(By.CSS_SELECTOR,'._6lioXX')
                            inStock_=inStock_elem.text 
                        except Exception as e:
                            inStock_=''
                            
                        inStock=re.findall('[0-9]+',inStock_)[0]
                        
                        isActive=1
                        detail_.append(productID)
                        detail_.append(skuName)
                        detail_.append(price)
                        detail_.append(inStock)
                        detail_.append(isActive) 
                        DetailSele.append(detail_)
                        
                        action2.reset_actions()
                        action2.click(on_element=option2_button)
                        action2.perform()
                        sleep(1)
                    else:
                        skuName=f'{option1_list[i]},{option2_list[j]}'
                        
                        price=''
                        inStock=''
                        isActive=0
                        detail_.append(productID)
                        detail_.append(skuName)
                        detail_.append(price)
                        detail_.append(inStock)
                        detail_.append(isActive)
                        DetailSele.append(detail_)                     
                action1.reset_actions()
                
            else:
                for j in range(len(option2_list)):
                    detail_=[]
                    skuName=f'{option1_list[i]},{option2_list[j]}'
                    
                    price=''
                    inStock=''
                    isActive=0
                    detail_.append(productID)
                    detail_.append(skuName)
                    detail_.append(price)
                    detail_.append(inStock)
                    detail_.append(isActive)
                    DetailSele.append(detail_)
    
def Get_Multi_Product_Selenium(): 
    
    for i in range(len(product_URLs)):
        group_urls=product_URLs[i:i+10]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(Get_Selenium_Information,drivers_2,group_urls)

def Create_DataFrame():
    
    df_MasterProduct=pd.DataFrame(data=Master_Product,columns=['Item ID','Title','Category','Brand','Location','Shop ID'])
    df_Marketing=pd.DataFrame(data=Marketing,columns=['Item ID','Rating star','Count reviews','Sold items'])
    df_DetailAPI=pd.DataFrame(data=DetailAPI,columns=['Product ID','SKU ID','SKU name'])
    df_DetailSele=pd.DataFrame(data=DetailSele,columns=['Product ID','SKU name','Price','In stock','Is active'])
    df_ProductDetail=pd.merge(df_DetailAPI,df_DetailSele,how='left',on=['Product ID','SKU name'])
  
    # df_Seller=pd.DataFrame(data=Seller,columns=['Shop ID','Shop name','Item count','Rating star','Response rate','Cancel rate','Follower count'])
    
    # Clean_Master_Product(df_MasterProduct)
    # Clean_Product_Details(df_ProductDetail)
    # Clean_Marketing(df_Marketing)
    # Clean_Seller(df_Seller)
    
    # Dataframe to Excel 
    df_MasterProduct.to_excel('Master Product.xlsx')
    df_DetailAPI.to_excel('Detail API.xlsx')
    df_DetailSele.to_excel('Detail Sele.xlsx')
    df_ProductDetail.to_excel('Product Detail.xlsx')
    df_Marketing.to_excel('Marketing.xlsx')
    print('-------Insert data to excel file successfully-------')
    
    # #DataFrame to MySQL
    # mysql_engine=connect_MySQL()
    # df_MasterProduct.to_sql('master product',con=mysql_engine,if_exists='append',index=False)
    # df_ProductDetail.to_sql('product detail',con=mysql_engine,if_exists='append',index=False)
    # df_Marketing.to_sql('marketing',con=mysql_engine,if_exists='append',index=False)
    # print('-------Insert data to MySQL successfully-------')
    
    # #DataFrame to AWS Redshift
    # redshift_engine=connect_AWSRedshift()
    # df_MasterProduct.to_sql('master product',con=redshift_engine,if_exists='append',index=False)
    # df_ProductDetail.to_sql('product detail',con=redshift_engine,if_exists='append',index=False)
    # df_Marketing.to_sql('marketing',con=redshift_engine,if_exists='append',index=False)
    # print('-------Insert data to AWS Redshift successfully-------')
    

# def Clean_Product_Details(df):
#     df['Item ID']=df['Item ID'].astype(np.int64)
#     df['Model ID']=df['Model ID'].astype(np.int64)
    
    
# def Clean_Marketing(df):
#     pass

# def Clean_Master_Product(df):
#     df['Item ID']=df['Item ID'].astype(np.int64)
#     df['Shop ID']=df['Shop ID'].astype(np.int64)

# def Clean_Seller(df):
#     df['Shop ID']=df['Shop ID'].astype(np.int64)

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
    DetailSele=[]
    
    page_urls=[]
    for i in range(1,3):
        url=f'https://shopee.vn/search?category=11036030&keyword=%C4%91i%E1%BB%87n%20tho%E1%BA%A1i%20di%20%C4%91%E1%BB%99ng&page={i}'
        page_urls.append(url)
        

    drivers_1=[]
    Open_Multi_Driver(drivers_1,n=2)
    Get_Multi_Pages()
    
    drivers_2=[]
    Get_Multi_Product_API()
    Open_Multi_Driver2(drivers_2,n=9)
    Get_Multi_Product_Selenium()
    Create_DataFrame()

    end_time=time.perf_counter()
    print(f'Executive time {end_time-start_time}')