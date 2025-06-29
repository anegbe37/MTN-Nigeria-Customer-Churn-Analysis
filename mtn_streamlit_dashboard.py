import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import base64
from io import BytesIO
import zipfile

# Import the analysis model
from mtn_churn_model import MTNChurnAnalysis

# Page configuration
st.set_page_config(
    page_title="MTN Customer Churn Analysis Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #FF6B00, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
    }
    
    .warning-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
    }
    
    .info-box {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MTNChurnAnalysis()
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def load_data():
    """Load data from uploaded file"""
    if st.session_state.uploaded_file is not None:
        try:
            # Save uploaded file temporarily
            with open("temp_data.csv", "wb") as f:
                f.write(st.session_state.uploaded_file.getbuffer())
            
            # Load data using the analyzer
            if st.session_state.analyzer.load_data("temp_data.csv"):
                st.session_state.data_loaded = True
                st.session_state.analysis_complete = False
                
                # Clean up temp file
                os.remove("temp_data.csv")
                
                st.success(f"✅ Data loaded successfully! {len(st.session_state.analyzer.df)} records found.")
                return True
            else:
                st.error("❌ Failed to load data. Please check your file format.")
                return False
                
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            return False
    return False

def run_analysis():
    """Run complete analysis"""
    if st.session_state.data_loaded:
        with st.spinner("🔄 Running comprehensive analysis..."):
            if st.session_state.analyzer.run_complete_analysis():
                st.session_state.analysis_complete = True
                st.success("✅ Analysis completed successfully!")
                return True
            else:
                st.error("❌ Analysis failed. Please check your data.")
                return False
    else:
        st.warning("⚠️ Please load data first.")
        return False

def create_download_link(data, filename, file_format="csv"):
    """Create download link for data"""
    if file_format == "csv":
        csv = data.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download {filename}</a>'
    else:
        # For Excel files
        output = BytesIO()
        data.to_excel(output, index=False)
        excel_data = output.getvalue()
        b64 = base64.b64encode(excel_data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Download {filename}</a>'
    
    return href

def format_number(num):
    """Format numbers with commas"""
    if pd.isna(num) or num is None:
        return "N/A"
    try:
        # Handle both integer and float values
        if isinstance(num, (int, float)):
            return f"{num:,.0f}"
        else:
            # Try to convert to float first
            return f"{float(num):,.0f}"
    except (ValueError, TypeError):
        return str(num)

def format_currency(num):
    """Format currency with Naira symbol"""
    if pd.isna(num) or num is None:
        return "N/A"
    try:
        if isinstance(num, (int, float)):
            return f"₦{num:,.2f}"
        else:
            # Try to convert to float first
            return f"₦{float(num):,.2f}"
    except (ValueError, TypeError):
        return str(num)

def format_percentage(num):
    """Format percentage"""
    if pd.isna(num) or num is None:
        return "N/A"
    try:
        if isinstance(num, (int, float)):
            return f"{num:.1f}%"
        else:
            return f"{float(num):.1f}%"
    except (ValueError, TypeError):
        return str(num)

# Sidebar
st.sidebar.title("📱 MTN Churn Analysis")
st.sidebar.markdown("---")

# File upload
st.sidebar.subheader("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Choose your CSV file",
    type=['csv'],
    help="Upload your customer data CSV file",
    key="uploaded_file",
    on_change=load_data
)

# Analysis controls
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Analysis Controls")

if st.sidebar.button("🚀 Run Complete Analysis", disabled=not st.session_state.data_loaded):
    run_analysis()

if st.sidebar.button("📥 Export All Results", disabled=not st.session_state.analysis_complete):
    with st.spinner("Exporting results..."):
        excel_file = st.session_state.analyzer.export_to_excel()
        csv_files = st.session_state.analyzer.export_to_csv()
        
        if excel_file:
            st.sidebar.success(f"✅ Results exported to: {excel_file}")
        if csv_files:
            st.sidebar.success(f"✅ {len(csv_files)} CSV files exported")

# Main content
st.markdown('<h1 class="main-header">MTN Customer Churn Analysis Dashboard</h1>', unsafe_allow_html=True)

# Create tabs
if st.session_state.data_loaded:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏠 Home", "📊 Primary KPIs", "😊 Satisfaction Analysis", 
        "🗺️ Geographic Analysis", "📱 Device Analysis", 
        "👥 Customer Segmentation", "🔮 Predictive Analytics"
    ])
    
    with tab1:
        st.markdown("## 📊 Executive Summary")
        
        if st.session_state.analysis_complete:
            # Display summary report
            summary_report = st.session_state.analyzer.get_summary_report()
            st.markdown(f"```\n{summary_report}\n```")
            
            # Key metrics in cards
            if 'primary_kpis' in st.session_state.analyzer.analysis_results:
                kpis = st.session_state.analyzer.analysis_results['primary_kpis']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Customers</div>
                        <div class="metric-value">{format_number(kpis.get('total_customers', 0))}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    churn_rate = kpis.get('churn_rate', 0)
                    color = "#e74c3c" if churn_rate > 20 else "#f39c12" if churn_rate > 10 else "#27ae60"
                    st.markdown(f"""
                    <div class="metric-card" style="background: {color};">
                        <div class="metric-label">Churn Rate</div>
                        <div class="metric-value">{format_percentage(churn_rate)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Revenue at Risk</div>
                        <div class="metric-value">{format_currency(kpis.get('revenue_at_risk', 0))}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    satisfaction = kpis.get('avg_satisfaction', 0)
                    color = "#e74c3c" if satisfaction < 2.5 else "#f39c12" if satisfaction < 3.5 else "#27ae60"
                    st.markdown(f"""
                    <div class="metric-card" style="background: {color};">
                        <div class="metric-label">Avg Satisfaction</div>
                        <div class="metric-value">{satisfaction:.1f}/5.0</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Additional insights
                st.markdown("### 🎯 Key Insights")
                
                insight_col1, insight_col2 = st.columns(2)
                
                with insight_col1:
                    st.markdown("""
                    <div class="info-box">
                        <h4>📈 Business Impact</h4>
                        <p>Monitor churn trends and revenue protection strategies</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with insight_col2:
                    st.markdown("""
                    <div class="info-box">
                        <h4>🎯 Action Items</h4>
                        <p>Focus on satisfaction improvement and geographic hotspots</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("🔄 Please run the analysis to see the executive summary.")
            if st.button("🚀 Run Analysis Now"):
                run_analysis()
    
    with tab2:
        st.markdown("## 📊 Primary KPIs Dashboard")
        
        if st.session_state.analysis_complete and 'primary_kpis' in st.session_state.analyzer.analysis_results:
            kpis = st.session_state.analyzer.analysis_results['primary_kpis']
            
            # KPI Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Total Customers",
                    value=format_number(kpis.get('total_customers', 0)),
                    delta=f"Active: {format_number(kpis.get('active_customers', 0))}"
                )
            
            with col2:
                churn_rate = kpis.get('churn_rate', 0)
                st.metric(
                    label="Churn Rate",
                    value=f"{churn_rate:.1f}%",
                    delta=f"Churned: {format_number(kpis.get('churned_customers', 0))}"
                )
            
            with col3:
                st.metric(
                    label="Revenue at Risk",
                    value=format_currency(kpis.get('revenue_at_risk', 0)),
                    delta=f"{kpis.get('revenue_risk_percentage', 0):.1f}% of total revenue"
                )
            
            # Churn Rate Gauge Chart
            st.markdown("### 📊 Churn Rate Gauge")
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = churn_rate,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Churn Rate (%)"},
                delta = {'reference': 15, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
                gauge = {
                    'axis': {'range': [None, 50]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 10], 'color': "lightgreen"},
                        {'range': [10, 20], 'color': "yellow"},
                        {'range': [20, 50], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 25
                    }
                }
            ))
            fig_gauge.update_layout(height=400)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Export option
            st.markdown("### 📥 Export KPIs")
            kpis_df = pd.DataFrame([kpis])
            csv = kpis_df.to_csv(index=False)
            st.download_button(
                label="Download KPIs as CSV",
                data=csv,
                file_name=f"primary_kpis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("🔄 Please run the analysis to see Primary KPIs.")
    
    with tab3:
        st.markdown("## 😊 Satisfaction vs Churn Analysis")
        
        if st.session_state.analysis_complete and 'satisfaction_analysis' in st.session_state.analyzer.analysis_results:
            satisfaction_data = st.session_state.analyzer.analysis_results['satisfaction_analysis']
            
            if 'summary' in satisfaction_data:
                summary_df = satisfaction_data['summary']
                
                # Display summary table
                st.markdown("### 📋 Satisfaction Summary")
                st.dataframe(summary_df.style.format({
                    'Total_Customers': '{:,.0f}',
                    'Churned_Customers': '{:,.0f}',
                    'Churn_Rate': '{:.1f}%',
                    'Total_Revenue': '₦{:,.2f}'
                }))
                
                # Satisfaction vs Churn Rate Chart
                st.markdown("### 📊 Satisfaction vs Churn Rate")
                
                fig_satisfaction = px.bar(
                    summary_df.reset_index(),
                    x='Satisfaction_Rate',
                    y='Churn_Rate',
                    title='Churn Rate by Satisfaction Score',
                    labels={'Churn_Rate': 'Churn Rate (%)', 'Satisfaction_Rate': 'Satisfaction Score'},
                    color='Churn_Rate',
                    color_continuous_scale='Reds'
                )
                fig_satisfaction.update_layout(height=500)
                st.plotly_chart(fig_satisfaction, use_container_width=True)
                
                # Customer Distribution by Satisfaction
                st.markdown("### 👥 Customer Distribution by Satisfaction")
                
                fig_dist = px.pie(
                    summary_df.reset_index(),
                    values='Total_Customers',
                    names='Satisfaction_Rate',
                    title='Customer Distribution by Satisfaction Score'
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # Critical insights
                st.markdown("### 🚨 Critical Insights")
                
                low_satisfaction = summary_df[summary_df.index <= 2]
                if len(low_satisfaction) > 0:
                    low_sat_customers = low_satisfaction['Total_Customers'].sum()
                    low_sat_churn_rate = low_satisfaction['Churn_Rate'].mean()
                    
                    st.warning(f"⚠️ **Satisfaction Alert**: {low_sat_customers:,.0f} customers have satisfaction scores ≤ 2 with an average churn rate of {low_sat_churn_rate:.1f}%")
                
                # Export option
                st.markdown("### 📥 Export Satisfaction Analysis")
                csv = summary_df.to_csv()
                st.download_button(
                    label="Download Satisfaction Analysis as CSV",
                    data=csv,
                    file_name=f"satisfaction_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("🔄 Please run the analysis to see Satisfaction Analysis.")
    
    with tab4:
        st.markdown("## 🗺️ Geographic Analysis")
        
        if st.session_state.analysis_complete and 'geographic_analysis' in st.session_state.analyzer.analysis_results:
            geo_data = st.session_state.analyzer.analysis_results['geographic_analysis']
            
            if 'state_summary' in geo_data:
                state_df = geo_data['state_summary']
                
                # Display state summary
                st.markdown("### 📋 State-wise Performance")
                st.dataframe(state_df.style.format({
                    'Total_Customers': '{:,.0f}',
                    'Churned_Customers': '{:,.0f}',
                    'Churn_Rate': '{:.1f}%',
                    'Total_Revenue': '₦{:,.2f}',
                    'Avg_Satisfaction': '{:.1f}'
                }))
                
                # Top 10 states by churn rate
                st.markdown("### 🔥 Top 10 High-Risk States")
                
                top_10_states = state_df.head(10)
                
                fig_states = px.bar(
                    top_10_states.reset_index(),
                    x='State',
                    y='Churn_Rate',
                    title='Top 10 States by Churn Rate',
                    labels={'Churn_Rate': 'Churn Rate (%)', 'State': 'State'},
                    color='Churn_Rate',
                    color_continuous_scale='Reds'
                )
                fig_states.update_layout(height=500, xaxis_tickangle=-45)
                st.plotly_chart(fig_states, use_container_width=True)
                
                # Revenue impact by state
                st.markdown("### 💰 Revenue Impact by State")
                
                fig_revenue = px.scatter(
                    state_df.reset_index(),
                    x='Total_Revenue',
                    y='Churn_Rate',
                    size='Total_Customers',
                    hover_name='State',
                    title='Revenue vs Churn Rate by State',
                    labels={'Total_Revenue': 'Total Revenue (₦)', 'Churn_Rate': 'Churn Rate (%)'}
                )
                st.plotly_chart(fig_revenue, use_container_width=True)
                
                # High-risk states alert
                if 'high_risk_states' in geo_data:
                    high_risk = geo_data['high_risk_states']
                    if len(high_risk) > 0:
                        st.markdown("### 🚨 High-Risk States Alert")
                        st.error(f"⚠️ **{len(high_risk)} states** have churn rates above the national average of {geo_data.get('avg_churn_rate', 0):.1f}%")
                        
                        # Show top 3 high-risk states
                        top_3_risk = high_risk.head(3)
                        for idx, (state, data) in enumerate(top_3_risk.iterrows()):
                            st.warning(f"#{idx+1}. **{state}**: {data['Churn_Rate']:.1f}% churn rate ({data['Total_Customers']:,.0f} customers)")
                
                # Export option
                st.markdown("### 📥 Export Geographic Analysis")
                csv = state_df.to_csv()
                st.download_button(
                    label="Download Geographic Analysis as CSV",
                    data=csv,
                    file_name=f"geographic_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("🔄 Please run the analysis to see Geographic Analysis.")
    
    with tab5:
        st.markdown("## 📱 Device Performance Analysis")
        
        if st.session_state.analysis_complete and 'device_analysis' in st.session_state.analyzer.analysis_results:
            device_df = st.session_state.analyzer.analysis_results['device_analysis']
            
            # Display device summary
            st.markdown("### 📋 Device Performance Summary")
            st.dataframe(device_df.style.format({
                'Total_Customers': '{:,.0f}',
                'Churned_Customers': '{:,.0f}',
                'Churn_Rate': '{:.1f}%',
                'Total_Revenue': '₦{:,.2f}',
                'Avg_Unit_Price': '₦{:,.2f}',
                'Avg_Satisfaction': '{:.1f}'
            }))
            
            # Device churn rate comparison
            st.markdown("### 📊 Churn Rate by Device Type")
            
            fig_device = px.bar(
                device_df.reset_index(),
                x='MTN_Device',
                y='Churn_Rate',
                title='Churn Rate by Device Type',
                labels={'Churn_Rate': 'Churn Rate (%)', 'MTN_Device': 'Device Type'},
                color='Churn_Rate',
                color_continuous_scale='RdYlBu_r'
            )
            fig_device.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig_device, use_container_width=True)
            
            # Device performance donut chart
            st.markdown("### 🍩 Customer Distribution by Device")
            
            fig_donut = px.pie(
                device_df.reset_index(),
                values='Total_Customers',
                names='MTN_Device',
                title='Customer Distribution by Device Type',
                hole=0.4
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
            # Revenue vs Satisfaction scatter
            st.markdown("### 💰 Revenue vs Satisfaction by Device")
            
            fig_scatter = px.scatter(
                device_df.reset_index(),
                x='Avg_Satisfaction',
                y='Total_Revenue',
                size='Total_Customers',
                hover_name='MTN_Device',
                title='Revenue vs Satisfaction by Device Type',
                labels={'Avg_Satisfaction': 'Average Satisfaction', 'Total_Revenue': 'Total Revenue (₦)'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Device insights
            st.markdown("### 🎯 Device Insights")
            
            if len(device_df) > 0:
                worst_device = device_df.index[0]
                worst_rate = device_df.iloc[0]['Churn_Rate']
                best_device = device_df.index[-1]
                best_rate = device_df.iloc[-1]['Churn_Rate']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.error(f"🚨 **Highest Risk**: {worst_device} with {worst_rate:.1f}% churn rate")
                
                with col2:
                    st.success(f"✅ **Best Performer**: {best_device} with {best_rate:.1f}% churn rate")
            
            # Export option
            st.markdown("### 📥 Export Device Analysis")
            csv = device_df.to_csv()
            st.download_button(
                label="Download Device Analysis as CSV",
                data=csv,
                file_name=f"device_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("🔄 Please run the analysis to see Device Analysis.")
    
    with tab6:
        st.markdown("## 👥 Customer Segmentation Analysis")
        
        if st.session_state.analysis_complete and 'segmentation_analysis' in st.session_state.analyzer.analysis_results:
            seg_data = st.session_state.analyzer.analysis_results['segmentation_analysis']
            
            # Age Group Analysis
            if 'age_analysis' in seg_data:
                st.markdown("### 👶 Age Group Analysis")
                age_df = seg_data['age_analysis']
                
                st.dataframe(age_df.style.format({
                    'Total_Customers': '{:,.0f}',
                    'Churned_Customers': '{:,.0f}',
                    'Churn_Rate': '{:.1f}%',
                    'Total_Revenue': '₦{:,.2f}',
                    'Avg_Satisfaction': '{:.1f}'
                }))
                
                # Age group churn visualization
                fig_age = px.bar(
                    age_df.reset_index(),
                    x='Age_Group',
                    y='Churn_Rate',
                    title='Churn Rate by Age Group',
                    labels={'Churn_Rate': 'Churn Rate (%)', 'Age_Group': 'Age Group'},
                    color='Churn_Rate',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_age, use_container_width=True)
                
                # Export age analysis
                csv_age = age_df.to_csv()
                st.download_button(
                    label="Download Age Analysis as CSV",
                    data=csv_age,
                    file_name=f"age_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Tenure Analysis
            if 'tenure_analysis' in seg_data:
                st.markdown("### ⏰ Customer Tenure Analysis")
                tenure_df = seg_data['tenure_analysis']
                
                st.dataframe(tenure_df.style.format({
                    'Total_Customers': '{:,.0f}',
                    'Churned_Customers': '{:,.0f}',
                    'Churn_Rate': '{:.1f}%',
                    'Total_Revenue': '₦{:,.2f}',
                    'Avg_Satisfaction': '{:.1f}'
                }))
                
                # Tenure churn visualization
                fig_tenure = px.line(
                    tenure_df.reset_index(),
                    x='Tenure_Group',
                    y='Churn_Rate',
                    title='Churn Rate by Tenure Group',
                    labels={'Churn_Rate': 'Churn Rate (%)', 'Tenure_Group': 'Tenure Group'},
                    markers=True
                )
                st.plotly_chart(fig_tenure, use_container_width=True)
                
                # Export tenure analysis
                csv_tenure = tenure_df.to_csv()
                st.download_button(
                    label="Download Tenure Analysis as CSV",
                    data=csv_tenure,
                    file_name=f"tenure_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Subscription Plan Analysis
            if 'plan_analysis' in seg_data:
                st.markdown("### 📋 Subscription Plan Analysis")
                plan_df = seg_data['plan_analysis']
                
                st.dataframe(plan_df.style.format({
                    'Total_Customers': '{:,.0f}',
                    'Churned_Customers': '{:,.0f}',
                    'Churn_Rate': '{:.1f}%',
                    'Total_Revenue': '₦{:,.2f}',
                    'Avg_Unit_Price': '₦{:,.2f}',
                    'Avg_Satisfaction': '{:.1f}'
                }))
                
                # Plan performance visualization
                fig_plan = px.scatter(
                    plan_df.reset_index(),
                    x='Avg_Unit_Price',
                    y='Churn_Rate',
                    size='Total_Customers',
                    hover_name='Subscription_Plan',
                    title='Plan Price vs Churn Rate',
                    labels={'Avg_Unit_Price': 'Average Unit Price (₦)', 'Churn_Rate': 'Churn Rate (%)'}
                )
                st.plotly_chart(fig_plan, use_container_width=True)
                
                # Export plan analysis
                csv_plan = plan_df.to_csv()
                st.download_button(
                    label="Download Plan Analysis as CSV",
                    data=csv_plan,
                    file_name=f"plan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("🔄 Please run the analysis to see Customer Segmentation.")
    
    with tab7:
        st.markdown("## 🔮 Predictive Analytics")
        
        if st.session_state.analysis_complete and 'predictive_analytics' in st.session_state.analyzer.analysis_results:
            pred_data = st.session_state.analyzer.analysis_results['predictive_analytics']
            
            # Predictive metrics
            st.markdown("### 📊 Predictive Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="At-Risk Customers",
                    value=format_number(pred_data.get('at_risk_count', 0)),
                    help="Customers with satisfaction ≤ 2"
                )
            
            with col2:
                st.metric(
                    label="At-Risk Revenue",
                    value=format_currency(pred_data.get('at_risk_revenue', 0)),
                    help="Revenue from at-risk customers"
                )
            
            with col3:
                st.metric(
                    label="New Customer Churn Rate",
                    value=format_percentage(pred_data.get('new_customer_churn_rate', 0)),
                    help="Churn rate for customers with < 6 months tenure"
                )
            
            # High-value customers at risk
            st.markdown("### 💎 High-Value Customers at Risk")
            
            hv_count = pred_data.get('high_value_at_risk_count', 0)
            hv_revenue = pred_data.get('high_value_at_risk_revenue', 0)
            
            if hv_count > 0:
                st.error(f"🚨 **Critical Alert**: {hv_count:,} high-value customers are at risk, representing {format_currency(hv_revenue)} in potential revenue loss!")
            else:
                st.success("✅ No high-value customers currently at risk")
            
            # Churn reasons analysis
            if 'churn_reasons' in st.session_state.analyzer.analysis_results:
                st.markdown("### 📋 Top Churn Reasons")
                
                reasons_df = st.session_state.analyzer.analysis_results['churn_reasons']
                
                if len(reasons_df) > 0:
                    # Display top reasons
                    st.dataframe(reasons_df.style.format({
                        'Count': '{:,.0f}',
                        'Percentage': '{:.1f}%'
                    }))
                    
                    # Visualize top reasons
                    fig_reasons = px.bar(
                        reasons_df.head(10),
                        x='Percentage',
                        y='Reason',
                        orientation='h',
                        title='Top 10 Churn Reasons',
                        labels={'Percentage': 'Percentage (%)', 'Reason': 'Churn Reason'}
                    )
                    fig_reasons.update_layout(height=500)
                    st.plotly_chart(fig_reasons, use_container_width=True)
                    
                    # Export churn reasons
                    csv_reasons = reasons_df.to_csv(index=False)
                    st.download_button(
                        label="Download Churn Reasons as CSV",
                        data=csv_reasons,
                        file_name=f"churn_reasons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            # Action recommendations
            st.markdown("### 🎯 Recommended Actions")
            
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                st.markdown("""
                <div class="info-box">
                    <h4>🚨 Immediate Actions</h4>
                    <ul>
                        <li>Contact at-risk customers immediately</li>
                        <li>Implement retention campaigns</li>
                        <li>Review pricing strategies</li>
                        <li>Improve network quality in high-churn areas</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with action_col2:
                st.markdown("""
                <div class="info-box">
                    <h4>📊 Monitoring Focus</h4>
                    <ul>
                        <li>Track satisfaction scores weekly</li>
                        <li>Monitor new customer onboarding</li>
                        <li>Analyze competitive responses</li>
                        <li>Review device performance regularly</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Export predictive analytics
            st.markdown("### 📥 Export Predictive Analytics")
            pred_df = pd.DataFrame([pred_data])
            csv_pred = pred_df.to_csv(index=False)
            st.download_button(
                label="Download Predictive Analytics as CSV",
                data=csv_pred,
                file_name=f"predictive_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("🔄 Please run the analysis to see Predictive Analytics.")

else:
    # Welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>Welcome to MTN Customer Churn Analysis Dashboard</h2>
        <p>Upload your customer data CSV file to get started with comprehensive churn analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Required columns info box
    st.info("""
    📋 **Required Data Columns**
    
    Make sure your CSV file contains the following columns:
    - Customer_ID
    - Full_Name  
    - Date_of_Purchase
    - Age
    - State
    - MTN_Device
    - Gender
    - Satisfaction_Rate
    - Customer_Review
    - Customer_Tenure_in_months
    - Subscription_Plan
    - Unit_Price
    - Number_of_Times_Purchased
    - Total_Revenue
    - Data_Usage
    - Customer_Churn_Status
    - Reasons_for_Churn
    """)
    
    # Instructions
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. **Upload Data**: Use the file uploader in the sidebar to upload your CSV file
    2. **Run Analysis**: Click the "Run Complete Analysis" button after data is loaded
    3. **Explore Results**: Navigate through the different tabs to view insights
    4. **Export Results**: Download your analysis results in CSV or Excel format
    """)
    
    # Sample data format
    st.markdown("### 📊 Sample Data Format")
    sample_data = {
        'Customer_ID': ['C001', 'C002', 'C003'],
        'Full_Name': ['John Doe', 'Jane Smith', 'Mike Johnson'],
        'Age': [25, 30, 35],
        'State': ['Lagos', 'Abuja', 'Kano'],
        'Satisfaction_Rate': [4, 2, 5],
        'Customer_Churn_Status': ['No', 'Yes', 'No']
    }
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df)
    
    # Features highlight
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Analytics Features**
        - Primary KPIs Dashboard
        - Customer Satisfaction Analysis
        - Geographic Performance
        - Device Performance Metrics
        """)
    
    with col2:
        st.markdown("""
        **👥 Segmentation**
        - Age Group Analysis
        - Tenure-based Insights
        - Subscription Plan Performance
        - Customer Lifetime Value
        """)
    
    with col3:
        st.markdown("""
        **🔮 Predictive Insights**
        - At-Risk Customer Identification
        - Revenue Impact Analysis
        - Churn Reason Analysis
        - Actionable Recommendations
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p><strong>MTN Customer Churn Analysis Dashboard</strong> | Built with Streamlit</p>
    <p>📊 Comprehensive Analytics • 🔄 Real-time Processing • 📥 Export Ready</p>
</div>
""", unsafe_allow_html=True)