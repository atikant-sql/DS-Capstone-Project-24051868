import streamlit as st
import pandas as pd
import numpy as np
import hashlib

# Function to group ages
def group_ages(df, age_col):
    bins = [0, 18, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = ['<18', '18-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91+']
    df[age_col] = pd.cut(df[age_col], bins=bins, labels=labels, right=False)
    return df

# Function to randomly adjust ages
def random_adjust_age(df, age_col):
    np.random.seed(42)  # For reproducibility
    adjustment = np.random.randint(-5, 6, size=len(df))  # Randomly choose from -5 to +5
    df[age_col] = df[age_col] + adjustment
    return df

# Function to implement k-anonymity
def k_anonymity(df, k, columns):
    # Generalization for specified columns
    if 'Age Group' in columns:
        # Example of binning ages into groups
        df['Age Group'] = pd.cut(df['Age at Colln'], bins=[0, 18, 20, 30, 40, 50, 60, 70, 80, 90, 100], 
                                 labels=['<18', '18-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '90+'])
        columns.append('Age Group')
    
    # Grouping to ensure k-anonymity
    grouped_df = df.groupby(columns).size().reset_index(name='count')
    
    # Filter groups that meet the k-anonymity requirement
    valid_groups = grouped_df[grouped_df['count'] >= k]
    
    if valid_groups.empty:
        return pd.DataFrame()  # Return an empty DataFrame if no valid groups exist
    
    # Merge back to the original DataFrame to keep valid rows
    df = df.merge(valid_groups[columns], on=columns, how='inner')
    
    return df.drop(columns=['count'])  # Drop the count column before returning

# Function to hash sensitive data
def hash_data(df, columns):
    for col in columns:
        df[col] = df[col].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest())
    return df

# Function to de-identify geographic data
def deidentify_geo_data(df, geo_columns):
    for col in geo_columns:
        df[col] = df[col].apply(lambda x: "De-identified " + x.split(",")[0])  # Example masking
    return df

# Streamlit UI
st.title("Healthcare Data De-identification")

# File uploader
uploaded_file = st.file_uploader("Upload a CSV file with healthcare data", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded Data:")
    st.dataframe(df)

    # Select age column and adjustment method
    age_column = st.selectbox("Select the Age Column", df.columns.tolist())
    adjustment_method = st.selectbox("Select Age Adjustment Method", ["Age Group", "Randomly Adjust Age"])
    
    # Apply age adjustment based on selected method
    if adjustment_method == "Age Group":
        df = group_ages(df, age_column)
        st.write("Data after Age Grouping:")
    elif adjustment_method == "Randomly Adjust Age":
        df = random_adjust_age(df, age_column)
        st.write("Data after Random Age Adjustment:")
    
    st.dataframe(df)

    # Select columns for k-anonymity
    k = st.number_input("Enter value of k for k-anonymity", min_value=1, value=5)
    k_columns = st.multiselect("Select columns for k-anonymity", df.columns.tolist())
    
    if st.button("Apply k-anonymity"):
        df = k_anonymity(df, k, k_columns)
        st.write("Data after k-anonymity:")
        st.dataframe(df)

    # Select columns for geographic data de-identification
    geo_columns = st.multiselect("Select Geo Columns for De-identification", 
                                  ["Performing Lab", "Clinic Location", "Region", "Clinic Name"])
    
    if st.button("Apply Geographic De-identification"):
        df = deidentify_geo_data(df, geo_columns)
        st.write("Data after Geographic De-identification:")
        st.dataframe(df)

    # Allow the user to choose columns to delete
    columns_to_delete = st.multiselect("Choose columns to delete from the output", df.columns.tolist())
    if columns_to_delete:
        df.drop(columns=columns_to_delete, inplace=True)

    # Download button for the updated data
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Updated Data",
        data=csv,
        file_name="deidentified_data.csv",
        mime="text/csv"
    )
else:
    st.info("Please upload a CSV file to proceed.")
