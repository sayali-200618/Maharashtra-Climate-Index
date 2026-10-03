import streamlit as st
import pandas as pd

st.title("Maharashtra Climate Change Index")

file = "Maharashtra_36_Districts_PCA_CCI_Final_Ranking.xlsx"

excel_file = pd.ExcelFile(file)

st.write("Sheets available in Excel:")
st.write(excel_file.sheet_names)
