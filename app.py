import streamlit as st
import subprocess
import sys
import os
import asyncio

# --- 1. وظيفة التثبيت الفوري مع تحديث المسارات ---
def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        # إجبار البايثون على تحديث قائمة المكتبات لديه
        import site
        from importlib import reload
        reload(site)

# تنفيذ التثبيت قبل أي شيء
with st.spinner("جاري تهيئة المحركات..."):
    install_and_import("playwright")
    install_and_import("playwright-stealth", "playwright_stealth")
    install_and_import("google-generativeai", "google.generativeai")
    # تحميل الكروم
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

# استدعاء المكتبات الآن بعد الضمان
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import google.generativeai as genai

st.set_page_config(page_title="AI Captcha Agent", layout="wide")
st.title("🤖 AI Captcha Web Agent")

# واجهة المستخدم
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("Target URL", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 إطلاق العميل")

async def run_process():
    if not api_key:
        st.error("أدخل المفتاح أولاً")
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await stealth_async(page)
        
        try:
            await page.goto(target_url, timeout=60000)
            await page.screenshot(path="view.png")
            st.image("view.png")
            
            # محاولة حل الكابتشا
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img")
            if captcha:
                await captcha.screenshot(path="cap.png")
                with open("cap.png", "rb") as f:
                    res = model.generate_content(["حل الكابتشا", {"mime_type": "image/png", "data": f.read()}])
                st.success(f"الحل: {res.text}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            await browser.close()

if run_btn:
    asyncio.run(run_process())
