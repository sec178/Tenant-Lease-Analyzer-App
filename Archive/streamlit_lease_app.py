"""
Streamlit Web Interface for Tenant Lease Analyzer

Run with: streamlit run streamlit_lease_app.py
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from datetime import datetime
from lease_analyzer_app import LeaseAnalyzerAgent, format_analysis_report

from dotenv import load_dotenv 
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="TenFi: Your Tenant Lease Companion",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        padding: 1rem 0 0.5rem 0;
        border-bottom: 2px solid #3498db;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .danger-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'lease_loaded' not in st.session_state:
    st.session_state.lease_loaded = False
if 'input_method' not in st.session_state:
    st.session_state.input_method = "Upload PDF"


def initialize_analyzer():
    """Initialize the lease analyzer with API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        st.error("⚠️ ANTHROPIC_API_KEY not found in environment variables. Please set it to use this app.")
        st.info("You can set it in a .env file or as an environment variable.")
        st.stop()
    
    if st.session_state.analyzer is None:
        with st.spinner("Initializing AI analyzer..."):
            st.session_state.analyzer = LeaseAnalyzerAgent(api_key)
    
    return st.session_state.analyzer


def reset_analysis():
    """Reset the analysis state."""
    st.session_state.lease_loaded = False
    st.session_state.results = None
    if st.session_state.analyzer:
        st.session_state.analyzer.lease_text = None
        st.session_state.analyzer.metadata = None


def main():
    """Main application."""
    
    # Header
    st.markdown('<div class="main-header">🏠 TenFi</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="text-align: center; font-size: 1.1rem; color: #555;">
    Hello, I'm TenFi! An AI-powered tool to help tenants understand and negotiate their leases
    </p>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 About This Tool")
        st.write("""
        This tool helps you:
        - 📄 Summarize your lease
        - 🚨 Identify problematic clauses
        - 💰 Compare rental prices
        - ✏️ Get rewrite suggestions
        - ⚖️ Learn your tenant rights
        """)
        
        st.divider()
        
        st.header("⚙️ Settings")
        analysis_mode = st.radio(
            "Analysis Mode",
            ["Full Analysis", "Step-by-Step"],
            help="Full Analysis runs everything at once. Step-by-Step lets you choose what to analyze."
        )
        
        st.divider()
        
        st.header("⚠️ Disclaimer")
        st.caption("""
        This tool provides general information and suggestions. 
        It is NOT legal advice. For specific legal issues, 
        consult a qualified attorney or tenant rights organization.
        """)
    
    # Initialize analyzer
    analyzer = initialize_analyzer()
    
    # ================================
    # Provide lease section
    # ================================
    st.markdown('<div class="section-header">📤 Provide Your Lease</div>', unsafe_allow_html=True)
    
    input_method = st.radio(
        "Choose how to provide your lease:",
        ["Upload PDF", "Paste Text", "Enter Details Manually"],
        horizontal=True,
        key="input_method_radio"
    )
    
    # -------------------------------
    # OPTION 1: UPLOAD PDF
    # -------------------------------
    if input_method == "Upload PDF":
        uploaded_file = st.file_uploader(
            "Choose your lease PDF file",
            type=['pdf'],
            help="Upload your lease agreement in PDF format"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            if not st.session_state.lease_loaded:
                with st.spinner("📄 Loading and processing lease..."):
                    load_result = analyzer.load_lease(tmp_file_path)
                
                if load_result['status'] == 'success':
                    st.session_state.lease_loaded = True
                    st.success("✅ Lease loaded successfully!")
                    
                    # Display metadata
                    metadata = load_result.get('metadata', {})
                    display_metadata(metadata)
                else:
                    st.error(f"❌ Error loading lease: {load_result.get('message', 'Unknown error')}")
                
                # Cleanup temp file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
    
    # -------------------------------
    # OPTION 2: PASTE TEXT
    # -------------------------------
    elif input_method == "Paste Text":
        lease_text_input = st.text_area(
            "Paste your lease text here",
            height=300,
            placeholder="Paste your full lease or specific clauses...",
            help="Copy and paste the text of your lease document"
        )
        
        if st.button("Load Lease Text", type="primary"):
            if lease_text_input.strip() == "":
                st.error("Please paste lease text first")
            else:
                with st.spinner("Loading lease text..."):
                    load_result = analyzer.load_lease_text(lease_text_input)
                
                if load_result["status"] == "success":
                    st.session_state.lease_loaded = True
                    st.success("✅ Lease text loaded successfully!")
                    
                    # Display extracted metadata
                    metadata = load_result.get('metadata', {})
                    if metadata:
                        display_metadata(metadata)
                else:
                    st.error(f"❌ Error: {load_result['message']}")
    
    # -------------------------------
    # OPTION 3: MANUAL ENTRY
    # -------------------------------
    elif input_method == "Enter Details Manually":
        st.info("📝 Fill in the lease details below. You can fill in as much or as little as you know.")
        
        with st.form("manual_lease_form"):
            st.subheader("Property Information")
            col1, col2 = st.columns(2)
            
            with col1:
                property_address = st.text_input("Property Address", help="Full street address")
                city = st.text_input("City", help="City where property is located")
                state = st.text_input("State", help="State (e.g., CA, NY, TX)")
            
            with col2:
                zip_code = st.text_input("ZIP Code", help="5-digit ZIP code")
                landlord_name = st.text_input("Landlord/Property Manager Name", help="Name of landlord or company")
            
            st.divider()
            st.subheader("Financial Details")
            col3, col4 = st.columns(2)
            
            with col3:
                monthly_rent = st.number_input("Monthly Rent ($)", min_value=0.0, step=100.0, help="Monthly rent amount")
                security_deposit = st.number_input("Security Deposit ($)", min_value=0.0, step=100.0, help="Security deposit amount")
            
            with col4:
                number_of_bedrooms = st.number_input("Number of Bedrooms", min_value=0, max_value=10, step=1, value=1)
                number_of_bathrooms = st.number_input("Number of Bathrooms", min_value=0.0, max_value=10.0, step=0.5, value=1.0)
            
            st.divider()
            st.subheader("Lease Term")
            col5, col6 = st.columns(2)
            
            with col5:
                lease_start_date = st.date_input("Lease Start Date", help="Date lease begins")
            
            with col6:
                lease_end_date = st.date_input("Lease End Date", help="Date lease ends")
            
            st.divider()
            st.subheader("Lease Terms & Clauses")
            lease_clauses = st.text_area(
                "Paste key lease clauses or concerns (optional)",
                height=200,
                placeholder="Example: 'Tenant is responsible for all repairs regardless of cause...'\n\nPaste any specific clauses you're concerned about, or leave blank to focus on the information above.",
                help="Include any specific lease language you want analyzed"
            )
            
            submitted = st.form_submit_button("Load Manual Entry", type="primary")
            
            if submitted:
                # Validate required fields
                if not city or not state:
                    st.error("⚠️ City and State are required for analysis.")
                else:
                    # Build metadata dictionary
                    manual_metadata = {
                        "property_address": property_address if property_address else None,
                        "city": city,
                        "state": state,
                        "zip_code": zip_code if zip_code else None,
                        "monthly_rent": float(monthly_rent) if monthly_rent > 0 else None,
                        "security_deposit": float(security_deposit) if security_deposit > 0 else None,
                        "lease_start_date": str(lease_start_date) if lease_start_date else None,
                        "lease_end_date": str(lease_end_date) if lease_end_date else None,
                        "landlord_name": landlord_name if landlord_name else None,
                        "number_of_bedrooms": int(number_of_bedrooms) if number_of_bedrooms else None,
                        "number_of_bathrooms": float(number_of_bathrooms) if number_of_bathrooms else None
                    }
                    
                    # Create a lease text from the clauses or metadata
                    if lease_clauses.strip():
                        lease_text = f"Lease for property at {property_address or 'address not specified'}, {city}, {state}.\n\n"
                        lease_text += f"Monthly Rent: ${monthly_rent}\n"
                        lease_text += f"Security Deposit: ${security_deposit}\n"
                        lease_text += f"Lease Term: {lease_start_date} to {lease_end_date}\n\n"
                        lease_text += "Key Clauses:\n\n"
                        lease_text += lease_clauses
                    else:
                        # Generate minimal lease text from metadata
                        lease_text = f"Lease Agreement\n\n"
                        lease_text += f"Property: {property_address or 'Not specified'}\n"
                        lease_text += f"Location: {city}, {state} {zip_code or ''}\n"
                        lease_text += f"Landlord: {landlord_name or 'Not specified'}\n"
                        lease_text += f"Monthly Rent: ${monthly_rent}\n"
                        lease_text += f"Security Deposit: ${security_deposit}\n"
                        lease_text += f"Bedrooms: {number_of_bedrooms}, Bathrooms: {number_of_bathrooms}\n"
                        lease_text += f"Lease Term: {lease_start_date} to {lease_end_date}\n"
                    
                    with st.spinner("Loading manual entry..."):
                        load_result = analyzer.load_lease_text(lease_text, manual_metadata)
                    
                    if load_result["status"] == "success":
                        st.session_state.lease_loaded = True
                        st.success("✅ Manual entry loaded successfully!")
                        
                        # Display the metadata
                        display_metadata(manual_metadata)
                    else:
                        st.error(f"❌ Error: {load_result['message']}")
    
    # ================================
    # Analysis Section
    # ================================
    if st.session_state.lease_loaded:
        st.divider()
        st.markdown('<div class="section-header">🔍 Analysis Options</div>', unsafe_allow_html=True)
        
        col_reset, col_analyze = st.columns([1, 4])
        
        with col_reset:
            if st.button("🔄 Start Over", use_container_width=True):
                reset_analysis()
                st.rerun()
        
        with col_analyze:
            if analysis_mode == "Full Analysis":
                if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
                    with st.spinner("🔍 Running comprehensive analysis... This may take a minute."):
                        st.session_state.results = analyzer.analyze_full_lease()
                    st.success("✅ Analysis complete!")
                    st.rerun()
            else:
                st.info("👇 Choose specific analyses below in step-by-step mode")
        
        # Display results if available
        if st.session_state.results:
            st.divider()
            display_full_results(st.session_state.results)
        
        # Step-by-step analysis options
        if analysis_mode == "Step-by-Step" and not st.session_state.results:
            st.divider()
            display_step_by_step_analysis(analyzer)


def display_metadata(metadata):
    """Display lease metadata in a nice format."""
    if not metadata:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rent = metadata.get('monthly_rent')
        if rent:
            st.metric("Monthly Rent", f"${rent:,.2f}" if isinstance(rent, (int, float)) else f"${rent}")
        else:
            st.metric("Monthly Rent", "Not specified")
    
    with col2:
        deposit = metadata.get('security_deposit')
        if deposit:
            st.metric("Security Deposit", f"${deposit:,.2f}" if isinstance(deposit, (int, float)) else f"${deposit}")
        else:
            st.metric("Security Deposit", "Not specified")
    
    with col3:
        bedrooms = metadata.get('number_of_bedrooms', 'N/A')
        bathrooms = metadata.get('number_of_bathrooms', 'N/A')
        st.metric("Bed/Bath", f"{bedrooms}BR / {bathrooms}BA")
    
    with st.expander("📍 Full Property Details"):
        st.write(f"**Address:** {metadata.get('property_address', 'Not specified')}")
        st.write(f"**City:** {metadata.get('city', 'Not specified')}, {metadata.get('state', 'Not specified')} {metadata.get('zip_code', '')}")
        st.write(f"**Landlord:** {metadata.get('landlord_name', 'Not specified')}")
        st.write(f"**Lease Term:** {metadata.get('lease_start_date', 'Not specified')} to {metadata.get('lease_end_date', 'Not specified')}")


def display_full_results(results):
    """Display complete analysis results."""
    
    tabs = st.tabs([
        "📋 Summary",
        "🚨 Issues",
        "💰 Pricing",
        "✏️ Rewrites",
        "⚖️ Rights",
        "📄 Full Report"
    ])
    
    # Tab 1: Summary
    with tabs[0]:
        st.markdown('<div class="section-header">📋 Lease Summary</div>', unsafe_allow_html=True)
        st.write(results.get('summary', 'No summary available'))
    
    # Tab 2: Issues
    with tabs[1]:
        st.markdown('<div class="section-header">🚨 Problematic Clauses</div>', unsafe_allow_html=True)
        
        clauses = results.get('problematic_clauses', [])
        if clauses:
            # Summary metrics
            high_severity = sum(1 for c in clauses if c.get('severity') == 'High')
            medium_severity = sum(1 for c in clauses if c.get('severity') == 'Medium')
            low_severity = sum(1 for c in clauses if c.get('severity') == 'Low')
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Issues", len(clauses))
            col2.metric("🔴 High", high_severity)
            col3.metric("🟡 Medium", medium_severity)
            col4.metric("🟢 Low", low_severity)
            
            st.divider()
            
            # Display each clause
            for i, clause in enumerate(clauses, 1):
                severity = clause.get('severity', 'Unknown')
                
                # Choose styling based on severity
                if severity == 'High':
                    icon = "🔴"
                elif severity == 'Medium':
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                with st.expander(f"{icon} Issue {i}: {severity} Severity"):
                    st.write(f"**Clause:** {clause.get('clause', 'N/A')}")
                    st.write(f"**Issue:** {clause.get('issue', 'N/A')}")
                    
                    if clause.get('potentially_illegal'):
                        st.error("⚠️ This clause may be illegal or unenforceable")
                    
                    st.write(f"**Recommendation:** {clause.get('recommendation', 'N/A')}")
        else:
            st.success("✅ No significant issues identified in this lease!")
    
    # Tab 3: Pricing
    with tabs[2]:
        st.markdown('<div class="section-header">💰 Rental Price Analysis</div>', unsafe_allow_html=True)
        
        if results.get('rental_price_analysis'):
            st.write(results['rental_price_analysis'])
            
            st.info("""
            **💡 Tip:** To get accurate current market data, check:
            - Zillow.com
            - Apartments.com
            - Craigslist
            - RentData.org
            - HUD Fair Market Rent data
            """)
        else:
            st.warning("Price analysis not available. Ensure your lease has location and rent information.")
    
    # Tab 4: Rewrites
    with tabs[3]:
        st.markdown('<div class="section-header">✏️ Suggested Lease Rewrites</div>', unsafe_allow_html=True)
        
        rewrites = results.get('rewrite_suggestions', [])
        if rewrites:
            st.write(f"Found {len(rewrites)} clauses that could be improved:")
            
            for i, rewrite in enumerate(rewrites, 1):
                with st.expander(f"Rewrite Suggestion {i}: {rewrite.get('severity', '')} Severity Issue"):
                    st.write("**Original Clause:**")
                    st.code(rewrite.get('original_clause', 'N/A'), language=None)
                    
                    st.divider()
                    
                    st.write("**Suggested Changes:**")
                    st.write(rewrite.get('rewrite_suggestion', 'N/A'))
        else:
            st.info("No rewrites suggested. Either no significant issues were found, or the lease terms are fair.")
    
    # Tab 5: Rights
    with tabs[4]:
        st.markdown('<div class="section-header">⚖️ Your Tenant Rights</div>', unsafe_allow_html=True)
        st.write(results.get('tenant_rights', 'No rights information available'))
        
        st.warning("""
        **⚠️ Important:** This is general information. Tenant rights vary by location and circumstances.
        
        For specific legal advice, contact:
        - Local tenant rights organizations
        - Legal aid clinics
        - Your state attorney general's office
        - A qualified attorney
        """)
    
    # Tab 6: Full Report
    with tabs[5]:
        st.markdown('<div class="section-header">📄 Complete Analysis Report</div>', unsafe_allow_html=True)
        
        report = format_analysis_report(results)
        
        st.text_area("Full Report", report, height=400)
        
        # Download button
        report_filename = f"lease_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        st.download_button(
            label="📥 Download Report",
            data=report,
            file_name=report_filename,
            mime="text/plain",
            use_container_width=True
        )


def display_step_by_step_analysis(analyzer):
    """Display step-by-step analysis options."""
    
    st.markdown('<div class="section-header">🔍 Choose Analysis Steps</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Summarize Lease", use_container_width=True):
            with st.spinner("Analyzing..."):
                summary = analyzer.analyzer.summarize_lease(analyzer.lease_text)
            st.write(summary)
        
        if st.button("🚨 Find Problematic Clauses", use_container_width=True):
            with st.spinner("Analyzing..."):
                clauses = analyzer.analyzer.identify_problematic_clauses(analyzer.lease_text)
            
            st.write(f"Found {len(clauses)} potential issues:")
            for i, clause in enumerate(clauses, 1):
                with st.expander(f"Issue {i}: {clause.get('severity', 'Unknown')} Severity"):
                    st.write(f"**Clause:** {clause.get('clause', 'N/A')}")
                    st.write(f"**Issue:** {clause.get('issue', 'N/A')}")
                    st.write(f"**Recommendation:** {clause.get('recommendation', 'N/A')}")
        
        if st.button("💰 Check Rental Prices", use_container_width=True):
            metadata = analyzer.metadata
            if metadata and metadata.get('monthly_rent') and metadata.get('city'):
                with st.spinner("Analyzing market rates..."):
                    price_analysis = analyzer.analyzer.get_rental_price_context(
                        metadata.get('city', ''),
                        metadata.get('state', ''),
                        metadata.get('zip_code', ''),
                        metadata.get('number_of_bedrooms', 1),
                        metadata.get('monthly_rent', 0)
                    )
                st.write(price_analysis)
            else:
                st.error("Could not extract rent and location information from lease")
    
    with col2:
        if st.button("✏️ Get Rewrite Suggestions", use_container_width=True):
            with st.spinner("Generating suggestions..."):
                clauses = analyzer.analyzer.identify_problematic_clauses(analyzer.lease_text)
                rewrites = analyzer.analyzer.suggest_lease_rewrites(clauses, analyzer.lease_text)
            
            if rewrites:
                for i, rewrite in enumerate(rewrites, 1):
                    with st.expander(f"Suggestion {i}"):
                        st.write("**Original:**")
                        st.code(rewrite.get('original_clause', 'N/A'), language=None)
                        st.write("**Suggested Changes:**")
                        st.write(rewrite.get('rewrite_suggestion', 'N/A'))
            else:
                st.info("No rewrites suggested")
        
        if st.button("⚖️ Learn Your Rights", use_container_width=True):
            metadata = analyzer.metadata
            if metadata:
                with st.spinner("Researching tenant rights..."):
                    rights_info = analyzer.analyzer.get_tenant_rights_advice(
                        analyzer.lease_text,
                        metadata.get('state', ''),
                        metadata.get('city')
                    )
                st.write(rights_info)
            else:
                st.error("Location information not available")


if __name__ == "__main__":
    main()
