from flask import Flask, render_template, request, jsonify
import pandas as pd
import io
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from data_clean import clean_dataset
from chat import find_chart, find_columns

app = Flask(__name__)

# Global DataFrame to store the latest uploaded file
df = None


# Determine column types
def infer_column_types(df):
    column_types = {}
    for column in df.columns:
        sample_data = df[column].dropna().iloc[:5]  # Use a small sample for inference
        if pd.api.types.is_numeric_dtype(sample_data):
            column_types[column] = "Number"
        elif pd.api.types.is_datetime64_any_dtype(sample_data):
            column_types[column] = "Date"
        else:
            column_types[column] = "String"
    return column_types

def generate_bar_chart(df, cols):
    """Generate a bar chart from the specified DataFrame columns."""
    if len(cols) == 0:
        raise ValueError("The 'cols' array must contain at least one column name.")
    elif len(cols) > 2:
        raise ValueError("The 'cols' array must contain at most two column names.")
    
    x_column = cols[0]
    y_column = cols[1] if len(cols) == 2 else None

    if x_column not in df.columns:
        raise ValueError(f"Column '{x_column}' not found in DataFrame.")
    if y_column and y_column not in df.columns:
        raise ValueError(f"Column '{y_column}' not found in DataFrame.")

    plt.figure(figsize=(10, 6))
    
    if y_column is None:
        value_counts = df[x_column].value_counts()
        sns.barplot(x=value_counts.index, y=value_counts.values)
        plt.xlabel(x_column)
        plt.ylabel('Count')
        plt.title(f'Bar chart of value counts in {x_column}')
    else:
        x_is_numeric = pd.api.types.is_numeric_dtype(df[x_column])
        y_is_numeric = pd.api.types.is_numeric_dtype(df[y_column])
        
        if x_is_numeric and y_is_numeric:
            sns.barplot(x=x_column, y=y_column, data=df)
            plt.title(f'Bar chart of {y_column} vs {x_column}')
        elif x_is_numeric and not y_is_numeric:
            sns.barplot(x=x_column, y=y_column, data=df, estimator=lambda x: len(x))
            plt.title(f'Bar chart of count of {y_column} vs {x_column}')
        elif not x_is_numeric and y_is_numeric:
            sns.barplot(x=x_column, y=y_column, data=df)
            plt.title(f'Bar chart of {y_column} vs {x_column}')
        else:
            sns.countplot(x=x_column, hue=y_column, data=df)
            plt.title(f'Count plot of {y_column} vs {x_column}')
    
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

def generate_line_chart(df, col1, col2):
    # Check if the specified columns exist in the DataFrame
    if col1 not in df.columns or col2 not in df.columns:
        raise ValueError(f"Columns '{col1}' or '{col2}' not found in DataFrame.")
    
    # Check data types for both columns
    col1_is_numeric = pd.api.types.is_numeric_dtype(df[col1])
    col2_is_numeric = pd.api.types.is_numeric_dtype(df[col2])
    
    col1_is_datetime = pd.api.types.is_datetime64_any_dtype(df[col1])
    col2_is_datetime = pd.api.types.is_datetime64_any_dtype(df[col2])
    
    # Attempt to convert to datetime if either column is a string
    if pd.api.types.is_string_dtype(df[col1]):
        df[col1] = pd.to_datetime(df[col1], errors='coerce')
        col1_is_datetime = pd.api.types.is_datetime64_any_dtype(df[col1])
    if pd.api.types.is_string_dtype(df[col2]):
        df[col2] = pd.to_datetime(df[col2], errors='coerce')
        col2_is_datetime = pd.api.types.is_datetime64_any_dtype(df[col2])
    
    # Determine roles for x and y axis
    if col1_is_datetime:
        x_column, y_column = col1, col2
    elif col2_is_datetime:
        x_column, y_column = col2, col1
    elif col1_is_numeric:
        x_column, y_column = col1, col2
    elif col2_is_numeric:
        x_column, y_column = col2, col1
    else:
        raise ValueError("At least one column must be datetime or numeric for a line chart.")
    
    # Check if y_column is numeric
    y_is_numeric = pd.api.types.is_numeric_dtype(df[y_column])

    if not y_is_numeric:
        raise ValueError(f"Y-axis column '{y_column}' must be numeric for a valid line chart.")
    
    # Handle datetime x_column: group by date and aggregate y_column
    if pd.api.types.is_datetime64_any_dtype(df[x_column]):
        df_grouped = df.groupby(x_column)[y_column].sum().reset_index()
    else:
        # For numeric x_column, no need to group; directly plot the values
        df_grouped = df
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(df_grouped[x_column], df_grouped[y_column], marker='o', label=f'{y_column} Trend')
    
    # Customize plot
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(f'Trend of {y_column} over {x_column}')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

def generate_single_pie_chart(df, category_column, value_column):
    # Check if the specified columns exist in the DataFrame
    if category_column not in df.columns or value_column not in df.columns:
        raise ValueError(f"Columns '{category_column}' or '{value_column}' not found in DataFrame.")
    
    # Check if the value column is numeric
    if pd.api.types.is_numeric_dtype(df[value_column]):
        # If the value column is numeric, sum the values for each category
        pie_data = df.groupby(category_column)[value_column].sum().reset_index()
    else:
        # If the value column is categorical, count the occurrences of each category in the category column
        pie_data = df[category_column].value_counts().reset_index()
        pie_data.columns = [category_column, value_column]  # Rename columns for consistency
    
    # Remove rows where the value is zero to avoid empty slices (only applies to numeric data)
    if pd.api.types.is_numeric_dtype(df[value_column]):
        pie_data = pie_data[pie_data[value_column] > 0]
    
    # Handle case when there's no valid data after filtering
    if pie_data.empty:
        print("No valid data available to plot.")
        return
    
    # Plotting the pie chart
    plt.figure(figsize=(8, 8))  # Set the figure size
    plt.pie(pie_data[value_column], labels=pie_data[category_column], autopct='%1.1f%%', startangle=90)
    plt.title(f'Distribution of {category_column}')
    plt.axis('equal')  # Equal aspect ratio ensures that pie chart is a circle.
    # plt.show()

def generate_single_pie_chart_from_one_column(df, column):
    # Check if the specified column exists in the DataFrame
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    # Determine the data type of the column and handle accordingly
    if pd.api.types.is_string_dtype(df[column]) or pd.api.types.is_categorical_dtype(df[column]):
        # Count occurrences for string/categorical values
        pie_data = df[column].value_counts()
    elif pd.api.types.is_numeric_dtype(df[column]):
        # Sum values for numeric data (aggregating the total for the column)
        dummy_category = 'Total'
        pie_data = pd.Series([df[column].sum()], index=[dummy_category])
    else:
        raise ValueError("Column must contain either string, categorical, or numeric values.")

    # If there's nothing to plot, handle the case
    if pie_data.empty:
        print("No valid data available to plot.")
        return

    # Plotting the pie chart
    plt.figure(figsize=(8, 8))  # Set the figure size
    plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=90)
    plt.title(f'{column}')  # Set the title
    plt.axis('equal')  # Equal aspect ratio ensures that pie chart is a circle.
    # plt.show()

def generate_scatter_plot(df, x_column, y_columns):
    # Check if the specified columns exist in the DataFrame
    if x_column not in df.columns:
        raise ValueError(f"Column '{x_column}' not found in DataFrame.")
    
    # Check if y_columns are valid (either a single column or a list of columns)
    if isinstance(y_columns, str):
        y_columns = [y_columns]  # Convert to list if a single column is passed
    
    for y_column in y_columns:
        if y_column not in df.columns:
            raise ValueError(f"Column '{y_column}' not found in DataFrame.")
    
    # Ensure both x_column and y_columns are numeric
    if not pd.api.types.is_numeric_dtype(df[x_column]):
        raise ValueError(f"Column '{x_column}' must be numeric.")
    
    for y_column in y_columns:
        if not pd.api.types.is_numeric_dtype(df[y_column]):
            raise ValueError(f"Column '{y_column}' must be numeric.")
    
    # Plotting
    plt.figure(figsize=(10, 6))
    for y_column in y_columns:
        plt.scatter(df[x_column], df[y_column], label=y_column)
    
    # Title and labels
    plt.xlabel(x_column)
    plt.ylabel('Values')
    plt.title(f'Relationship between {x_column} and {", ".join(y_columns)}')
    plt.legend(title="Columns")
    plt.grid(True)
    # plt.show()

def generate_histogram(df, columns):
    # Ensure columns is a list
    if isinstance(columns, str):
        columns = [columns]  # Convert to list if a single column is passed

    # Check if columns exist in the DataFrame and if they are numeric
    for column in columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"Column '{column}' must be numeric.")

    # Plotting
    plt.figure(figsize=(10, 6))
    for column in columns:
        # Plot histogram with KDE (default color for KDE)
        sns.histplot(df[column], kde=True, label=column, bins=20)

    # Add title, labels, and legend
    plt.title(f'Histograms for {", ".join(columns)}')
    plt.xlabel('Values')
    plt.ylabel('Frequency')
    plt.legend(title="Columns")
    # plt.show()

def generate_box_plot(df, y_columns):
    # Ensure y_columns is a list
    if isinstance(y_columns, str):
        y_columns = [y_columns]  # Convert to list if a single column is passed

    # Check if columns exist in the DataFrame and if they are numeric
    for column in y_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"Column '{column}' must be numeric.")

    # Plotting the box plot
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df[y_columns])

    # Add title, labels, and customize x-ticks
    plt.title(f'Box Plot for {", ".join(y_columns)}')
    plt.ylabel('Values')
    plt.xticks(range(len(y_columns)), y_columns, rotation=45)
    # plt.show()

def save_chart_to_base64():
    """
    Saves the current matplotlib chart to a Base64-encoded string.
    """
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return "data:image/png;base64," + base64.b64encode(img.getvalue()).decode("utf-8")


@app.route("/", methods=["POST"])
def home():
    global df  # Ensure we're working with the global DataFrame
    chart_url = None
    error_message = None
    column_data = {}
    chart = None
    cols = None

    if request.method == "POST":
        # If the request contains a JSON payload for chart generation
        if request.is_json:
            if df is None:
                return jsonify({"error_message": "No file has been uploaded yet."})
            
            data = request.get_json()  # Parse JSON data
            user_prompt = data.get("user_query", "")

            # Process the query
            chart = find_chart(user_prompt, df)  # Determine chart type
            cols = find_columns(user_prompt, df, chart)  # Get column names

            try:
                if chart == "bar":
                    generate_bar_chart(df, cols)
                    chart_url = save_chart_to_base64()
                elif chart == "line":
                    generate_line_chart(df, cols[0], cols[1])
                    chart_url = save_chart_to_base64()
                elif chart == "pie":
                    if len(cols) == 1:
                        generate_single_pie_chart_from_one_column(df, cols[0])
                    else:
                        generate_single_pie_chart(df, cols[0], cols[1])
                    chart_url = save_chart_to_base64()
                elif chart == "scatter":
                    generate_scatter_plot(df, cols[0], cols[1])
                    chart_url = save_chart_to_base64()
                elif chart == "histogram":
                    generate_histogram(df, cols)
                    chart_url = save_chart_to_base64()
                elif chart == "box":
                    generate_box_plot(df, cols)
                    chart_url = save_chart_to_base64()
                else:
                    error_message = "Chart type not supported."
            except ValueError as e:
                error_message = str(e)

            return jsonify({
                "chart_url": chart_url,
                "error_message": error_message,
                "chart_type": chart,
                "chart_cols": cols
            })

        # Handle file upload via form-data
        elif 'uploaded_file' in request.files:
            file = request.files['uploaded_file']

            # Ensure a file is selected
            if file.filename == '':
                return jsonify({"error_message": "No file selected for upload."})

            # Check if the file is CSV
            if not file.filename.endswith('.csv'):
                return jsonify({"error_message": "Unsupported file type. Please upload a CSV file."})

            try:
                # Load CSV file into DataFrame
                file_stream = io.StringIO(file.stream.read().decode('utf-8'))
                df = pd.read_csv(file_stream)
                df = clean_dataset(df)  # Optional cleaning step
                column_data = infer_column_types(df)
            except Exception as e:
                error_message = str(e)

            return jsonify({
                "error_message": error_message,
                "columns": column_data
            })
        else:
            return jsonify({"error_message": "Invalid request type."})

@app.route("/", methods=["GET"])
def render_home():
    """
    Separate function to handle GET requests and render the index.html template.
    """
    return render_template("index1.html")

if __name__ == "__main__":
    # app.run(debug=True)
    app.run()
