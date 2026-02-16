"""
Simple Example: Using the Lease Analyzer

This script demonstrates basic usage of the lease analyzer.
"""

import os
from dotenv import load_dotenv
from lease_analyzer_app import LeaseAnalyzer

# Load environment variables
load_dotenv()

def simple_example():
    """
    Simple example: Analyze individual components of a lease.
    """
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found")
        return
    
    # Initialize analyzer
    print("🤖 Initializing AI analyzer...")
    analyzer = LeaseAnalyzer(api_key)
    
    # Example: Analyze a sample lease clause
    sample_clause = """
    LATE FEES: If rent is not received by the 1st day of the month, 
    a late fee of $150 will be charged immediately. An additional $50 
    will be charged for each day rent remains unpaid.
    """
    
    print("\n" + "="*60)
    print("Example 1: Analyzing a Late Fee Clause")
    print("="*60)
    print(f"\nClause:\n{sample_clause}")
    
    # Create a minimal "lease" for analysis
    mini_lease = f"""
    RESIDENTIAL LEASE AGREEMENT
    
    Property: 123 Main Street, Apt 4B, San Francisco, CA 94102
    Monthly Rent: $2,500
    Security Deposit: $2,500
    Lease Term: 12 months starting January 1, 2025
    
    TERMS AND CONDITIONS:
    
    {sample_clause}
    
    LANDLORD ENTRY: Landlord reserves the right to enter the premises 
    at any time without notice for any reason.
    
    MAINTENANCE: Tenant is responsible for all repairs and maintenance, 
    including structural repairs, plumbing, electrical, and HVAC systems.
    """
    
    # Identify problems
    print("\n🔍 Analyzing for problems...")
    issues = analyzer.identify_problematic_clauses(mini_lease)
    
    print(f"\n✅ Found {len(issues)} potential issues:\n")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. [{issue['severity']} Severity]")
        print(f"   Clause: {issue['clause'][:100]}...")
        print(f"   Issue: {issue['issue']}")
        print(f"   Potentially Illegal: {issue['potentially_illegal']}")
        print(f"   Recommendation: {issue['recommendation']}")
        print()
    
    # Get rewrite suggestions
    print("="*60)
    print("Example 2: Getting Rewrite Suggestions")
    print("="*60)
    
    print("\n✏️ Generating rewrite suggestions...")
    rewrites = analyzer.suggest_lease_rewrites(issues, mini_lease)
    
    if rewrites:
        for i, rewrite in enumerate(rewrites, 1):
            print(f"\nRewrite Suggestion {i}:")
            print("-" * 60)
            print(f"Original: {rewrite['original_clause'][:150]}...")
            print(f"\n{rewrite['rewrite_suggestion']}")
            print()
    
    # Rental price context
    print("="*60)
    print("Example 3: Rental Price Analysis")
    print("="*60)
    
    print("\n💰 Analyzing rental prices for San Francisco...")
    price_analysis = analyzer.get_rental_price_context(
        city="San Francisco",
        state="California",
        zip_code="94102",
        bedrooms=1,
        current_rent=2500
    )
    
    print(f"\n{price_analysis}")
    
    # Tenant rights
    print("\n" + "="*60)
    print("Example 4: Tenant Rights Information")
    print("="*60)
    
    print("\n⚖️ Getting tenant rights info for California...")
    rights = analyzer.get_tenant_rights_advice(
        mini_lease,
        state="California",
        city="San Francisco"
    )
    
    print(f"\n{rights}")


def metadata_extraction_example():
    """
    Example: Extract metadata from a lease.
    """
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found")
        return
    
    analyzer = LeaseAnalyzer(api_key)
    
    sample_lease = """
    RESIDENTIAL LEASE AGREEMENT
    
    THIS LEASE AGREEMENT ("Lease") is made on January 1, 2025, between:
    
    LANDLORD: Property Management Inc.
    123 Landlord Ave, San Francisco, CA 94101
    
    TENANT: Jane Doe
    
    PROPERTY: 456 Market Street, Unit 3C
             San Francisco, California 94102
    
    LEASE TERM: This lease begins on February 1, 2025 and ends on 
                January 31, 2026 (12 months).
    
    RENT: Tenant agrees to pay $3,200.00 per month, due on the 1st.
    
    SECURITY DEPOSIT: Tenant has paid $3,200.00 as a security deposit.
    
    PROPERTY DESCRIPTION: 2 bedroom, 1 bathroom apartment
    """
    
    print("\n" + "="*60)
    print("Extracting Lease Metadata")
    print("="*60)
    
    print("\n📋 Analyzing lease document...")
    metadata = analyzer.extract_lease_metadata(sample_lease)
    
    print("\n✅ Extracted Information:")
    print(f"   Address: {metadata.get('property_address')}")
    print(f"   City: {metadata.get('city')}, {metadata.get('state')} {metadata.get('zip_code')}")
    print(f"   Monthly Rent: ${metadata.get('monthly_rent')}")
    print(f"   Security Deposit: ${metadata.get('security_deposit')}")
    print(f"   Lease Start: {metadata.get('lease_start_date')}")
    print(f"   Lease End: {metadata.get('lease_end_date')}")
    print(f"   Landlord: {metadata.get('landlord_name')}")
    print(f"   Bedrooms: {metadata.get('number_of_bedrooms')}")
    print(f"   Bathrooms: {metadata.get('number_of_bathrooms')}")


if __name__ == "__main__":
    print("\n🏠 Tenant Lease Analyzer - Examples\n")
    
    # Run examples
    simple_example()
    
    print("\n" + "="*60 + "\n")
    
    metadata_extraction_example()
    
    print("\n" + "="*60)
    print("✅ Examples Complete!")
    print("="*60 + "\n")
    
    print("Next steps:")
    print("1. Try uploading your own lease PDF")
    print("2. Run: streamlit run streamlit_lease_app.py")
    print("3. Or: python lease_analyzer_app.py your_lease.pdf")
    print()
