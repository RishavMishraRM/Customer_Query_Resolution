# Build a Real-Time FinTech Agent-Assist Copilot on My Laptop

## 1. Your Role

Act as a practical Python developer and AI engineer. Build a working prototype of my M.Tech AI and Data Science project, **Real-Time FinTech Agent-Assist Copilot**, based on the requirements below.

I will run this project locally on my Windows laptop using you as my coding agent.

Write code that a beginner can understand. Use straightforward Python, meaningful variable names, small functions, comments where necessary, and a clear folder structure. Avoid unnecessary abstractions, complicated design patterns, and enterprise infrastructure.

Do not just give me code snippets or instructions. Inspect my development environment, create the project files, implement the application, execute it, test it, fix errors, and provide exact commands to run it.

Before making major changes to my system, installing large dependencies, downloading models, or modifying existing files, explain what you intend to do.

## 2. Project Objective

Build a local AI assistant that helps a banking customer-support agent answer customer questions accurately using:

1. Live customer speech from my laptop microphone.
2. Existing sample audio recordings.
3. Customer and transaction information stored in MongoDB or provided through local sample JSON files.
4. Bank SOP and policy documents in PDF, TXT, or Markdown format.
5. Speech-to-text, retrieval-augmented generation (RAG), a local LLM, and safety guardrails.

The application should display a customer-ready response on the screen that I can read aloud to the customer.

Initially, this is a demonstration using synthetic customer data and sample policies. Do not connect to a real bank, real customers, real telephony systems, or production databases.

## 3. Inspect My Laptop First

Before choosing dependencies or models:

- Inspect the installed Python version, available RAM, GPU information, and whether Ollama is installed and running.
- Check which Ollama models are already available.
- Inspect the existing project directory if one exists.
- Recommend a model and speech-to-text configuration suitable for my actual hardware.
- Prefer CPU-compatible and quantized models when appropriate.
- Do not assume that my laptop can run a 26-billion-parameter model.
- Do not download a large model or start a costly cloud service without my approval.

If I do not have a suitable local model installed, give me the exact installation command and explain the approximate hardware requirements before proceeding.

## 4. Technology Choices

Prefer the following technologies, selecting simpler alternatives when a component creates unnecessary complexity:

- Language: Python
- User interface: Streamlit
- Speech-to-text: Faster-Whisper or another suitable local speech recognition engine
- LLM: Ollama with a locally available instruction-tuned model
- LLM routing: LiteLLM where practical
- SOP retrieval: ChromaDB or FAISS, choosing one
- Embeddings: A lightweight embedding model suitable for local use
- Customer context: MongoDB using PyMongo when locally available, with a local JSON fallback
- Document processing: A simple PDF and text extraction library
- Testing: pytest
- Data validation: Pydantic if needed for structured outputs

Prefer local processing so voice recordings and customer details do not need to leave my laptop.

Do not add Docker, Kubernetes, cloud GPUs, QLoRA training, GCP deployment, or a microservices architecture to the initial version. Keep those as future enhancements.

## 5. Feature One: Customer Dashboard

Create a simple, professional banking-agent dashboard.

Display the following information:

- Call ID
- Customer name or masked identifier
- Customer tier
- Transaction ID
- Transaction type
- Transaction amount
- Transaction status
- Transaction time, when available
- Live call timer

Load customer information from the local MongoDB database if configured. Otherwise, use clearly labelled synthetic JSON records.

Provide a dropdown to select a sample customer or active call.

Create at least three fictional customer scenarios with different transaction situations, such as a failed IMPS transaction, a pending UPI transaction, and a disputed card transaction.

All records must be fictional. Do not invent a real customer's account information or claim that sample records came from a bank system.

## 6. Feature Two: Live Microphone Input and Tap-to-Now

This is a core requirement.

I will personally speak into my laptop microphone to simulate the customer talking. I must not need a telephony provider or a real phone call.

Implement a usable live-call demonstration with:

1. A button to start the simulated live call and begin microphone capture.
2. A live talking-time timer.
3. A button labelled "Mark Question Start".
4. An audio buffer that retains the ongoing recording and the position at which I marked the question start.
5. A button labelled "Get Answer Now".
6. Extraction of the audio segment between the marked question start and the current capture endpoint.
7. Submission of that segment to the speech-to-text component.
8. Display of the transcribed customer question and generated answer.

For example, I may begin speaking about a transaction, mark the start when I reach the question, and click "Get Answer Now" at the end of that question.

The system should process only the selected portion of the call rather than automatically submitting the entire recording.

Use a straightforward, reliable microphone-capture implementation compatible with the chosen UI. If continuous browser audio buffering requires a separate component, keep that component small and explain how it works.

If the preferred live-capture library is unreliable in my environment, implement the simplest working microphone recording flow first, then improve it to support question-start markers. Do not pretend the exact Tap-to-Now functionality works until you have tested it.

Handle microphone permission errors, missing microphones, empty recordings, and recordings that are too short.

## 7. Feature Three: Upload and Test Sample Audio

Provide a separate "Sample Audio" mode.

I should be able to:

- Upload a WAV or MP3 file.
- Play the uploaded audio when supported.
- Transcribe the recording.
- Review or edit the transcribed text.
- Submit the text to the copilot.
- Compare answers for different recordings.

Include a small sample-data folder and instructions for adding my own test recordings.

The live microphone mode and uploaded-audio mode must use the same downstream question-answering pipeline.

## 8. Feature Four: Speech-to-Text

Convert the selected audio segment into readable text using a local speech recognition engine when feasible.

Display the resulting transcription on the dashboard.

Handle recognition failures, inaudible speech, empty transcriptions, and unsupported audio formats.

Keep transcription code in a separate, easy-to-understand Python file.

Do not claim a fixed transcription latency or accuracy without measuring it on this laptop.

## 9. Feature Five: SOP Documents and RAG

Create a knowledge base from policy documents stored in a local folder named `data/sops/`.

The system must:

- Read PDF, TXT, and Markdown documents.
- Extract their text.
- Split text into manageable chunks.
- Preserve the policy document name and SOP or policy identifier.
- Create embeddings and index the chunks.
- Retrieve the most relevant passages when a question is submitted.
- Display the retrieved passages and their source documents.
- Rebuild or update the index when I add or change policy documents.

Include several clearly labelled example SOPs written for demonstration purposes.

One example can explain the fictional procedure for investigating a failed IMPS transaction. Another can explain a pending UPI transaction. A third can explain disputed card transactions.

These policies are demonstration documents, not authoritative banking or RBI guidance. Do not present fictional refund periods, compensation rules, or financial entitlements as real policy.

Make the folder easy for me to populate with actual documents later.

## 10. Feature Six: LLM Answer Generation

Use the configured local Ollama model, preferably through LiteLLM if it can be integrated without unnecessary complexity.

The pipeline should combine:

- The transcribed customer question.
- The selected customer's permitted context.
- Relevant retrieved SOP passages.
- Instructions to generate a clear response for a banking call-center agent.

Return a structured result containing:

- `agent_script`: A concise response the agent can read to the customer.
- `sop_policy_id`: The identifier of the supporting policy, if available.
- `next_action`: A recommended next step.
- `confidence_score`: An explicitly labelled estimate, not a calibrated probability unless independently validated.
- `source_passages`: The supporting policy excerpts.
- `escalation_required`: True or False.
- `escalation_reason`: The reason for escalation, when applicable.

Validate the response and handle malformed model output gracefully.

Do not let the LLM invent transaction statuses, transaction IDs, balances, dates, policy identifiers, or customer eligibility.

## 11. Feature Seven: Banking Safety Guardrails

Apply safety checks before sending information to the model and before displaying the answer.

Required rules:

1. Never invent a banking policy or present unsupported information as fact.
2. Use available customer records and retrieved policy passages as the evidence for answers.
3. Mask sensitive information such as PAN, Aadhaar, CVV, PIN, full card numbers, account identifiers, and mobile numbers when applicable.
4. Never include CVV, PIN, or full payment-card details in the generated customer-facing response.
5. Do not promise fee waivers, refunds, or compensation unless supported by the configured policy and relevant customer data.
6. Include a verified source policy identifier when a supporting policy exists.
7. If the required customer record is missing, the retrieved evidence is insufficient, or retrieval confidence is below a configurable threshold of 0.75, recommend human review or Tier-2 escalation.
8. A score from the LLM alone must not override missing evidence or a failed safety check.
9. Never execute financial transactions or modify customer records automatically.
10. Keep the database connection read-only for the copilot workflow.

Use a simple, separate safety-check function with understandable logic. Do not rely on a second LLM call as the only safety mechanism.

Clearly distinguish a demo policy from a verified real banking policy.

## 12. Feature Eight: Display the Final Answer

The screen should show:

- Original audio or uploaded filename
- Transcribed question
- Selected customer context
- Relevant SOP excerpts
- Proposed agent script
- SOP or policy identifier
- Recommended next action
- Safety-check result
- Escalation status and reason, if applicable

Include a button to copy the proposed script.

Make it obvious when an answer is unsupported or when human review is needed. Show a warning instead of fabricating an answer when relevant evidence cannot be found.

## 13. Suggested Project Structure

Create a structure similar to this, adjusting it only when necessary:

`fintech-agent-assist-copilot/`

- `app.py` — Streamlit user interface
- `src/audio_capture.py` — Live microphone and audio buffering
- `src/transcription.py` — Speech-to-text
- `src/customer_context.py` — Customer records and database access
- `src/knowledge_base.py` — SOP loading, chunking and retrieval
- `src/copilot.py` — LLM orchestration and answer generation
- `src/safety.py` — PII masking, evidence checks and escalation
- `src/schemas.py` — Structured input/output models, if needed
- `data/sops/` — Example policy documents and user-provided documents
- `data/sample_customers.json` — Synthetic customer records
- `data/sample_audio/` — Optional audio test samples
- `tests/` — Basic unit tests
- `requirements.txt` — Dependencies
- `.env.example` — Configuration template
- `.gitignore` — Exclude environment files, recordings and local secrets
- `README.md` — Setup, execution and testing instructions

Do not put the entire application into one huge Python file. Also avoid creating separate files for trivial functions that do not need their own module.

## 14. Feature Nine: Testing and Evaluation

Create basic tests for:

- SOP document extraction and retrieval.
- Customer-context selection.
- PII masking.
- Policy citation handling.
- Missing customer information.
- Unsupported questions.
- Mandatory escalation conditions.
- Structured LLM response parsing.

Provide a manual test checklist for live microphone input and uploaded audio.

Create an evaluation script or report that records:

- Transcription output.
- Retrieval relevance.
- Whether the response is supported by the retrieved evidence.
- Correctness against manually written expected answers.
- Safety-rule violations.
- End-to-end response latency.
- Escalation decisions.

Use a small, labelled set of synthetic questions and expected answers.

Do not claim the accuracy, faithfulness, hallucination rate, or latency numbers from my presentation unless actual experiments support those numbers. Report the number of test cases and measured results.

## 15. Setup and Execution

Make the project easy to run on Windows.

Provide exact PowerShell commands for:

1. Creating or entering the project directory.
2. Creating a Python virtual environment.
3. Activating the environment.
4. Installing dependencies.
5. Installing or configuring the chosen local model and speech recognizer.
6. Configuring MongoDB if required, with a sample-data fallback.
7. Running the Streamlit application.
8. Running the tests.

Use a configuration file or environment variables for model names, database settings, and other changeable values.

The README must explain every setup step, common errors, microphone permissions, model availability, and how to add SOP documents and audio samples.

## 16. Implementation Strategy

Build and validate the project in this order:

Phase 1: Inspect the laptop and prepare the environment.

Phase 2: Build a basic dashboard with synthetic customer data.

Phase 3: Implement sample audio upload and transcription.

Phase 4: Implement working live microphone capture and question-start selection.

Phase 5: Add SOP ingestion, indexing, and retrieval.

Phase 6: Add local LLM answer generation through the configured interface.

Phase 7: Add PII masking, policy citations, and escalation guardrails.

Phase 8: Integrate the components into one end-to-end workflow.

Phase 9: Run the tests, resolve errors, and document how to verify the system manually.

At every phase, execute a small test before continuing. If a component fails, investigate and fix the actual error rather than bypassing it or declaring it complete.

## 17. Final Acceptance Criteria

The prototype is complete only when:

- The application launches locally.
- I can select a synthetic customer record.
- I can speak into my laptop microphone.
- I can mark the start of a customer question and request an answer using the selected audio segment.
- I can upload and process a separate audio sample.
- The question is transcribed.
- The system retrieves relevant passages from the local SOP knowledge base.
- The LLM generates a structured agent script grounded in the available evidence.
- The screen displays the supporting policy and recommended next action.
- Unsupported answers trigger an appropriate warning or escalation.
- Sensitive information is masked before model inference.
- Basic tests pass, and known limitations are documented.

Start by inspecting my laptop and describing the proposed implementation in simple terms. Then proceed with the implementation, showing me what you have created, the commands you ran, any errors you fixed, and how I can verify each feature.

Prioritize a working, understandable local prototype over an ambitious architecture that has not been tested.