"""
Tenant Lease Analyzer - AI-Powered Lease Review Application

This app helps tenants:
- Upload and analyze lease documents
- Identify predatory or unusual clauses
- Compare rental prices
- Get rewrite suggestions for negotiable terms
- Understand their legal rights

Requirements:
pip install langchain langchain-anthropic langchain-community pypdf python-dotenv streamlit pandas
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

#from langchain_classic.chains import LLMChain
#from langchain_classic.agents import AgentExecutor, create_react_agent, Tool
from langchain_classic.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, create_react_agent, Tool



# Standard library imports
import json
from datetime import datetime


class LeaseAnalyzer:
    """Main class for analyzing lease documents."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the lease analyzer.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.llm = ChatAnthropic(
            api_key=api_key,
            model=model,
            temperature=0.2,  # Lower for more factual analysis
            max_tokens=4096
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def extract_lease_text(self, file_path: str) -> str:
        """
        Extract text from PDF lease document.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text from the lease
        """
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # Combine all pages
        full_text = "\n\n".join([page.page_content for page in pages])
        return full_text
    
    def extract_lease_metadata(self, lease_text: str) -> Dict[str, Any]:
        """
        Extract key metadata from the lease (address, rent amount, dates, etc.).
        
        Args:
            lease_text: Full text of the lease
            
        Returns:
            Dictionary with extracted metadata
        """
        prompt = PromptTemplate(
            input_variables=["lease_text"],
            template="""
You are a lease analysis expert. Extract the following information from this lease document.
Return ONLY valid JSON with no additional text.

Required fields (use null if not found):
- property_address: Full address
- city: City name
- state: State
- zip_code: ZIP code
- monthly_rent: Monthly rent amount (number only)
- security_deposit: Security deposit amount (number only)
- lease_start_date: Start date (YYYY-MM-DD format)
- lease_end_date: End date (YYYY-MM-DD format)
- landlord_name: Landlord or property management company name
- number_of_bedrooms: Number of bedrooms (number only)
- number_of_bathrooms: Number of bathrooms (number only)

Lease text:
{lease_text}

Return JSON only:
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(lease_text=lease_text[:8000])  # Limit to avoid token limits
        
        try:
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                metadata = json.loads(json_match.group())
            else:
                metadata = json.loads(result)
        except json.JSONDecodeError:
            metadata = {
                "error": "Could not parse lease metadata",
                "raw_response": result
            }
        
        return metadata
    
    def summarize_lease(self, lease_text: str) -> str:
        """
        Generate a comprehensive summary of the lease.
        
        Args:
            lease_text: Full text of the lease
            
        Returns:
            Lease summary
        """
        prompt = PromptTemplate(
            input_variables=["lease_text"],
            template="""
You are a tenant rights advocate helping renters understand their leases.

Provide a clear, comprehensive summary of this lease in plain English. Include:

1. **Basic Terms**: Rent amount, security deposit, lease duration, property address
2. **Key Obligations**: What the tenant must do (pay rent, maintain property, etc.)
3. **Key Rights**: What the tenant is entitled to (repairs, privacy, quiet enjoyment, etc.)
4. **Important Restrictions**: Pet policies, subletting rules, guest policies, noise restrictions
5. **Financial Terms**: Late fees, utilities included/excluded, renewal terms
6. **Maintenance & Repairs**: Who is responsible for what
7. **Termination Terms**: Notice requirements, early termination clauses, penalties

Keep your summary under 500 words and use clear, accessible language.

Lease text:
{lease_text}

Summary:
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        summary = chain.run(lease_text=lease_text)
        
        return summary
    
    def identify_problematic_clauses(self, lease_text: str) -> List[Dict[str, str]]:
        """
        Identify unusual, unfair, or potentially predatory clauses.
        
        Args:
            lease_text: Full text of the lease
            
        Returns:
            List of problematic clauses with analysis
        """
        prompt = PromptTemplate(
            input_variables=["lease_text"],
            template="""
You are a tenant rights attorney reviewing a lease for potential problems.

Analyze this lease and identify any clauses that are:
1. Unusually restrictive or punitive
2. Potentially illegal or unenforceable
3. Heavily favor the landlord over the tenant
4. Common predatory practices (excessive fees, unfair penalties, etc.)
5. Vague or ambiguous terms that could be exploited

For each problematic clause, provide:
- The exact clause or provision (quote it)
- Why it's problematic
- The severity level (Low/Medium/High concern)
- Whether it might be illegal or unenforceable

Return your analysis as a JSON array with objects containing:
- "clause": the actual text from the lease
- "issue": description of the problem
- "severity": "Low", "Medium", or "High"
- "potentially_illegal": true/false
- "recommendation": what the tenant should do

Lease text:
{lease_text}

Return ONLY valid JSON array:
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(lease_text=lease_text)
        
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                clauses = json.loads(json_match.group())
            else:
                clauses = json.loads(result)
        except json.JSONDecodeError:
            clauses = [{
                "clause": "Error parsing response",
                "issue": "Could not analyze lease",
                "severity": "Unknown",
                "potentially_illegal": False,
                "recommendation": "Manual review required"
            }]
        
        return clauses
    
    def get_rental_price_context(self, city: str, state: str, zip_code: str, 
                                 bedrooms: int, monthly_rent: float) -> str:
        """
        Analyze whether the rental price is fair for the market.
        
        Args:
            city: City name
            state: State
            zip_code: ZIP code
            bedrooms: Number of bedrooms
            monthly_rent: Monthly rent amount
            
        Returns:
            Price analysis with market context
        """
        prompt = PromptTemplate(
            input_variables=["city", "state", "zip_code", "bedrooms", "monthly_rent"],
            template="""
You are a real estate market analyst. Provide context on whether this rental price is reasonable.

Location: {city}, {state} {zip_code}
Bedrooms: {bedrooms}
Monthly Rent: ${monthly_rent}

Provide:
1. General market trends for this area (if you have knowledge)
2. Typical rent ranges for {bedrooms}-bedroom units in this area
3. Assessment of whether this price seems fair, high, or low
4. Suggestions for resources to verify current market rates (Zillow, Apartments.com, etc.)
5. Factors that could justify higher or lower rent

Note: Your knowledge may be outdated. Always recommend checking current listings.

Analysis:
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        analysis = chain.run(
            city=city,
            state=state,
            zip_code=zip_code,
            bedrooms=bedrooms,
            monthly_rent=monthly_rent
        )
        
        return analysis
    
    def suggest_lease_rewrites(self, problematic_clauses: List[Dict[str, str]], 
                              lease_text: str) -> List[Dict[str, str]]:
        """
        Suggest rewritten versions of problematic clauses.
        
        Args:
            problematic_clauses: List of identified problematic clauses
            lease_text: Full lease text for context
            
        Returns:
            List of rewrite suggestions
        """
        if not problematic_clauses:
            return []
        
        # Focus on high and medium severity issues
        high_priority = [c for c in problematic_clauses 
                        if c.get('severity') in ['High', 'Medium']]
        
        if not high_priority:
            return []
        
        rewrites = []
        
        for clause_info in high_priority[:5]:  # Limit to top 5 issues
            prompt = PromptTemplate(
                input_variables=["clause", "issue"],
                template="""
You are a tenant rights attorney helping to negotiate fair lease terms.

Original problematic clause:
{clause}

Issue identified:
{issue}

Provide:
1. A rewritten version of this clause that is fair to both parties
2. Key changes you made and why
3. Talking points the tenant can use when negotiating

Keep suggestions practical and reasonable.

Response:
"""
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            suggestion = chain.run(
                clause=clause_info.get('clause', ''),
                issue=clause_info.get('issue', '')
            )
            
            rewrites.append({
                "original_clause": clause_info.get('clause', ''),
                "severity": clause_info.get('severity', ''),
                "rewrite_suggestion": suggestion
            })
        
        return rewrites
    
    def get_tenant_rights_advice(self, lease_text: str, state: str, 
                                city: Optional[str] = None) -> str:
        """
        Provide tenant rights information relevant to the lease and location.
        
        Args:
            lease_text: Full lease text
            state: State where property is located
            city: Optional city for more specific information
            
        Returns:
            Tenant rights information
        """
        location = f"{city}, {state}" if city else state
        
        prompt = PromptTemplate(
            input_variables=["location", "lease_text"],
            template="""
You are a tenant rights expert. Provide important tenant rights information for this location.

Location: {location}

Based on this lease and general tenant rights in this location, explain:
1. Key tenant rights (habitability, privacy, repairs, etc.)
2. Landlord obligations
3. Security deposit rules
4. Notice requirements for entry and termination
5. Protections against unfair practices
6. Where to get help (legal aid, tenant unions, etc.)

Note: Recommend checking current local laws as they may have changed.

Lease excerpt (for context):
{lease_text}

Tenant rights information:
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        rights_info = chain.run(
            location=location,
            lease_text=lease_text[:4000]  # Limit for context
        )
        
        return rights_info


class LeaseAnalyzerAgent:
    """Agent that uses LeaseAnalyzer with conversational memory."""
    
    def __init__(self, api_key: str):
        """Initialize the agent."""
        self.analyzer = LeaseAnalyzer(api_key)
        self.lease_text = None
        self.metadata = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def load_lease(self, file_path: str) -> Dict[str, Any]:
        """
        Load and process a lease PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Status and metadata
        """
        try:
            print(f"Loading lease from: {file_path}")
            self.lease_text = self.analyzer.extract_lease_text(file_path)
            print(f"Extracted {len(self.lease_text)} characters")
            
            print("Extracting metadata...")
            self.metadata = self.analyzer.extract_lease_metadata(self.lease_text)
            
            return {
                "status": "success",
                "message": "Lease loaded successfully",
                "metadata": self.metadata
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def load_lease_text(self, text: str, manual_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load lease directly from text instead of PDF.
        
        Args:
            text: The lease text
            manual_metadata: Optional dictionary with manually entered metadata
            
        Returns:
            Status dictionary
        """
        try:
            self.lease_text = text
            
            # If manual metadata provided, use it; otherwise try to extract
            if manual_metadata:
                self.metadata = manual_metadata
            else:
                print("Extracting metadata from text...")
                self.metadata = self.analyzer.extract_lease_metadata(text)
            
            return {
                "status": "success",
                "message": "Lease text loaded successfully",
                "metadata": self.metadata
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _get_summary_wrapper(self, input: str) -> str:
        """Wrapper for lease summary."""
        if not self.lease_text:
            return "Error: No lease loaded. Please load a lease first."
        
        return self.analyzer.summarize_lease(self.lease_text)
    
    def _get_issues_wrapper(self, input: str) -> str:
        """Wrapper for identifying problematic clauses."""
        if not self.lease_text:
            return "Error: No lease loaded. Please load a lease first."
        
        clauses = self.analyzer.identify_problematic_clauses(self.lease_text)
        
        if not clauses:
            return "No problematic clauses identified."
        
        result = f"Found {len(clauses)} potential issues:\n\n"
        for i, clause in enumerate(clauses, 1):
            result += f"{i}. [{clause.get('severity', 'Unknown')}] "
            if clause.get('potentially_illegal'):
                result += "⚠️ POTENTIALLY ILLEGAL\n"
            else:
                result += "\n"
            result += f"   Clause: {clause.get('clause', '')[:150]}...\n"
            result += f"   Issue: {clause.get('issue', '')}\n"
            result += f"   Recommendation: {clause.get('recommendation', '')}\n\n"
        
        return result
    
    def _get_price_analysis_wrapper(self, input: str) -> str:
        """Wrapper for rental price analysis."""
        if not self.metadata:
            return "Error: No lease loaded or metadata unavailable."
        
        city = self.metadata.get('city')
        state = self.metadata.get('state')
        zip_code = self.metadata.get('zip_code')
        bedrooms = self.metadata.get('number_of_bedrooms', 1)
        rent = self.metadata.get('monthly_rent')
        
        if not all([city, state, rent]):
            return "Error: Missing required information (city, state, or rent amount)"
        
        return self.analyzer.get_rental_price_context(city, state, zip_code, bedrooms, rent)
    
    def _get_rewrites_wrapper(self, input: str) -> str:
        """Wrapper for rewrite suggestions."""
        if not self.lease_text:
            return "Error: No lease loaded. Please load a lease first."
        
        # First identify issues
        clauses = self.analyzer.identify_problematic_clauses(self.lease_text)
        
        if not clauses:
            return "No problematic clauses identified."
        
        # Get rewrites
        rewrites = self.analyzer.suggest_lease_rewrites(clauses, self.lease_text)
        
        if not rewrites:
            return "No significant issues found that require rewriting."
        
        # Format results
        result = f"Suggested rewrites for {len(rewrites)} clauses:\n\n"
        for i, rewrite in enumerate(rewrites, 1):
            result += f"{i}. {rewrite.get('severity', '')} Severity Issue\n"
            result += f"   Original: {rewrite.get('original_clause', '')[:150]}...\n"
            result += f"   {rewrite.get('rewrite_suggestion', '')}\n\n"
        
        return result
    
    def _get_rights_wrapper(self, input: str) -> str:
        """Wrapper for tenant rights information."""
        if not self.lease_text or not self.metadata:
            return "Error: No lease loaded. Please load a lease first."
        
        state = self.metadata.get('state', 'Unknown')
        city = self.metadata.get('city')
        
        return self.analyzer.get_tenant_rights_advice(self.lease_text, state, city)
    
    def analyze_full_lease(self) -> Dict[str, Any]:
        """
        Run complete analysis on the currently loaded lease.
        
        Returns:
            Complete analysis results
        """
        if not self.lease_text:
            return {
                "status": "error",
                "message": "No lease loaded. Please load a lease first."
            }
        
        print("🏠 Starting comprehensive lease analysis...\n")
        
        results = {
            "metadata": self.metadata,
            "summary": None,
            "problematic_clauses": None,
            "rental_price_analysis": None,
            "rewrite_suggestions": None,
            "tenant_rights": None
        }
        
        # 1. Summarize
        print("📋 Summarizing lease...")
        results['summary'] = self.analyzer.summarize_lease(self.lease_text)
        print("✅ Summary complete\n")
        
        # 2. Identify problems
        print("🔍 Identifying problematic clauses...")
        results['problematic_clauses'] = self.analyzer.identify_problematic_clauses(self.lease_text)
        print(f"✅ Found {len(results['problematic_clauses'])} potential issues\n")
        
        # 3. Check rental prices
        if self.metadata.get('monthly_rent') and self.metadata.get('city'):
            print("💰 Analyzing rental prices...")
            results['rental_price_analysis'] = self.analyzer.get_rental_price_context(
                self.metadata.get('city', ''),
                self.metadata.get('state', ''),
                self.metadata.get('zip_code', ''),
                self.metadata.get('number_of_bedrooms', 1),
                self.metadata.get('monthly_rent', 0)
            )
            print("✅ Price analysis complete\n")
        
        # 4. Suggest rewrites
        print("✏️ Generating rewrite suggestions...")
        results['rewrite_suggestions'] = self.analyzer.suggest_lease_rewrites(
            results['problematic_clauses'],
            self.lease_text
        )
        print(f"✅ Generated {len(results['rewrite_suggestions'])} suggestions\n")
        
        # 5. Get tenant rights
        print("⚖️ Researching tenant rights...")
        results['tenant_rights'] = self.analyzer.get_tenant_rights_advice(
            self.lease_text,
            self.metadata.get('state', ''),
            self.metadata.get('city')
        )
        print("✅ Rights analysis complete\n")
        
        print("🎉 Full analysis complete!")
        
        return results


def format_analysis_report(results: Dict[str, Any]) -> str:
    """Format analysis results into a readable report."""
    
    report = "=" * 80 + "\n"
    report += "LEASE ANALYSIS REPORT\n"
    report += "=" * 80 + "\n\n"
    
    # Metadata
    report += "📍 PROPERTY INFORMATION\n"
    report += "-" * 80 + "\n"
    metadata = results.get('metadata', {})
    report += f"Address: {metadata.get('property_address', 'N/A')}\n"
    report += f"City: {metadata.get('city', 'N/A')}, {metadata.get('state', 'N/A')} {metadata.get('zip_code', 'N/A')}\n"
    report += f"Monthly Rent: ${metadata.get('monthly_rent', 'N/A')}\n"
    report += f"Security Deposit: ${metadata.get('security_deposit', 'N/A')}\n"
    report += f"Lease Term: {metadata.get('lease_start_date', 'N/A')} to {metadata.get('lease_end_date', 'N/A')}\n"
    report += f"Bedrooms: {metadata.get('number_of_bedrooms', 'N/A')}, Bathrooms: {metadata.get('number_of_bathrooms', 'N/A')}\n"
    report += "\n"
    
    # Summary
    report += "📋 LEASE SUMMARY\n"
    report += "-" * 80 + "\n"
    report += results.get('summary', 'N/A') + "\n\n"
    
    # Problematic clauses
    report += "🚨 PROBLEMATIC CLAUSES IDENTIFIED\n"
    report += "-" * 80 + "\n"
    clauses = results.get('problematic_clauses', [])
    if clauses:
        for i, clause in enumerate(clauses, 1):
            report += f"\n{i}. [{clause.get('severity', 'Unknown').upper()}] "
            if clause.get('potentially_illegal'):
                report += "⚠️ POTENTIALLY ILLEGAL\n"
            else:
                report += "\n"
            report += f"   Clause: {clause.get('clause', 'N/A')}\n"
            report += f"   Issue: {clause.get('issue', 'N/A')}\n"
            report += f"   Recommendation: {clause.get('recommendation', 'N/A')}\n"
    else:
        report += "No significant issues identified.\n"
    report += "\n"
    
    # Rental price analysis
    if results.get('rental_price_analysis'):
        report += "💰 RENTAL PRICE ANALYSIS\n"
        report += "-" * 80 + "\n"
        report += results['rental_price_analysis'] + "\n\n"
    
    # Rewrite suggestions
    report += "✏️ SUGGESTED LEASE REWRITES\n"
    report += "-" * 80 + "\n"
    rewrites = results.get('rewrite_suggestions', [])
    if rewrites:
        for i, rewrite in enumerate(rewrites, 1):
            report += f"\n{i}. {rewrite.get('severity', '')} Severity Issue\n"
            report += f"   Original Clause: {rewrite.get('original_clause', 'N/A')}\n"
            report += f"   Suggested Changes:\n"
            report += f"   {rewrite.get('rewrite_suggestion', 'N/A')}\n"
    else:
        report += "No rewrites suggested.\n"
    report += "\n"
    
    # Tenant rights
    report += "⚖️ YOUR TENANT RIGHTS\n"
    report += "-" * 80 + "\n"
    report += results.get('tenant_rights', 'N/A') + "\n\n"
    
    report += "=" * 80 + "\n"
    report += "END OF REPORT\n"
    report += "=" * 80 + "\n"
    
    return report


# Example usage
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Check for lease file argument
    if len(sys.argv) < 2:
        print("Usage: python lease_analyzer_app.py <path_to_lease.pdf>")
        sys.exit(1)
    
    lease_file = sys.argv[1]
    
    if not os.path.exists(lease_file):
        print(f"Error: File not found: {lease_file}")
        sys.exit(1)
    
    # Run analysis
    agent = LeaseAnalyzerAgent(api_key)
    load_result = agent.load_lease(lease_file)
    
    if load_result['status'] == 'success':
        results = agent.analyze_full_lease()
        
        # Generate and display report
        report = format_analysis_report(results)
        print("\n" + report)
        
        # Optionally save to file
        output_file = f"lease_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {output_file}")
    else:
        print(f"Error loading lease: {load_result['message']}")
