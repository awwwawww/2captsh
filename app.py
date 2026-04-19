import os
import subprocess
import sys

# 1. وظيفة التثبيت الإجباري (قبل أي استدعاء آخر)
def initial_setup():
    try:
        import playwright_stealth
        import google.generativeai
    except ImportError:
        # إذا لم يجد المكتبات، سيقوم بتثبيتها فوراً
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright-stealth", "playwright", "google-generativeai"])
        # تحميل المتصفح
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        # إعادة تشغيل التطبيق ليعمل بالمكتبات الجديدة
        import streamlit as st
        st.rerun()

# تشغيل التثبيت
initial_setup()

# الآن نستدعي المكتبات بأمان
import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import google.generativeai as genai

# --- واجهة التطبيق ---
st.set_page_config(page_title="AI Captcha Solver", layout="wide")
st.title("🤖 AI Captcha Web Agent")

with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("رابط الموقع", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 تشغيل الآن")

status = st.empty()
image_col = st.empty()

async def run_bot():
    if not api_key:
        st.error("يرجى إدخال API Key")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        status.info("⏳ جاري فتح المتصفح...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page)

        try:
            status.info(f"🔗 فتح الرابط: {target_url}")
            await page.goto(target_url, timeout=60000)
            await asyncio.sleep(5)
            
            # لقطة شاشة للمعاينة
            await page.screenshot(path="screen.png")
            image_col.image("screen.png", caption="رؤية البوت الحالية")

            # البحث عن كابتشا
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img")
            if captcha:
                status.warning("📸 تم العثور على كابتشا، جاري الحل...")
                await captcha.screenshot(path="cap.png")
                
                with open("cap.png", "rb") as f:
                    response = model.generate_content([
                        "ما النص في الصورة؟ أجب بالنص فقط.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                ans = response.text.strip()
                status.success(f"✅ تم الحل: {ans}")

                input_box = await page.query_selector("input[type='text'], input[name*='captcha']")
                if input_box:
                    await input_box.fill(ans)
                    await page.keyboard.press("Enter")
                    status.success("🚀 تم إرسال الحل!")
            else:
                status.error("❌ لم يتم العثور على كابتشا")

        except Exception as e:
            st.error(f"خطأ: {e}")
        await browser.close()

if run_btn:
    asyncio.run(run_bot())
