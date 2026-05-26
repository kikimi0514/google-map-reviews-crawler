import time
from playwright.sync_api import sync_playwright


def make_page():
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=True
    )

    page = browser.new_page(
        locale="zh-TW",
        viewport={"width": 1920, "height": 1080}
    )

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

        # 找評論 tab
        review = page.locator("text=評論").first

        review.click()

        print("已點擊評論")

        time.sleep(5)
        view_all_button = page.locator("button:has-text('查看全部')").first

        box = view_all_button.bounding_box()
        print("查看全部 bounding box：", box)

        if box:
            page.mouse.click(
                box["x"] + box["width"] / 2,
                box["y"] + box["height"] / 2
            )

        print("已用滑鼠座標點擊查看全部")
        time.sleep(5)
        print("查看全部後網址：", page.url)
        print("查看全部後標題：", page.title())
        
        all_text = page.locator("button").all_inner_texts()

        print(all_text)
        
        print("已印出所有 button")
        time.sleep(30)

        print("測試結束")


    finally:
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    main()
