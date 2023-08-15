from RPA.Browser import Selenium

from libraries import common


class CentralReachBillingListOfColumn:
    def __init__(self, browser: Selenium, column_name: str):
        self.browser = browser
        self.column_name = column_name
        self.text_type = ''
        self.text_filter =''

        if self.column_name is "Location":
            self.text_type = 'locations'
            self.text_filter ='Location'

        if self.column_name is "Payor":
            self.text_type = 'insurances'
            self.text_filter = 'Insurance'

        if self.column_name is "Client":
            self.text_type = 'clients'
            self.text_filter = 'Client'

    def __open_window_with_list__(self) -> None:
        common.click_and_wait(
            browser=self.browser,
            locator_for_click=f"//th[contains(.,'{self.column_name}')]/a/i",
            locator_for_wait=f"//div/span[text()='{self.text_type}']"
        )
        common.wait_element_is_exit(self.browser, f"//div/span[text()='{self.text_type}']/../../div/ul/li",180)

    def close_window_with_list(self) -> None:
        try:
            if self.browser.is_element_visible(f"//div/span[text()='{self.text_type}']//preceding-sibling::div/a[@class='box-close' and @data-click='closeFilterList']"):
                self.browser.click_element_when_visible(f"//div/span[text()='{self.text_type}']//preceding-sibling::div/a[@class='box-close' and @data-click='closeFilterList']")
        except:
            pass

    def __get_list_from_current_page__(self) -> list:
        common.wait_element_is_exit(browser=self.browser,locator=f"//div/span[text()='{self.text_type}']/../../div/ul/li", timeout=180)
        all_items = self.browser.find_elements(f"//div/span[text()='{self.text_type}']/../../div/ul/li")
        list_of_valid_items = []
        for item in all_items:
            item_name = str(item.text)
            if len(item_name) > 0 and not item_name.startswith('>'):
                list_of_valid_items.append(
                    str(item.find_element_by_tag_name('span').get_attribute('innerHTML')))

        return list_of_valid_items

    def __is_click_next_clients_page__(self, window_title: str) -> bool:
        selector_next_element = f'//div/span[text()="{window_title}"]/../../div/ul/li/a[@data-bind="visible: canPageUp"]'

        if self.browser.does_page_contain_element(selector_next_element):
            if self.browser.find_element(selector_next_element).is_displayed():
                self.browser.click_element_when_visible(selector_next_element)
                self.browser.wait_until_element_is_not_visible(
                    f'//div/span[text()="{window_title}"]/../../div/div[@data-bind="visible: loading()"]')
                return True
            else:
                return False
        else:
            return False

    def __scroll_into_view_item__(self, selector_for_click: str, selector_as_result: str, window_title: str) -> bool:
        try:
            while not self.browser.does_page_contain_element(selector_for_click):
                if not self.__is_click_next_clients_page__(window_title):
                    return
            common.wait_element_is_exit(self.browser, selector_for_click)
            self.browser.scroll_element_into_view(selector_for_click)
        except:
            pass
        finally:
            self.browser.click_element_when_visible(selector_for_click)
            common.wait_element_is_exit(self.browser, selector_as_result)

    def get_list(self) -> list:
        self.__open_window_with_list__()
        list_of_valid_locations: list = self.__get_list_from_current_page__()

        while True:
            if self.__is_click_next_clients_page__(self.text_type):
                temp: list = self.__get_list_from_current_page__()
                list_of_valid_locations += temp
            else:
                break

        return list_of_valid_locations

    def select_item_from_list(self, item_name: str) -> None:
        self.browser.reload_page()
        self.__open_window_with_list__()

        selector_for_click: str = f'//div[contains(@id, FilterList)]/div/div/ul/li/a/span[contains(text(),"{item_name}")]/..'
        selector_as_result: str = f'//em[contains(.,"{self.text_filter}:") and contains(.,"{item_name.strip()}")]'
        self.__scroll_into_view_item__(selector_for_click, selector_as_result, self.text_type)
        common.wait_element_is_exit(self.browser, selector_as_result)

    def remove_item_filter(self, item_name: str):
        locator = f'//em[contains(.,"{self.text_filter}:") and contains(.,"{item_name.strip()}")]/following-sibling::a[@title="Remove filter"]'
        common.wait_element_is_exit(self.browser, locator)
        self.browser.click_element_when_visible(locator)


