#!/usr/bin/env python3
"""
Streamlit app for Mistral OCR - PDF to Markdown/DOCX converter
"""
import streamlit as st
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64
import requests

# Import OCR functions from mistral_ocr
import mistral_ocr

# Configure Streamlit page
st.set_page_config(
    page_title="Suvichaar Doc Intelligence Platform",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = None
if 'pages_text' not in st.session_state:
    st.session_state.pages_text = []
if 'md_text' not in st.session_state:
    st.session_state.md_text = None
if 'docx_path' not in st.session_state:
    st.session_state.docx_path = None

def get_config_from_secrets():
    """Load configuration from Streamlit secrets"""
    try:
        return {
            'endpoint': st.secrets['mistral']['ocr_endpoint'],
            'api_key': st.secrets['mistral']['api_key'],
            'model': st.secrets['mistral'].get('model', 'mistral-document-ai-2505')
        }
    except KeyError as e:
        st.error(f"Missing configuration in secrets.toml: {e}")
        st.info("Please configure your secrets.toml file. See README.md for details.")
        return None

def post_ocr_with_config(payload: dict, config: dict):
    """Post OCR request using configuration from secrets"""
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    r = requests.post(config['endpoint'], headers=headers, json=payload, timeout=600)
    if r.status_code >= 400:
        st.error(f"API Error {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
    return r.json()

def process_pdf(pdf_bytes: bytes, config: dict, title: Optional[str] = None, 
                insert_page_breaks: bool = True) -> Dict[str, Any]:
    """Process PDF through OCR and return results"""
    
    # Convert PDF to data URL
    data_url = mistral_ocr.bytes_to_data_url("application/pdf", pdf_bytes)
    
    # Prepare payload
    payload = {
        "model": config['model'],
        "document": {"type": "document_url", "document_url": data_url},
        "include_image_base64": False,  # Text-only mode
    }
    
    # Call OCR API
    with st.spinner("Processing PDF with  Doc Intelligence..."):
        resp = post_ocr_with_config(payload, config)
    
    # Unwrap response container
    container = mistral_ocr.unwrap_container(resp)
    pages = container.get("pages")
    
    if not isinstance(pages, list) or not pages:
        # Try to get top-level text
        top = ""
        for k in ("markdown", "full_text", "content", "text", "raw_text"):
            if isinstance(container.get(k), str) and container[k].strip():
                top = container[k]
                break
        if not top.strip():
            raise ValueError("No pages and no usable top-level text found in OCR response.")
        pages = [{"markdown": top}]
    
    # Extract text from pages
    pages_text: List[str] = []
    for i, p in enumerate(pages, start=1):
        txt = mistral_ocr.extract_from_page(p if isinstance(p, dict) else {}) or ""
        if title and i == 1:
            txt = f"# {title}\n\n{txt}"
        pages_text.append(txt)
    
    # Build markdown
    md_text = mistral_ocr.build_markdown(
        pages_text,
        images_by_page={},  # No images in text-only mode
        crops_by_page={},   # No crops in text-only mode
        insert_page_breaks=insert_page_breaks,
        image_max_width_in=6.5,
    )
    
    return {
        'response': resp,
        'pages_text': pages_text,
        'md_text': md_text,
        'num_pages': len(pages)
    }

def create_docx(md_text: str, pages_text: List[str], output_dir: Path, 
                insert_page_breaks: bool) -> Path:
    """Create DOCX file from markdown"""
    docx_path = output_dir / "output.docx"
    
    with st.spinner("Generating DOCX file..."):
        mistral_ocr.build_hybrid_docx(
            md_text,
            pages_text,
            images_by_page={},
            crops_by_page={},
            out_path=docx_path,
            insert_page_breaks=insert_page_breaks,
            image_max_width_in=6.5,
        )
    
    return docx_path

def main():
    st.title("📄 Suvichaar Doc Intelligence Platform Test")
    st.markdown("Upload a PDF file to extract text and convert it to Markdown and DOCX formats.")
    
    # Load configuration
    config = get_config_from_secrets()
    if not config:
        st.stop()
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        title = st.text_input("Document Title (optional)", help="Will be added as H1 heading on first page")
        insert_page_breaks = st.checkbox("Insert page breaks", value=True, 
                                         help="Add page breaks between pages in output")
        st.divider()
        st.info("💡 Configure your API credentials in `.streamlit/secrets.toml`")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload PDF File",
        type=['pdf'],
        help="Select a PDF file to process"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_size = len(uploaded_file.getvalue())
        st.info(f"📎 File: {uploaded_file.name} ({file_size:,} bytes)")
        
        # Process button
        if st.button("🚀 Process PDF", type="primary", use_container_width=True):
            try:
                pdf_bytes = uploaded_file.getvalue()
                
                # Process PDF
                result = process_pdf(
                    pdf_bytes,
                    config,
                    title=title if title else None,
                    insert_page_breaks=insert_page_breaks
                )
                
                # Store in session state
                st.session_state.ocr_result = result['response']
                st.session_state.pages_text = result['pages_text']
                st.session_state.md_text = result['md_text']
                
                st.success(f"✅ Successfully processed {result['num_pages']} page(s)!")
                
            except Exception as e:
                st.error(f"❌ Error processing PDF: {str(e)}")
                st.exception(e)
        
        # Display results if available
        if st.session_state.md_text:
            st.divider()
            st.header("📊 Results")
            
            # Create temporary directory for outputs
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                
                # Save markdown
                md_path = tmp_path / "output.md"
                md_path.write_text(st.session_state.md_text, encoding="utf-8")
                
                # Create DOCX
                try:
                    docx_path = create_docx(
                        st.session_state.md_text,
                        st.session_state.pages_text,
                        tmp_path,
                        insert_page_breaks
                    )
                    
                    # Download buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="📥 Download Markdown",
                            data=st.session_state.md_text,
                            file_name="output.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with col2:
                        if docx_path.exists():
                            docx_bytes = docx_path.read_bytes()
                            st.download_button(
                                label="📥 Download DOCX",
                                data=docx_bytes,
                                file_name="output.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                    
                    # Preview tabs
                    tab1, tab2, tab3 = st.tabs(["📝 Markdown Preview", "📄 Pages", "🔍 Raw Response"])
                    
                    with tab1:
                        st.markdown("### Markdown Output")
                        st.code(st.session_state.md_text, language="markdown")
                    
                    with tab2:
                        st.markdown("### Extracted Pages")
                        for i, page_text in enumerate(st.session_state.pages_text, start=1):
                            with st.expander(f"Page {i}", expanded=(i == 1)):
                                st.text(page_text)
                    
                    with tab3:
                        st.markdown("### Raw OCR Response")
                        st.json(st.session_state.ocr_result)
                
                except Exception as e:
                    st.error(f"❌ Error creating DOCX: {str(e)}")
                    st.exception(e)
                    
                    # Still offer markdown download
                    st.download_button(
                        label="📥 Download Markdown (DOCX failed)",
                        data=st.session_state.md_text,
                        file_name="output.md",
                        mime="text/markdown"
                    )

if __name__ == "__main__":
    main()

