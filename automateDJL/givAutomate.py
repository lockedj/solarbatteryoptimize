from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from automateDJL import utils
import time
import logging

# -This module uses screen scraping to access the giv web portal,
# navigate to the config settings page and to set the battery
# charge, start, end and charge to percent.
#
# NOTE: This module is now redundent as GIV have implemented a public
# API that enables the battery settings to be queried and set.


class GivAutomate:

    def __init__(self, cdir, system="giv", id="DLocke"):
        self.id = id
        self.system = system
        self.configdir = cdir
        self.driver = ""
        self.logger = logging.getLogger("automateDJL")
        return

    def setChromeDriverLocal(self):
        self.logger.info("using local chrome web driver")
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")
        # self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(30)
        return

    def setChromeDriverRemote(self, url='http://127.0.0.1:4444/wd/hub'):
        self.logger.info("using remote web driver: "+url)
        capabilities = DesiredCapabilities.CHROME.copy()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Remote(
            command_executor=url,
            desired_capabilities=capabilities,
            options=chrome_options
        )
        self.driver.implicitly_wait(30)
        return

    def configBatteryCharge(self, fromTime, toTime, maxCharge):
        assert(self.driver != ""), "Web driver not set"

        try:
            self.logger.info(
                f"Set Giv to charge between {fromTime} & {toTime} charging to {maxCharge}%")

            util = utils.Utils(self.configdir+"battery.conf")
            pwd = util.getKey(self.system, self.id)

            self.driver.get("https://www.givenergy.cloud/GivManage")
            # time.sleep(1)
            self.logger.info(f"using account id {self.id}")
            self.logger.info(f"At web page {self.driver.title}")
            # elem = WebDriverWait(self.driver, 10).until(
            #    EC.presence_of_element_located((By.ID, "account")))
            #self.logger.info("Login clickable?")
            elem = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "account")))
            elem = self.driver.find_element_by_id("account")
            elem.click()
            elem.clear()
            elem.send_keys(self.id)

            elem = self.driver.find_element_by_id("password")
            elem.click()
            elem.clear()
            elem.send_keys(pwd)
            # time.sleep(1)
            self.logger.info("Press Login")

            elem = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "loginButton")))
            # self.logger.info("Login click")
            elem.click()
            time.sleep(5)
            # for handle in self.driver.window_handles:
            #     self.logger.info(f"handle {handle}")
            self.logger.info(f"At web page {self.driver.title}")

            if "Login" in self.driver.title:
                raise UserWarning("Cannot login - bad user or password?")

            # for e in elems:
            #     self.logger.info(f"button {e.text}")
            self.driver.find_element_by_xpath(
                "//button[contains(text(), 'System Mode Settings')]").click()
            # the page asyncrhnously loads data so need to give it some time
            time.sleep(5)
            act = True
            i = 0
            while i < 10:
                if act == True:
                    self.logger.info(f"At web page {self.driver.title}")
                    elem = self.driver.find_element_by_id("input94_ModeBSC")
                    elem.click()
                    elem.clear()
                    elem.send_keys(fromTime)
                    elem = self.driver.find_element_by_id("input95_ModeBSC")
                    elem.clear()
                    elem.send_keys(toTime)

                    elem = self.driver.find_element_by_id("input116_ModeBSC")
                    elem.clear()
                    elem.send_keys(maxCharge)

                    elem = self.driver.find_element_by_id("modeBSCCheckbox")
                    self.logger.info(
                        f"Smart charge selected? {elem.is_selected()}")
                    if elem.is_selected() == False:
                        elem.click()

#                    elem = self.driver.find_element_by_xpath(
#                        "(//button[@type='button'])[5]")
                    elem = self.driver.find_element_by_id("confirmBSC")
                    elem.click()

                    time.sleep(5)  # wait 5 seconds for action to take place

                elem = self.driver.find_element_by_xpath(
                    "//tr[@id='datagrid-row-r1-2-0']/td[3]/div")
                if elem.text.startswith("SUCCESS"):
                    self.logger.info(
                        f"Successfully set Giv to charge between {fromTime} & {toTime} charging to {maxCharge}%")
                    break
                elif elem.text.startswith("SETTING"):
                    self.logger.info(
                        f"Waiting for update action to complated attempt {i} status is {elem.text} trying again")
                    act = False
                    i = i + 1
                    time.sleep(5)
                elif i < 10:
                    act = True
                    i = i + 1
                    self.logger.info(
                        f"Giv update attempt {i} failed {elem.text} trying again")
                    time.sleep(10)
                else:
                    self.logger.exception(
                        f"Giving up after {i} attempts to update giv energy cloud|")
        except:
            self.logger.exception("update of givcloud failed")
        finally:
            self.driver.close
            self.driver.quit
            self.logger.info("close webdriver")

        return
