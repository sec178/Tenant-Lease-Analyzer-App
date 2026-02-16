# 🏠 Tenant Lease Analyzer

An AI-powered application that helps tenants understand, analyze, and negotiate their lease agreements using LangChain and Claude.

## Features

✅ **Lease Summarization** - Get a plain-English summary of your lease terms
✅ **Clause Analysis** - Identify predatory, unusual, or potentially illegal clauses  
✅ **Rental Price Comparison** - Compare your rent to market rates in your area
✅ **Rewrite Suggestions** - Get alternative wording for unfair or negotiable terms
✅ **Tenant Rights Education** - Learn about your legal rights and protections

## Installation

### Prerequisites

- Python 3.9 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/)). Paste in .env

### Setup

1. **Clone or download this repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your API key**

Create a `.env` file in the project root:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

Or set it as an environment variable:
```bash
export ANTHROPIC_API_KEY=your_api_key_here  # Mac/Linux
set ANTHROPIC_API_KEY=your_api_key_here     # Windows
```

## Usage

### Option 1: Web Interface (Recommended)

Run the Streamlit web app:

```bash
streamlit run streamlit_lease_app.py

* The following commands may also need to be run in bash to activate the virtual environment:
cd .\TenFi_App1
venv\Scripts\activate
streamlit run streamlit_lease_app.py
```

Then:
1. Open your browser to http://localhost:8501
2. Upload your lease PDF
3. Choose "Full Analysis" or "Step-by-Step" mode
4. Review the analysis results
5. Download a complete report

### Option 2: Command Line

Run analysis from the terminal:

```bash
python lease_analyzer_app.py path/to/your/lease.pdf
```

This will:
- Analyze the lease completely
- Print results to the console
- Save a report to `lease_analysis_TIMESTAMP.txt`

### Option 3: Python API

Use the analyzer in your own code:

```python
from lease_analyzer_app import LeaseAnalyzerAgent
import os

# Initialize
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = LeaseAnalyzerAgent(api_key)

# Analyze a lease
results = agent.analyze_full_lease("path/to/lease.pdf")

# Access specific results
print(results['summary'])
print(results['problematic_clauses'])
print(results['rental_price_analysis'])
print(results['rewrite_suggestions'])
print(results['tenant_rights'])
```

## Example Output

### Lease Summary
```
Basic Terms: This is a 12-month lease for a 2-bedroom apartment at 
123 Main St, starting January 1, 2025. Monthly rent is $1,800 with 
a $1,800 security deposit...

Key Obligations: Tenant must pay rent by the 1st of each month, 
maintain the property in good condition, and provide 30 days notice 
before moving out...
```

### Problematic Clauses
```
1. [HIGH SEVERITY] ⚠️ POTENTIALLY ILLEGAL
   Clause: "Landlord may enter the premises at any time without notice."
   Issue: This violates tenant privacy rights. Most states require 
          24-48 hours notice except in emergencies.
   Recommendation: Request this be changed to require reasonable notice 
                   (typically 24-48 hours) for non-emergency entry.

2. [MEDIUM SEVERITY]
   Clause: "Late fees of $100 will be charged if rent is not received by 
           the 1st of the month."
   Issue: This late fee may be excessive. Many jurisdictions limit 
          late fees to 5-10% of monthly rent.
   Recommendation: Negotiate a more reasonable late fee structure...
```

### Rewrite Suggestions
```
Original Clause:
"Landlord may enter the premises at any time without notice."

Suggested Rewrite:
"Landlord may enter the premises after providing at least 24 hours 
written notice to tenant, except in cases of emergency (fire, flood, 
or immediate threat to property). Entry will be during reasonable 
hours (9 AM - 6 PM) unless otherwise agreed."

Negotiation Tips:
- Emphasize that reasonable notice protects both parties
- Cite state law requirements for notice
- Offer to be flexible for emergencies and scheduled repairs

Legal Basis:
Most states require 24-48 hours notice for non-emergency entry. 
Check your state's landlord-tenant laws for specific requirements.
```

## Features in Detail

### 1. Lease Summarization
- Extracts key terms (rent, deposit, duration, etc.)
- Summarizes tenant obligations
- Highlights important restrictions and policies
- Uses plain language for accessibility

### 2. Problematic Clause Detection
Identifies:
- Illegal or unenforceable terms
- Excessive fees or penalties
- Privacy violations
- Unfair maintenance obligations
- Predatory practices
- Vague or exploitable language

Severity levels:
- 🔴 **High**: Potentially illegal or severely unfair
- 🟡 **Medium**: Unfavorable but common; worth negotiating
- 🟢 **Low**: Minor issues or best practices

### 3. Rental Price Analysis
- Compares your rent to market rates
- Considers location, bedrooms, and property type
- Flags if rent is above/below market
- Suggests researching comparable listings

**Note**: For production use, integrate with real estate APIs like:
- Zillow API
- Rentometer API
- HUD Fair Market Rent data

### 4. Rewrite Suggestions
For problematic clauses, provides:
- Fair alternative wording
- Negotiation strategies
- Compromise options
- Legal justification

### 5. Tenant Rights Education
Covers:
- State-specific tenant protections
- Security deposit laws
- Repair and habitability standards
- Eviction protections
- Privacy rights
- Fair housing laws

## Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Web UI                │
│  (streamlit_lease_app.py)               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      LeaseAnalyzerAgent                  │
│  (lease_analyzer_app.py)                 │
│  - Orchestrates analysis workflow        │
│  - Manages conversation state            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         LeaseAnalyzer                    │
│  - PDF extraction (PyPDF)                │
│  - Claude API calls (LangChain)          │
│  - Analysis functions                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Claude Sonnet 4                  │
│  - Lease understanding                   │
│  - Legal reasoning                       │
│  - Tenant advocacy                       │
└──────────────────────────────────────────┘
```

## Customization

### Change AI Model

In `lease_analyzer_app.py`:
```python
self.llm = ChatAnthropic(
    api_key=api_key,
    model="claude-sonnet-4-20250514",  # Change model here
    temperature=0.2
)
```

### Adjust Analysis Depth

Modify prompts in `LeaseAnalyzer` class methods:
- `summarize_lease()` - Summary detail level
- `identify_problematic_clauses()` - Severity thresholds
- `get_tenant_rights_advice()` - Legal detail depth

### Add Custom Tools

Extend `LeaseAnalyzerAgent.tools`:
```python
Tool(
    name="CustomTool",
    func=self._custom_function,
    description="What this tool does"
)
```

## Limitations & Disclaimers

⚠️ **This is NOT legal advice.** This tool provides general information and suggestions based on AI analysis. It should not replace consultation with a qualified attorney.

**Known limitations:**
- Rental price estimates use AI knowledge, not real-time market data
- Legal advice is general and may not reflect recent law changes
- PDF extraction may miss scanned/image-based text
- Analysis quality depends on lease clarity and structure

**Always:**
- Consult a local attorney for specific legal issues
- Verify information with tenant rights organizations
- Check current state/local laws
- Get professional review before signing

## Production Enhancements

For production deployment, consider adding:

1. **Real-time rental price data**
   - Integrate Zillow, Rentometer, or similar APIs
   - Use HUD Fair Market Rent datasets

2. **Legal database integration**
   - Connect to state/local tenant law databases
   - Automate legal citation verification

3. **User accounts & history**
   - Save analyzed leases
   - Track negotiation outcomes
   - Share analysis with lawyers/advocates

4. **Multi-format support**
   - Word documents (.docx)
   - Scanned PDFs (OCR)
   - Images (OCR)

5. **Lawyer referral system**
   - Integrate with legal aid directories
   - Direct chat with tenant advocates

6. **Multilingual support**
   - Translate leases and analysis
   - Support non-English speakers

## Cost Estimates

Anthropic Claude API pricing (as of Feb 2025):
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

Typical lease analysis:
- Input: ~15,000 tokens (lease + prompts)
- Output: ~8,000 tokens (analysis)
- **Cost per lease: ~$0.15 - $0.25**

For high-volume use:
- Consider caching common prompts
- Batch process multiple leases
- Use Claude Haiku for less complex analysis

## Contributing

Contributions welcome! Areas for improvement:
- Additional analysis features
- Better PDF extraction
- Real-time data integrations
- UI/UX enhancements
- Test coverage
- Documentation

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review documentation
3. Contact the maintainer

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- UI with [Streamlit](https://streamlit.io/)

---

**Remember**: This tool empowers tenants with information, but always seek professional legal advice for important decisions.
