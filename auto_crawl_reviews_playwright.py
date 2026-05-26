import time
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright

PLACES = {
    "北投運動中心": "1Ywfz9KlXmiRlKWqOETWJJ-6dVs_MnbMR2L_W--jCwsw",
    "士林運動中心": "1Dwr4cNIaEWHkXj-yDTP3wb5_M63lgCqNTV5Wfd3CyyE",
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

TZ = "Asia/Taipei"
GSHEET_CREDS = os.environ["GSHEET_CREDENTIALS"]


def search_place(page, place):
    page.goto(
        f"https://www.google.com/maps/search/{place}?hl=zh-TW&gl=tw",
        wait_until="domcontentloaded",
        timeout=60000
    )

    time.sleep(10)

    results = page.locator("a.hfpxzc")
    count = results.count()

    print("搜尋結果數量：", count)

    for i in range(count):
        result = results.nth(i)
        aria = result.get_attribute("aria-label") or ""

        print("找到結果：", aria)

        if aria.strip() == place:
            result.click()
            print("已點擊完全符合結果：", aria)
            time.sleep(10)
            return True

    print("沒有找到完全符合結果，可能已直接進入場館頁")
    return True

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

def review_key(review):
    return (
        review["name"],
        review["rating"],
        review["time"],
        review["review"]
    )


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
            seen.add(review_key(review))

    print(f"已讀取舊評論：{len(seen)} 則")
    return seen

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


def append_new_reviews_to_sheet(ws, place, reviews, seen):
    new_rows = []
    crawl_time = time.strftime("%Y-%m-%d %H:%M:%S")

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
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")

    return len(new_rows), len(reviews)

def make_page():
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-webgl",
            "--use-gl=swiftshader",
            "--disable-blink-features=AutomationControlled",
        ]
    )

    context = browser.new_context(
        locale="zh-TW",
        timezone_id="Asia/Taipei",
        viewport={"width": 1920, "height": 1080},
        permissions=["geolocation"],
        geolocation={
            "latitude": 25.0330,
            "longitude": 121.5659
        },
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        )
    )

    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    page = context.new_page()

    return playwright, browser, page

def main():
    client = get_gsheet_client()
    playwright, browser, page = make_page()

    try:
        for place, spreadsheet_id in PLACES.items():

            print("=" * 60)
            print("開始爬：", place)
            print("=" * 60)

            ws = get_worksheet(client, spreadsheet_id)
            seen = load_seen_reviews_from_sheet(ws)

            search_place(page, place)

            sort_button = page.locator("button:has-text('排序')").first
            sort_button.wait_for(timeout=30000)
            sort_button.click()

            time.sleep(3)

            newest = page.locator("div[role='menuitemradio']:has-text('最新')").first
            newest.click()

            print("已切換最新排序")

            time.sleep(5)

            reviews_locator = page.locator("div.jftiEf")
            reviews_locator.first.wait_for(timeout=30000)
            review_count = reviews_locator.count()

            print("畫面評論數量：", review_count)

            reviews = []

            for i in range(review_count):

                block = reviews_locator.nth(i)

                try:
                    name = block.locator(".d4r55").inner_text()
                except:
                    name = ""

                try:
                    rating = block.locator(".kvMYJc").get_attribute("aria-label") or ""
                except:
                    rating = ""

                try:
                    review_time = block.locator(".rsqaWe").inner_text()
                except:
                    review_time = ""

                try:
                    review_text = block.locator(".wiI7pd").inner_text()
                except:
                    review_text = ""

                if not is_within_one_day(review_time):
                    print("出現超過一天的評論，停止收集")
                    break

                reviews.append({
                    "name": name,
                    "rating": rating,
                    "time": review_time,
                    "review": review_text,
                })

            new_count, total_count = append_new_reviews_to_sheet(
                ws,
                place,
                reviews,
                seen
            )

            print(f"{place}：新增 {new_count} 則，檢查 {total_count} 則")

            time.sleep(5)

    finally:
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()
