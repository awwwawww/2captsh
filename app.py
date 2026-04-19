import streamlit as st
import asyncio
import os

# محاولة الاستدعاء
try:
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth_async
    import google.generativeai as genai
except ImportError:
    st.error("المكتبات لا تزال في طور التثبيت... يرجى الانتظار دقيقة وعمل Refresh للصفحة.")
    st.stop()

st.set_page_config(page_title="AI Captcha Solver", layout="wide")
st.title("🤖 AI Captcha Web Agent")

with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("رابط الموقع", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 تشغيل الآن")

async def run_logic():
    # التأكد من تحميل المتصفح داخل السيرفر
    os.system("playwright install chromium")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page)
        
        await page.goto(target_url)
        st.info("تم فتح الموقع بنجاح، جاري فحص الكابتشا...")
        await page.screenshot(path="screen.png")
        st.image("screen.png")
        await browser.close()

if run_btn and api_key:
    asyncio.run(run_logic())
