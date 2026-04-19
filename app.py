import streamlit as st
import subprocess
import sys
import os
import asyncio

# --- 1. وظيفة التثبيت القسري للمكتبات والمحركات ---
def install_requirements():
    try:
        import playwright_stealth
        import google.generativeai
    except ImportError:
        with st.status("🛠️ جاري تهيئة بيئة العمل وتثبيت المحركات... قد يستغرق ذلك دقيقة"):
            # تثبيت المكتبات البرمجية
            subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "playwright-stealth", "google-generativeai"])
            # تثبيت متصفح كروم داخل السيرفر
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        st.success("✅ تمت التهيئة بنجاح! أعد الضغط على الزر.")
        st.rerun()

# --- 2. إعداد واجهة المستخدم ---
st.set_page_config(page_title="AI Captcha Web Agent", layout="wide")
st.title("🤖 AI Captcha Web Agent")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("Gemini API Key", type="password", help="أدخل مفتاح جوجل جيمناي هنا")
    target_url = st.text_input("رابط الموقع المستهدف", value="https://2captcha.com/enterpage")
    run_btn = st.button("🚀 إطلاق العميل الذكي", use_container_width=True)

# أماكن عرض النتائج
status_placeholder = st.empty()
log_placeholder = st.expander("سجل العمليات التفصيلي", expanded=True)
image_placeholder = st.empty()

# --- 3. الدالة الأساسية للتشغيل ---
async def start_agent():
    # استدعاء المكتبات داخل الدالة لمنع ImportError عند بداية التشغيل
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth_async
    import google.generativeai as genai

    if not api_key:
        st.error("⚠️ يرجى إدخال Gemini API Key في القائمة الجانبية!")
        return

    # إعداد نموذج Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        status_placeholder.info("🌐 جاري تشغيل المتصفح الخفي...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # تفعيل وضع التخفي لتجنب كشف البوت
        await stealth_async(page)

        try:
            status_placeholder.info(f"🔗 جاري الدخول إلى: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5) # انتظار تحميل الصفحة بالكامل
            
            # أخذ لقطة شاشة للمعالجة والعرض
            await page.screenshot(path="live_view.png")
            image_placeholder.image("live_view.png", caption="رؤية العميل الحالية للموقع")

            # البحث عن عنصر الكابتشا (img أو canvas)
            log_placeholder.write("🔍 البحث عن رموز الكابتشا...")
            captcha_element = await page.query_selector("img[src*='captcha'], canvas, .captcha-img, #captcha-img")
            
            if captcha_element:
                log_placeholder.warning("📸 تم العثور على كابتشا! جاري التحليل برؤية Gemini...")
                await captcha_element.screenshot(path="captcha_crop.png")
                
                # إرسال الصورة للذكاء الاصطناعي لحلها
                with open("captcha_crop.png", "rb") as f:
                    response = model.generate_content([
                        "ما هو النص أو الأرقام الموجودة في هذه الكابتشا؟ أجب بالحل فقط بدقة شديدة وبدون أي كلمات أخرى.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                captcha_solution = response.text.strip()
                log_placeholder.success(f"✅ الحل المستخرج: {captcha_solution}")

                # البحث عن خانة الإدخال وكتابة الحل
                input_field = await page.query_selector("input[name*='captcha'], input[id*='captcha'], input[type='text']")
                if input_field:
                    await input_field.fill(captcha_solution)
                    log_placeholder.write("⌨️ تم إدخال الحل في الموقع...")
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(3)
                    
                    # تحديث الصورة النهائية
                    await page.screenshot(path="final_result.png")
                    image_placeholder.image("final_result.png", caption="النتيجة بعد محاولة الحل")
                    status_placeholder.success("🚀 تمت العملية بنجاح!")
            else:
                log_placeholder.error("❌ لم يتم العثور على كابتشا في هذه الصفحة.")
                status_placeholder.warning("انتهى الفحص: لم تظهر أي كابتشا.")

        except Exception as e:
            st.error(f"حدث خطأ تقني: {str(e)}")
        finally:
            await browser.close()

# --- 4. معالج الضغط على الزر ---
if run_btn:
    # التأكد من التثبيت أولاً
    install_requirements()
    # تشغيل العملية البرمجية
    asyncio.run(start_agent())
