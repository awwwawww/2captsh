import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import google.generativeai as genai

# إعدادات الصفحة
st.set_page_config(page_title="AI Captcha Solver", layout="wide")

st.title("🤖 AI Captcha Web Agent")

# مدخلات المستخدم
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("رابط الموقع", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 تشغيل الآن")

# أماكن العرض
log_area = st.empty()
img_area = st.empty()

async def solve():
    if not api_key:
        st.error("أدخل الـ API Key أولاً")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        log_area.info("⏳ جاري فتح المتصفح...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await stealth_async(page)

        try:
            await page.goto(target_url)
            await asyncio.sleep(5)
            
            # أخذ لقطة شاشة للمعاينة
            await page.screenshot(path="screen.png")
            img_area.image("screen.png", caption="رؤية البوت الحالية")

            # البحث عن الكابتشا
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img")
            if captcha:
                log_area.warning("📸 تم العثور على كابتشا، جاري الحل...")
                await captcha.screenshot(path="cap.png")
                
                with open("cap.png", "rb") as f:
                    response = model.generate_content([
                        "ما النص في الصورة؟ أجب بالنص فقط.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                ans = response.text.strip()
                log_area.success(f"✅ الحل: {ans}")
                
                # كتابة الحل
                input_box = await page.query_selector("input[type='text'], input[name*='captcha']")
                if input_box:
                    await input_box.fill(ans)
                    await page.keyboard.press("Enter")
                    log_area.success("🚀 تم إرسال الحل!")
            else:
                log_area.error("❌ لم يتم العثور على كابتشا")
        except Exception as e:
            st.error(f"خطأ: {e}")
        await browser.close()

if run_btn:
    asyncio.run(solve())
