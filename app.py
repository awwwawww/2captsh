import os
import sys
import subprocess

# وظيفة لإجبار السيرفر على تثبيت المكتبات الناقصة فوراً
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from playwright_stealth import stealth_async
except ImportError:
    install_package("playwright-stealth")
    from playwright_stealth import stealth_async

try:
    import google.generativeai as genai
except ImportError:
    install_package("google-generativeai")
    import google.generativeai as genai

import streamlit as st
import asyncio
from playwright.async_api import async_playwright

# --- إعدادات الواجهة ---
st.set_page_config(page_title="AI Agent Solver", layout="wide")
st.title("🤖 AI Captcha Web Agent")

with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("رابط الموقع", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 تشغيل العميل")

log_status = st.empty()
display_col = st.columns(1)[0]

async def run_logic():
    if not api_key:
        st.error("يرجى إدخال مفتاح API")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        log_status.info("⏳ جاري تحضير المتصفح...")
        # إجبار السيرفر على تحميل محرك الكروم إذا لم يكن موجوداً
        os.system("playwright install chromium") 
        
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page)

        try:
            log_status.info(f"🔗 فتح الرابط: {target_url}")
            await page.goto(target_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # أخذ لقطة شاشة للمعاينة
            await page.screenshot(path="view.png")
            st.image("view.png", caption="ما يراه العميل الآن")

            # محاولة حل الكابتشا
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img")
            if captcha:
                log_status.warning("📸 اكتشاف كابتشا! جاري الحل بالذكاء الاصطناعي...")
                await captcha.screenshot(path="cap.png")
                
                with open("cap.png", "rb") as f:
                    response = model.generate_content([
                        "ما هو النص في هذه الصورة؟ أجب بالنص فقط.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                solution = response.text.strip()
                log_status.success(f"✅ الحل المستخرج: {solution}")

                input_box = await page.query_selector("input[type='text'], input[name*='captcha']")
                if input_box:
                    await input_box.fill(solution)
                    await page.keyboard.press("Enter")
                    log_status.success("🚀 تم إرسال الحل!")
            else:
                log_status.error("❌ لم يتم العثور على كابتشا")

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
        
        await browser.close()

if run_btn:
    asyncio.run(run_logic())
