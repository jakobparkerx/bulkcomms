import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.title("XML Extractor from CSV")

# Define available XML tags to extract
AVAILABLE_TAGS = ["StatusSMI", "OverallStatus", "Warnings", "DaysSinceLastComms"]

# Function to extract selected tags from a single XML string
def extract_selected_tags(xml_str, selected_tags):
    result = {}
    try:
        root = ET.fromstring(xml_str)
        ns = {'ns': 'http://www.smartaccess.co.uk/SmartAccess'}
        for tag in selected_tags:
            el = root.find(f'.//ns:{tag}', ns)  # ✅ Deep search to handle nesting
            result[tag] = el.text if el is not None else ''
    except Exception as e:
        for tag in selected_tags:
            result[tag] = ''
    return result

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of uploaded data", df.head())

    # Let user pick the column that contains XML
    column_name = st.selectbox("Select the column with XML content", df.columns)

    # Let user pick which tags to extract
    selected_tags = st.multiselect("Select XML fields to extract", AVAILABLE_TAGS, default=["StatusSMI"])

    if st.button("Extract Selected Fields"):
        # Apply XML extraction
        df[column_name] = df[column_name].astype(str)
        extracted_df = df[column_name].apply(lambda x: extract_selected_tags(x, selected_tags)).apply(pd.Series)

        # Merge extracted columns back into original df
        df = pd.concat([df, extracted_df], axis=1)

        st.write("### Extracted Data", df[[column_name] + selected_tags].head())

        # Allow CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Full Result CSV", data=csv, file_name="xml_extraction_output.csv", mime="text/csv")
