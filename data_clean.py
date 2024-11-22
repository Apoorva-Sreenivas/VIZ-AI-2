import pandas as pd
import numpy as np
from llm_with_memory import llama3_mem

def clean_dataset(df):

    # Find the total number of missing values
    total_missing = df.isnull().sum().sum() + (df == 'NA').sum().sum() + (df == '_').sum().sum()
 

    # Computing the percentage of missing values
    total_values = df.size
    percentage = total_missing / total_values

    # Deciding whether to remove or fill the missing values
    if(percentage<=0.1):
    # Replace 'NA', '-', and None (null) with NaN, then drop rows with missing values
        df_cleaned = df.replace(['NA', '_', None], np.nan).dropna()

    else :
    # Handle missing values: Fill missing numerical values with mean and categorical values with mode
        df['Income'] = df['Income'].fillna(df['Income'].mean())
        df['Education'] = df['Education'].fillna(df['Education'].mode()[0])



    return df 
    
    