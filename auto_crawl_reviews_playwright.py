import time
from playwright.sync_api import sync_playwright


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
    playwright, browser, page = make_page()

    try:
        page.goto(
            "https://www.google.com/maps/search/北投運動中心?hl=zh-TW&gl=tw",
            wait_until="domcontentloaded",
            timeout=60000
        )

        time.sleep(10)

        print("目前標題：", page.title())
        print("目前網址：", page.url)

        review_url = page.url.split("?")[0] + "/reviews?hl=zh-TW&gl=tw"

        print("評論網址：", review_url)

        page.goto(
            review_url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        time.sleep(10)

        print("進評論網址後標題：", page.title())
        print("進評論網址後網址：", page.url)

        sort_button = page.locator(
            "button:has-text('排序')"
        ).first
        
        sort_button.click()
        
        print("已點擊排序")
        
        time.sleep(3)
        
        menu_text = page.locator(
            "div[role='menuitemradio']"
        ).all_inner_texts()
        
        print("排序選單：", menu_text)
        
        newest = page.locator(
            "div[role='menuitemradio']:has-text('最新')"
        ).first
        
        newest.click()
        
        print("已點擊最新")
        
        time.sleep(5)

        reviews = page.locator("div.jftiEf")

        print("評論數量：", reviews.count())
        
        for i in range(min(5, reviews.count())):
        
            review = reviews.nth(i)
        
            try:
                name = review.locator(".d4r55").inner_text()
            except:
                name = ""
        
            try:
                content = review.locator(".wiI7pd").inner_text()
            except:
                content = ""
        
            try:
                time_text = review.locator(".rsqaWe").inner_text()
            except:
                time_text = ""
        
            print("=" * 40)
            print("作者：", name)
            print("時間：", time_text)
            print("評論：", content)

    finally:
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()
