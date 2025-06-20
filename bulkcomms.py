import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.title("XML Field Extractor from CSV")

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of uploaded data", df.head())

    # Try to auto-detect column with XML content
    xml_column_guess = None
    for col in df.columns:
        if df[col].astype(str).str.startswith("<").sum() > 0:
            xml_column_guess = col
            break

    column_name = st.selectbox("Select the column with XML content", df.columns, index=df.columns.get_loc(xml_column_guess) if xml_column_guess else 0)

    # Try to auto-detect XML tags from first non-empty row
    detected_tags = set()
    try:
        first_xml = str(df[column_name].dropna().iloc[0])
        root = ET.fromstring(first_xml)
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            detected_tags.add(tag)
    except Exception as e:
        st.warning(f"Failed to auto-detect tags from sample row. Error: {e}")

    # User selects which XML fields to extract
    selected_tags = st.multiselect("Select XML fields to extract", sorted(detected_tags), default=[])

    # User selects final CSV fields (optional)
    final_csv_fields = st.multiselect("Select columns to include in final CSV", df.columns.tolist() + list(detected_tags), default=[])

    # XML extraction logic
    def extract_selected_tags(xml_str, selected_tags):
        result = {}
        try:
            root = ET.fromstring(xml_str)
            ns = {}
            if root.tag.startswith('{'):
                uri = root.tag.split('}')[0].strip('{')
                ns = {'ns': uri}
            for tag in selected_tags:
                el = root.find(f'.//ns:{tag}', ns) if ns else root.find(f'.//{tag}')
                result[tag] = el.text if el is not None else ''
        except Exception:
            for tag in selected_tags:
                result[tag] = ''
        return result

    if st.button("Extract Selected Fields"):
        df[column_name] = df[column_name].astype(str)
        extracted_df = df[column_name].apply(lambda x: extract_selected_tags(x, selected_tags)).apply(pd.Series)

        # Merge extracted data
        df = pd.concat([df, extracted_df], axis=1)

        # Determine which columns to show and export
        output_columns = final_csv_fields if final_csv_fields else df.columns
        st.write("### Extracted Data", df[output_columns].head())

        # Download button
        csv = df[output_columns].to_csv(index=False).encode("utf-8")
        st.download_button("Download Full Result CSV", data=csv, file_name="xml_extraction_output.csv", mime="text/csv")

