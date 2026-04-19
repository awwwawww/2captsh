import streamlit as st
import asyncio
import os
import sys

# --- حل مشكلة المكتبات الناقصة برمجياً ---
def install_requirements():
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async
        import google.generativeai as genai
    except ImportError:
        st.info("📦 جاري تهيئة بيئة العمل وتثبيت المكتبات اللازمة... قد يستغرق هذا دقيقة.")
        os.system("pip install playwright playwright-stealth google-generativeai")
        os.system("playwright install chromium")
        st.rerun()

install_requirements()

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import google.generativeai as genai

# إعدادات الصفحة
st.set_page_config(page_title="AI Captcha Web Agent v2", layout="wide")

st.title("🤖 AI Captcha Web Agent - النسخة الاحترافية")
st.markdown("---")

# واجهة المستخدم في الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("Gemini API Key", type="password", help="أدخل مفتاح جوجل جيمناي")
    target_url = st.text_input("رابط الموقع المستهدف", value="https://2captcha.com/enterpage")
    st.markdown("---")
    run_btn = st.button("🚀 إطلاق العميل الذكي", use_container_width=True)

# تقسيم الشاشة للعرض
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("📺 بث حي لرؤية العميل")
    screenshot_placeholder = st.empty()
with col2:
    st.subheader("📝 سجل العمليات")
    log_placeholder = st.empty()

def update_log(msg, type="info"):
    if type == "info": st.toast(msg)
    log_placeholder.write(f"[{sys.platform}] {msg}")

async def run_agent():
    if not api_key:
        st.error("⚠️ يرجى إدخال Gemini API Key أولاً!")
        return

    # إعداد Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    async with async_playwright() as p:
        update_log("🌐 جاري تشغيل المتصفح (Chromium)...")
        # تشغيل المتصفح في وضع الخفاء للسيرفر
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        await stealth_async(page)

        try:
            update_log(f"🔗 الانتقال إلى: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # تحديث الصورة للمستخدم
            await page.screenshot(path="view.png")
            screenshot_placeholder.image("view.png")

            # البحث عن الكابتشا
            update_log("🔍 فحص الصفحة بحثاً عن كابتشا...")
            captcha = await page.query_selector("img[src*='captcha'], canvas, .captcha-img, #captcha-img")
            
            if captcha:
                update_log("📸 تم اكتشاف كابتشا! جاري التحليل برؤية الذكاء الاصطناعي...")
                await captcha.screenshot(path="captcha_crop.png")
                
                # إرسال الصورة لـ Gemini
                with open("captcha_crop.png", "rb") as f:
                    response = model.generate_content([
                        "ما هو النص أو الأرقام الموجودة في هذه الكابتشا؟ أجب بالحل فقط بدقة.",
                        {"mime_type": "image/png", "data": f.read()}
                    ])
                
                solution = response.text.strip()
                update_log(f"✅ الحل المقترح: {solution}")

                # إدخال الحل تلقائياً
                # نحاول البحث عن أكثر من نوع لخانة الإدخال
                input_field = await page.query_selector("input[name*='captcha'], input[id*='captcha'], input[type='text']")
                if input_field:
                    await input_field.fill(solution)
                    update_log("⌨️ تم إدخال الحل في الخانة المناسبة.")
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(2)
                    
                    # لقطة نهائية للنتيجة
                    await page.screenshot(path="final.png")
                    screenshot_placeholder.image("final.png", caption="النتيجة بعد محاولة الحل")
            else:
                update_log("❌ لم يتم العثور على كابتشا واضحة في هذه الصفحة.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء التنفيذ: {e}")
        finally:
            await browser.close()
            update_log("🏁 تم إغلاق الجلسة.")

if run_btn:
    asyncio.run(run_agent())
