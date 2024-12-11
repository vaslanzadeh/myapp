import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
import os

# Specify directory containing CSV files
data_directory = "data/"

# Load all CSV files into a dictionary of DataFrames based on filename
data_files = {
    file: pd.read_csv(os.path.join(data_directory, file))
    for file in os.listdir(data_directory)
    if file.endswith(".csv")
}

# Sequence annotation to display on top of each heatmap

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("Interactive Scatter Plot and Heatmaps of CSV Data"),

    # Dropdowns for selecting file pairs
    html.Label("Select first CSV file:"),
    dcc.Dropdown(id="file1-dropdown", options=[{"label": name, "value": name} for name in data_files.keys()], multi=False),

    html.Label("Select second CSV file:"),
    dcc.Dropdown(id="file2-dropdown", options=[{"label": name, "value": name} for name in data_files.keys()], multi=False),

    # Dropdown to select multiple features for coloring
    html.Label("Select up to 4 columns for conditional coloring:"),
    dcc.Dropdown(
        id="color-dropdown",
        options=[
            {"label": "site_1", "value": "site_1"},
            {"label": "site_2", "value": "site_2"},
            {"label": "ab8307_site", "value": "ab8307_site"},
            {"label": "ab8314_site", "value": "ab8314_site"},
            {"label": "c_c", "value": "c_c"}
        ],
        multi=True,
    ),

    # Scatter plot display
    dcc.Graph(id="scatter-plot"),

    # Heatmaps for each individual file
    html.Div([
        html.Label("Heatmap of first selected CSV file:"),
        dcc.Graph(id="heatmap1"),

        html.Label("Heatmap of second selected CSV file:"),
        dcc.Graph(id="heatmap2")
    ])
])

# Callback to update scatter plot and heatmaps based on file selections and coloring choice
@app.callback(
    [Output("scatter-plot", "figure"),
     Output("heatmap1", "figure"),
     Output("heatmap2", "figure")],
    [Input("file1-dropdown", "value"),
     Input("file2-dropdown", "value"),
     Input("color-dropdown", "value")]
)
def update_plots(file1, file2, color_columns):
    if file1 is None or file2 is None or file1 == file2:
        return {}, {}, {}

    # Load and merge data based on `position`
    df1 = data_files[file1]
    df2 = data_files[file2]
    merged_df = pd.merge(df1, df2, on="position", suffixes=("_1", "_2"))

    # Restrict to the first 4 selected color columns
    if color_columns:
        color_columns = color_columns[:4]

    # Create color categories for each selected column
    color_map = {
        "site_1": "green",
        "site_2": "blue",
        "ab8307_site": "violet",
        "ab8314_site": "darkbrown",
        "c_c": "orange"
    }

    # Initialize a color column as "gray" for default
    merged_df["color"] = "gray"
    if color_columns:
        for col in color_columns:
            color = color_map.get(col, "gray")
            merged_df.loc[merged_df[col + "_1"] == "yes", "color"] = color

    # Generate scatter plot
    scatter_fig = px.scatter(
        merged_df,
        x="median_score_1",
        y="median_score_2",
        color="color",
        hover_data=["position"]
    )

    # Add position annotations for selected color points
    annotations = [
        dict(
            x=row["median_score_1"],
            y=row["median_score_2"],
            text=row["position"],
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-20,
            bgcolor="rgba(255,255,255,0.7)"
        )
        for _, row in merged_df[merged_df["color"] != "gray"].iterrows()
    ]
    scatter_fig.update_layout(annotations=annotations)

    # Set white background, gridlines, axis labels, plot border, and larger tick font size
    scatter_fig.update_layout(
        title=f"Scatter Plot of {file1} vs {file2}",
        xaxis_title=f"<b>Median Score ({file1})</b>",
        yaxis_title=f"<b>Median Score ({file2})</b>",
        xaxis=dict(showgrid=True, gridcolor='lightgray', tickfont=dict(size=14)),  # Increase tick size
        yaxis=dict(showgrid=True, gridcolor='lightgray', tickfont=dict(size=14)),  # Increase tick size
        plot_bgcolor='white',
        clickmode="event+select",
        autosize=False,
        width=700, height=600,  # Make x-axis a bit longer
        margin=dict(l=50, r=50, b=50, t=50),  # Add space for border
        paper_bgcolor="white",
        shapes=[  # Add black border around plot
            dict(
                type="rect",
                xref="paper", yref="paper",
                x0=0, y0=0, x1=1, y1=1,
                line=dict(color="black", width=2)
            ),
            # Add vertical line at x=0
            dict(
                type="line",
                xref="x",
                yref="y",
                x0=0, y0=min(merged_df["median_score_2"]),
                x1=0, y1=max(merged_df["median_score_2"]),
                line=dict(color="black", width=1)
            ),
            # Add horizontal line at y=0
            dict(
                type="line",
                xref="x",
                yref="y",
                x0=min(merged_df["median_score_1"]), y0=0,
                x1=max(merged_df["median_score_1"]), y1=0,
                line=dict(color="black", width=1)
            )
        ]
    )

   

    wt_aa = df1["wt_aa"].values  # Assuming wt_aa is already a column in df2

    # Generate hover text including wt_aa information
 # Generate hover text matrix that matches the shape of z (A-Y columns by positions)
    hover_text = [
        [
            f"Position: {pos}<br>WT aa: {wt}<br>Variant aa: {variant}<br>Variant Score: {score:.4f}<br>Median Score: {median:.4f}"
            for pos, score, wt, median in zip(
                df2["position"],
                row,
                df2["wt_aa"],
                df2["median_score"]
            )
        ]
        for variant, row in zip(df2.loc[:, "A":"Y"].columns, df2.loc[:, "A":"Y"].values.T)
    ]

    # Create heatmap figure
    heatmap_fig1 = go.Figure(data=go.Heatmap(
        z=df1.loc[:, "A":"Y"].values.T,
        x=df1["position"],
        y=df1.loc[:, "A":"Y"].columns,
        colorscale="RdBu_r",
        zmin=-0.8,
        zmax=0.8,
        colorbar=dict(
            title=dict(
                text="variant score (log2)",
                side="right",
                font=dict(size=12)
            ),
            tickvals=[-0.8, 0, 0.8]
        ),
        hoverongaps=False,
        text=hover_text,  # Custom hover text with wt_aa included
        hovertemplate="%{text}"  # Display custom hover text
    ))

    # Update layout settings
    heatmap_fig1.update_layout(
        title=file1,
        xaxis=dict(title="Position", showgrid=False),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(df2.loc[:, "A":"Y"].columns))),
            ticktext=df2.loc[:, "A":"Y"].columns,
            automargin=True,
            fixedrange=True,
            showgrid=False
        ),
        plot_bgcolor="grey",
    )



    
    #wt_aa = df2["wt_aa"].values  # Assuming wt_aa is already a column in df2
    median_score = df2["median_score"].values

    # Generate hover text including wt_aa information
 # Generate hover text matrix that matches the shape of z (A-Y columns by positions)
    hover_text = [
        [
            f"Position: {pos}<br>WT aa: {wt}<br>Variant aa: {variant}<br>Variant Score: {score:.4f}<br>Median Score: {median:.4f}"
            for pos, score, wt, median in zip(
                df2["position"],
                row,
                df2["wt_aa"],
                df2["median_score"]
            )
        ]
        for variant, row in zip(df2.loc[:, "A":"Y"].columns, df2.loc[:, "A":"Y"].values.T)
    ]

    # Create heatmap figure
    heatmap_fig2 = go.Figure(data=go.Heatmap(
        z=df2.loc[:, "A":"Y"].values.T,
        x=df2["position"],
        y=df2.loc[:, "A":"Y"].columns,
        colorscale="RdBu_r",
        zmin=-0.8,
        zmax=0.8,
        colorbar=dict(
            title=dict(
                text="variant score (log2)",
                side="right",
                font=dict(size=12)
            ),
            tickvals=[-0.8, 0, 0.8]
        ),
        hoverongaps=False,
        text=hover_text,  # Custom hover text with wt_aa included
        hovertemplate="%{text}"  # Display custom hover text
    ))

    # Update layout settings
    heatmap_fig2.update_layout(
        title=file2,
        xaxis=dict(title="Position", showgrid=False),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(df2.loc[:, "A":"Y"].columns))),
            ticktext=df2.loc[:, "A":"Y"].columns,
            automargin=True,
            fixedrange=True,
            showgrid=False
        ),
        plot_bgcolor="grey",
    )

    return scatter_fig, heatmap_fig1, heatmap_fig2

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=int(os.getenv("PORT", 8051)), host="0.0.0.0")


