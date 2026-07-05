import streamlit as st
import json
import time
import pandas as pd
import random
from datetime import datetime
from groq import Groq

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="GuardEye: Complete Autonomous Traffic Enforcement Suite",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Light Mode (White/Slate) Styling
st.markdown("""
<style>
    /* Global Background and Typography overrides */
    .reportview-container { background: #f8fafc; color: #1e293b; }
    .stApp { background-color: #f8fafc; }
    .stCodeBlock { border-radius: 8px; border: 1px solid #e2e8f0; }
    
    /* Make sure all titles and text render sharp in light mode */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #1e293b !important;
    }
    
    /* Premium White Card Containers */
    .soc-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    
    /* Agent Reasoning Containers - Color coded for premium readability */
    .thought-container {
        background-color: #eff6ff;
        border-left: 5px solid #3b82f6;
        padding: 12px;
        margin: 8px 0px;
        border-radius: 6px;
        color: #1e3a8a;
        font-family: 'Courier New', Courier, monospace;
    }
    .action-container {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 12px;
        margin: 8px 0px;
        border-radius: 6px;
        color: #78350f;
        font-family: 'Courier New', Courier, monospace;
    }
    .observation-container {
        background-color: #f0fdf4;
        border-left: 5px solid #10b981;
        padding: 12px;
        margin: 8px 0px;
        border-radius: 6px;
        color: #065f46;
        font-family: 'Courier New', Courier, monospace;
    }
    .dispatch-alert {
        background-color: #fef2f2;
        border: 1px solid #fca5a5;
        color: #991b1b;
        padding: 12px;
        border-radius: 6px;
        margin-top: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- IN-MEMORY DATABASE STATE (PostgreSQL Simulator via Session State) ---
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = True
    
    # Live Violation Logs Table (Simulating YOLOv8 pipeline database logs)
    st.session_state.violations_db = [
        {"violation_id": "V-901", "timestamp": "2026-07-04 09:12:04", "junction": "Junction-04 (Hitec City)", "vehicle_id": "TS03EP4412", "type": "Helmet Violation", "confidence": 0.94, "processed": True},
        {"violation_id": "V-902", "timestamp": "2026-07-04 10:45:19", "junction": "Junction-04 (Hitec City)", "vehicle_id": "TS08EQ1102", "type": "Speeding (84 km/h)", "confidence": 0.91, "processed": False},
        {"violation_id": "V-903", "timestamp": "2026-07-04 14:22:50", "junction": "Junction-02 (KITS Campus)", "vehicle_id": "TS03EP4412", "type": "Triple Riding", "confidence": 0.89, "processed": True},
        {"violation_id": "V-904", "timestamp": "2026-07-04 15:05:11", "junction": "Junction-11 (Begumpet)", "vehicle_id": "TS11ER9982", "type": "Red Light Jump", "confidence": 0.95, "processed": False},
    ]
    
    # Historical Vehicle Profile Database (Simulating master records)
    st.session_state.vehicle_registry_db = {
        "TS03EP4412": {"owner": "A. Srinivas", "total_past_offenses": 4, "status": "FLAGGED_REPEAT_OFFENDER", "unpaid_fines": 3500},
        "TS11ER9982": {"owner": "M. Karthik", "total_past_offenses": 3, "status": "FLAGGED_REPEAT_OFFENDER", "unpaid_fines": 2000},
        "TS08EQ1102": {"owner": "K. Shruthi", "total_past_offenses": 1, "status": "STANDARD_WARNING", "unpaid_fines": 500},
        "AP36AT0091": {"owner": "V. Prasad", "total_past_offenses": 0, "status": "CLEAN_PROFILE", "unpaid_fines": 0}
    }
    
    # Active Citations Issued Table
    st.session_state.citations_db = []
    
    # Live Real-time Dispatch Terminal Notifications
    st.session_state.dispatch_notifications = [
        {"timestamp": "11:54:00", "junction": "System Monitor", "message": "GuardEye Core Operating Console initialized successfully."}
    ]

# --- SIDEBAR: CONTROL AND API INTEGRATION ---
st.sidebar.image("https://img.icons8.com/clouds/100/000000/traffic-light.png", width=70)
st.sidebar.title("GuardEye SOC Hub")
st.sidebar.write("Unified Computer Vision Engine & Autonomous AI-Agent.")

# Groq Credentials Input
user_key = st.sidebar.text_input("Enter Groq API Key", type="password", placeholder="gsk_...")

st.sidebar.markdown("---")
st.sidebar.subheader("YOLOv8 Detection Parameters")
conf_threshold = st.sidebar.slider("YOLOv8 Detection Confidence Threshold", 0.50, 0.99, 0.85)
detection_delay = st.sidebar.slider("Thought Loop Delay (seconds)", 1.0, 4.0, 1.5)

# --- FUNCTION ENGINE: EXPOSING AGENT-CAPABLE TOOLS ---

def query_postgresql_violations(junction_id: str, date: str) -> str:
    """Queries your simulated PostgreSQL database to retrieve live YOLOv8 violation records matching a junction and date."""
    results = [v for v in st.session_state.violations_db if v["junction"] == junction_id]
    return json.dumps({"junction": junction_id, "date": date, "record_count": len(results), "data": results})

def check_repeat_offender_history(vehicle_id: str) -> str:
    """Queries master database profiles to evaluate vehicle recidivism, past unpaid fines, and flagged offender status."""
    profile = st.session_state.vehicle_registry_db.get(
        vehicle_id, 
        {"owner": "Unknown", "total_past_offenses": 0, "status": "CLEAN_PROFILE", "unpaid_fines": 0}
    )
    return json.dumps({"vehicle_id": vehicle_id, "profile_details": profile})

def generate_official_citation(vehicle_id: str, violation_id: str, violation_type: str) -> str:
    """Invokes generator backend to write a binding citation file into the system database."""
    fine_matrix = {
        "Helmet Violation": 500,
        "Speeding (84 km/h)": 1000,
        "Speeding (92 km/h)": 1500,
        "Triple Riding": 1200,
        "Red Light Jump": 1000
    }
    fine_amount = fine_matrix.get(violation_type, 500)
    citation_id = f"CIT-{random.randint(10000, 99999)}"
    
    new_citation = {
        "citation_id": citation_id,
        "vehicle_id": vehicle_id,
        "violation_id": violation_id,
        "violation_type": violation_type,
        "fine_amount": f"₹{fine_amount}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # Append citation directly to stateful database
    st.session_state.citations_db.append(new_citation)
    
    # Mark violation as processed
    for v in st.session_state.violations_db:
        if v["violation_id"] == violation_id:
            v["processed"] = True
            
    return json.dumps({"status": "SUCCESS_CITATION_GENERATED", "details": new_citation})

def dispatch_officer_alert(junction_id: str, alert_message: str) -> str:
    """Triggers an active broadcast event notification to on-duty regional enforcement dispatch terminals."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.dispatch_notifications.insert(0, {
        "timestamp": timestamp,
        "junction": junction_id,
        "message": alert_message
    })
    return json.dumps({
        "status": "DISPATCH_SUCCESS",
        "timestamp": timestamp,
        "target": f"MOBILE_FIELD_UNIT_{junction_id.split()[0].upper()}",
        "alert_broadcasted": alert_message
    })

# Mapping operational tools for agent execution
TOOLS = {
    "query_postgresql_violations": query_postgresql_violations,
    "check_repeat_offender_history": check_repeat_offender_history,
    "generate_official_citation": generate_official_citation,
    "dispatch_officer_alert": dispatch_officer_alert
}

# --- AGENT PIPELINE RECONSTRUCTION ---
def run_guardeye_agent_groq(user_prompt: str, api_key: str):
    """Executes a structured ReAct Agent loop using the newly supported llama-3.1-8b-instant model on Groq."""
    if not api_key:
        st.error("⚠️ Please input a valid Groq API Key in the left sidebar to start the cognitive dispatch loop.")
        return None

    system_prompt = """
    You are GuardEye-Agent, an autonomous AI Traffic Enforcement Dispatcher built on top of a YOLOv8 computer vision detection framework.
    Your mission is to process high-level queries from dispatchers, autonomously inspect PostgreSQL violation databases, analyze profiles, issue citations, and coordinate on-field alerts.
    
    You have access to these exact tools:
    1. query_postgresql_violations(junction_id, date) -> Returns YOLOv8 detection records for a junction & date.
    2. check_repeat_offender_history(vehicle_id) -> Checks historical records and profiles a driver.
    3. generate_official_citation(vehicle_id, violation_id, violation_type) -> Generates legal fine documents and updates state.
    4. dispatch_officer_alert(junction_id, alert_message) -> Broadcasts instant messages to active police terminals.
    
    You must reason step-by-step using a strict format.
    Your output MUST follow this format exactly in every turn, containing only one step at a time:
    
    THOUGHT: Reason about what tool you need next or if you have enough information to write the final response.
    ACTION: call_name(param1, param2...)
    
    Once you get the OBSERVATION from the tool execution, you will write the next THOUGHT.
    Once you have successfully executed all procedures, output:
    
    FINAL_RESPONSE: A highly structured incident report summarizing detections, recidivism analysis, generated citation IDs, and dispatch logs.
    
    Do not output any text before THOUGHT. Only call one tool at a time.
    """

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Groq Client: {str(e)}")
        return None
    
    conversation_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    max_steps = 6
    
    for step in range(max_steps):
        # Call Groq API using the highly responsive and active llama-3.1-8b-instant model
        for attempt in range(5):
            try:
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=conversation_history,
                    temperature=0.2,
                    max_tokens=800
                )
                break
            except Exception as e:
                if attempt == 4:
                    st.error(f"Groq API connection failed: {str(e)}")
                    return None
                time.sleep(2**attempt)
                
        model_output = completion.choices[0].message.content
        
        thought, action, final_resp = "", "", ""
        lines = model_output.split("\n")
        for line in lines:
            if line.startswith("THOUGHT:"):
                thought = line.replace("THOUGHT:", "").strip()
            elif line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("FINAL_RESPONSE:"):
                final_resp = line.replace("FINAL_RESPONSE:", "").strip()
        
        if not thought and not final_resp:
            thought = model_output.strip()

        # Render step thought live
        if thought:
            with st.chat_message("assistant", avatar="🧠"):
                st.markdown(f"<div class='thought-container'>🧠 <b>Thought:</b> {thought}</div>", unsafe_allow_html=True)
            time.sleep(detection_delay)
            
        # Execute Action
        if action:
            with st.chat_message("assistant", avatar="⚙️"):
                st.markdown(f"<div class='action-container'>🛠️ <b>Action:</b> Invoking ` {action} `</div>", unsafe_allow_html=True)
            
            try:
                func_name = action.split("(")[0].strip()
                args_raw = action.split("(")[1].replace(")", "").replace("'", "").replace('"', "").strip()
                args = [a.strip() for a in args_raw.split(",")]
                
                if len(args) == 3:
                    observation = TOOLS[func_name](args[0], args[1], args[2])
                elif len(args) == 2:
                    observation = TOOLS[func_name](args[0], args[1])
                else:
                    observation = TOOLS[func_name](args[0])
            except Exception as e:
                observation = f"Execution error: {str(e)}"
                
            with st.chat_message("assistant", avatar="📋"):
                st.markdown(f"<div class='observation-container'>📡 <b>Observation:</b> {observation}</div>", unsafe_allow_html=True)
            
            conversation_history.append({"role": "assistant", "content": model_output})
            conversation_history.append({"role": "user", "content": f"OBSERVATION: {observation}"})
            time.sleep(detection_delay)
            
        elif final_resp or "FINAL_RESPONSE" in model_output:
            if not final_resp:
                final_resp = model_output.split("FINAL_RESPONSE:")[-1].strip()
            st.balloons()
            return final_resp
            
    return "Agent process did not conclude within safe operational loops."

# --- MAIN WORKSPACE INTERFACE ---
st.title("🚨 GuardEye: High-Impact Computer Vision \& Agentic Enforcement Suite")
st.write("A complete, end-to-end recreation of your conference-published YOLOv8 system combined with multi-step ReAct Agentic dispatch automation.")

tab1, tab2, tab3 = st.tabs(["🚀 Complete System Suite", "📊 Database explorer (PostgreSQL)", "📋 Real-Time Dispatch Terminal"])

# --- TAB 1: INTEGRATED YOLO INTERFACE + AGENT MONITOR ---
with tab1:
    col_left, col_right = st.columns([1.1, 1.1])
    
    with col_left:
        st.markdown("<div class='soc-card'>", unsafe_allow_html=True)
        st.subheader("📸 YOLOv8 Video Feed Simulation")
        st.write("Trigger your core computer vision model to scan active camera frames and detect helmet, speeding, or red-light infractions.")
        
        sim_junction = st.selectbox("Select Camera Junction to Monitor", ["Junction-04 (Hitec City)", "Junction-02 (KITS Campus)", "Junction-11 (Begumpet)"])
        
        # Interactive Detector simulation panel
        detector_col, reset_col = st.columns(2)
        with detector_col:
            if st.button("🖼_ Run YOLOv8 on Simulated Camera Feed", use_container_width=True):
                # Generates a randomized but highly realistic violation detection profile
                random_plates = ["TS03EP4412", "TS11ER9982", "TS08EQ1102", "AP36AT0091"]
                random_violations = ["Helmet Violation", "Speeding (92 km/h)", "Triple Riding", "Red Light Jump"]
                
                new_v_id = f"V-{random.randint(910, 999)}"
                new_vehicle = random.choice(random_plates)
                new_type = random.choice(random_violations)
                new_conf = round(random.uniform(0.86, 0.98), 2)
                
                if new_conf >= conf_threshold:
                    new_violation = {
                        "violation_id": new_v_id,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "junction": sim_junction,
                        "vehicle_id": new_vehicle,
                        "type": new_type,
                        "confidence": new_conf,
                        "processed": False
                    }
                    st.session_state.violations_db.insert(0, new_violation)
                    st.success(f"🚨 YOLOv8 Detection Triggered: {new_type} by {new_vehicle} at {sim_junction} (Confidence: {new_conf*100}%)!")
                else:
                    st.info(f"Scan complete: Object detected but fell below current {conf_threshold*100}% confidence gate.")
                    
        with reset_col:
            if st.button("🧹 Flush Simulated Databases", use_container_width=True):
                st.session_state.violations_db = []
                st.session_state.citations_db = []
                st.session_state.dispatch_notifications = [{"timestamp": "00:00:00", "junction": "System Monitor", "message": "Databases flushed."}]
                st.info("Simulated records successfully cleared.")
                
        # Drawing a live representation of a captured traffic feed
        st.markdown("""
        <div style="background-color: #f1f5f9; height: 180px; border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 2px dashed #cbd5e1; position: relative;">
            <div style="text-align: center; color: #475569;">
                <p style="font-size: 24px; margin: 0; font-weight: bold;">📹 ACTIVE CAMERA FEED</p>
                <p style="font-size: 14px; margin: 4px 0 0 0;">YOLOv8 Core Pipeline Loaded and Standby</p>
                <span style="position: absolute; top: 10px; left: 10px; background-color: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">LIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # High level dispatch instructions
        st.markdown("<div class='soc-card'>", unsafe_allow_html=True)
        st.subheader("🧠 Autonomous Dispatch AI Console")
        st.write("Write an command to watch the agent analyze logs, check databases, execute actions, and dispatch units.")
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        default_prompt = (
            f"Analyze infractions at {sim_junction} today ({today_date}). "
            "Examine if any vehicles are repeat offenders, immediately generate legal citations for them, "
            "and alert the active dispatch units near the junction with vehicle descriptions."
        )
        user_query = st.text_area("Command Prompt Input:", value=default_prompt, height=100)
        run_btn = st.button("🚀 Run Agentic Control Chain", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.subheader("⚙️ Agentic Telemetry Console")
        st.write("Telemetry logs outlining the active cognition of GuardEye Agent:")
        
        telemetry_box = st.empty()
        if not user_key:
            telemetry_box.error("Failed to communicate with Groq API. Check network connection or API Key.")
        else:
            telemetry_box.success("System Ready: Groq Llama-3 Agent Online")
            
        if run_btn:
            if not user_key:
                st.warning("⚠️ Enter a valid Groq API Key in the left panel to execute.")
            else:
                with st.spinner("Initializing GuardEye Reasoning Loop..."):
                    agent_result = run_guardeye_agent_groq(user_query, user_key)
                    if agent_result:
                        st.markdown("<div class='soc-card'>", unsafe_allow_html=True)
                        st.subheader("📋 Agent Execution Report Summary")
                        st.success(agent_result)
                        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: POSTGRESQL STATEFUL DATABASE EXPLORER ---
with tab2:
    st.subheader("📊 Relational Database Explorer")
    st.write("Inspect live relational tables simulated via stateful memory structures matching your PostgreSQL schema:")
    
    col_db_l, col_db_r = st.columns([1.2, 1])
    
    with col_db_l:
        st.subheader("📋 `violations_logs` Table")
        st.write("Real-time detections recorded by the YOLOv8 model:")
        if len(st.session_state.violations_db) > 0:
            df_v = pd.DataFrame(st.session_state.violations_db)
            st.dataframe(df_v, use_container_width=True)
        else:
            st.info("No logs present in the violations database. Trigger detections above.")
            
    with col_db_r:
        st.subheader("📄 `issued_citations` Table")
        st.write("Official fines generated dynamically by the GuardEye Agent:")
        if len(st.session_state.citations_db) > 0:
            df_c = pd.DataFrame(st.session_state.citations_db)
            st.dataframe(df_c, use_container_width=True)
        else:
            st.info("No citations issued yet. Run the Autonomous AI-Agent to auto-generate fines.")

    st.markdown("---")
    st.subheader("👥 `vehicle_master` Registry Profiles")
    df_reg = pd.DataFrame.from_dict(st.session_state.vehicle_registry_db, orient='index').reset_index().rename(columns={'index': 'vehicle_id'})
    st.dataframe(df_reg, use_container_width=True)

# --- TAB 3: DISPATCH NOTIFICATION FEED ---
with tab3:
    st.subheader("🚨 Field Dispatch Broadcast Feed")
    st.write("Real-time events and officer alerts issued autonomously by the AI-Agent loop:")
    
    for notification in st.session_state.dispatch_notifications:
        st.markdown(f"""
        <div style="background-color: #ffffff; border-left: 5px solid #ef4444; padding: 12px; margin-bottom: 8px; border-radius: 4px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);">
            <span style="font-size: 11px; color: #64748b;">[{notification['timestamp']}] - Location: <b>{notification['junction']}</b></span>
            <p style="margin: 4px 0 0 0; font-size: 14px; font-weight: bold; color: #b91c1c;">📟 Broadcast Alert: {notification['message']}</p>
        </div>
        """, unsafe_allow_html=True)