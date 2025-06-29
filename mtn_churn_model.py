import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class MTNChurnAnalysis:
    def __init__(self, data_path=None):
        """
        Initialize MTN Churn Analysis Model
        
        Args:
            data_path (str): Path to the CSV file containing customer data
        """
        self.data_path = data_path
        self.df = None
        self.analysis_results = {}
        self.export_folder = "analysis_exports"
        self._create_export_folder()
    
    def _create_export_folder(self):
        """Create export folder if it doesn't exist"""
        Path(self.export_folder).mkdir(exist_ok=True)
    
    def load_data(self, data_path=None):
        """
        Load customer data from CSV file
        
        Args:
            data_path (str): Path to CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if data_path:
                self.data_path = data_path
            
            if not self.data_path:
                raise ValueError("No data path provided")
            
            self.df = pd.read_csv(self.data_path)
            
            # Clean and prepare data
            self._prepare_data()
            
            print(f"✅ Data loaded successfully: {len(self.df)} records")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return False
    
    def _prepare_data(self):
        """Clean and prepare data for analysis"""
        # Convert date columns
        if 'Date_of_Purchase' in self.df.columns:
            self.df['Date_of_Purchase'] = pd.to_datetime(self.df['Date_of_Purchase'], errors='coerce')
        
        # Clean numeric columns
        numeric_columns = ['Age', 'Satisfaction_Rate', 'Customer_Tenure_in_months', 
                          'Unit_Price', 'Number_of_Times_Purchased', 'Total_Revenue', 'Data_Usage']
        
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Create churn binary column
        if 'Customer_Churn_Status' in self.df.columns:
            self.df['Churn_Binary'] = self.df['Customer_Churn_Status'].map({
                'Churned': 1, 'Active': 0, 'Yes': 1, 'No': 0, True: 1, False: 0
            }).fillna(0)
    
    def calculate_primary_kpis(self):
        """Calculate primary KPIs for executive dashboard"""
        results = {}
        
        try:
            # Overall Churn Rate
            total_customers = len(self.df)
            churned_customers = self.df['Churn_Binary'].sum()
            churn_rate = (churned_customers / total_customers) * 100
            
            # Revenue at Risk
            revenue_at_risk = self.df[self.df['Churn_Binary'] == 1]['Total_Revenue'].sum()
            total_revenue = self.df['Total_Revenue'].sum()
            revenue_risk_percentage = (revenue_at_risk / total_revenue) * 100
            
            # Average satisfaction score
            avg_satisfaction = self.df['Satisfaction_Rate'].mean()
            
            results = {
                'total_customers': total_customers,
                'churned_customers': int(churned_customers),
                'churn_rate': round(churn_rate, 2),
                'revenue_at_risk': revenue_at_risk,
                'total_revenue': total_revenue,
                'revenue_risk_percentage': round(revenue_risk_percentage, 2),
                'avg_satisfaction': round(avg_satisfaction, 2),
                'active_customers': total_customers - int(churned_customers)
            }
            
            self.analysis_results['primary_kpis'] = results
            print("✅ Primary KPIs calculated")
            
        except Exception as e:
            print(f"❌ Error calculating primary KPIs: {str(e)}")
        
        return results
    
    def satisfaction_churn_analysis(self):
        """Analyze satisfaction vs churn correlation"""
        try:
            satisfaction_analysis = self.df.groupby(['Satisfaction_Rate', 'Churn_Binary']).size().unstack(fill_value=0)
            satisfaction_summary = self.df.groupby('Satisfaction_Rate').agg({
                'Churn_Binary': ['count', 'sum', 'mean'],
                'Total_Revenue': 'sum'
            }).round(2)
            
            # Flatten column names
            satisfaction_summary.columns = ['Total_Customers', 'Churned_Customers', 'Churn_Rate', 'Total_Revenue']
            satisfaction_summary['Churn_Rate'] = satisfaction_summary['Churn_Rate'] * 100
            
            self.analysis_results['satisfaction_analysis'] = {
                'crosstab': satisfaction_analysis,
                'summary': satisfaction_summary
            }
            
            print("✅ Satisfaction-Churn analysis completed")
            return satisfaction_summary
            
        except Exception as e:
            print(f"❌ Error in satisfaction analysis: {str(e)}")
            return pd.DataFrame()
    
    def geographic_analysis(self):
        """Analyze churn by geographic regions (states)"""
        try:
            geo_analysis = self.df.groupby('State').agg({
                'Customer_ID': 'count',
                'Churn_Binary': ['sum', 'mean'],
                'Total_Revenue': 'sum',
                'Satisfaction_Rate': 'mean'
            }).round(2)
            
            # Flatten column names
            geo_analysis.columns = ['Total_Customers', 'Churned_Customers', 'Churn_Rate', 'Total_Revenue', 'Avg_Satisfaction']
            geo_analysis['Churn_Rate'] = geo_analysis['Churn_Rate'] * 100
            geo_analysis = geo_analysis.sort_values('Churn_Rate', ascending=False)
            
            # Identify high-risk states (above average churn rate)
            avg_churn = geo_analysis['Churn_Rate'].mean()
            high_risk_states = geo_analysis[geo_analysis['Churn_Rate'] > avg_churn]
            
            self.analysis_results['geographic_analysis'] = {
                'state_summary': geo_analysis,
                'high_risk_states': high_risk_states,
                'avg_churn_rate': round(avg_churn, 2)
            }
            
            print("✅ Geographic analysis completed")
            return geo_analysis
            
        except Exception as e:
            print(f"❌ Error in geographic analysis: {str(e)}")
            return pd.DataFrame()
    
    def device_performance_analysis(self):
        """Analyze churn by device type"""
        try:
            device_analysis = self.df.groupby('MTN_Device').agg({
                'Customer_ID': 'count',
                'Churn_Binary': ['sum', 'mean'],
                'Total_Revenue': 'sum',
                'Unit_Price': 'mean',
                'Satisfaction_Rate': 'mean'
            }).round(2)
            
            # Flatten column names
            device_analysis.columns = ['Total_Customers', 'Churned_Customers', 'Churn_Rate', 'Total_Revenue', 'Avg_Unit_Price', 'Avg_Satisfaction']
            device_analysis['Churn_Rate'] = device_analysis['Churn_Rate'] * 100
            device_analysis = device_analysis.sort_values('Churn_Rate', ascending=False)
            
            self.analysis_results['device_analysis'] = device_analysis
            
            print("✅ Device performance analysis completed")
            return device_analysis
            
        except Exception as e:
            print(f"❌ Error in device analysis: {str(e)}")
            return pd.DataFrame()
    
    def customer_segmentation_analysis(self):
        """Analyze customer segments by age, tenure, and subscription plan"""
        try:
            # Age group analysis
            self.df['Age_Group'] = pd.cut(self.df['Age'], 
                                        bins=[0, 25, 35, 45, 55, 100], 
                                        labels=['18-25', '26-35', '36-45', '46-55', '55+'])
            
            age_analysis = self.df.groupby('Age_Group').agg({
                'Customer_ID': 'count',
                'Churn_Binary': ['sum', 'mean'],
                'Total_Revenue': 'sum',
                'Satisfaction_Rate': 'mean'
            }).round(2)
            
            age_analysis.columns = ['Total_Customers', 'Churned_Customers', 'Churn_Rate', 'Total_Revenue', 'Avg_Satisfaction']
            age_analysis['Churn_Rate'] = age_analysis['Churn_Rate'] * 100
            
            # Tenure analysis
            self.df['Tenure_Group'] = pd.cut(self.df['Customer_Tenure_in_months'], 
                                           bins=[0, 6, 12, 24, 36, 100], 
                                           labels=['0-6 months', '7-12 months', '13-24 months', '25-36 months', '36+ months'])
            
            tenure_analysis = self.df.groupby('Tenure_Group').agg({
                'Customer_ID': 'count',
                'Churn_Binary': ['sum', 'mean'],
                'Total_Revenue': 'sum',
                'Satisfaction_Rate': 'mean'
            }).round(2)
            
            tenure_analysis.columns = ['Total_Customers', 'Churned_Customers', 'Churn_Rate', 'Total_Revenue', 'Avg_Satisfaction']
            tenure_analysis['Churn_Rate'] = tenure_analysis['Churn_Rate'] * 100
            
            # Subscription plan analysis
            plan_analysis = self.df.groupby('Subscription_Plan').agg({
                'Customer_ID': 'count',
                'Churn_Binary': ['sum', 'mean'],
                'Total_Revenue': 'sum',
                'Unit_Price': 'mean',
                'Satisfaction_Rate': 'mean'
            }).round(2)
            
            plan_analysis.columns = ['Total_Customers', 'Churned_Customers', 'Churn_Rate', 'Total_Revenue', 'Avg_Unit_Price', 'Avg_Satisfaction']
            plan_analysis['Churn_Rate'] = plan_analysis['Churn_Rate'] * 100
            
            self.analysis_results['segmentation_analysis'] = {
                'age_analysis': age_analysis,
                'tenure_analysis': tenure_analysis,
                'plan_analysis': plan_analysis
            }
            
            print("✅ Customer segmentation analysis completed")
            return {
                'age_analysis': age_analysis,
                'tenure_analysis': tenure_analysis,
                'plan_analysis': plan_analysis
            }
            
        except Exception as e:
            print(f"❌ Error in customer segmentation: {str(e)}")
            return {}
    
    def churn_reasons_analysis(self):
        """Analyze reasons for churn"""
        try:
            churned_customers = self.df[self.df['Churn_Binary'] == 1]
            
            if 'Reasons_for_Churn' in churned_customers.columns:
                reason_counts = churned_customers['Reasons_for_Churn'].value_counts()
                reason_percentages = (reason_counts / len(churned_customers) * 100).round(2)
                
                churn_reasons_df = pd.DataFrame({
                    'Reason': reason_counts.index,
                    'Count': reason_counts.values,
                    'Percentage': reason_percentages.values
                })
                
                self.analysis_results['churn_reasons'] = churn_reasons_df
                
                print("✅ Churn reasons analysis completed")
                return churn_reasons_df
            else:
                print("⚠️ Reasons_for_Churn column not found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error in churn reasons analysis: {str(e)}")
            return pd.DataFrame()
    
    def predictive_analytics(self):
        """Calculate predictive metrics and at-risk customers"""
        try:
            # At-risk customers (satisfaction <= 2)
            at_risk_customers = self.df[self.df['Satisfaction_Rate'] <= 2]
            at_risk_count = len(at_risk_customers)
            at_risk_revenue = at_risk_customers['Total_Revenue'].sum()
            
            # New customers (tenure < 6 months)
            new_customers = self.df[self.df['Customer_Tenure_in_months'] < 6]
            new_customer_churn_rate = (new_customers['Churn_Binary'].mean() * 100) if len(new_customers) > 0 else 0
            
            # High-value customers at risk
            revenue_threshold = self.df['Total_Revenue'].quantile(0.75)
            high_value_at_risk = self.df[
                (self.df['Total_Revenue'] >= revenue_threshold) & 
                (self.df['Satisfaction_Rate'] <= 2)
            ]
            
            predictive_results = {
                'at_risk_count': at_risk_count,
                'at_risk_revenue': at_risk_revenue,
                'new_customer_churn_rate': round(new_customer_churn_rate, 2),
                'high_value_at_risk_count': len(high_value_at_risk),
                'high_value_at_risk_revenue': high_value_at_risk['Total_Revenue'].sum()
            }
            
            self.analysis_results['predictive_analytics'] = predictive_results
            
            print("✅ Predictive analytics completed")
            return predictive_results
            
        except Exception as e:
            print(f"❌ Error in predictive analytics: {str(e)}")
            return {}
    
    def run_complete_analysis(self):
        """Run all analysis components"""
        print("🚀 Starting MTN Churn Analysis...")
        
        if self.df is None:
            print("❌ No data loaded. Please load data first.")
            return False
        
        # Run all analysis components
        self.calculate_primary_kpis()
        self.satisfaction_churn_analysis()
        self.geographic_analysis()
        self.device_performance_analysis()
        self.customer_segmentation_analysis()
        self.churn_reasons_analysis()
        self.predictive_analytics()
        
        print("✅ Complete analysis finished!")
        return True
    
    def export_to_csv(self, analysis_name=None):
        """Export analysis results to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_files = []
        
        try:
            if analysis_name and analysis_name in self.analysis_results:
                # Export specific analysis
                data = self.analysis_results[analysis_name]
                filename = f"{self.export_folder}/{analysis_name}_{timestamp}.csv"
                
                if isinstance(data, dict):
                    # Handle complex data structures
                    for key, value in data.items():
                        if isinstance(value, pd.DataFrame):
                            sub_filename = f"{self.export_folder}/{analysis_name}_{key}_{timestamp}.csv"
                            value.to_csv(sub_filename)
                            export_files.append(sub_filename)
                else:
                    data.to_csv(filename)
                    export_files.append(filename)
            else:
                # Export all analysis results
                for name, data in self.analysis_results.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, pd.DataFrame):
                                filename = f"{self.export_folder}/{name}_{key}_{timestamp}.csv"
                                value.to_csv(filename)
                                export_files.append(filename)
                    elif isinstance(data, pd.DataFrame):
                        filename = f"{self.export_folder}/{name}_{timestamp}.csv"
                        data.to_csv(filename)
                        export_files.append(filename)
            
            print(f"✅ Exported {len(export_files)} files to {self.export_folder}/")
            return export_files
            
        except Exception as e:
            print(f"❌ Error exporting to CSV: {str(e)}")
            return []
    
    def export_to_excel(self, filename=None):
        """Export all analysis results to a single Excel file with multiple sheets"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.export_folder}/MTN_Churn_Analysis_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Export primary KPIs
                if 'primary_kpis' in self.analysis_results:
                    kpis_df = pd.DataFrame([self.analysis_results['primary_kpis']])
                    kpis_df.to_excel(writer, sheet_name='Primary_KPIs', index=False)
                
                # Export other analysis results
                for name, data in self.analysis_results.items():
                    if name == 'primary_kpis':
                        continue
                        
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, pd.DataFrame):
                                sheet_name = f"{name}_{key}"[:31]  # Excel sheet name limit
                                value.to_excel(writer, sheet_name=sheet_name)
                    elif isinstance(data, pd.DataFrame):
                        sheet_name = name[:31]
                        data.to_excel(writer, sheet_name=sheet_name)
            
            print(f"✅ Excel file exported: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting to Excel: {str(e)}")
            return None
    
    def get_summary_report(self):
        """Generate executive summary report"""
        if not self.analysis_results:
            return "No analysis results available. Please run analysis first."
        
        summary = []
        summary.append("MTN CUSTOMER CHURN ANALYSIS - EXECUTIVE SUMMARY")
        summary.append("=" * 60)
        
        # Primary KPIs
        if 'primary_kpis' in self.analysis_results:
            kpis = self.analysis_results['primary_kpis']
            summary.append(f"\n📊 KEY METRICS:")
            summary.append(f"• Total Customers: {kpis.get('total_customers', 0):,}")
            summary.append(f"• Churn Rate: {kpis.get('churn_rate', 0)}%")
            summary.append(f"• Revenue at Risk: ₦{kpis.get('revenue_at_risk', 0):,.2f}")
            summary.append(f"• Average Satisfaction: {kpis.get('avg_satisfaction', 0)}/5.0")
        
        # Geographic insights
        if 'geographic_analysis' in self.analysis_results:
            geo_data = self.analysis_results['geographic_analysis']
            summary.append(f"\n🗺️ GEOGRAPHIC INSIGHTS:")
            summary.append(f"• Average State Churn Rate: {geo_data.get('avg_churn_rate', 0)}%")
            if 'high_risk_states' in geo_data:
                high_risk = geo_data['high_risk_states']
                if len(high_risk) > 0:
                    top_risk_state = high_risk.index[0]
                    top_risk_rate = high_risk.iloc[0]['Churn_Rate']
                    summary.append(f"• Highest Risk State: {top_risk_state} ({top_risk_rate}%)")
        
        # Device performance
        if 'device_analysis' in self.analysis_results:
            device_data = self.analysis_results['device_analysis']
            if len(device_data) > 0:
                worst_device = device_data.index[0]
                worst_rate = device_data.iloc[0]['Churn_Rate']
                summary.append(f"\n📱 DEVICE INSIGHTS:")
                summary.append(f"• Highest Risk Device: {worst_device} ({worst_rate}%)")
        
        # Predictive insights
        if 'predictive_analytics' in self.analysis_results:
            pred_data = self.analysis_results['predictive_analytics']
            summary.append(f"\n🔮 PREDICTIVE INSIGHTS:")
            summary.append(f"• At-Risk Customers: {pred_data.get('at_risk_count', 0):,}")
            summary.append(f"• At-Risk Revenue: ₦{pred_data.get('at_risk_revenue', 0):,.2f}")
        
        return "\n".join(summary)


# Usage example and testing
if __name__ == "__main__":
    # Initialize the analysis model
    analyzer = MTNChurnAnalysis()
    
    # Example usage:
    # analyzer.load_data("path/to/your/customer_data.csv")
    # analyzer.run_complete_analysis()
    # analyzer.export_to_excel()
    # print(analyzer.get_summary_report())
    
    print("MTN Churn Analysis Model initialized successfully!")
    print("Usage:")
    print("1. analyzer.load_data('your_data_file.csv')")
    print("2. analyzer.run_complete_analysis()")
    print("3. analyzer.export_to_excel()")
