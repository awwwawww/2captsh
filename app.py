import streamlit as st
import os
import subprocess
import sys

# 1. تثبيت المكتبات في الخلفية فور تشغيل الموقع (إجباري)
def install_packages():
    try:
        import playwright_stealth
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright-stealth", "playwright", "google-generativeai"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        st.rerun()

# تنفيذ التثبيت أولاً
install_packages()

# --- إعدادات الواجهة ---
st.set_page_config(page_title="AI Captcha Solver", layout="wide")
st.title("🤖 AI Captcha Web Agent")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("Gemini API Key", type="password")
    target_url = st.text_input("رابط الموقع", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 تشغيل العميل")

status = st.empty()
image_placeholder = st.empty()

# 2. دالة التشغيل التي تحتوي على الـ Imports بالداخل لمنع الخطأ عند البدء
async def start_process():
    # استدعاء المكتبات هنا (داخل الدالة) يمنع الـ ImportError عند بداية التشغيل
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth_async
    import google.generativeai as genai
    import asyncio

    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح API أولاً")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        status.info("⏳ جاري فتح المتصفح...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # تفعيل وضع التخفي
        await stealth_async(page)

        try:
            status.info(f"🔗 الانتقال إلى: {target_url}")
            await page.goto(target_url, timeout=60000)
            await asyncio.sleep(5)
            
            # عرض رؤية البوت الحالية
            await page.screenshot(path="live.png")
            image_placeholder.image("live.png", caption="لقطة شاشة حية للموقع")

            # البحث عن الكابتشا وحلها
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img")
            if captcha:
                status.warning("📸 تم العثور على كابتشا، جاري الحل...")
                await captcha.screenshot(path="cap.png")
                
                with open("cap.png", "rb") as f:
                    res = model.generate_content([
                        "حل الكابتشا في هذه الصورة، أجب بالنص فقط.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                solution = res.text.strip()
                status.success(f"✅ الحل المستخرج: {solution}")

                input_box = await page.query_selector("input[type='text'], input[name*='captcha']")
                if input_box:
                    await input_box.fill(solution)
                    await page.keyboard.press("Enter")
                    status.success("🚀 تم الإرسال!")
            else:
                status.error("❌ لم يتم العثور على كابتشا")

        except Exception as e:
            st.error(f"حدث خطأ: {e}")
        finally:
            await browser.close()

# 3. تشغيل الدالة عند ضغط الزر
if run_btn:
    import asyncio
    asyncio.run(start_process())
