import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="HW1-1: Interactive Linear Regression Visualizer",
    page_icon="📊",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 2rem;
        color: #2e8b57;
        font-weight: bold;
        margin: 1.5rem 0 1rem 0;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .coefficient-text {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

def generate_data_and_model(n_points, coefficient_a, noise_var):
    """Generate synthetic data and fit linear regression model"""
    # Generate synthetic data
    np.random.seed(42)  # For reproducibility
    x = np.random.uniform(0, 10, n_points)
    true_intercept = np.random.uniform(-5, 5)
    noise = np.random.normal(0, np.sqrt(noise_var), n_points)
    y = coefficient_a * x + true_intercept + noise
    
    # Create DataFrame
    data = pd.DataFrame({
        'x': x,
        'y': y,
        'true_y': coefficient_a * x + true_intercept,
        'noise': noise
    })
    
    # Fit linear regression model
    X = data[['x']]
    y_values = data['y']
    
    model = LinearRegression()
    model.fit(X, y_values)
    predictions = model.predict(X)
    
    # Outlier detection using IQR method
    Q1_y = data['y'].quantile(0.25)
    Q3_y = data['y'].quantile(0.75)
    IQR_y = Q3_y - Q1_y
    lower_bound = Q1_y - 1.5 * IQR_y
    upper_bound = Q3_y + 1.5 * IQR_y
    
    outlier_mask = (data['y'] < lower_bound) | (data['y'] > upper_bound)
    outliers = data[outlier_mask].copy()
    outliers['residuals'] = abs(outliers['y'] - (model.coef_[0] * outliers['x'] + model.intercept_))
    
    return data, model, predictions, outliers, true_intercept

def create_visualization(data, model, outliers):
    """Create interactive visualization with Plotly"""
    fig = go.Figure()
    
    # Add data points
    fig.add_trace(go.Scatter(
        x=data['x'],
        y=data['y'],
        mode='markers',
        name='Generated Data',
        marker=dict(color='#0066CC', size=6, opacity=0.8),
        showlegend=True
    ))
    
    # Add regression line
    x_line = np.linspace(data['x'].min(), data['x'].max(), 100)
    y_line = model.coef_[0] * x_line + model.intercept_
    
    fig.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode='lines',
        name='Linear Regression',
        line=dict(color='#CC0000', width=3),
        showlegend=True
    ))
    
    # Add outliers
    if len(outliers) > 0:
        # Add outlier labels with index numbers
        outlier_labels = []
        for idx, row in outliers.iterrows():
            outlier_labels.append(f'Outlier {idx}')
        
        fig.add_trace(go.Scatter(
            x=outliers['x'],
            y=outliers['y'],
            mode='markers+text',
            name='Outliers',
            marker=dict(color='purple', size=10, symbol='diamond'),
            text=outlier_labels,
            textposition='top center',
            textfont=dict(color='purple', size=10),
            showlegend=False
        ))
    
    fig.update_layout(
        title={
            'text': "Linear Regression with Outliers",
            'font': {'size': 20, 'color': '#000000'}
        },
        xaxis_title="X",
        yaxis_title="Y",
        xaxis=dict(
            visible=True,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True
        ),
        yaxis=dict(
            visible=True,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True
        ),
        hovermode='closest',
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.5)",
            borderwidth=2,
            font=dict(size=14, color='#000000')
        ),
        width=800,
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=14, color='#000000')
    )
    
    # Update axis properties separately with explicit settings
    fig.update_xaxes(
        title_font=dict(size=16, color='#000000'),
        tickfont=dict(size=14, color='#000000'),
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=1,
        showticklabels=True,
        tickmode='linear',
        tick0=0,
        dtick=1,
        showline=True,
        linewidth=2,
        linecolor='black',
        ticks='outside',
        tickwidth=2,
        tickcolor='black',
        ticklen=8
    )
    fig.update_yaxes(
        title_font=dict(size=16, color='#000000'),
        tickfont=dict(size=14, color='#000000'),
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=1,
        showticklabels=True,
        tickmode='auto',
        showline=True,
        linewidth=2,
        linecolor='black',
        ticks='outside',
        tickwidth=2,
        tickcolor='black',
        ticklen=8
    )
    
    return fig

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">HW1-1: Interactive Linear Regression Visualizer</div>', unsafe_allow_html=True)
    
    # Sidebar Configuration
    st.sidebar.header("Configuration")
    
    # User inputs
    n_points = st.sidebar.slider(
        "Number of data points (n)",
        min_value=50,
        max_value=1000,
        value=505,
        step=5
    )
    
    coefficient_a = st.sidebar.slider(
        "Coefficient 'a' (y = ax + b + noise)",
        min_value=0.1,
        max_value=10.0,
        value=5.20,
        step=0.1
    )
    
    noise_var = st.sidebar.slider(
        "Noise Variance (var)",
        min_value=1,
        max_value=1000,
        value=510,
        step=10
    )
    
    # Generate data and model
    data, model, predictions, outliers, true_intercept = generate_data_and_model(
        n_points, coefficient_a, noise_var
    )
    
    # Generated Data and Linear Regression section
    st.markdown('<div class="section-header">Generated Data and Linear Regression</div>', 
               unsafe_allow_html=True)
    
    # Create and display visualization
    fig = create_visualization(data, model, outliers)
    st.plotly_chart(fig, use_container_width=True)
    
    # Model Coefficients section
    st.markdown('<div class="section-header">Model Coefficients</div>', 
               unsafe_allow_html=True)
    
    st.markdown('<div class="coefficient-text">', unsafe_allow_html=True)
    st.write(f"**Coefficient (a)**: {model.coef_[0]:.2f}")
    st.write(f"**Intercept (b)**: {model.intercept_:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Top 5 Outliers section
    st.markdown('<div class="section-header">Top 5 Outliers</div>', 
               unsafe_allow_html=True)
    
    if len(outliers) > 0:
        # Sort outliers by residuals and get top 5
        top_outliers = outliers.sort_values('residuals', ascending=False).head(5)
        
        # Create outliers table
        outliers_table = pd.DataFrame({
            'x': top_outliers['x'].round(4),
            'y': top_outliers['y'].round(4),
            'residuals': top_outliers['residuals'].round(4)
        })
        
        # Reset index to show original data point indices
        outliers_table.index = top_outliers.index
        outliers_table.index.name = 'Index'
        
        st.dataframe(outliers_table, use_container_width=True)
    else:
        st.write("No outliers detected")

if __name__ == "__main__":
    main()