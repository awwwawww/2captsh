import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import google.generativeai as genai
import os
from datetime import datetime

st.set_page_config(page_title="AI Captcha Solver Web", layout="wide")

st.title("🤖 AI Captcha Web Agent")
st.markdown("تحويل الذكاء الاصطناعي إلى عميل يقوم بحل الكابتشا آلياً")

# مدخلات المستخدم
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("Target URL", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 إطلاق العميل")

# حاويات العرض
status_log = st.empty()
col1, col2 = st.columns(2)
screenshot_placeholder = col1.empty()
result_placeholder = col2.empty()

async def solve_captcha_web():
    if not api_key:
        st.error("يرجى إدخال API Key")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        status_log.info("🌐 جاري تشغيل المتصفح الخفي...")
        # ملاحظة: في الاستضافة (Streamlit Cloud) يجب إعداد المتصفح بشكل خاص
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await stealth_async(page)

        try:
            status_log.info(f"🔗 الدخول إلى: {target_url}")
            await page.goto(target_url, wait_until="networkidle")
            
            # أخذ لقطة شاشة أولية
            await page.screenshot(path="view.png")
            screenshot_placeholder.image("view.png", caption="رؤية العميل الحالية")

            # البحث عن الكابتشا
            status_log.warning("🔍 جاري البحث عن كابتشا...")
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img")
            
            if captcha:
                await captcha.screenshot(path="captcha_crop.png")
                result_placeholder.image("captcha_crop.png", caption="الكابتشا التي رآها العميل")
                
                # تحليل Gemini
                status_log.info("🧠 Gemini يقوم بالتحليل والحل...")
                with open("captcha_crop.png", "rb") as f:
                    response = model.generate_content([
                        "ما هو النص في هذه الكابتشا؟ أجب بالنص فقط.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                solution = response.text.strip()
                status_log.success(f"✅ تم الحل: {solution}")
                
                # إدخال الحل
                input_box = await page.query_selector("input[type='text'], input[name*='captcha']")
                if input_box:
                    await input_box.fill(solution)
                    await page.keyboard.press("Enter")
                    status_log.success("🚀 تم إرسال الحل للموقع!")
                    
                    # لقطة شاشة أخيرة للنتيجة
                    await asyncio.sleep(3)
                    await page.screenshot(path="result.png")
                    screenshot_placeholder.image("result.png", caption="النتيجة بعد الحل")
            else:
                status_log.error("❌ لم يتم العثور على كابتشا في هذه الصفحة")

        except Exception as e:
            status_log.error(f"حدث خطأ: {str(e)}")
        
        await browser.close()

if run_btn:
    asyncio.run(solve_captcha_web())