# === streamlit_app.py ===
import streamlit as st
import asyncio
import os
import io
import sys
from pipeline import run_pipeline
from service_mapper import map_services
from gpt_cost import (print_cost_summary, reset_cost_summary, tracked_chat_completion)


st.set_page_config(page_title="Sustainability Report Analyzer", layout="centered")
st.title("📄 Sustainability Report Analyzer")

st.markdown("""
Upload a **Sustainability Report PDF**, and click **Run Pipeline** to detect digitalization needs.
Then click **Map Services** to match them with Ergosign offerings.
""")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)
uploaded_file = st.file_uploader("Upload Sustainability Report PDF", type=["pdf"])

if uploaded_file:
    uploaded_name = uploaded_file.name

    if st.session_state.get("last_uploaded_file") != uploaded_name:
        reset_cost_summary()  # ✅ Reset only when new file uploaded
        st.session_state["last_uploaded_file"] = uploaded_name

    temp_pdf_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state["pdf_path"] = temp_pdf_path

    if "pipeline_done" not in st.session_state:
        st.session_state["pipeline_done"] = False
    if "mapping_done" not in st.session_state:
        st.session_state["mapping_done"] = False

    if st.button("▶️ Run Pipeline (Digitalization Detection)"):
        async def run_with_output():
            queue = asyncio.Queue()
            output_area = st.empty()

            async def display_output():
                while True:
                    msg_type, msg = await queue.get()
                    if msg_type == "update":
                        output_area.text(msg)
                    elif msg_type == "done":
                        break

            display_task = asyncio.create_task(display_output())
            await run_pipeline(temp_pdf_path, output_queue=queue)
            await queue.put(("done", ""))
            await display_task

        with st.spinner("Running pipeline..."):
            asyncio.run(run_with_output())

        if os.path.exists("opportunities.pdf") and os.path.exists("opportunities.xlsx"):
            st.session_state["pipeline_done"] = True
            st.success("Pipeline completed!")

    if st.session_state["pipeline_done"]:
        with open("opportunities.xlsx", "rb") as f:
            st.download_button("📅 Download Excel Report", f, file_name="opportunities.xlsx")

    if st.button("💼 Map Services to Digitalization Suggestions"):
        if st.session_state["pipeline_done"]:
            with st.spinner("Mapping services..."):
                asyncio.run(map_services())

            if os.path.exists("mapped_services.pdf") and os.path.exists("mapped_services.xlsx"):
                st.session_state["mapping_done"] = True
                st.success("Mapping completed!")
        else:
            st.warning("Please run the pipeline first.")

    if st.session_state["mapping_done"]:
        with open("mapped_services.xlsx", "rb") as f:
            st.download_button("📅 Download Mapped Services Excel", f, file_name="mapped_services.xlsx")

    # GPT Cost Tracker Button
    if st.button("GPT cost tracker"):
        buffer = io.StringIO()
        sys.stdout = buffer
        try:
            print_cost_summary()
        finally:
            sys.stdout = sys.__stdout__
        st.code(buffer.getvalue(), language="text")
