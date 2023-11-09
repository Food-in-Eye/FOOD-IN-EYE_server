from datetime import datetime, timedelta
from dotenv import load_dotenv

import os
import httpx

from core.common.mongo import MongodbController
from core.common.s3 import Storage
from .src import DataLoader
from v2.routers.src.util import Util

DB = MongodbController('FIE_DB2')
storage = Storage('foodineye2')

class CallAnalysis:
    @staticmethod
    async def sale_stats(today:datetime):
        """
            하루동안의 판매 통계를 하는 함수이다.
            1. 어제 00:00 ~ 오늘 00:00 까지의 주문(orders)를 불러온다.
            2. orders에 s_num, f_num을 추가한다.
            3. orders를 s_num, f_num으로 분류하여 저장한다.
            4. 분류된 데이터(store_data)에 대한 보고서를 불러와 리턴한다.
        """
        load_dotenv()

        yesterday = today - timedelta(1)
        
        # orderDB에서 어제 하루동안의 모든 주문내역 불러오기
        query = {
            'date':{"$gte": yesterday, "$lte": today}
            }
        # orders = DB.read_all_by_query('order', query)
        orders = DataLoader.get_orders(query)

        # s_num table, f_num table 불러옴 (각 _id 와 num이 매칭되어있음)
        s_table = DataLoader.get_store_table()
        f_table = DataLoader.get_food_table()

        anlz_sale_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/sale/execute"
        headers = {"Content-Type": "application/json"}
        payload = {
            "orders": orders,
            "s_table": s_table,
            "f_table": f_table
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(anlz_sale_url, json=payload, headers=headers)
            data = response.json()

        return data

    @staticmethod
    async def aoi_stats(today:datetime):
        load_dotenv()
        
        yesterday = today - timedelta(1)
        query = {
            'date':{"$gte": yesterday, "$lte": today},
            'aoi_analysis':{"$ne":None}
            }
        aoi_datas = DataLoader.get_aoi_reports(query)

        aoi_daily_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/aoi/daily"
        headers = {"Content-Type": "application/json"}

        payload = {
            "aoi_datas": aoi_datas
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(aoi_daily_url, json=payload, headers=headers)
            data = response.json()

        return data

    async def daily_summary(today:datetime):
        # today = datetime(2023, 8, 17)
        sale_report = await CallAnalysis.sale_stats(today)
        aoi_report = await CallAnalysis.aoi_stats(today)

        result = {
            'date': today - timedelta(days=1),
            'update_date': datetime.now()
        }

        for store in sale_report.keys():
            report_data = {
                'sale_summary': sale_report[store],
                'aoi_summary': aoi_report[store]
            }
            key = str(storage.upload(report_data, "json", "exhibition/daily"))

            result[store] = key

        try:
            object_id = DB.insert_one('daily', result)
            return str(object_id)

        except Exception as e:
            print(e)
            return False
        


    # 모든 데이터를 하루의 report로 생성 하기 위한 코드
    @staticmethod
    async def sale_stats_oneday(yesterday:datetime, today:datetime, o_id_list:list):
        """
            하루동안의 판매 통계를 하는 함수이다.
            1. 어제 00:00 ~ 오늘 00:00 까지의 주문(orders)를 불러온다.
            2. orders에 s_num, f_num을 추가한다.
            3. orders를 s_num, f_num으로 분류하여 저장한다.
            4. 분류된 데이터(store_data)에 대한 보고서를 불러와 리턴한다.
        """
        load_dotenv()
        
        pipeline = [
            { "$match": { "_id": { "$in": o_id_list}, "date": {"$gte": yesterday, "$lte": today} }},
            { "$project": { 's_id': 1, 'date':1, 'f_list':1 }}
        ]

        # 모든 데이터를 이용하여 하루에 대한 report 생성
        orders = DataLoader.get_orders_oneday(pipeline)

        s_table = DataLoader.get_store_table()
        f_table = DataLoader.get_food_table()

        anlz_sale_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/sale/execute"
        headers = {"Content-Type": "application/json"}
        payload = {
            "orders": orders,
            "s_table": s_table,
            "f_table": f_table
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(anlz_sale_url, json=payload, headers=headers)
            data = response.json()

        return data

    @staticmethod
    async def aoi_stats_oneday(yesterday:datetime, today:datetime, h_id_list:list):
        load_dotenv()
        
        pipeline = [
            { "$match": { "_id": { "$in": h_id_list}, "date": {"$gte": yesterday, "$lte": today}, 'aoi_analysis':{"$ne":None} }  },
            { "$project": {'date':1, 'aoi_analysis':1, 'u_id':1} }
        ]

        # 모든 데이터를 이용하여 하루에 대한 report 생성
        aoi_datas = DataLoader.get_aoi_reports_oneday(pipeline)
        
        aoi_daily_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/aoi/daily"
        headers = {"Content-Type": "application/json"}

        payload = {
            "aoi_datas": aoi_datas
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(aoi_daily_url, json=payload, headers=headers)
            data = response.json()

        return data


    async def daily_summary_oneday(h_id_list:list, o_id_list:list):

        # 모든 데이터를 이용하여 하루에 대한 report 생성
        yesterday = Util.get_utc_time_by_str("2023-09-12")
        today = Util.get_utc_time_by_str("2023-09-25")

        sale_report = await CallAnalysis.sale_stats_oneday(yesterday, today, o_id_list)
        aoi_report = await CallAnalysis.aoi_stats_oneday(yesterday, today, h_id_list)
        
        result = {
            'date': datetime(2022,10,31,15,0,0),
            'update_date': datetime.now()
        }
        print(aoi_report)
        for store in sale_report.keys():
            report_data = {
                'sale_summary': sale_report[store],
                'aoi_summary': aoi_report[store]
            }
            key = str(storage.upload(report_data, "json", "exhibition/daily"))

            result[store] = key

        try:
            object_id = DB.insert_one('daily', result)
            return str(object_id)

        except Exception as e:
            print(e)
            return False
        


    # 2주 동안의 report로 생성 하기 위한 코드
    @staticmethod
    async def sale_stats_2weeks(yesterday:datetime, today:datetime, o_id_list:list):
        """
            하루동안의 판매 통계를 하는 함수이다.
            1. 어제 00:00 ~ 오늘 00:00 까지의 주문(orders)를 불러온다.
            2. orders에 s_num, f_num을 추가한다.
            3. orders를 s_num, f_num으로 분류하여 저장한다.
            4. 분류된 데이터(store_data)에 대한 보고서를 불러와 리턴한다.
        """
        load_dotenv()
        
        pipeline = [
            { "$match": { "_id": { "$in": o_id_list}, "date": {"$gte": yesterday, "$lte": today} }},
            { "$project": { 's_id': 1, 'date':1, 'f_list':1 }}
        ]

        # 하루에 대한 report 생성
        orders = DataLoader.get_orders(pipeline)

        s_table = DataLoader.get_store_table()
        f_table = DataLoader.get_food_table()

        anlz_sale_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/sale/execute"
        headers = {"Content-Type": "application/json"}
        payload = {
            "orders": orders,
            "s_table": s_table,
            "f_table": f_table
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(anlz_sale_url, json=payload, headers=headers)
            data = response.json()

        return data

    @staticmethod
    async def aoi_stats_2weeks(yesterday:datetime, today:datetime, h_id_list:list):
        load_dotenv()
        
        pipeline = [
            { "$match": { "_id": { "$in": h_id_list}, "date": {"$gte": yesterday, "$lte": today}, 'aoi_analysis':{"$ne":None} }  },
            { "$project": {'date':1, 'aoi_analysis':1, 'u_id':1} }
        ]

        # 하루에 대한 report 생성
        aoi_datas = DataLoader.get_aoi_reports(pipeline)
        
        aoi_daily_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/aoi/daily"
        headers = {"Content-Type": "application/json"}

        payload = {
            "aoi_datas": aoi_datas
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(aoi_daily_url, json=payload, headers=headers)
            data = response.json()

        return data


    async def daily_summary_2weeks(h_id_list:list, o_id_list:list, today:datetime):

        # 하루에 대한 report 생성
        yesterday = today - timedelta(1)

        sale_report = await CallAnalysis.sale_stats_oneday(yesterday, today, o_id_list)
        aoi_report = await CallAnalysis.aoi_stats_oneday(yesterday, today, h_id_list)

        result = {
            'date': yesterday,
            'update_date': datetime.now()
        }

        for store in sale_report.keys():
            report_data = {
                'sale_summary': sale_report[store],
                'aoi_summary': aoi_report[store]
            }
            key = str(storage.upload(report_data, "json", "exhibition/daily"))

            result[store] = key

        try:
            object_id = DB.insert_one('daily', result)
            return str(object_id)

        except Exception as e:
            print(e)
            return False
        