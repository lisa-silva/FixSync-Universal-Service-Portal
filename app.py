import streamlit as st
from datetime import datetime, timedelta
import uuid
import os
import json
from PIL import Image
import io
import base64
from typing import Dict, List, Optional
import time
from collections import defaultdict

# Page config
st.set_page_config(
    page_title="FixSync – Universal Service Portal",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }
    .quote-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .message-customer {
        border-left: 4px solid #4CAF50;
        padding-left: 1rem;
        background: #f8fff8;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .message-technician {
        border-left: 4px solid #2196F3;
        padding-left: 1rem;
        background: #f5f9ff;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if "jobs" not in st.session_state:
        st.session_state.jobs = {}
    if "users" not in st.session_state:
        st.session_state.users = {}
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "notifications" not in st.session_state:
        st.session_state.notifications = defaultdict(list)

init_session_state()

# Mock database class (replace with real DB in production)
class MockDB:
    @staticmethod
    def save_job(job_id: str, job_data: Dict):
        st.session_state.jobs[job_id] = job_data
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Dict]:
        return st.session_state.jobs.get(job_id)
    
    @staticmethod
    def get_all_jobs() -> Dict:
        return st.session_state.jobs
    
    @staticmethod
    def add_user(email: str, password: str, role: str):
        st.session_state.users[email] = {
            "password": password,
            "role": role,
            "created": datetime.now().isoformat()
        }
    
    @staticmethod
    def authenticate(email: str, password: str) -> bool:
        user = st.session_state.users.get(email)
        return user and user["password"] == password

# Authentication system
def show_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔧 FixSync")
        st.markdown("**Intelligent Service Collaboration Platform**")
        
        tab1, tab2, tab3 = st.tabs(["📱 Customer", "👨‍🔧 Technician", "👑 Admin"])
        
        with tab1:
            st.subheader("Customer Portal")
            email = st.text_input("Email", key="cust_email")
            if st.button("Start New Job", type="primary", use_container_width=True):
                if email:
                    job_id = str(uuid.uuid4())[:8].upper()
                    MockDB.save_job(job_id, {
                        "id": job_id,
                        "customer_email": email,
                        "created": datetime.now().isoformat(),
                        "photos": [],
                        "messages": [],
                        "quotes": [],
                        "status": "open",
                        "assigned_tech": None,
                        "priority": "medium",
                        "category": None,
                        "location": "",
                        "description": ""
                    })
                    st.session_state.current_user = {
                        "email": email,
                        "role": "customer",
                        "job_id": job_id
                    }
                    st.query_params["job_id"] = job_id
                    st.rerun()
                else:
                    st.warning("Please enter your email")
            
            st.divider()
            existing_job = st.text_input("Already have a job ID?")
            if st.button("Access Existing Job", use_container_width=True):
                if existing_job and MockDB.get_job(existing_job):
                    st.session_state.current_user = {
                        "role": "customer",
                        "job_id": existing_job
                    }
                    st.query_params["job_id"] = existing_job
                    st.rerun()
                else:
                    st.error("Job not found")
        
        with tab2:
            st.subheader("Technician Login")
            tech_email = st.text_input("Email", key="tech_email")
            tech_pass = st.text_input("Password", type="password", key="tech_pass")
            
            if st.button("Login as Technician", type="primary", use_container_width=True):
                if tech_email and tech_pass:
                    # For demo - create user if not exists
                    if tech_email not in st.session_state.users:
                        MockDB.add_user(tech_email, tech_pass, "technician")
                    
                    if MockDB.authenticate(tech_email, tech_pass):
                        st.session_state.current_user = {
                            "email": tech_email,
                            "role": "technician"
                        }
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please enter credentials")
        
        with tab3:
            st.subheader("Admin Dashboard")
            admin_pass = st.text_input("Admin Password", type="password")
            if st.button("Access Dashboard", use_container_width=True):
                if admin_pass == "admin123":  # Change in production
                    st.session_state.current_user = {"role": "admin"}
                    st.rerun()

# Job room component
def show_job_room(job_id: str):
    job = MockDB.get_job(job_id)
    if not job:
        st.error("Job not found")
        st.stop()
    
    # Header
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.title(f"🔧 Job #{job_id}")
    with col2:
        status_colors = {
            "open": "#FFA726",
            "in_progress": "#29B6F6",
            "quoted": "#9C27B0",
            "approved": "#4CAF50",
            "completed": "#66BB6A",
            "cancelled": "#EF5350"
        }
        status = st.selectbox(
            "Status",
            list(status_colors.keys()),
            index=list(status_colors.keys()).index(job.get("status", "open")),
            key=f"status_{job_id}"
        )
        if status != job.get("status"):
            job["status"] = status
            MockDB.save_job(job_id, job)
    with col3:
        if st.button("Exit Job", type="secondary"):
            del st.query_params["job_id"]
            st.session_state.current_user = None
            st.rerun()
    
    # Main layout
    tab1, tab2, tab3, tab4 = st.tabs(["📷 Photos", "💬 Chat", "💰 Quotes", "ℹ️ Details"])
    
    with tab1:
        st.subheader("Visual Documentation")
        
        # Upload section
        with st.expander("📤 Add Photos/Video", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                uploaded = st.file_uploader(
                    "Upload photos",
                    accept_multiple_files=True,
                    type=["png", "jpg", "jpeg", "heic"],
                    key=f"upload_{job_id}"
                )
            with col2:
                video = st.file_uploader("Upload video", type=["mp4", "mov"])
                if video:
                    st.video(video.getvalue())
            
            if uploaded:
                for file in uploaded:
                    img = Image.open(file)
                    # Compress image
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
                    job["photos"].append({
                        "data": base64.b64encode(img_byte_arr.getvalue()).decode(),
                        "timestamp": datetime.now().isoformat(),
                        "uploaded_by": st.session_state.current_user.get("role", "unknown")
                    })
                MockDB.save_job(job_id, job)
                st.success(f"Added {len(uploaded)} photo(s)")
                st.rerun()
        
        # Display photos in grid
        if job["photos"]:
            st.markdown(f"### 📸 Gallery ({len(job['photos'])} images)")
            cols = st.columns(4)
            for idx, photo in enumerate(job["photos"][-12:]):  # Show last 12
                with cols[idx % 4]:
                    img_data = base64.b64decode(photo["data"])
                    st.image(img_data, use_column_width=True)
                    st.caption(f"Added by {photo['uploaded_by']}")
        else:
            st.info("No photos uploaded yet. Add photos to help technicians understand the issue.")
    
    with tab2:
        st.subheader("Live Collaboration")
        
        # Chat messages
        chat_container = st.container(height=400)
        with chat_container:
            for msg in job.get("messages", []):
                if msg.get("type") == "system":
                    st.markdown(f"🔔 *{msg['text']}*")
                else:
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        if msg.get("role") == "customer":
                            st.markdown(f"""
                            <div class='message-customer'>
                                <strong>👤 Customer</strong> <small>{msg.get('time', '')}</small><br>
                                {msg['text']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class='message-technician'>
                                <strong>🔧 {msg.get('sender', 'Technician')}</strong> <small>{msg.get('time', '')}</small><br>
                                {msg['text']}
                            </div>
                            """, unsafe_allow_html=True)
        
        # Chat input
        col1, col2 = st.columns([4, 1])
        with col1:
            message = st.text_input(
                "Type your message...",
                key=f"chat_input_{job_id}",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Send", type="primary", use_container_width=True):
                if message:
                    msg = {
                        "role": st.session_state.current_user.get("role", "unknown"),
                        "text": message,
                        "time": datetime.now().strftime("%I:%M %p"),
                        "sender": st.session_state.current_user.get("email", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                    job["messages"].append(msg)
                    MockDB.save_job(job_id, job)
                    st.rerun()
    
    with tab3:
        st.subheader("Quotes & Pricing")
        
        # Technician quote submission
        if st.session_state.current_user.get("role") == "technician":
            with st.expander("💵 Create New Quote", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input("Amount ($)", min_value=0.0, step=10.0)
                    breakdown = st.text_area("Breakdown", placeholder="Labor: $200\nParts: $150\nTax: $35")
                with col2:
                    timeline = st.selectbox("Timeline", ["ASAP", "1-2 days", "3-5 days", "1 week+", "Custom"])
                    warranty = st.selectbox("Warranty", ["30 days", "90 days", "1 year", "Lifetime"])
                
                if st.button("Submit Quote", type="primary", use_container_width=True):
                    quote_id = str(uuid.uuid4())[:8]
                    job["quotes"].append({
                        "id": quote_id,
                        "amount": amount,
                        "breakdown": breakdown,
                        "timeline": timeline,
                        "warranty": warranty,
                        "technician": st.session_state.current_user.get("email"),
                        "created": datetime.now().isoformat(),
                        "status": "pending"
                    })
                    job["messages"].append({
                        "type": "system",
                        "text": f"New quote submitted for ${amount}"
                    })
                    MockDB.save_job(job_id, job)
                    st.success("Quote submitted!")
                    st.rerun()
        
        # Display quotes
        if job.get("quotes"):
            for quote in reversed(job["quotes"]):
                with st.container():
                    st.markdown(f"""
                    <div class='quote-card'>
                        <h3>${quote['amount']:.2f}</h3>
                        <p><strong>Timeline:</strong> {quote['timeline']}</p>
                        <p><strong>Warranty:</strong> {quote['warranty']}</p>
                        <p><strong>By:</strong> {quote['technician']}</p>
                        <small>{quote['created'][:10]}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    if st.session_state.current_user.get("role") == "customer":
                        with col1:
                            if st.button("✅ Approve", key=f"approve_{quote['id']}"):
                                quote["status"] = "approved"
                                job["status"] = "approved"
                                MockDB.save_job(job_id, job)
                                st.rerun()
                        with col2:
                            if st.button("❌ Decline", key=f"decline_{quote['id']}"):
                                quote["status"] = "declined"
                                MockDB.save_job(job_id, job)
                                st.rerun()
                    st.text_area("Breakdown", quote["breakdown"], height=100, disabled=True)
                    st.divider()
        else:
            st.info("No quotes submitted yet.")
    
    with tab4:
        st.subheader("Job Details")
        
        col1, col2 = st.columns(2)
        with col1:
            job["category"] = st.selectbox(
                "Category",
                ["Plumbing", "Electrical", "HVAC", "Appliance", "Structural", "Other"],
                index=["Plumbing", "Electrical", "HVAC", "Appliance", "Structural", "Other"].index(job.get("category", "Other")) if job.get("category") in ["Plumbing", "Electrical", "HVAC", "Appliance", "Structural", "Other"] else 5
            )
            job["priority"] = st.selectbox(
                "Priority",
                ["low", "medium", "high", "emergency"],
                index=["low", "medium", "high", "emergency"].index(job.get("priority", "medium"))
            )
        with col2:
            job["location"] = st.text_input("Location", job.get("location", ""))
            if st.session_state.current_user.get("role") in ["technician", "admin"]:
                job["assigned_tech"] = st.text_input("Assigned Technician", job.get("assigned_tech", ""))
        
        job["description"] = st.text_area(
            "Problem Description",
            job.get("description", ""),
            height=150,
            placeholder="Describe the issue in detail..."
        )
        
        if st.button("Save Details", type="secondary"):
            MockDB.save_job(job_id, job)
            st.success("Details updated!")
        
        st.divider()
        st.markdown("### 📊 Job Timeline")
        timeline_data = [
            ("Created", job.get("created")),
            ("First Message", job.get("messages")[0]["timestamp"] if job.get("messages") else None),
            ("First Photo", job.get("photos")[0]["timestamp"] if job.get("photos") else None),
            ("First Quote", job.get("quotes")[0]["created"] if job.get("quotes") else None),
            ("Status Updated", datetime.now().isoformat())
        ]
        
        for event, timestamp in timeline_data:
            if timestamp:
                st.write(f"**{event}:** {timestamp[:16].replace('T', ' ')}")

# Admin dashboard
def show_admin_dashboard():
    st.title("👑 Admin Dashboard")
    
    jobs = MockDB.get_all_jobs()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jobs", len(jobs))
    with col2:
        open_jobs = sum(1 for j in jobs.values() if j.get("status") == "open")
        st.metric("Open Jobs", open_jobs)
    with col3:
        revenue = sum(q["amount"] for j in jobs.values() for q in j.get("quotes", []) if q.get("status") == "approved")
        st.metric("Total Revenue", f"${revenue:,.2f}")
    
    st.divider()
    
    # Jobs table
    st.subheader("All Jobs")
    for job_id, job in jobs.items():
        with st.expander(f"Job #{job_id} - {job.get('category', 'Unknown')} - {job.get('status', 'unknown')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Customer:** {job.get('customer_email', 'N/A')}")
                st.write(f"**Created:** {job.get('created', '')[:10]}")
            with col2:
                st.write(f"**Photos:** {len(job.get('photos', []))}")
                st.write(f"**Messages:** {len(job.get('messages', []))}")
            with col3:
                st.write(f"**Quotes:** {len(job.get('quotes', []))}")
                if job.get("quotes"):
                    st.write(f"**Highest Quote:** ${max(q.get('amount', 0) for q in job['quotes']):.2f}")
            
            if st.button(f"Delete Job #{job_id}", type="secondary", key=f"delete_{job_id}"):
                del st.session_state.jobs[job_id]
                st.rerun()

# Main app logic
def main():
    # Check if user is authenticated
    if st.session_state.current_user is None and "job_id" not in st.query_params:
        show_auth()
        return
    
    # Check if in job room
    if "job_id" in st.query_params:
        job_id = st.query_params["job_id"][0]
        show_job_room(job_id)
    elif st.session_state.current_user and st.session_state.current_user.get("role") == "admin":
        show_admin_dashboard()
    else:
        # Dashboard for technicians
        st.title("👨‍🔧 Technician Dashboard")
        st.write(f"Welcome, {st.session_state.current_user.get('email', 'Technician')}!")
        
        jobs = MockDB.get_all_jobs()
        my_jobs = [j for j in jobs.values() if j.get("assigned_tech") == st.session_state.current_user.get("email")]
        
        if my_jobs:
            st.subheader("Your Assigned Jobs")
            for job in my_jobs:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**Job #{job['id']}** - {job.get('category', 'Unknown')}")
                        st.write(f"Customer: {job.get('customer_email', 'N/A')}")
                    with col2:
                        st.write(f"Status: {job.get('status', 'unknown')}")
                    with col3:
                        if st.button("Open", key=f"open_{job['id']}"):
                            st.query_params["job_id"] = job['id']
                            st.rerun()
                    st.divider()
        else:
            st.info("No jobs assigned to you yet.")
        
        st.subheader("All Open Jobs")
        open_jobs = [j for j in jobs.values() if j.get("status") == "open"]
        for job in open_jobs:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**Job #{job['id']}** - {job.get('category', 'Unknown')}")
                with col2:
                    st.write(f"Photos: {len(job.get('photos', []))}")
                with col3:
                    if st.button("Claim Job", key=f"claim_{job['id']}"):
                        job["assigned_tech"] = st.session_state.current_user.get("email")
                        job["status"] = "in_progress"
                        MockDB.save_job(job["id"], job)
                        st.rerun()
                st.divider()

# Run the app
if __name__ == "__main__":
    main()
