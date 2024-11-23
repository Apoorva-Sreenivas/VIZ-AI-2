import pandas as pd
import numpy as np

def clean_dataset(df):
    """
    Cleans the dataset by handling missing values.
    Dynamically processes all columns based on their data type.

    Parameters:
        df (pd.DataFrame): The input DataFrame to clean.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    # Replace placeholders ('NA', '-', None) with np.nan
    df = df.replace(['NA', '-', None], np.nan)
    
    # Find the total number of missing values
    total_missing = df.isnull().sum().sum()
    
    # Computing the percentage of missing values
    total_values = df.size
    percentage = total_missing / total_values
    
    if percentage <= 0.1:
        # Drop rows with missing values if less than 10% of values are missing
        df_cleaned = df.dropna()
    else:
        # Fill missing values dynamically based on column data types
        df_cleaned = df.copy()  # Create a copy to avoid modifying the original DataFrame
        for column in df.columns:
            if df[column].dtype == 'object':  # Categorical columns
                df_cleaned[column] = df[column].fillna(df[column].mode()[0])  # Fill with mode
            else:  # Numerical columns
                df_cleaned[column] = df[column].fillna(df[column].mean())  # Fill with mean
    
    return df_cleaned
