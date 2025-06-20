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
            el = root.find(f".//ns:{tag}", ns)
            result[tag] = el.text if el is not None else ''
    except Exception:
        for tag in selected_tags:
            result[tag] = ''
    return result

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of uploaded data", df.head())

    # Let user pick the column with XML content
    column_name = st.selectbox("Select the column with XML content", df.columns)

    # Let user select XML tags to extract
    selected_tags = st.multiselect("Select XML fields to extract", AVAILABLE_TAGS, default=["StatusSMI"])

    # Preview output columns BEFORE clicking extract
    st.markdown("### Step 2: Choose columns to include in final output")
    default_output_columns = [column_name] + selected_tags
    all_possible_columns = df.columns.tolist() + selected_tags
    selected_output_columns = st.multiselect(
        "Select columns for output CSV",
        options=all_possible_columns,
        default=default_output_columns
    )

    # When user clicks the extract button
    if st.button("Extract Selected Fields"):
        # Make sure XML column is string
        df[column_name] = df[column_name].astype(str)

        # Extract selected XML fields into columns
        extracted_df = df[column_name].apply(lambda x: extract_selected_tags(x, selected_tags)).apply(pd.Series)

        # Add extracted fields to original DataFrame
        df = pd.concat([df, extracted_df], axis=1)

        # Filter based on selected output columns
        output_df = df[selected_output_columns]

        # Show results
        st.write("### Extracted & Filtered Data", output_df.head())

        # Download button
        csv = output_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Selected Columns as CSV",
            data=csv,
            file_name="xml_extraction_output.csv",
            mime="text/csv"
        )

