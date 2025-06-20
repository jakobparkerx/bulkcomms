import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.title("Bulk XML Scrubber")

# Function to detect possible XML tags in the first few rows
def detect_xml_tags(xml_series, sample_size=10):
    tags = set()
    ns = {'ns': 'http://www.smartaccess.co.uk/SmartAccess'}

    for xml_str in xml_series.dropna().astype(str).head(sample_size):
        try:
            root = ET.fromstring(xml_str)
            for elem in root.iter():
                tag = elem.tag
                if '}' in tag:
                    tag = tag.split('}', 1)[1]  # remove namespace
                tags.add(tag)
        except Exception:
            continue
    return sorted(tags)

# Function to extract selected XML tags from a single XML string
def extract_selected_tags(xml_str, selected_tags):
    result = {}
    try:
        root = ET.fromstring(xml_str)
        ns = {'ns': 'http://www.smartaccess.co.uk/SmartAccess'}
        for tag in selected_tags:
            el = root.find(f'.//ns:{tag}', ns)
            result[tag] = el.text if el is not None else ''
    except Exception:
        for tag in selected_tags:
            result[tag] = ''
    return result

# File uploader
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of uploaded data", df.head())

    # Automatically detect the XML column
    xml_column = None
    for col in df.columns:
        sample = df[col].dropna().astype(str).head(5).tolist()
        if all(s.strip().startswith("<?xml") or "<ClientResponse" in s for s in sample):
            xml_column = col
            break

    if not xml_column:
        xml_column = st.selectbox("Could not auto-detect. Select XML column manually", df.columns)

    st.write(f"Using column: `{xml_column}` for XML extraction")

    # Detect tags from sample XML
    detected_tags = detect_xml_tags(df[xml_column])

    # Combined dropdown to select both extracted XML fields and final CSV columns
    all_possible_fields = df.columns.tolist() + detected_tags
    selected_fields = st.multiselect(
        "Select fields to extract from XML and include in final CSV",
        options=all_possible_fields,
        default=[],
    )

    if st.button("Extract Selected Fields"):
        # Separate tags from static dataframe columns
        selected_tags = [field for field in selected_fields if field in detected_tags]
        final_csv_fields = selected_fields

        # Extract selected XML tags
        if selected_tags:
            df[xml_column] = df[xml_column].astype(str)
            extracted_df = df[xml_column].apply(lambda x: extract_selected_tags(x, selected_tags)).apply(pd.Series)
            df = pd.concat([df, extracted_df], axis=1)

        # Display and download
        if final_csv_fields:
            st.write("### Final Extracted Data", df[final_csv_fields].head())
            csv = df[final_csv_fields].to_csv(index=False).encode("utf-8")
            st.download_button("Download Full Result CSV", data=csv, file_name="xml_extraction_output.csv", mime="text/csv")
