import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.title("XML Extractor from CSV")

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of uploaded data", df.head())

    # Auto-detect XML column
    xml_column = None
    for col in df.columns:
        sample = str(df[col].dropna().astype(str).iloc[0]) if not df[col].dropna().empty else ""
        if sample.startswith("<?xml") or "<ClientResponse" in sample:
            xml_column = col
            break

    column_name = st.selectbox("Select the column with XML content", df.columns, index=df.columns.get_loc(xml_column) if xml_column else 0)

    # Auto-detect all tags in first XML
    detected_tags = set()
    try:
        root = ET.fromstring(str(df[column_name].dropna().iloc[0]))
        for elem in root.iter():
            if elem.tag.startswith("{"):
                tag_name = elem.tag.split("}", 1)[1]
            else:
                tag_name = elem.tag
            detected_tags.add(tag_name)
    except Exception:
        pass

    detected_tags = sorted(detected_tags)

    # Let user pick which tags to extract
    selected_tags = st.multiselect("Select XML fields to extract", detected_tags, default=[])

    # Select output columns
    all_columns = list(df.columns) + selected_tags
    st.caption("Tip: You might want to include identifiers like MPxN or commission_start along with your extracted tags.")
    output_columns = st.multiselect("Select columns to include in final CSV", all_columns, default=[])

    # XML extraction logic
    def extract_selected_tags(xml_str, selected_tags):
        result = {}
        try:
            root = ET.fromstring(xml_str)
            ns = {'ns': 'http://www.smartaccess.co.uk/SmartAccess'}
            for tag in selected_tags:
                el = root.find(f'.//ns:{tag}', ns) or root.find(f'.//{tag}')
                result[tag] = el.text if el is not None else ''
        except Exception:
            for tag in selected_tags:
                result[tag] = ''
        return result

    if st.button("Extract Selected Fields"):
        df[column_name] = df[column_name].astype(str)
        extracted_df = df[column_name].apply(lambda x: extract_selected_tags(x, selected_tags)).apply(pd.Series)

        df = pd.concat([df, extracted_df], axis=1)

        if output_columns:
            output_df = df[output_columns]
        else:
            output_df = df

        st.write("### Extracted Data", output_df.head())

        csv = output_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Full Result CSV", data=csv, file_name="xml_extraction_output.csv", mime="text/csv")
