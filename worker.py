from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import date
from db.sqlite import SQLite
import requests
import pandas as pd
import glob
import pickle
import time

db = SQLite("db\\worker.db")


class UtilitiesWorker:
    def __init__(self):
        pass
    #TODO Сделать время обновления прокси, считывать его перед обновлением, продумать логику
    def _refresh_proxy(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }

        response = requests.get('http://176.106.53.179:8051/restart/42090/Fvsd45', headers=headers, verify=False)
        
        if response.status_code == 400:
            time.sleep(55)
            return self._refresh_proxy()
    
    def _load_cookie(self, driver, login: str):
        path = f"cookies\\{login}_cookies"
        cookies = pickle.load(open(path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

    def _save_cookie(driver, login: str):
        pickle.dump(driver.get_cookies(), open(rf"cookies/{login}_cookies", "wb"))
    #TODO сделать нормальные пути
    def _combine_csv(self):  
        list_csv = []
        # list_csv.extend(glob.glob('C:\\Users\\Arbitrazh\\Downloads\\***.csv'))
        list_csv.extend(glob.glob('C:\\Users\\Kraze\\Downloads\\***.csv'))
        df = pd.concat([pd.read_csv(f) for f in list_csv], ignore_index=True)
        sorted_df = df.sort_values('group', key=lambda x: x.str.split('.').str[-1].astype(int))
        sorted_df.to_csv("C:\\Users\\Kraze\\Downloads\\result.csv", index=False)
    
    def _driver_selenium(self, pth_chromedriver:str, pth_chrome:str): # C:\Program Files\Google\Chrome\Application\chrome.exe

        service = Service(pth_chromedriver)

        options = webdriver.ChromeOptions()
        # убирает режим автоматизации, нас не видят как бота
        options.add_argument('--disable-blink-features=AutomationControlled')
        # Отключает логи, кроме первой строки инициализации:
        options.add_argument('--log-level=3')
        options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        options.binary_location = pth_chrome

        driver = webdriver.Chrome(service=service, options=options)

        return driver


class Worker(UtilitiesWorker):
    def __init__(self, chromedriver:str='webdriver/chromedriver.exe', chrome:str="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"):
        self.chromedriver = chromedriver
        self.chrome = chrome
    
    def _driver_init(self):
        self.driver = self._driver_selenium(self.chromedriver, self.chrome)
    
    def set_cookie(self):
        self._driver_init()
        try:
            self.driver.get('https://nooklz.com/')
            time.sleep(40)
            self._save_cookie(self.driver, 'nooklz')
        finally:
            self.driver.close()
            self.driver.quit()
    #TODO Создать второй лист для инпута в бд, сравнить 1 и 2 список, добавить в бд только разницу
    def take_accs(self, url_page:str="1", packs_quantity:int=1, accs_quantity:int=1, group_num:int=1, proxy_id:str='71790'):
        self._driver_init()
        
        try:
            self.driver.get('https://crm.clickengine.net/admin/main')
            self._load_cookie(self.driver, 'CRM')
            time.sleep(2)
            
            url = 'https://crm.clickengine.net/admin/buyer/accs-fb?page=' + url_page
            self.driver.get(url)
            time.sleep(2)

            
            db.create_table_takeaccs(table="usedaccs")
            db.take_all(table="usedaccs")
            ids_list = db.ids_out
            acc_count = 0
            ostatok = accs_quantity
            while packs_quantity > 0:

                for i in range(100, 0, -1):

                    is_octa_fill = self.driver.find_element(
                        By.XPATH, f'//tbody/tr[{i}]/td[7]/div[1]//*[name()="svg"]').get_attribute("fill")
                    acc_id = self.driver.find_element(
                        By.XPATH, f'/html/body/div[1]/div[1]/div[2]/div/div/div/form/div[2]/div/table/tbody/tr[{i}]/td[1]/div').text.strip()

                    if is_octa_fill == "red" and acc_id not in ids_list:
                        checkbox = self.driver.find_element(
                            By.XPATH, f'/html/body/div[1]/div[1]/div[2]/div/div/div/form/div[2]/div/table/tbody/tr[{i}]/td[10]/div/div/div/div/input')
                        try:
                            checkbox.click()
                            time.sleep(0.35)
                            acc_count += 1
                            ids_list.append(acc_id)
                        except:
                            self.driver.execute_script(
                                "arguments[0].click();", checkbox)
                            time.sleep(0.35)
                            acc_count += 1
                            ids_list.append(acc_id)

                    if acc_count == ostatok:

                        packs_quantity -= 1
                        acc_count = 0
                        ostatok = accs_quantity
                        self.__download_xls(str(group_num), accs_quantity=accs_quantity, proxy_id=proxy_id)
                        group_num += 1
                        break
                if acc_count < accs_quantity and i == 1:
                    if acc_count > 0:
                        self.__download_xls(str(group_num), accs_quantity=accs_quantity, proxy_id=proxy_id)
                        ostatok = accs_quantity - acc_count

                    acc_count = 0
                    url_page = str(int(url_page) - 1)
                    url = 'https://crm.clickengine.net/admin/buyer/accs-fb?page=' + url_page
                    self.driver.get(url)
                    time.sleep(2)

        except Exception as ex:
            print('[INFO] Ошибка при сборке аккаунтов')
            with open('log_worker_tkaccounts.txt', 'a') as f:
                f.write(f"\n{str(ex)}")
        else:
            print('[INFO] Ошибок нет')
        finally:
            db.delete_all(table="usedaccs")
            for id in ids_list:
                db.insert(table="usedaccs", ids=id)
            
            self._combine_csv()
            print("Сборка аккаунтов закончена")
            
            self.driver.close()
            self.driver.quit()
    
    def __upload_octa(self):

        self.driver.find_element(By.CLASS_NAME, 'ts-control').click()
        time.sleep(1)

        upload_button = self.driver.find_element(
            By.CLASS_NAME, 'ts-dropdown-content').find_elements(By.TAG_NAME, 'div')[1]
        upload_button.click()
        time.sleep(1)

        self.driver.find_element(
            By.CSS_SELECTOR, '#post-form > fieldset > div > div.form-group.mb-0 > button').click()
        time.sleep(1)
        self.driver.find_element(
            By.CSS_SELECTOR, '#confirm-dialog > div > div > div.modal-footer > div > button').click()
        time.sleep(20)
        
    def __download_xls(self, group_num:str="1", accs_quantity:int=1, proxy_id:str="1"):
        today = date.today().strftime("%d.%m")
        if accs_quantity == 100:
            group_name = today + " 100." + group_num
        else:
            group_name = today + "." + group_num

        export_button = self.driver.find_element(
            By.CLASS_NAME, 'form-group').find_element(By.TAG_NAME, 'button')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        time.sleep(3)
        export_button.click()
        time.sleep(1)
        
        group_input = self.driver.find_element(By.NAME, 'group')
        group_input.clear()
        group_input.send_keys(group_name)
        time.sleep(1)

        proxy_input = self.driver.find_element(By.NAME, 'proxy')
        proxy_input.clear()
        proxy_input.send_keys(proxy_id)
        time.sleep(1)
        # убираем чек бокс check_updates
        self.driver.find_element(
            By.CLASS_NAME, 'form-check').find_element(By.NAME, 'check_updates').click()
        time.sleep(1)
        # кликаем выгрузить
        self.driver.find_element(By.ID, 'submit-modal-exportNooklz').click()
        time.sleep(2)
        self.driver.find_element(By.CLASS_NAME, 'btn-close').click()
        time.sleep(1)

        self.__upload_octa()
        
    def check_accs(self, start:str, end:str):
        self._driver_init()
        self.driver.maximize_window()
        
        try:
            self.driver.get('https://nooklz.com/')
            self._load_cookie(self.driver, 'nooklz')
            time.sleep(2)
            
            url = 'https://nooklz.com/profiles'
            self.driver.get(url)
            self.__check_first_loading()
            
            self.__group_by_label()
            self.__open_group_filters()
            self.__click_select_all()
            self.__sort_label()
            amount_groups = self.__take_label(start, end)
            
            for i in range(1, amount_groups+1):
                self._refresh_proxy()
                chekbox_task = self.driver.find_element(
                    By.XPATH, f'//div[@class="ag-full-width-container"]/div[{i}]/span/span[3]/div/div/div[2]/input')
                chekbox_task.click()
                time.sleep(0.2)

                self.__open_tasks()
                self.driver.find_element(By.ID, 'check-m-cookies').click()
                time.sleep(20)
                
                self.__check_finish()
                # прокрутка страницы максимально вверх
                self.driver.execute_script("window.scrollTo(0, 0);")
                chekbox_task2 = self.driver.find_element(
                    By.XPATH, f'//div[@class="ag-full-width-container"]/div[{i}]/span/span[3]/div/div/div[2]/input')
                time.sleep(2)
                chekbox_task2.click()
        except Exception as ex:
            print('[INFO] Ошибка при чеке аккаунтов')
            with open('log_worker_chkaccounts.txt', 'a') as f:
                f.write(f"\n{str(ex)}")
        else:
            print('[INFO] Ошибок нет')
        finally:
            print("Чек аккаунтов закончен")
            
            self.driver.close()
            self.driver.quit()
            
    def __check_first_loading(self):
        loading = self.driver.find_element(
            By.XPATH, '/html/body/div[1]/div[3]/div/div/div[1]/div/div/div[2]/div[2]/div/div[2]/div[2]/div[7]')
        class_loading = loading.get_attribute('class')
        if class_loading == 'ag-overlay':
            time.sleep(10)
            self.__check_first_loading()
            
    def __group_by_label(self):
        self.driver.find_element(
            By.ID, 'dropdownMenuClickableInside').click()
        time.sleep(1)
        self.driver.find_element(By.ID, 'labelCheck').click()
        time.sleep(1)
        
    def __open_group_filters(self):
        filters = self.driver.find_element(By.CLASS_NAME, 'ag-side-button').click()
        time.sleep(1)
        labels = self.driver.find_elements(
            By.CLASS_NAME, 'ag-filter-toolpanel-group-wrapper')[5].click()
        time.sleep(1)
        
    def __click_select_all(self):
        checkbox = self.driver.find_element(
                By.XPATH, f'/html[1]/body[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]/div[2]/div[6]/div[1]/div[3]/div[1]/div[2]/div[1]/form[1]/div[1]/div[1]/div[4]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/input[1]')
        checkbox.click()
        time.sleep(0.2)
        
    def __sort_label(self):
        self.driver.find_element(
            By.XPATH, '//div[@class="ag-column-drop-wrapper"]/div[1]/div[2]/span').click()
        time.sleep(0.2) 
        
    def __take_label(self, start: str, end: str):
        group_text_list = self.__create_list_text_group()

        start_index, end_index = group_text_list.index(
            start), group_text_list.index(end)
        task_list = group_text_list[start_index:end_index+1]

        for task in task_list:
            index_xpath = group_text_list.index(task)
            checkbox = self.driver.find_element(
                By.XPATH, f'//div[@class="ag-virtual-list-container ag-filter-virtual-list-container"]/div[{index_xpath+1}]/div[1]/div[1]/div[2]/input[1]')
            self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", checkbox)
            time.sleep(0.3)
            try:
                checkbox.click()
                time.sleep(0.2)
            except:
                self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", checkbox)
                time.sleep(1)
                checkbox.click()
                time.sleep(0.2)
            
            
            tree = self.driver.find_element(
                By.XPATH, f'//div[@class="ag-full-width-container"]/div/span/span[1]/span')
            self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", tree)
            time.sleep(0.5)
            try:
                tree.click()
                time.sleep(0.2)
            except:
                self.driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", tree)
                time.sleep(1)
                tree.click()
                time.sleep(0.2)

        return len(task_list)

    def __create_list_text_group(self):
        # ? Очень полезный способ искать элементы на странице
        group_divtext_list = self.driver.find_elements(
            By.XPATH, '//div[@class="ag-set-filter-item-checkbox ag-labeled ag-label-align-right ag-checkbox ag-input-field"]/div[1]')

        group_text_list = [x.text for x in group_divtext_list]

        return group_text_list
    
    def __open_tasks(self):
        self.driver.find_element(By.ID, 'dropdownMenuReference').click()
        time.sleep(1)
        
    def __check_finish(self):
        try:
            log = self.driver.find_element(By.ID, 'quill_log').find_element(
                By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'p')
            log_text = [x.text for x in log]
            if '[-] Task finished' not in log_text:
                time.sleep(10)
                self.__check_finish()
        except:
            time.sleep(10)
            self.__check_finish()