import pytest
import allure
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as chrome_options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture   # запускает хромдрайвер
def get_chrome_options():
    options = chrome_options()
    options.add_argument('chrome')
    options.add_argument('--start-maximized')
    options.add_argument('--window-size 1650, 900')
    return options

@pytest.fixture()    # инициализирует вебдрайвер
def get_webdriver(get_chrome_options):
    options = get_chrome_options
    driver = webdriver.Chrome(options=options)
    return driver

@pytest.fixture(scope="function")    # указывает с чего начать и закрывает браузер
def setup(request, get_webdriver):
    driver = get_webdriver
    base_url = 'https://www.labirint.ru/'
    if request.cls is not None:
        request.cls.driver = driver
    driver.get(base_url)
    driver.delete_all_cookies()    # удаляет куки
    yield driver
    driver.quit()

#@pytest.fixture
#def chrome_options(chrome_options):
    #chrome_options.add_argument('--no-sandbox')
    #chrome_options.add_argument('--log-level=3')

    #return chrome_options


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item):
    # This function helps to detect that some test failed
    # and pass this information to teardown:

    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    return rep


@pytest.fixture
def web_browser(request, get_webdriver):

    browser = get_webdriver
    browser.set_window_size(1600, 1000)

    # Return browser instance to test case:
    yield browser

    # Do teardown (this code will be executed after each test):

    if request.node.rep_call.failed:
        # Make the screen-shot if test failed:
        try:
            browser.execute_script("document.body.bgColor = 'white';")

            # Make screen-shot for local debug:
            browser.save_screenshot('screenshots/' + str(uuid.uuid4()) + '.png')

            # Attach screenshot to Allure report:
            allure.attach(browser.get_screenshot_as_png(),
                          name=request.function.__name__,
                          attachment_type=allure.attachment_type.PNG)

            # For happy debugging:
            print('URL: ', browser.current_url)
            print('Browser logs:')
            for log in browser.get_log('browser'):
                print(log)

        except:
            pass # just ignore any errors here


def get_test_case_docstring(item):
    """ Данная функция получает строку документа из тестового примера и форматирует ее,
        что бы показывать эту строку документа вместо имени тестового примера в отчетах.
    """

    full_name = ''

    if item._obj.__doc__:
        # Remove extra whitespaces from the doc string:
        name = str(item._obj.__doc__.split('.')[0]).strip()
        full_name = ' '.join(name.split())

        # Generate the list of parameters for parametrized test cases:
        if hasattr(item, 'callspec'):
            params = item.callspec.params

            res_keys = sorted([k for k in params])
            # Create List based on Dict:
            res = ['{0}_"{1}"'.format(k, params[k]) for k in res_keys]
            # Add dict with all parameters to the name of test case:
            full_name += ' Parameters ' + str(', '.join(res))
            full_name = full_name.replace(':', '')

    return full_name


def pytest_itemcollected(item):
    """ Данная функция изменяет имена тестовых случаев "on the fly" во время выполнения тест-кейсов.
    """

    if item._obj.__doc__:
        item._nodeid = get_test_case_docstring(item)


def pytest_collection_finish(session):
    """ Данная функция изменяла имена тестовых случаев "on the fly".
        когда мы используем параметр --collect-only для pytest
        (чтобы получить полный список всех существующих тестов).
    """

    if session.config.option.collectonly is True:
        for item in session.items:
            # If test case has a doc string we need to modify it's name to
            # it's doc string to show human-readable reports and to
            # automatically import test cases to test management system.
            if item._obj.__doc__:
                full_name = get_test_case_docstring(item)
                print(full_name)

        pytest.exit('Выполнено!')
