import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.title("XML Extractor from CSV")

# --- XML detection utilities ---
def detect_xml_column(df):
    for col in df.columns:
        sample_values = df[col].dropna().astype(str).head(10)
        if sample_values.str.contains(r"<[^>]+>").any():
            return col
    return None

def extract_all_tags(xml_strs):
    tags = set()
    def recurse_tags(elem):
        for child in elem:
            tag = child.tag.split("}")[-1]  # Strip namespace
            tags.add(tag)
            recurse_tags(child)

    for xml in xml_strs:
        try:
            root = ET.fromstring(xml)
            recurse_tags(root)
        except:
            continue
    return sorted(tags)

# --- Tag extraction from XML ---
def extract_selected_tags(xml_str, selected_tags):
    result = {}
    try:
        root = ET.fromstring(xml_str)
        for tag in selected_tags:
            # Try finding all matches with the tag, ignoring namespaces
            match = root.findall(f".//{{*}}{tag}")
            result[tag] = match[0].text if match else ''
    except:
        for tag in selected_tags:
            result[tag] = ''
    return result

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of uploaded data", df.head())

    # --- Auto-detect XML column ---
    default_xml_column = detect_xml_column(df)
    column_name = st.selectbox("Select the column with XML content", df.columns, index=df.columns.get_loc(default_xml_column) if default_xml_column else 0)

    # --- Auto-detect available tags ---
    sample_xmls = df[column_name].dropna().astype(str).head(10)
    available_tags = extract_all_tags(sample_xmls)

    if not available_tags:
        st.warning("No XML tags found. Check if the selected column contains valid XML.")
    else:
        # --- Select tags to extract ---
        selected_tags = st.multiselect("Select XML fields to extract", available_tags, default=["StatusSMI"] if "StatusSMI" in available_tags else [])

        # --- Select output columns ---
        all_columns = list(df.columns) + selected_tags
        output_columns = st.multiselect("Select columns to include in final CSV", all_columns, default=list(df.columns) + selected_tags)

        # --- Run extraction ---
        if st.button("Extract Selected Fields"):
            df[column_name] = df[column_name].astype(str)
            extracted_df = df[column_name].apply(lambda x: extract_selected_tags(x, selected_tags)).apply(pd.Series)

            df = pd.concat([df, extracted_df], axis=1)

            st.write("### Extracted Data", df[output_columns].head())

            csv = df[output_columns].to_csv(index=False).encode("utf-8")
            st.download_button("Download Full Result CSV", data=csv, file_name="xml_extraction_output.csv", mime="text/csv")


