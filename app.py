import streamlit as st
import pandas as pd
import io
from collections import defaultdict

# KW Command Template Headers (Exact output needed)
KW_TEMPLATE_HEADERS = [
    "First Name", "Middle Name", "Last Name", "Prefix", "Suffix", "Full Legal Name",
    "About", "Birthday", "Home Anniversary",
    "Cell Phone", "Is Primary? (mark Y)",
    "Home Phone", "Is Primary? (mark Y)",
    "Work Phone", "Is Primary? (mark Y)",
    "Other Phone", "Is Primary? (mark Y)",
    "Personal Email", "Primary? (mark Y)",
    "Work Email", "Primary? (mark Y)",
    "Other Email", "Primary? (mark Y)",
    # Address Block 1
    "Address line one", "Address line two", "City", "State", "Zip code", "Country", "Label", "",
    # Address Block 2
    "Address line one", "Address line two", "City", "State", "Zip code", "Country", "Label", "",
    # Address Block 3
    "Address line one", "Address line two", "City", "State", "Zip code", "Country", "Label", "",
    "Tags", "Source", "Notes",
    "Facebook", "Twitter", "Linkedin", "Pinterest", "Instagram"
]

REQUIRED_COLUMNS = ["first_name", "last_name"]

def format_phone_number(phone_value):
    """Format 10-digit numbers as ###-###-####; otherwise return string as-is."""
    if pd.isna(phone_value):
        return ""
    s = str(phone_value).strip()
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return s if s else ""

def get_unique_headers(headers):
    """Make headers unique for Streamlit display (e.g., 'Address.1', 'Address.2')."""
    seen = defaultdict(int)
    unique = []
    for h in headers:
        if h in seen:
            # First occurrence gets name, subsequent get name.1, name.2, etc.
            # Actually, usually first is name, second is name.1
            count = seen[h]
            if count == 0:
                seen[h] += 1
                unique.append(h)
            else:
                seen[h] += 1
                unique.append(f"{h}.{count}")
        else:
            seen[h] += 1
            unique.append(h)
    return unique

# Generate unique headers for DataFrame display
# Note: Logic above creates Name, Name.1, Name.2 which matches Pandas behavior roughly
# But wait, seen[h] starts at 0? No, defaultdict(int) starts at 0.
# Iter 1: count=0. seen=1. append(h).
# Iter 2: count=1. seen=2. append(h.1).
# Iter 3: count=2. seen=3. append(h.2).
# Correct.
UNIQUE_HEADERS = get_unique_headers(KW_TEMPLATE_HEADERS)

def main():
    st.title("Real Intent to KW Command Converter")
    st.info("Upload a Real Intent CSV to convert it for KW Command import.")

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    col1, col2 = st.columns(2)
    with col1:
        custom_tags = st.text_input("Tags (optional)", placeholder="e.g. realintent, seller")
    with col2:
        source_val = st.text_input("Source", value="Real Intent")

    if uploaded_file is None:
        return

    df = pd.read_csv(uploaded_file)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"The uploaded file is missing required columns: {', '.join(missing)}.")
        return

    output_rows = []
    
    for _, row in df.iterrows():
        # Initialize row with empty strings
        row_data = [""] * len(KW_TEMPLATE_HEADERS)
        
        # Helper to safely get string value
        def get_val(col_name):
            val = row.get(col_name, "")
            return str(val).strip() if not pd.isna(val) else ""

        # 1. Names
        row_data[0] = get_val("first_name")  # First Name
        row_data[2] = get_val("last_name")   # Last Name
        
        # 2. Phones
        p1 = row.get("phone_1")
        if not pd.isna(p1):
            row_data[9] = format_phone_number(p1) # Cell Phone
            row_data[10] = "Y"                    # Is Primary?
            
        p2 = row.get("phone_2")
        if not pd.isna(p2):
            row_data[11] = format_phone_number(p2) # Home Phone
            
        # 3. Emails
        e1 = row.get("email_1")
        if not pd.isna(e1):
            row_data[17] = str(e1).strip()        # Personal Email
            row_data[18] = "Y"                    # Primary?
            
        e2 = row.get("email_2")
        if not pd.isna(e2):
            row_data[19] = str(e2).strip()        # Work Email
            
        # 4. Address (Block 1 - Indices 23-30)
        addr = get_val("address")
        if addr:
            row_data[23] = addr                   # Address line one
            row_data[25] = get_val("city")        # City
            row_data[26] = get_val("state")       # State
            row_data[27] = get_val("zip_code")    # Zip code
            row_data[28] = "USA"                  # Country
            row_data[29] = "Home"                 # Label

        # 5. Metadata
        tags_list = []
        if custom_tags:
            tags_list.append(custom_tags)
        
        # Auto-add "REAL INTENT.SELLERS" tag if Sellers column has "X"
        if "Sellers" in row.index:
            sellers_val = str(row.get("Sellers", "")).strip().upper()
            if sellers_val == "X":
                tags_list.append("REAL INTENT.SELLERS")
        
        row_data[47] = ", ".join(tags_list) if tags_list else ""  # Tags
        
        row_data[48] = source_val                 # Source
        row_data[49] = get_val("insight")         # Notes

        output_rows.append(row_data)

    # Create DataFrame with UNIQUE headers for display
    result = pd.DataFrame(output_rows, columns=UNIQUE_HEADERS)
    
    st.write("Converted data (preview):")
    st.dataframe(result)
    
    # Write to CSV buffer with ORIGINAL DUPLICATE headers
    csv_buffer = io.StringIO()
    # Pass the original headers to to_csv to write them as the first row
    # Note: to_csv(header=list) uses the list as aliases for the columns.
    # Since we have same number of columns, this maps unique->duplicate correctly.
    result.to_csv(csv_buffer, index=False, header=KW_TEMPLATE_HEADERS)
    
    st.download_button(
        label="Download converted CSV",
        data=csv_buffer.getvalue().encode('utf-8'),
        file_name="kw_command_import.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()
