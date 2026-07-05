# GuardEye-Traffic-Agent
# GuardEye: Autonomous AI Traffic Enforcement Suite

GuardEye is an end-to-end, autonomous AI-agent traffic enforcement pipeline that bridges the gap between raw computer vision and structured action. This project is a functional recreation of my research paper published in the proceedings of **ICASET-2026**.

## 🛠️ Technical Stack
- **AI Agent Engine:** Meta Llama-3 (via Groq LPU) running a multi-step Reasoning and Action (ReAct) loop.
- **Vision Model (Simulation Source):** Custom-trained YOLOv8 (28 FPS, 94.8% accuracy).
- **Backend & Database:** PostgreSQL Simulation via Streamlit stateful session storage.
- **Framework:** Streamlit for live diagnostic telemetry and dashboards.

## 🚀 Key Features
- **Real-Time Database Explorer:** Inspects dynamic live detection logs and master RTO registration tables.
- **ReAct Telemetry Console:** Displays the exact thought, action, and observation sequences of the agent in real time.
- **Autonomous Citations & Dispatch:** Automatically updates SQL registries and issues active dispatch signals.

## ⚙️ How to Run Locally
1. Clone this repository: `git clone <YOUR-GITHUB-LINK>`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`
