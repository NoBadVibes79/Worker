from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from datetime import date
from db.sqlite import SQLite
import datetime
import requests
import pandas as pd
import glob
import pickle
import time

db = SQLite("db\\worker.db")


class Utilities:
    def __init__(self):
        self.proxy_in = None
        self.proxy_out = None
        self.proxy_diff = None
        self.proxy_diff_seconds = 120

    def _refresh_proxy(self):
        """
        Refreshes the proxy if necessary. If the proxy has been in use for more than 120 seconds, 
        it restarts the proxy by sending a request to the specified URL. 
        If the request returns a status code of 429, it sleeps for 15 seconds and tries to refresh the proxy again.
        If the proxy has been in use for less than 20 seconds, it sleeps for the remaining time before refreshing the proxy.
        """
        if self.proxy_out is not None:
            self.proxy_in = datetime.datetime.now()
            self.proxy_diff = self.proxy_in - self.proxy_out
            self.proxy_diff_seconds = self.proxy_diff.total_seconds()
        
        if self.proxy_diff_seconds is None or self.proxy_diff_seconds >= 20:

            headers = {
                'authority': 'i.fxdx.in',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'max-age=0',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            }

            response = requests.get('https://i.fxdx.in/api-rt/changeip/RG683v9gUF/x6WKAGMSTENK7', headers=headers)
            
            if response.status_code == 429:
                time.sleep(15)
                return self._refresh_proxy()
            else:
                self.proxy_out = datetime.datetime.now()
        else:
            sleep = 20 - self.proxy_diff_seconds
            time.sleep(sleep)
            return self._refresh_proxy()
        
    def _load_cookie(self, driver, login: str):
        """
        Load cookies for the specified login user and add them to the provided driver.
        
        :param driver: WebDriver object to which the cookies will be added
        :param login: str representing the login user
        """
        path = f"cookies\\{login}_cookies"
        cookies = pickle.load(open(path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

    def _save_cookie(self, login: str):
        """
        Save the cookies for the given login using the provided driver.

        Parameters:
            driver: WebDriver - The WebDriver object for the browser session.
            login: str - The login name for which the cookies are being saved.
        """
        pickle.dump(self.driver.get_cookies(), open(rf"cookies/{login}_cookies", "wb"))
    #TODO сделать нормальные пути
    def _combine_csv(self):  
        """
        Combine multiple CSV files into a single DataFrame and sort the DataFrame by the 'group' column. 
        Save the sorted DataFrame to a new CSV file.
        """
        list_csv = []
        list_csv.extend(glob.glob('C:\\Users\\Kraze\\Downloads\\***.csv'))
        df = pd.concat([pd.read_csv(f) for f in list_csv], ignore_index=True)
        sorted_df = df.sort_values('group', key=lambda x: x.str.split('.').str[-1].astype(int))
        sorted_df.to_csv("C:\\Users\\Kraze\\Downloads\\result.csv", index=False)
    
    def _driver_selenium(self, pth_chromedriver:str, pth_chrome:str):
        """
        Initializes and configures a Selenium WebDriver using the provided chromedriver and chrome paths.

        :param pth_chromedriver: str - The path to the chromedriver executable.
        :param pth_chrome: str - The path to the chrome executable.
        :return: WebDriver - The configured Selenium WebDriver.
        """
        service = Service(pth_chromedriver)

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--log-level=3')
        options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        options.binary_location = pth_chrome

        driver = webdriver.Chrome(service=service, options=options)

        return driver


class Worker(Utilities):
    def __init__(self, chromedriver:str='webdriver/chromedriver.exe', chrome:str="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"):
        super().__init__()
        self.chromedriver = chromedriver
        self.chrome = chrome
    
    def _driver_init(self):
        """
        Initializes the driver by creating a new selenium driver instance using the specified chromedriver and chrome options. 
        Delays the execution for 0.5 seconds and maximizes the window of the driver.
        """
        self.driver = self._driver_selenium(self.chromedriver, self.chrome)
        time.sleep(0.5)
        self.driver.maximize_window()
    
    def _start_nklz(self):
        self.driver.get('https://nooklz.com/')
        self._load_cookie(self.driver, 'nooklz')
        time.sleep(2)

    def set_cookie(self):
        """
        Initializes the driver, sets a cookie for 'https://nooklz.com/', and closes the driver.
        """
        self._driver_init()
        try:
            self.driver.get('https://nooklz.com/')
            time.sleep(40)
            self._save_cookie('nooklz')
        finally:
            self.driver.close()
            self.driver.quit()

    def take_accs(self, url_page:str="1", packs_quantity:int=1, accs_quantity:int=1, group_num:int=1, proxy_id:str='71790'):
        """
        A function to take accounts with specified parameters and handle exceptions.
        Parameters:
        - url_page: str, default="1"
        - packs_quantity: int, default=1
        - accs_quantity: int, default=1
        - group_num: int, default=1
        - proxy_id: str, default='71790'
        """
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
            new_ids = []
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
                            new_ids.append(acc_id)
                        except:
                            self.driver.execute_script(
                                "arguments[0].click();", checkbox)
                            time.sleep(0.35)
                            acc_count += 1
                            ids_list.append(acc_id)
                            new_ids.append(acc_id)

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
            for id in new_ids:
                db.insert(table="usedaccs", ids=id)
            
            self._combine_csv()
            print("Сборка аккаунтов закончена")
            
            self.driver.close()
            self.driver.quit()
    #TODO Сделать ожидание элемента, который после загрузки в окту появляется
    def __upload_octa(self):
        """
        Uploads an octa by clicking various elements on the webpage using the self.driver.
        """
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
        """
        Downloads an XLS file with the specified group number, accounts quantity, and proxy ID.

        Args:
            group_num (str): The group number (default is "1").
            accs_quantity (int): The quantity of accounts (default is 1).
            proxy_id (str): The proxy ID (default is "1").
        """
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
        self.driver.find_element(
            By.CLASS_NAME, 'form-check').find_element(By.NAME, 'check_updates').click()
        time.sleep(1)

        self.driver.find_element(By.ID, 'submit-modal-exportNooklz').click()
        time.sleep(2)
        self.driver.find_element(By.CLASS_NAME, 'btn-close').click()
        time.sleep(1)

        self.__upload_octa()
        
    def check_accs(self, start:str, end:str):
        """
        Check accounts and perform various actions on the web page.
        
        Parameters:
            start (str): The start parameter for the account check.
            end (str): The end parameter for the account check.
        """
        self._driver_init()
        self.driver.maximize_window()
        
        try:
            self._start_nklz()
            
            self.driver.get('https://nooklz.com/profiles')
            self._check_first_loading()
            
            self._group_by_label()
            self._open_filters()
            self._click_selectall()
            self.__sort_label()
            amount_groups = self.__take_labels(start, end)
            
            for i in range(1, amount_groups+1):
                self._refresh_proxy()
                chekbox_task = self.driver.find_element(
                    By.XPATH, f'//div[@class="ag-full-width-container"]/div[{i}]/span/span[3]/div/div/div[2]/input')
                chekbox_task.click()
                time.sleep(0.2)

                self._open_tasks()
                self.driver.find_element(By.ID, 'check-m-cookies').click()
                time.sleep(20)
                
                self._check_finish()

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
            
    def _check_first_loading(self):
        """
        Check if the page is still loading, and if so, wait for 10 seconds and check again.
        """
        try:
            loading = self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div[3]/div/div/div[1]/div/div/div[2]/div[2]/div/div[2]/div[2]/div[7]')
            class_loading = loading.get_attribute('class')
            if class_loading == 'ag-overlay':
                time.sleep(10)
                self._check_first_loading()
        except:
            pass
            
    def _group_by_label(self):
        """
        This function groups elements by label using the Selenium WebDriver.
        """
        self.driver.find_element(
            By.ID, 'dropdownMenuClickableInside').click()
        time.sleep(1)
        self.driver.find_element(By.ID, 'labelCheck').click()
        time.sleep(1)
        
    def _open_filters(self):
        """
        Open group filters and perform actions on specific elements.
        """
        filters = self.driver.find_element(By.CLASS_NAME, 'ag-side-button').click()
        time.sleep(1)
        labels = self.driver.find_elements(
            By.CLASS_NAME, 'ag-filter-toolpanel-group-wrapper')[5].click()
        time.sleep(1)
        
    def _click_selectall(self):
        """
        Clicks the 'select all' checkbox in the web page.
        """
        checkbox = self.driver.find_element(
                By.XPATH, f'/html[1]/body[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/div[3]/div[2]/div[2]/div[2]/div[6]/div[1]/div[3]/div[1]/div[2]/div[1]/form[1]/div[1]/div[1]/div[4]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/input[1]')
        checkbox.click()
        time.sleep(0.2)
        
    def __sort_label(self):
        """
        Sorts the label using the driver's find_element method and then adds a small delay.
        """
        self.driver.find_element(
            By.XPATH, '//div[@class="ag-column-drop-wrapper"]/div[1]/div[2]/span').click()
        time.sleep(0.2) 
        
    def __take_labels(self, start: str, end: str) -> int:
        """
        Private method to extract a sublist from a list, interact with checkboxes and trees in a web page,
        and return the length of the extracted sublist.
        
        Parameters:
            start (str): The start element of the sublist.
            end (str): The end element of the sublist.
        
        Returns:
            int: The length of the extracted sublist.
        """
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

    def __create_list_text_group(self) -> list[str]:
        """
        Create a list of text groups by finding elements using XPath, and return the list of text.
        """
        group_divtext_list = self.driver.find_elements(
            By.XPATH, '//div[@class="ag-set-filter-item-checkbox ag-labeled ag-label-align-right ag-checkbox ag-input-field"]/div[1]')

        group_text_list = [x.text for x in group_divtext_list]

        return group_text_list
    
    def _open_tasks(self):
        """
        Private method to perform the open tasks, including clicking on a dropdown element and adding a delay for 1 second.
        """
        self.driver.find_element(By.ID, 'dropdownMenuReference').click()
        time.sleep(1)
        
    def _check_finish(self):
        """
        Recursive function to check if the task has finished by searching for a specific log message.
        """
        try:
            log = self.driver.find_element(By.ID, 'quill_log').find_element(
                By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'p')
            log_text = [x.text for x in log]
            if '[-] Task finished' not in log_text:
                time.sleep(10)
                self._check_finish()
        except:
            time.sleep(10)
            self._check_finish()

    def create_pages(self, start:str, end:str, fp:int=1):
        """
        A function to create pages with given start and end points, and an optional number of iterations.

        Parameters:
            start (str): The start point for page creation.
            end (str): The end point for page creation.
            fp (int, optional): The number of iterations for page creation. Defaults to 1.

        Returns:
            str: A message indicating the number of errors during page creation.
        """
        self._driver_init()
        self.driver.maximize_window()
        
        try:
            self._start_nklz()
            
            self.driver.get('https://nooklz.com/profiles')
            self._check_first_loading()

            self._group_by_label()

            self._open_filters()
            self._click_selectall()
            self.__sort_label()
            amount_groups = self.__take_labels(start, end)

            errors = 0
            while fp > 0:
                for i in range(1, amount_groups+1):
                    self._refresh_proxy()
                    time.sleep(2)
                    chekbox_task = self.driver.find_element(
                        By.XPATH, f'//div[@class="ag-full-width-container"]/div[{i}]/span/span[3]/div/div/div[2]/input')
                    chekbox_task.click()
                    time.sleep(0.2)

                    self._open_tasks()

                    self.driver.find_element(By.ID, 'create-page').click()
                    time.sleep(2)

                    self.driver.find_element(By.ID, 'random-page-names').click()
                    time.sleep(0.3)
                    startpagetask = self.driver.find_element(
                        By.ID, 'startPageTask')
                    startpagetask.click()

                    self._check_finish()
                    errors += len(self._check_errors())
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    chekbox_task2 = self.driver.find_element(
                        By.XPATH, f'//div[@class="ag-full-width-container"]/div[{i}]/span/span[3]/div/div/div[2]/input')
                    time.sleep(2)
                    chekbox_task2.click()
                fp -= 1
            
        except Exception as ex:
            print('[INFO] Ошибка при создании фп')
            with open('log_worker_crtepages.txt', 'a') as f:
                f.write(f"\n{str(ex)}")
        else:
            print('[INFO] Ошибок нет')
            return f'Количество ошибок при создании фп: *{errors}*'
        finally:
            print("Сооздание фп закончено")
            
            self.driver.close()
            self.driver.quit()

    def _check_errors(self):
        """
        Check for errors in the log and return the quantity of errors.
        """
        log_color = []
        
        log = self.driver.find_element(By.ID, 'quill_log').find_element(
            By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'p')

        try:
            log_color = [x.find_element(By.TAG_NAME, 'strong').get_attribute(
                'style').replace('color: ', '').replace(';', '') for x in log]
        except:
            for el in log:
                try:
                    color = el.find_element(By.TAG_NAME, 'strong').get_attribute('style').replace('color: ', '').replace(';', '')
                    log_color.append(color)
                except:
                    continue

        log_error_quantity = [x for x in log_color if x == 'red']

        return log_error_quantity

    def upload_accs(self, path:str):
        """
        A function to upload accounts using the specified path.

        Parameters:
        path (str): The path to the file to upload.

        """
        
        self._driver_init()
        self.driver.maximize_window()
        
        try:
            self._start_nklz()
            
            self.driver.get('https://nooklz.com/profiles')
            self._check_first_loading()

            self.driver.find_element(By.XPATH, '//*[@id="layout-wrapper"]/div[3]/div/div/div[1]/div/div/div[1]/div/div/button').click()
            time.sleep(0.5)
            
            self.driver.find_element(By.ID, 'profile-tab-center').click()
            time.sleep(0.3)
            
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
            file_inputs[-1].send_keys(path)
            time.sleep(5)
            
            self.driver.find_element(By.ID, 'importMultipleAccounts').click()
            time.sleep(1)
        except Exception as ex:
            print('[ERROR] Ошибка при выгрузке аккаунтов')
            with open('log_worker_uploadaccs.txt', 'a') as f:
                f.write(f"\n{str(ex)}")
        else:
            print('[INFO] Ошибок нет')
        finally:
            print("[INFO] Загрузка аккаунтов закончена")
            
            self.driver.close()
            self.driver.quit()



class WorkerAD(Worker):
    def _open_filters(self):
        """
        Open group filters and perform actions on specific elements.
        """
        filters = self.driver.find_element(By.CLASS_NAME, 'ag-side-button').click()
        time.sleep(1)
        labels = self.driver.find_elements(
            By.CLASS_NAME, 'ag-filter-toolpanel-group-wrapper')[-1].click()
        time.sleep(1)
        
    
    def _click_selectall(self):
        """
        Clicks the 'select all' checkbox in the web page.
        """
        checkbox = self.driver.find_element(
                By.XPATH, f'/html/body/div[1]/div[3]/div/div/div[1]/div/div/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div[11]/div/div[3]/div/div[2]/div/form/div/div/div[4]/div/div[2]/div[1]/div/div/div[2]/input')
        checkbox.click()
        time.sleep(0.2)

    def __take_label(self, target:str):
        divs_labels = self.driver.find_element(By.XPATH, '//*[@id="actsGrid"]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div[11]/div/div[3]/div/div[2]/div/form/div/div/div[4]/div/div[2]').find_elements(By.XPATH, 'div')
        for el in divs_labels:
            texto = el.find_element(By.XPATH, 'div/div/div[1]/div').text
            if target in texto:
                checkbox = el.find_element(By.XPATH, 'div/div/div[2]/input')
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
                break

    def _check_finish(self):
        """
        Recursive function to check if the task has finished by searching for a specific log message.
        """
        try:
            log = self.driver.find_element(By.ID, 'quill_log').find_element(
                By.TAG_NAME, 'div').find_elements(By.TAG_NAME, 'p')
            log_text = [x.text for x in log]
            if '[-] Task finished. No task_ids left' not in log_text:
                time.sleep(10)
                self._check_finish()
        except:
            time.sleep(10)
            self._check_finish()

    def link_cards_once(self, target:str, cards:list):
        
        self._driver_init()
        self.driver.maximize_window()
        
        try:
            self._start_nklz()
            
            self.driver.get('https://nooklz.com/acts')
            self._check_first_loading()
            
            self._group_by_label()
            
            self._open_filters()
            self._click_selectall()

            self.__take_label(target)

            errors = 0
            self._refresh_proxy()
            time.sleep(2)
            
            chekbox_task = self.driver.find_element(
                By.XPATH, f'//div[@class="ag-full-width-container"]/div/span/span[3]/div/div/div[2]/input')
            chekbox_task.click()
            time.sleep(0.2)
            
            self._open_tasks()
            
            
            cards_task = self.driver.find_element(By.XPATH, '//*[@id="btgrp"]/div[1]/ul/li[1]')
            actions = ActionChains(self.driver)
            actions.move_to_element(cards_task).perform()
            time.sleep(0.3)
            
            self.driver.find_element(By.ID, 'link-card-act').click()
            time.sleep(0.5)
            
            string_cards = self.__cards_to_string(cards)
            
            cards_input = self.driver.find_element(By.ID, 'cards-input')
            cards_input.send_keys(string_cards)
            
            self.driver.find_element(By.ID, 'select2-link_type-container').click()
            time.sleep(0.2)
            
            mobile_method = self.driver.find_element(By.XPATH, '/html/body/span/span/span[2]/ul/li[3]')
            mobile_method.click()
            time.sleep(0.2)
            
            ivalid_card = self.driver.find_element(By.ID, 'invalidCardCheckChecked')
            ivalid_card.click()
            time.sleep(0.2)
            
            primary_card = self.driver.find_element(By.ID, 'primaryCheckChecked')
            primary_card.click()
            time.sleep(0.2)
            
            verify_3ds = self.driver.find_element(By.ID, 'verify3dsCheckChecked')
            verify_3ds.click()
            time.sleep(0.2)
            
            currency = self.driver.find_element(By.ID, 'currencyCheckChecked')
            currency.click()
            time.sleep(0.2)
            
            self.driver.find_element(By.ID, 'select2-currency_select-container').click()
            time.sleep(0.2)
            
            eur = self.driver.find_element(By.XPATH, '/html/body/span/span/span[1]/input')
            eur.send_keys('EUR')
            time.sleep(0.1)
            
            self.driver.find_element(By.XPATH, '/html/body/span/span/span[2]/ul/li').click()
            time.sleep(0.2)
            
            timezone = self.driver.find_element(By.XPATH, 
            '/html/body/div[1]/div[3]/div/div/div[5]/div/div/div[2]/div/div[1]/div[2]/div/div/form/ul/li/div[12]/div/input')
            timezone.click()
            time.sleep(0.2)
            
            self.driver.find_element(By.XPATH, '//*[@id="settings-form"]/ul/li/div[12]/span/span[1]/span').click()
            time.sleep(0.2)
            
            kiev = self.driver.find_element(By.XPATH, '/html/body/span/span/span[1]/input')
            kiev.send_keys('EUROPE_KIEV')
            time.sleep(0.1)
            
            self.driver.find_element(By.XPATH, '/html/body/span/span/span[2]/ul/li').click()
            time.sleep(0.2)
            
            delay = self.driver.find_element(By.ID, 'delayCardCheckChecked')
            delay.click()
            time.sleep(0.2)
            
            card_to = self.driver.find_element(By.ID, 'delayCardTo')
            card_to.clear()
            card_to.send_keys('25')
            time.sleep(0.2)
            
            card_from = self.driver.find_element(By.ID, 'delayCardFrom')
            card_from.clear()
            card_from.send_keys('20')
            time.sleep(0.2)
            
            self.driver.find_element(By.ID, 'startLinkCardTask').click()
            time.sleep(2)
            
            self._check_finish()
            errors += len(self._check_errors())
            
        except Exception as ex:
            print('[ERROR] Ошибка при Линковки карт')
            with open('log_worker_lnkcards.txt', 'a') as f:
                f.write(f"\n{str(ex)}")
        else:
            print('[INFO] Ошибок нет')
            return f'Количество ошибок при привязке карт: *{errors}*'
        finally:
            print("Линковка карт закончена")
            
            self.driver.close()
            self.driver.quit()

    def __cards_to_string(self, cards:list):
        """
        Convert a list of cards to a string format with each card on a new line.
        
        Parameters:
            cards (list): A list of cards to be converted to a string.
        
        Returns:
            string: A string representation of the list of cards with each card on a new line.
        """
        string_cards = ''
        for card in cards[:-1]:
            string_cards += card + '\n'
        string_cards += cards[-1]
        return string_cards
