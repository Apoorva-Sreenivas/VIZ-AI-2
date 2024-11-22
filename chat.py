from llm_with_memory import llama3_mem
from fuzzywuzzy import fuzz
import pandas as pd 

def find_chart(user_prompt, df):
    # Prepare a string with column names and their data types
    column_info = ", ".join([f"{col} ({df[col].dtype})" for col in df.columns])
    
    addition_prompt = f"what chart from the following (bar, line, pie, scatter, histogram, box) are they asking for? " \
                      f"Give only one word answer in lowercase, the dataset exists. The columns in the dataset are: {column_info}"
    
    prompts = user_prompt + addition_prompt
    chart = llama3_mem(prompts)
    
    # Post-process the output to ensure it's a single word chart type
    return chart.strip().split()[0]  # Only return the first word

def find_columns(user_prompt, df, chart):
    # Prepare a string with column names and their data types
    column_info = ", ".join([f"{col} ({df[col].dtype})" for col in df.columns])

    # Adjust the prompt depending on the chart type
    if chart == "histogram" or chart == "box":
        addition_prompt = f"{column_info}. What are the numerical columns being referenced? " \
                          f"Give only the numerical column names from the given list separated by commas, nothing else."
    elif chart == "pie":
        addition_prompt = f"{column_info}. What are the one or two categorical columns being referenced? " \
                          f"Give only the categorical column names from the given list separated by commas, nothing else."
    else:  # for bar, line, scatter
        addition_prompt = f"{column_info}. What are the TWO columns being referenced? " \
                          f"Give only the relevant column names from the given list separated by commas, nothing else."
    
    prompts = user_prompt + addition_prompt
    cols = llama3_mem(prompts)
    
    # Split the columns based on commas and clean up the response
    cols = [col.strip() for col in cols.split(",")]

    return cols
