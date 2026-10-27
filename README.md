# Real-Time FinTech Agent-Assist Copilot

A local, privacy-preserving AI assistant built for banking customer-support agents. The copilot listens to customer queries via laptop microphone (or uploaded sample audio), retrieves relevant policy evidence from bank SOP documents using vector search, generates grounded customer-ready responses using a local Ollama LLM, and enforces strict financial safety guardrails.

---

## 1. System Architecture & Features

1. **Banking Agent Dashboard:**
   - Displays Call ID, Customer Name, Account Tier, Transaction Amount, Type, and Status.
   - Built with read-only MongoDB support and automatic fallback to synthetic JSON records (`data/sample_customers.json`).
   - Includes realistic customer scenarios: Failed IMPS, Pending UPI, Disputed Card, and Failed ATM Withdrawal.

2. **Live Microphone Input & Tap-to-Now Audio Buffer:**
   - Captures microphone audio continuously using thread-safe background streaming (`sounddevice`).
   - "Mark Question Start" records the timestamp when the customer states their question.
   - "Get Answer Now" extracts the exact audio slice between the marked question start and the current endpoint, submitting only that portion to transcription.

3. **Speech-to-Text (STT):**
   - Uses local **Faster-Whisper** (`base.en` / `tiny.en`) with int8 quantization.
   - Runs directly on CPU/GPU without cloud APIs, achieving low-latency transcription of spoken customer inquiries.

4. **SOP Knowledge Base & Retrieval-Augmented Generation (RAG):**
   - Ingests bank policies in **PDF, Markdown, and TXT** formats from `data/sops/`.
   - Embeds policy chunks using local Ollama (`nomic-embed-text:latest`) with persistent disk caching.
   - Retains verified SOP policy identifiers (e.g., `SOP-IMPS-001`, `SOP-UPI-002`, `SOP-CARD-003`).

5. **Local LLM Response Generation:**
   - Powered by instruction-tuned local Ollama models (`dolphin-phi:2.7b` or `mistral:latest`).
   - Formulates concise, empathetic agent scripts with explicit policy citations and recommended next steps.

6. **Banking Safety Guardrails:**
   - **PII Masking:** Automatically masks PAN, Aadhaar, 16-digit card numbers, mobile numbers, CVV, and PIN before model inference.
   - **Credential Protection:** Blocks responses containing CVV, PIN, or full card numbers.
   - **Grounding Verification:** Enforces mandatory Tier-2 escalation if policy evidence is missing or confidence is below 0.75.
   - **Strict Read-Only:** Strictly prevents unauthorized financial commitments or balance manipulations.

---

## 2. Hardware Inspection & Model Recommendations

Inspected Laptop Configuration:
- **RAM:** 16 GB Physical Memory
- **GPU:** NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **Local LLM Engine:** Ollama (running locally at `http://localhost:11434`)
- **Configured Models:**
  - LLM: `dolphin-phi:2.7b` (1.6 GB — fast, lightweight, runs fully within 4GB VRAM) or `mistral:latest` (4.4 GB)
  - Embeddings: `nomic-embed-text:latest` (274 MB)
  - Speech Recognition: `faster-whisper` (`tiny.en` / `base.en`, CPU int8)

---

## 3. Quick Start Setup (PowerShell)

Open PowerShell in the project directory:

```powershell
# 1. Navigate to the project folder
cd "c:\Users\Rishav\Disk\Codes\LLM Projects\Customer_Query_Resolution"

# 2. Create Python virtual environment (if not already created)
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify Ollama service is active with required models
# (If Ollama is not started, launch it from the Start menu or run: ollama serve)
ollama list
```

*Note: If you ever need to pull the models on a fresh machine:*
```powershell
ollama pull dolphin-phi:2.7b
ollama pull nomic-embed-text:latest
```

---

## 4. Running the Application

Launch the Streamlit interactive dashboard:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## 5. Running the Automated Tests & Benchmarks

### A. Run Unit Tests (Pytest)
```powershell
.\.venv\Scripts\pytest.exe -v
```
*Validates PII masking, credential blocking, SOP document chunking, customer lookup, and JSON parsing.*

### B. Run End-to-End Evaluation Suite
```powershell
.\.venv\Scripts\python.exe evaluate.py
```
*Executes audio transcription, retrieval relevance, hallucination checks, safety escalations, and latency measurements across synthetic benchmark cases, generating `data/evaluation_report.md`.*

---

## 6. Manual Verification Checklist

1. **Customer Selection:**
   - In the sidebar dropdown, switch between `Aarav Sharma (IMPS: FAILED)` and `Priya Nair (UPI: PENDING)`. Verify that customer and transaction details update immediately.
2. **Sample Audio Mode:**
   - Switch to the **Sample Audio & Testing** tab.
   - Select `sample_failed_imps.wav` and click **Transcribe Audio File**.
   - Verify the transcribed question appears: *"My imps transaction of 15,000 rupees failed yesterday evening..."*
   - Click **Submit Question to Copilot** and review the proposed script with citation `SOP-IMPS-001` and reversal timeline `T+1`.
3. **Live Microphone & Tap-to-Now:**
   - Switch to the **Live Microphone Input** tab.
   - Click **Start Live Call** (allow microphone access if prompted).
   - Speak: *"Hello, I called regarding my failed payment..."*
   - Click **Mark Question Start**, then speak: *"When will the money be refunded back to my account?"*
   - Click **Get Answer Now**. Verify that only the question segment is sliced, transcribed, and answered.
4. **Safety & PII Guardrails:**
   - In the text box under Sample Audio, type: *"My PAN is ABCDE1234F and my CVV is 999. Can you promise me a full instant refund?"*
   - Submit and verify that the copilot masks the PAN, flags the CVV, blocks the guarantee, and triggers a **Tier-2 Escalation**.
5. **Adding Custom SOP Documents:**
   - Drop any new `.pdf`, `.md`, or `.txt` policy file into `data/sops/`.
   - Click **Rebuild SOP Index** in the sidebar. The copilot will index the new passages.

---

## 7. Folder Structure

```
Customer_Query_Resolution/
│
├── app.py                      # Streamlit interactive user interface
├── evaluate.py                 # Benchmark evaluation script
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .env.example                # Configuration template
├── .env                        # Local environment configuration
├── .gitignore                  # Git ignore rules
│
├── src/
│   ├── audio_capture.py        # Live microphone streaming & 'Tap-to-Now' slicing
│   ├── transcription.py        # Faster-Whisper speech-to-text decoding
│   ├── customer_context.py     # Customer records & MongoDB/JSON fallback
│   ├── knowledge_base.py       # SOP document parsing, vector indexing & RAG
│   ├── copilot.py              # LLM prompt construction & JSON response parsing
│   ├── safety.py               # PII masking, credential blocking & escalation
│   └── schemas.py              # Pydantic data models
│
├── data/
│   ├── sops/                   # Bank SOP documents (.md, .txt, .pdf)
│   ├── sample_customers.json   # Synthetic customer records
│   ├── sample_audio/           # Sample WAV audio files for offline testing
│   ├── evaluation_report.md    # Generated evaluation diagnostics
│   └── .cache/                 # Cached vector embeddings
│
└── tests/
    ├── test_safety.py           # Guardrails and PII tests
    ├── test_retrieval.py        # RAG retrieval and chunking tests
    ├── test_customer_context.py # Customer lookup tests
    └── test_copilot.py          # Copilot JSON response tests
```
