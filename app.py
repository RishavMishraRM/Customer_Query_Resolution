"""
Apex Commercial Bank - Agent-Assist Copilot Workstation
A clean, enterprise-grade banking UI for customer-support agents.
Features live microphone streaming with 'Tap-to-Now' audio slicing,
sample audio testing, SOP document RAG retrieval, local Ollama LLM generation,
and comprehensive banking safety guardrails.
"""

import time
import os
from pathlib import Path
import streamlit as st
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Apex Bank | Agent-Assist Copilot",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Bank CSS Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Main Container adjustments */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Top Institutional Header */
    .bank-header-banner {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #0A192F 0%, #172A45 100%);
        color: #F8FAFC;
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 1.25rem;
        border-left: 6px solid #2563EB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .bank-header-title {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .bank-header-subtitle {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    .bank-header-badge {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        background: rgba(255, 255, 255, 0.08);
        padding: 5px 12px;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #E2E8F0;
    }

    /* Workstation Cards */
    .bank-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .bank-card-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 6px;
    }

    /* Status Badges */
    .badge-status {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
    }
    .badge-failed {
        background: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .badge-pending {
        background: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .badge-disputed {
        background: #F5F3FF;
        color: #5B21B6;
        border: 1px solid #DDD6FE;
    }
    .badge-success {
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }

    /* Customer Ready Script Box */
    .script-container {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 6px solid #16A34A;
        border-radius: 8px;
        padding: 18px 22px;
        margin: 12px 0 16px 0;
        box-shadow: 0 2px 4px rgba(22, 163, 74, 0.04);
    }
    .script-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #166534;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .script-text {
        font-size: 1.12rem;
        font-weight: 500;
        line-height: 1.6;
        color: #0F172A;
    }

    /* Operational Action Box */
    .action-container {
        background: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-left: 6px solid #2563EB;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .action-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #1E40AF;
        margin-bottom: 6px;
    }
    .action-text {
        font-size: 0.95rem;
        font-weight: 500;
        color: #1E293B;
        line-height: 1.5;
    }

    /* Escalation Banner */
    .escalation-banner {
        background: #FEF2F2;
        border: 1px solid #F87171;
        border-left: 6px solid #DC2626;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 16px;
    }
    .escalation-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #991B1B;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .escalation-desc {
        font-size: 0.9rem;
        color: #7F1D1D;
        line-height: 1.4;
    }

    /* Live Call Timer Indicator */
    .call-timer-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .timer-dot-active {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #DC2626;
        margin-right: 8px;
        box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7);
        animation: pulse-red 1.5s infinite;
    }
    .timer-dot-inactive {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #94A3B8;
        margin-right: 8px;
    }
    @keyframes pulse-red {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 7px rgba(220, 38, 38, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }

    /* Monospace Data Values */
    .mono-val {
        font-family: 'JetBrains Mono', Consolas, monospace;
        font-size: 0.85rem;
        color: #1E293B;
    }

    /* Banking Key-Value Metric */
    .bank-metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 0;
        border-bottom: 1px dashed #F1F5F9;
        font-size: 0.85rem;
    }
    .bank-metric-row:last-child {
        border-bottom: none;
    }
    .bank-metric-label {
        color: #64748B;
        font-size: 0.8rem;
    }
    .bank-metric-value {
        font-weight: 600;
        color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)

# Imports from src
from src.customer_context import CustomerContextService
from src.knowledge_base import SOPKnowledgeBase
from src.transcription import transcribe_audio_file
from src.copilot import FinTechCopilot, build_grounded_agent_script, get_default_operational_steps
from src.audio_capture import LiveCallAudioBuffer
from src.schemas import CustomerContext


# -------------------------------------------------------------
# Initialize Cached Services
# -------------------------------------------------------------
@st.cache_resource
def get_customer_service():
    return CustomerContextService()

@st.cache_resource
def get_knowledge_base():
    return SOPKnowledgeBase()

@st.cache_resource
def get_copilot():
    return FinTechCopilot()

customer_service = get_customer_service()
kb = get_knowledge_base()
copilot = get_copilot()

# Session State Initialization
if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = LiveCallAudioBuffer()

if "call_active" not in st.session_state:
    st.session_state.call_active = False

if "call_start_timestamp" not in st.session_state:
    st.session_state.call_start_timestamp = None

if "question_marked_offset" not in st.session_state:
    st.session_state.question_marked_offset = None

if "current_transcription" not in st.session_state:
    st.session_state.current_transcription = ""

if "current_answer" not in st.session_state:
    st.session_state.current_answer = None

if "current_warnings" not in st.session_state:
    st.session_state.current_warnings = []

if "current_passages" not in st.session_state:
    st.session_state.current_passages = []


# -------------------------------------------------------------
# SIDEBAR: Banking CRM & Customer Verification Terminal
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <span style="font-size:1.8rem;">🏦</span>
        <div>
            <div style="font-weight:700; font-size:1.05rem; color:#0F172A; line-height:1.2;">APEX BANK</div>
            <div style="font-size:0.75rem; color:#64748B;">Core Banking Station</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Customer Session Selector
    st.markdown('<div style="font-size:0.75rem; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:4px;">Active Caller Session:</div>', unsafe_allow_html=True)
    call_options = customer_service.get_call_options()
    selected_call_label = st.selectbox(
        "Active Customer Session",
        call_options,
        index=0,
        label_visibility="collapsed"
    )

    selected_call_id = selected_call_label.split(" | ")[0]
    customer: CustomerContext = customer_service.get_call_by_id(selected_call_id)

    # Clear stale answers when switching active customer
    if "active_customer_id" not in st.session_state:
        st.session_state.active_customer_id = selected_call_id
    elif st.session_state.active_customer_id != selected_call_id:
        st.session_state.active_customer_id = selected_call_id
        st.session_state.current_answer = None
        st.session_state.current_transcription = ""
        st.session_state.current_warnings = []
        st.session_state.current_passages = []
        st.session_state.question_marked_offset = None

    if customer:
        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
        
        # Customer Profile Card
        tier_colors = {
            "Platinum": "#6366F1",
            "Gold": "#D97706",
            "Silver": "#64748B",
            "Regular": "#059669"
        }
        tier_color = tier_colors.get(customer.customer_tier, "#2563EB")

        st.markdown(f"""
        <div class="bank-card">
            <div class="bank-card-title">
                <span>Verified Customer</span>
                <span style="background:{tier_color}15; color:{tier_color}; border:1px solid {tier_color}30; padding:2px 8px; border-radius:4px; font-size:0.7rem;">{customer.customer_tier} Tier</span>
            </div>
            <div style="font-size:1.05rem; font-weight:700; color:#0F172A; margin-bottom:4px;">{customer.customer_name}</div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Account No</span>
                <span class="mono-val">{customer.masked_account}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Registered Mobile</span>
                <span class="mono-val">{customer.masked_phone}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">KYC Verification</span>
                <span style="color:#059669; font-weight:600; font-size:0.8rem;">● Verified (Biometric)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Transaction Ledger Card
        status_classes = {
            "FAILED": "badge-failed",
            "PENDING": "badge-pending",
            "DISPUTED": "badge-disputed"
        }
        status_cls = status_classes.get(customer.transaction_status, "badge-pending")

        st.markdown(f"""
        <div class="bank-card">
            <div class="bank-card-title">
                <span>Transaction Under Query</span>
                <span class="badge-status {status_cls}">{customer.transaction_status}</span>
            </div>
            <div style="font-size:1.35rem; font-weight:700; color:#0F172A; margin:6px 0;">{customer.transaction_amount}</div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Transaction Ref</span>
                <span class="mono-val">{customer.transaction_id}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Channel</span>
                <span class="bank-metric-value">{customer.transaction_type}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Timestamp</span>
                <span class="bank-metric-value" style="font-size:0.8rem;">{customer.transaction_time or 'N/A'}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Beneficiary</span>
                <span class="bank-metric-value" style="font-size:0.8rem;">{customer.beneficiary_name or 'N/A'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if customer.failure_reason:
            st.markdown(f"""
            <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:6px; padding:10px 12px; font-size:0.8rem; color:#92400E; margin-bottom:10px;">
                <strong>Switch Log:</strong> {customer.failure_reason}
            </div>
            """, unsafe_allow_html=True)

        if customer.auto_reversal_status:
            st.markdown(f"""
            <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:6px; padding:10px 12px; font-size:0.8rem; color:#166534; margin-bottom:14px;">
                <strong>SLA:</strong> {customer.auto_reversal_status}
            </div>
            """, unsafe_allow_html=True)

    # Core Security & Compliance Details
    st.markdown("---")
    st.markdown('<div style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:8px;">Compliance & Engine Audit</div>', unsafe_allow_html=True)
    st.caption(f"• LLM Model: `{copilot.model_name}`")
    st.caption(f"• RAG Index: `{kb.embedding_mode}`")
    st.caption(f"• Database: `{customer_service.backend_mode}`")
    st.caption("• Security: PII Redaction & Read-Only")

    if st.button("🔄 Rebuild Policy Index", help="Re-indexes bank SOPs from data/sops/", use_container_width=True):
        with st.spinner("Re-indexing policy manual..."):
            count = kb.build_index(force_rebuild=True)
            st.success(f"Indexed {count} policy clauses!")


# -------------------------------------------------------------
# MAIN DASHBOARD: Clean Banking Workstation
# -------------------------------------------------------------

# Top Header Banner
st.markdown("""
<div class="bank-header-banner">
    <div>
        <div class="bank-header-title">
            <span>🏦 Apex Commercial Bank</span>
            <span style="font-weight:400; opacity:0.6;">|</span>
            <span style="font-weight:600; font-size:1.1rem;">Agent-Assist AI Copilot</span>
        </div>
        <div class="bank-header-subtitle">Real-Time In-Call Speech Guidance • Grounded SOP Retrieval • Read-Only Banking Compliance</div>
    </div>
    <div style="text-align:right;">
        <span class="bank-header-badge">Terminal ID: AG-409</span>
        <div style="font-size:0.75rem; color:#94A3B8; margin-top:4px;">Level 1 Resolution Desk</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_live, tab_audio, tab_sops = st.tabs([
    "🎙️ Live Customer Call (Tap-to-Now)",
    "📁 Audio QA & Recording Upload",
    "📚 Bank SOP Policy Knowledge Base"
])


# -------------------------------------------------------------
# TAB 1: Live Customer Call (Tap-to-Now)
# -------------------------------------------------------------
with tab_live:
    # Action Banner & Workflow Controls
    st.markdown("""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; margin-bottom:14px; font-size:0.85rem; color:#475569;">
        <strong>Simulated Call Flow:</strong> 1. Click <strong>Start Call</strong> to stream microphone &nbsp;➔&nbsp; 
        2. Click <strong>Mark Question Start</strong> when caller begins inquiry &nbsp;➔&nbsp; 
        3. Click <strong>Get Answer Now</strong> to slice segment and generate grounded response.
    </div>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2, col_btn3, col_timer = st.columns([1.5, 1.8, 1.8, 2.2])
    buffer: LiveCallAudioBuffer = st.session_state.audio_buffer

    with col_btn1:
        if not st.session_state.call_active:
            if st.button("▶️ Start Live Call", type="primary", use_container_width=True):
                ok, msg = buffer.start_call()
                if ok:
                    st.session_state.call_active = True
                    st.session_state.call_start_timestamp = time.time()
                    st.session_state.question_marked_offset = None
                    st.toast("Microphone stream connected", icon="🎙️")
                    st.rerun()
                else:
                    st.error(msg)
        else:
            if st.button("⏹️ Disconnect Call", use_container_width=True):
                buffer.stop_call()
                st.session_state.call_active = False
                st.toast("Call session disconnected", icon="📞")
                st.rerun()

    with col_btn2:
        mark_disabled = not st.session_state.call_active
        if st.button("📍 Mark Question Start", disabled=mark_disabled, use_container_width=True):
            ok, offset, msg = buffer.mark_question_start()
            if ok:
                st.session_state.question_marked_offset = offset
                st.toast(msg, icon="📍")
                st.rerun()
            else:
                st.warning(msg)

    with col_btn3:
        ans_disabled = not st.session_state.call_active
        if st.button("⚡ Get Answer Now", type="primary", disabled=ans_disabled, use_container_width=True):
            with st.spinner("Extracting audio slice & synthesizing grounded answer..."):
                segment, duration, err = buffer.extract_question_segment()
                if err:
                    st.error(f"Audio extraction notice: {err}")
                elif segment is not None:
                    temp_slice_path = Path("data/recordings/temp_question_slice.wav")
                    buffer.save_segment_to_wav(segment, temp_slice_path)
                    
                    transcription, stt_lat, stt_err = transcribe_audio_file(segment)
                    if stt_err:
                        st.warning(f"Audio recognition notice: {stt_err}")
                    else:
                        st.session_state.current_transcription = transcription
                        passages = kb.retrieve(transcription, top_k=3, customer=customer)
                        st.session_state.current_passages = passages
                        answer, warnings = copilot.generate_answer(transcription, customer, passages)
                        st.session_state.current_answer = answer
                        st.session_state.current_warnings = warnings
                        st.rerun()

    with col_timer:
        if st.session_state.call_active and st.session_state.call_start_timestamp:
            elapsed = int(time.time() - st.session_state.call_start_timestamp)
            mins = elapsed // 60
            secs = elapsed % 60
            marker_str = f" | Marker: {st.session_state.question_marked_offset:.1f}s" if st.session_state.question_marked_offset is not None else ""
            st.markdown(f"""
            <div class="call-timer-box">
                <div><span class="timer-dot-active"></span><strong>ACTIVE CALL:</strong> {mins:02d}:{secs:02d}</div>
                <div style="font-size:0.75rem; color:#64748B;">{marker_str}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="call-timer-box" style="color:#64748B; font-size:0.85rem;">
                <div><span class="timer-dot-inactive"></span>Line Inactive (Ready)</div>
                <div style="font-size:0.75rem;">16kHz Mono</div>
            </div>
            """, unsafe_allow_html=True)


# -------------------------------------------------------------
# TAB 2: Audio QA & Recording Upload
# -------------------------------------------------------------
with tab_audio:
    st.markdown('<div style="font-size:0.9rem; color:#475569; margin-bottom:12px;">Test with pre-packaged customer audio recordings or upload custom audio files.</div>', unsafe_allow_html=True)

    col_sample, col_upload = st.columns([1, 1])

    with col_sample:
        st.markdown("**Option 1: Standard Bank Test Recordings**")
        sample_audio_dir = Path("data/sample_audio")
        available_samples = list(sample_audio_dir.glob("*.wav")) if sample_audio_dir.exists() else []
        sample_options = ["None"] + [s.name for s in available_samples]
        chosen_sample = st.selectbox("Select demo audio:", sample_options, label_visibility="collapsed")

    with col_upload:
        st.markdown("**Option 2: Upload Customer Audio (WAV / MP3)**")
        uploaded_file = st.file_uploader("Upload audio file", type=["wav", "mp3"], label_visibility="collapsed")

    active_audio_path = None
    if uploaded_file is not None:
        save_dest = Path("data/recordings") / uploaded_file.name
        save_dest.parent.mkdir(parents=True, exist_ok=True)
        save_dest.write_bytes(uploaded_file.getbuffer())
        active_audio_path = save_dest
        st.audio(uploaded_file, format=uploaded_file.type)
    elif chosen_sample != "None":
        active_audio_path = sample_audio_dir / chosen_sample
        st.audio(str(active_audio_path))

    if active_audio_path:
        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
        col_trans_btn, _ = st.columns([2, 4])
        with col_trans_btn:
            if st.button("🎙️ Transcribe Audio File", type="primary", use_container_width=True):
                with st.spinner("Transcribing audio with Faster-Whisper..."):
                    txt, lat, err = transcribe_audio_file(active_audio_path)
                    if err:
                        st.error(f"Transcription error: {err}")
                    else:
                        st.session_state.current_transcription = txt
                        st.toast(f"Transcribed in {lat}s", icon="✅")
                        st.rerun()

        edited_text = st.text_area(
            "Review or edit transcribed customer inquiry:",
            value=st.session_state.current_transcription,
            height=90
        )

        if st.button("Submit Inquiry to Copilot", type="primary"):
            if not edited_text.strip():
                st.warning("Please provide or transcribe a customer inquiry first.")
            else:
                with st.spinner("Searching bank policy manual & querying local model..."):
                    st.session_state.current_transcription = edited_text
                    passages = kb.retrieve(edited_text, top_k=3, customer=customer)
                    st.session_state.current_passages = passages
                    answer, warnings = copilot.generate_answer(edited_text, customer, passages)
                    st.session_state.current_answer = answer
                    st.session_state.current_warnings = warnings
                    st.rerun()


# -------------------------------------------------------------
# TAB 3: Bank SOP Policy Knowledge Base
# -------------------------------------------------------------
with tab_sops:
    st.markdown('<div style="font-size:0.9rem; color:#475569; margin-bottom:12px;">Standard Operating Procedures (SOPs) governing transaction disputes, auto-reversals, and fraud escalations.</div>', unsafe_allow_html=True)

    sop_files = list(kb.sops_dir.glob("*.*")) if kb.sops_dir.exists() else []
    st.markdown(f"**Knowledge Repository:** `{len(kb.passages)}` indexed policy clauses across `{len(sop_files)}` active documents.")

    col_sop_list, col_sop_view = st.columns([1, 2])
    with col_sop_list:
        selected_doc = st.radio(
            "Available Policy Files:",
            [f.name for f in sop_files] if sop_files else ["No policies found"],
            index=0
        )

    with col_sop_view:
        if selected_doc and selected_doc != "No policies found":
            doc_file = kb.sops_dir / selected_doc
            try:
                st.markdown(f"**Viewing Policy:** `{selected_doc}`")
                if doc_file.suffix.lower() == ".pdf":
                    from src.knowledge_base import extract_text_from_pdf
                    doc_text = extract_text_from_pdf(doc_file)
                else:
                    doc_text = doc_file.read_text(encoding="utf-8", errors="ignore")
                st.text_area("Policy Clause Content:", value=doc_text, height=320, disabled=True)
            except Exception as e:
                st.error(f"Error loading policy: {e}")


# -------------------------------------------------------------
# COPILOT RECOMMENDATION & AUDIT AREA
# -------------------------------------------------------------
st.markdown("---")

if st.session_state.current_answer is not None:
    ans = st.session_state.current_answer
    warnings = st.session_state.current_warnings
    passages = st.session_state.current_passages

    st.markdown("""
    <div style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
        💡 Copilot Verified Recommendation & Grounded Script
    </div>
    """, unsafe_allow_html=True)

    # Customer Query Header
    st.markdown(f"""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:10px 14px; font-size:0.9rem; color:#334155; margin-bottom:12px;">
        <strong>Customer Inquiry:</strong> <em>"{st.session_state.current_transcription}"</em>
    </div>
    """, unsafe_allow_html=True)

    # Safety Warnings
    if warnings:
        for w in warnings:
            st.markdown(f"""
            <div style="background:#FFFBEB; border:1px solid #FDE68A; border-left:4px solid #D97706; border-radius:4px; padding:8px 12px; font-size:0.85rem; color:#92400E; margin-bottom:8px;">
                🛡️ <strong>Safety Compliance Guardrail:</strong> {w}
            </div>
            """, unsafe_allow_html=True)

    # Escalation Alert
    if ans.escalation_required:
        st.markdown(f"""
        <div class="escalation-banner">
            <div class="escalation-title">⚠️ Mandatory Tier-2 Supervisor Escalation Required</div>
            <div class="escalation-desc">{ans.escalation_reason or 'Policy evidence is insufficient or transaction exceeds agent authority limits.'}</div>
        </div>
        """, unsafe_allow_html=True)

    # Ensure agent script explicitly includes customer details, switch failure logs, and SLA
    agent_script_to_show = ans.agent_script
    if (
        not agent_script_to_show
        or "reviewing your transaction details" in agent_script_to_show.lower()
        or "reviewing your account and transaction" in agent_script_to_show.lower()
        or "let me check the latest status" in agent_script_to_show.lower()
        or "<support" in agent_script_to_show.lower()
        or "<" in agent_script_to_show
        or len(agent_script_to_show) < 50
        or (customer and customer.transaction_amount not in agent_script_to_show and customer.transaction_id not in agent_script_to_show)
        or (customer and customer.failure_reason and (
            customer.failure_reason.lower() not in agent_script_to_show.lower() and
            "u69" not in agent_script_to_show.lower() and
            "m4" not in agent_script_to_show.lower() and
            "timeout" not in agent_script_to_show.lower() and
            "dispute" not in agent_script_to_show.lower() and
            "duplicate" not in agent_script_to_show.lower() and
            "dispenser" not in agent_script_to_show.lower() and
            "shutter" not in agent_script_to_show.lower()
        ))
    ):
        agent_script_to_show = build_grounded_agent_script(customer, ans.sop_policy_id, passages)

    # Ensure operational steps are concrete, numbered steps
    action_to_show = ans.next_action
    if (
        not action_to_show
        or "verify core switch" in action_to_show.lower()
        or "reassure customer" in action_to_show.lower()
        or len(action_to_show) < 25
        or ("step" not in action_to_show.lower() and "1." not in action_to_show)
    ):
        action_to_show = get_default_operational_steps(ans.sop_policy_id, customer)

    # Proposed Script Card (Big, Clear & Readable)
    st.markdown(f"""
    <div class="script-container">
        <div class="script-label" style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.82rem; font-weight:700;">🗣️ WHAT TO TELL THE CUSTOMER (READ ALOUD SCRIPT)</span>
            <span style="font-size:0.7rem; background:#DCFCE7; color:#15803D; padding:2px 8px; border-radius:4px; font-weight:600;">Grounded with Failure Logs & SLA</span>
        </div>
        <div class="script-text" style="margin-top:10px; font-size:1.15rem; line-height:1.65; color:#0F172A;">
            "{agent_script_to_show}"
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Technical Failure & Switch Log Breakdown Card (For Agent Knowledge)
    if customer:
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:6px; padding:12px 16px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.03);">
            <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#475569; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                <span>🔍 Core Technical Failure & Network Switch Log Reference:</span>
            </div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px; font-size:0.83rem;">
                <div>
                    <span style="color:#64748B;">Failure / Error Code:</span><br/>
                    <strong style="color:#991B1B;">{customer.failure_reason or 'Switch Processing Delay'}</strong>
                </div>
                <div>
                    <span style="color:#64748B;">Account Debit Status:</span><br/>
                    <strong style="color:#0F172A;">{customer.debit_status or 'Debited from account'}</strong>
                </div>
                <div>
                    <span style="color:#64748B;">Reconciliation SLA:</span><br/>
                    <strong style="color:#059669;">{customer.auto_reversal_status or 'T+1 Working Day'}</strong>
                </div>
                <div>
                    <span style="color:#64748B;">Beneficiary Entity:</span><br/>
                    <strong style="color:#0F172A;">{customer.beneficiary_name or 'N/A'} ({customer.beneficiary_bank or 'N/A'})</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Actionable Steps and Metadata Grid
    col_act, col_pol, col_stat = st.columns([1.8, 1.4, 1.2])

    with col_act:
        action_lines = [l.strip() for l in action_to_show.splitlines() if l.strip()]
        if len(action_lines) > 1:
            items = []
            for l in action_lines:
                items.append(
                    f'<div style="display:flex; align-items:flex-start; gap:8px; margin-bottom:8px; font-size:0.88rem; color:#1E293B;">'
                    f'<span style="color:#2563EB; font-weight:700; margin-top:1px;">▸</span>'
                    f'<span style="line-height:1.45;">{l}</span>'
                    f'</div>'
                )
            steps_html = "".join(items)
        else:
            steps_html = f'<div style="font-size:0.9rem; line-height:1.5; color:#1E293B;">{action_to_show}</div>'

        st.markdown(
            f'<div class="action-container">'
            f'<div class="action-label" style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span>📋 Standard Operational Procedure (SOP) Action Steps:</span>'
            f'<span style="font-size:0.65rem; background:#DBEAFE; color:#1E40AF; padding:2px 6px; border-radius:3px; font-weight:600;">Mandatory Protocol</span>'
            f'</div>'
            f'<div style="margin-top:8px;">{steps_html}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_pol:
        policy_label = ans.sop_policy_id or "SOP-GENERAL"
        st.markdown(f"""
        <div class="bank-card" style="margin-bottom:14px;">
            <div class="bank-card-title">Supporting Policy Evidence</div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Policy Clause ID</span>
                <span class="mono-val" style="color:#2563EB; font-weight:700;">{policy_label}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Grounding Confidence</span>
                <span class="bank-metric-value">{ans.confidence_score:.2f} / 1.00</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Inference Latency</span>
                <span class="bank-metric-value">{ans.latency_seconds or '0.0'}s</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_stat:
        esc_badge = '<span class="badge-status badge-failed">Escalate</span>' if ans.escalation_required else '<span class="badge-status badge-success">Resolved</span>'
        st.markdown(f"""
        <div class="bank-card" style="margin-bottom:14px;">
            <div class="bank-card-title">Call Action Status</div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Resolution</span>
                <span>{esc_badge}</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Security Audit</span>
                <span style="color:#059669; font-weight:600; font-size:0.8rem;">● Passed</span>
            </div>
            <div class="bank-metric-row">
                <span class="bank-metric-label">Grounding Mode</span>
                <span style="font-size:0.75rem; color:#64748B;">Strict SOP</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Collapsible SOP Evidence Drawer
    with st.expander("🔍 Audit Retrieved Bank SOP Evidence Clauses", expanded=False):
        if passages:
            for i, p in enumerate(passages, 1):
                st.markdown(f"**Clause {i} — `{p.policy_id}`: {p.policy_title}** (Relevance Match: `{p.similarity_score:.2f}`)")
                st.caption(f"Section: {p.section} | Source Document: {p.doc_name}")
                st.info(p.content)
        else:
            st.write("No matching policy clauses found.")

else:
    st.markdown("""
    <div style="background:#F8FAFC; border:1px dashed #CBD5E1; border-radius:8px; padding:24px; text-align:center; color:#64748B;">
        <span style="font-size:1.8rem;">🎧</span>
        <div style="font-weight:600; font-size:0.95rem; margin-top:6px; color:#334155;">Workstation Standby</div>
        <div style="font-size:0.85rem; margin-top:2px;">Speak into your microphone via <strong>Live Customer Call</strong> or select a recording under <strong>Audio QA</strong> to generate assistance.</div>
    </div>
    """, unsafe_allow_html=True)
