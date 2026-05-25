import json
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

import time
import os
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


PLACE = "臺北市松山運動中心"
TZ = ZoneInfo("Asia/Taipei")

GSHEET_CREDS = os.environ["GSHEET_CREDENTIALS"]
SHEET_IDS = {
    "士林運動中心": "1Dwr4cNIaEWHkXj-yDTP3wb5_M63lgCqNTV5Wfd3CyyE",
    "北投運動中心": "1Ywfz9KlXmiRlKWqOETWJJ-6dVs_MnbMR2L_W--jCwsw",
    "臺北市大同運動中心": "1w2yeAKHoFvGoFUaVIusBc7FFMGQ3NGlbxbKabeaecXo",
    "臺北市大安運動中心": "1f3c-sHp_uvHDmye4qMKHl3Q6oOb78NAn6QqSlfKFLto",
    "臺北市中山運動中心": "1UA80sFh0Ro6eSythWg5Kr68ACGf7fY02HWPHRXtzLnM",
    "臺北市內湖運動中心 Taipei Neihu Sports Center": "1dr_htEoWL_vv1S7sPzPBVJqTM_4nfI5Vo7XVeXu5Hg4",
    "臺北市文山運動中心": "1v0rVk7qcMThs4wt-zPu5uRz8Zx4WRG_d5a_4F2mJYa8",
    "臺北市松山運動中心": "1CF2FTTCf3MXObbMjSgXt1pLYVkGgl52O8lMBLfiSiwU",
    "臺北市信義運動中心 Taipei Xinyi Sports Center": "1KcAdgF92x-TM7YvUmKdt5QOZeFmZQHR0E9JGnyp2-Bc",
    "臺北萬華運動中心": "1UJFuQw6g7wAINWYDmtp6Uu4uCwZjWFMAOFu7xiUJtSk",
    "舞動陽光-中正運動中心": "16ahK9TfRC-l-CNk-3WO3MIJaxKZ1Jk3EnIxrdCLoM_0",
}

def make_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    return driver

from urllib.parse import quote


def search_place(driver, keyword):
    url = "https://www.google.com/maps/search/" + quote(keyword) + "?hl=zh-TW&gl=tw"
    driver.get(url)

    time.sleep(10)

    results = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
    print("搜尋結果數量：", len(results))

    clicked = False

    for r in results:
        try:
            aria = r.get_attribute("aria-label") or ""
            print("找到結果：", aria)

            if aria.strip() == PLACE:
                print("準備點擊：", aria)

                driver.execute_script(
                    "arguments[0].scrollIntoView(true);",
                    r
                )

                time.sleep(1)

                driver.execute_script(
                    "arguments[0].click();",
                    r
                )

                clicked = True
                print("已點擊")
                time.sleep(10)
                break

        except Exception as e:
            print(e)

    if not clicked:
        print("沒有搜尋結果清單，可能已直接進入場館頁")
        time.sleep(5)


def click_review_tab(driver):
    time.sleep(3)

    buttons = driver.find_elements(By.TAG_NAME, "button")

    for btn in buttons:
        try:
            text = btn.text.strip()
            aria = btn.get_attribute("aria-label") or ""

            if text == "評論" or "評論" in aria:
                driver.execute_script(
                    "arguments[0].click();",
                    btn
                )
                time.sleep(5)
                return True

        except:
            pass

    return False
    
def click_all_reviews(driver):

    time.sleep(3)

    try:

        all_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[text()='全部']"
                )
            )
        )

        print("找到全部按鈕")

        driver.execute_script(
            "arguments[0].click();",
            all_button
        )

        time.sleep(5)

        print("已點擊全部")

        return True

    except Exception as e:

        print("找不到全部按鈕")
        print(e)

        return False



def sort_reviews_by_newest(driver):
    time.sleep(3)

    buttons = driver.find_elements(By.TAG_NAME, "button")

    for btn in buttons:
        try:
            text = btn.text.strip()
            aria = btn.get_attribute("aria-label") or ""

            if "排序" in text or "排序" in aria:
                driver.execute_script(
                    "arguments[0].click();",
                    btn
                )
                time.sleep(2)
                break

        except:
            pass

    menu_items = driver.find_elements(By.CSS_SELECTOR, "div[role='menuitemradio']")

    for item in menu_items:
        try:
            text = item.text.strip()

            if "最新" in text:
                driver.execute_script(
                    "arguments[0].click();",
                    item
                )
                time.sleep(5)
                print("已切換成最新排序")
                return True

        except:
            pass

    print("找不到最新排序選項")
    return False



def click_more_buttons(driver):
    review_blocks = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")

    for block in review_blocks:
        try:
            buttons = block.find_elements(By.TAG_NAME, "button")

            for btn in buttons:
                text = btn.text.strip()

                if text == "全文":
                    driver.execute_script(
                        "arguments[0].click();",
                        btn
                    )
                    time.sleep(0.1)

        except:
            pass


def find_review_scrollable(driver):
    candidates = driver.find_elements(
        By.CSS_SELECTOR,
        "div[role='main'] div"
    )

    best = None
    max_scroll_height = 0

    for el in candidates:
        try:
            scroll_height = driver.execute_script(
                "return arguments[0].scrollHeight;",
                el
            )
            client_height = driver.execute_script(
                "return arguments[0].clientHeight;",
                el
            )

            if scroll_height > client_height and scroll_height > max_scroll_height:
                best = el
                max_scroll_height = scroll_height

        except:
            pass

    return best


def parse_visible_reviews(driver):

    soup = BeautifulSoup(
        driver.page_source,
        "html.parser"
    )

    reviews = []

    for block in soup.select("div.jftiEf"):

        name_tag = block.select_one(".d4r55")
        rating_tag = block.select_one(".kvMYJc")
        time_tag = block.select_one(".rsqaWe")
        text_tag = block.select_one(".wiI7pd")

        name = (
            name_tag.get_text(strip=True)
            if name_tag else ""
        )

        rating = (
            rating_tag.get("aria-label")
            if rating_tag else ""
        )

        review_time = (
            time_tag.get_text(strip=True)
            if time_tag else ""
        )

        review_text = (
            text_tag.get_text(strip=True)
            if text_tag else ""
        )

        if name or review_text:

            reviews.append({
                "name": name,
                "rating": rating,
                "time": review_time,
                "review": review_text
            })

    return reviews


def review_key(review):

    return (
        review["name"],
        review["rating"],
        review["time"],
        review["review"]
    )

def get_gsheet_client():
    creds = Credentials.from_service_account_info(
        json.loads(GSHEET_CREDS),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)


def get_worksheet(client, spreadsheet_id):
    sh = client.open_by_key(spreadsheet_id)
    ws = sh.sheet1

    values = ws.get_all_values()

    if not values:
        ws.append_row(["抓取時間", "場館", "作者", "評分", "評論時間", "評論內容"])

    return ws

def load_seen_reviews_from_sheet(ws):

    seen = set()

    rows = ws.get_all_records()

    for row in rows:

        review = {
            "name": str(row.get("作者", "")).strip(),
            "rating": str(row.get("評分", "")).strip(),
            "time": str(row.get("評論時間", "")).strip(),
            "review": str(row.get("評論內容", "")).strip(),
        }

        if review["name"] or review["review"]:

            seen.add(
                review_key(review)
            )

    print(f"已從 Google Sheets 讀取舊評論：{len(seen)} 則")

    return seen

def append_new_reviews_to_sheet(
    ws,
    place,
    reviews,
    seen
):

    new_rows = []

    crawl_time = datetime.now(TZ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for r in reviews:

        key = review_key(r)

        if key in seen:
            continue

        seen.add(key)

        new_rows.append([
            crawl_time,
            place,
            r["name"],
            r["rating"],
            r["time"],
            r["review"],
        ])

    if new_rows:

        ws.append_rows(
            new_rows,
            value_input_option="USER_ENTERED"
        )

    return len(new_rows), len(reviews)

def is_within_one_day(review_time):

    if not review_time:
        return True

    if "剛剛" in review_time:
        return True

    if "分鐘前" in review_time:
        return True

    if "小時前" in review_time:
        return True

    if review_time == "1 天前":
        return True

    return False


def crawl_reviews(driver, ws, stop_after_no_new=15):
    seen = load_seen_reviews_from_sheet(ws)

    click_more_buttons(driver)

    reviews = parse_visible_reviews(driver)
    
    target_reviews = []
    
    for r in reviews:
        if is_within_one_day(r["time"]):
            target_reviews.append(r)

    new_count, total_count = append_new_reviews_to_sheet(
        ws,
        PLACE,
        target_reviews,
        seen
    )

    print(
        f"初始寫入 {new_count} 則｜"
        f"累計 {len(seen)} 則"
    )

    scrollable = find_review_scrollable(driver)

    if scrollable is None:
        print("找不到評論滾動區")
        return seen

    no_new_count = 0

    scroll_count = 0

    last_scroll_top = -1

    same_scroll_count = 0
    old_batch_count = 0

    while True:

        if "/contrib/" in driver.current_url:
            print("跳到使用者個人頁了，停止程式")
            break

        scroll_count += 1

        driver.execute_script(
            "arguments[0].scrollTo(0, arguments[0].scrollHeight);",
            scrollable
        )
        time.sleep(3)

        time.sleep(1.8)

        click_more_buttons(driver)

        reviews = parse_visible_reviews(driver)
        
        target_reviews = []

        old_time_found = False
        for r in reviews:
            review_time = r["time"]
            if is_within_one_day(review_time):
                target_reviews.append(r)
            else:
                old_time_found = True
                break
        new_count, total_count = append_new_reviews_to_sheet(
            ws,
            PLACE,
            target_reviews,
            seen
        )       

        current_scroll_top = driver.execute_script(
            "return arguments[0].scrollTop;",
            scrollable
        )

        print(
            f"第 {scroll_count} 次滾動｜"
            f"新增 {new_count} 則｜"
            f"累計 {len(seen)} 則"
        )

        if new_count == 0:
            no_new_count += 1
        else:
            no_new_count = 0
        
        if total_count > 0:
            old_count = total_count - new_count
            old_ratio = old_count / total_count

            if old_ratio >= 0.8:
                old_batch_count += 1
            else:
                old_batch_count = 0

        if current_scroll_top == last_scroll_top:
            same_scroll_count += 1
        else:
            same_scroll_count = 0
            old_batch_count = 0

        last_scroll_top = current_scroll_top

        if old_time_found:
            print("已經出現太舊的評論，停止")
            break
        
        if (
            old_batch_count >= 3
            or
            (
                no_new_count >= stop_after_no_new
                and
                same_scroll_count >= 3
            )
        ):
            print("已經到底，沒有更多評論")
            break

    return seen


PLACES = [
    "北投運動中心",
    "士林運動中心",
    "臺北市大同運動中心",
    "臺北市大安運動中心",
    "舞動陽光-中正運動中心",
    "臺北市內湖運動中心 Taipei Neihu Sports Center",
    "臺北市松山運動中心",
    "臺北萬華運動中心",
    "臺北市文山運動中心",
    "臺北市信義運動中心 Taipei Xinyi Sports Center",
    "臺北市中山運動中心"
]


driver = make_driver()

try:

    for place in PLACES:

        PLACE = place
        spreadsheet_id = SHEET_IDS[place]
        client = get_gsheet_client()
        ws = get_worksheet(client, spreadsheet_id)

        print("=" * 60)
        print("開始爬：", PLACE)
        print("=" * 60)

        try:

            search_place(driver, PLACE)

            success = click_review_tab(driver)

            if not success:
                print("找不到評論按鈕")
                continue
            
            time.sleep(5)
            
            print("點評論後網址：", driver.current_url)
            print("點評論後標題：", driver.title)
            
            all_success = click_all_reviews(driver)
            
            if not all_success:
                print("沒有成功點擊全部，跳過這間")
                continue
            
            sorted_success = sort_reviews_by_newest(driver)
            
            if not sorted_success:
                print("沒有成功切換最新排序，跳過這間")
                continue
            
            seen_reviews = crawl_reviews(
                driver=driver,
                ws=ws,
                stop_after_no_new=15
            )

            print("完成：", PLACE)
            print("總共寫入：", len(seen_reviews), "則評論")
            print("已更新 Google Sheets")

            time.sleep(5)

        except Exception as e:

            print("這間失敗：", PLACE)
            print(e)

            continue

finally:

    driver.quit()

# def save_reviews(reviews):

#     seen = set()

#     with open(
#         "google_map_reviews.txt",
#         "w",
#         encoding="utf-8"
#     ) as f:

#         for r in reviews:

#             key = (
#                 r["name"],
#                 r["rating"],
#                 r["time"],
#                 r["review"]
#             )

#             if key in seen:
#                 continue

#             seen.add(key)

#             f.write(f"作者：{r['name']}\n")
#             f.write(f"評分：{r['rating']}\n")
#             f.write(f"時間：{r['time']}\n")
#             f.write(f"評論：{r['review']}\n")
#             f.write("-" * 50 + "\n")


# driver = make_driver()

# search_place(
#     driver,
#     "臺北市內湖運動中心"
# )

# success = click_review_tab(driver)

# if not success:
#     print("找不到評論按鈕")
#     driver.quit()
#     exit()

# time.sleep(5)

# scroll_reviews(
#     driver,
#     scroll_times=30
# )

# html = driver.page_source

# driver.quit()

# reviews = parse_reviews(html)

# print("總共爬到：", len(reviews), "則評論")

# save_reviews(reviews)

# print("已存成 google_map_reviews.txt")
