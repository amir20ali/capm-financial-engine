import pandas as pd
import numpy as np
from scipy.optimize import minimize
import plotly.graph_objects as go
import warnings

#warnings.filterwarnings('ignore')

def efficient_frontier(watchout_Assets, risk_return_data, risk_free_stock, cov_matrix, PROCESSED_DIR):
    """
    Calculate the efficient frontier for a portfolio with focus on watchout assets.
    
    The efficient frontier consists of portfolios that:
    - For each level of risk, achieve the maximum expected return
    - For each level of return, achieve the minimum risk
    
    Parameters:
    -----------
    watchout_Assets : list
        List of asset names to focus on and highlight in the plot
    risk_return_data : pd.DataFrame
        DataFrame with risk and return metrics (columns: asset names, rows: metrics)
    cov_matrix : pd.DataFrame
        Covariance matrix of returns (DataFrame with stock names as index/columns)
    
    Returns:
    --------
    tuple : (frontier_returns, frontier_risks, fig)
        Arrays of returns and risks along the efficient frontier, and the interactive plot figure
    """


    risk_free_rate = risk_return_data.loc[risk_free_stock, "Return"]
    
    try:
        
        # Extract expected returns from risk_return_data
        # risk_return_data has assets as index and columns: Return, Risk, Sharpe Ratio, Count
        if 'Return' in risk_return_data.columns:
            expected_returns = risk_return_data['Return']
        else:
            expected_returns = risk_return_data.iloc[:, 0]  # First column as returns
        
        # Convert to numeric
        #expected_returns = pd.to_numeric(expected_returns, errors='coerce')
        
        # Drop NaN values
        #expected_returns = expected_returns.dropna()
        
        # Verify we have enough assets
        if len(expected_returns) < 2:
            raise ValueError(f"❌ Not enough assets found ({len(expected_returns)}). Need at least 2.")
        
        asset_names = expected_returns.index.tolist()
        n_assets = len(expected_returns)
        
        # Convert to numpy array if it's a DataFrame
        if isinstance(cov_matrix, pd.DataFrame):
            
            # Filter to watchout assets only
            available_watchout = [asset for asset in watchout_Assets if asset in cov_matrix.index]
            missing_watchout = [asset for asset in watchout_Assets if asset not in cov_matrix.index]
            
            if missing_watchout:
                print(f"   ⚠️  Assets not found in covariance matrix: {missing_watchout}")
            
            if len(available_watchout) < 2:
                raise ValueError(f"❌ Less than 2 watchout assets found in covariance matrix")
            
            # Extract submatrix for watchout assets
            cov_matrix_filtered = cov_matrix.loc[available_watchout, available_watchout].values
            expected_returns_filtered = expected_returns.loc[available_watchout]
            asset_names_filtered = available_watchout
            
            cov_matrix = cov_matrix_filtered
            expected_returns = expected_returns_filtered
            asset_names = asset_names_filtered
            n_assets = len(asset_names)
        else:
            raise ValueError("❌ Covariance matrix must be a DataFrame for filtering")
        
        # Verify dimensions
        if cov_matrix.shape != (n_assets, n_assets):
            raise ValueError(
                f"❌ Covariance matrix shape {cov_matrix.shape} doesn't match "
                f"expected ({n_assets}, {n_assets}). Check asset alignment."
            )
                
        # Check if matrix is positive definite
        eigenvalues = np.linalg.eigvals(cov_matrix)
        min_eigenvalue = eigenvalues.min()
                
        if min_eigenvalue < 1e-10:
            print(f"   ⚠️  Matrix is not positive definite. Regularizing...")
            # Add small value to diagonal to ensure positive definiteness
            cov_matrix = cov_matrix + np.eye(n_assets) * 1e-6
            print(f"   ✓ Regularization applied")
        
        # Convert expected returns to numpy array
        expected_returns_array = expected_returns.values
        
        # Annualization factor based on observation counts
        if 'Counts' in risk_return_data.columns:
            counts = risk_return_data.loc[asset_names, 'Counts']
            counts = pd.to_numeric(counts, errors='coerce').dropna()
            if len(counts) != n_assets:
                raise ValueError("❌ Counts data must be present for all selected watchout assets.")
            rep = counts.mean()  #what is the correct way? mean or max?
        else:
            rep = 1.0
            print("   ⚠️  Counts column not found in risk_return_data, risk will not be annualized")
        

        def portfolio_metrics(weights, returns, cov_mat, rep):
            """
            Calculate portfolio return and standard deviation
            
            Parameters:
            weights : np.ndarray
                Array of asset weights (should sum to 1)
            mean_returns : np.ndarray
                Array of expected returns for each asset
            cov_mat : np.ndarray
                Covariance matrix of returns
            
            Returns:
            tuple : (portfolio_return, portfolio_std_dev)
            """
            portfolio_return = np.sum(returns * weights)
            portfolio_variance = np.dot(weights.T, np.dot(cov_mat, weights))
            portfolio_std_dev = np.sqrt(max(portfolio_variance, 0))  # Ensure non-negative
            portfolio_std_dev = portfolio_std_dev * (rep ** 0.5)
            return portfolio_return, portfolio_std_dev
        
        def objective_function(weights, mean_returns, cov_mat, target_return):
            """Minimize portfolio risk subject to return constraint"""
            _, portfolio_std = portfolio_metrics(weights, mean_returns, cov_mat, rep)
            return portfolio_std
        
        def constraint_weights_sum_to_one(weights):
            """Constraint: weights must sum to 1 (fully invested)"""
            return np.sum(weights) - 1
        
        # Define bounds: each weight between 0 and 1 (no short selling, no leverage)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Initial guess: equally weighted portfolio
        initial_weights = np.array([1.0 / n_assets] * n_assets)
    
        # Create target return range
        n_points = 50
        min_return = expected_returns_array.min()
        max_return = expected_returns_array.max()
        target_returns = np.linspace(min_return, max_return, num=n_points)
                
        frontier_returns = []
        frontier_risks = []
        frontier_weights_list = []
        successful_optimizations = 0
        failed_optimizations = 0
        
        for target_return in target_returns:
            try:
                # Define constraint for target return
                def target_return_constraint(weights):
                    portfolio_ret, _ = portfolio_metrics(
                        weights, expected_returns_array, cov_matrix, rep
                    )
                    return portfolio_ret - target_return
                
                # Constraints: (1) weights sum to 1, (2) portfolio return equals target
                constraints = [
                    {'type': 'eq', 'fun': constraint_weights_sum_to_one},
                    {'type': 'eq', 'fun': target_return_constraint}
                ]
                
                # Run optimization
                result = minimize(
                    fun=objective_function,
                    x0=initial_weights,
                    args=(expected_returns_array, cov_matrix, target_return),
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints,
                    options={
                        'ftol': 1e-12,
                        'maxiter': 1000,
                        'disp': False,
                        'eps': 1e-8
                    }
                )
                
                # Check if optimization was successful
                if result.success:
                    portfolio_ret, portfolio_risk = portfolio_metrics(
                        result.x, expected_returns_array, cov_matrix, rep
                    )
                    
                    # Verify the solution meets constraints (with tolerance)
                    if abs(portfolio_ret - target_return) < 1e-6 and portfolio_risk >= 0:
                        frontier_returns.append(portfolio_ret)
                        frontier_risks.append(portfolio_risk)
                        frontier_weights_list.append(result.x)
                        successful_optimizations += 1
                else:
                    failed_optimizations += 1
                    
            except Exception as e:
                failed_optimizations += 1
                
        if len(frontier_returns) == 0:
            raise ValueError("❌ Optimization failed for all target returns!")
        
        frontier_returns = np.array(frontier_returns)
        frontier_risks = np.array(frontier_risks)
        
        if failed_optimizations > 0:
            print(f"   ⚠️  {failed_optimizations} optimizations failed (normal at extremes)")
        

        # Create Interactive Plotly Visualization
        
        # Calculate Sharpe ratio for coloring (simplified: return/risk)
        sharpe_proxy = (frontier_returns - risk_free_rate) / (frontier_risks) 
        
        # Create interactive plotly figure
        fig = go.Figure()
        
        # Plot efficient frontier
        fig.add_trace(go.Scatter(
            x=frontier_risks,
            y=frontier_returns,
            mode='markers',
            marker=dict(
                size=8,
                color=sharpe_proxy,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Return/Risk<br>Ratio",
                    thickness=15,
                    len=0.7,
                    x=1.02
                ),
                line=dict(width=0.5, color='black')
            ),
            name='Efficient Frontier',
            hovertemplate='<b>Risk</b>: %{x:.6f}<br><b>Return</b>: %{y:.6f}<extra></extra>'
        ))
        
        # Add watchout assets as separate points
        watchout_risks = []
        watchout_returns = []
        watchout_names = []
        
        for asset in asset_names:
            # Get risk from risk_return_data
            if 'Risk' in risk_return_data.columns:
                asset_risk = risk_return_data.loc[asset, 'Risk']
            else:
                # Fallback: calculate from covariance matrix diagonal
                asset_risk = np.sqrt(cov_matrix[asset_names.index(asset), asset_names.index(asset)])
            
            # Get return from risk_return_data
            asset_return = expected_returns[asset]
            
            watchout_risks.append(asset_risk)
            watchout_returns.append(asset_return)
            watchout_names.append(asset)
        
        # Add watchout assets to plot
        fig.add_trace(go.Scatter(
            x=watchout_risks,
            y=watchout_returns,
            mode='markers+text',
            marker=dict(
                size=12,
                color='red',
                symbol='star',
                line=dict(width=2, color='darkred')
            ),
            text=watchout_names,
            textposition='top center',
            textfont=dict(size=10, color='darkred'),
            name='Watchout Assets',
            hovertemplate='<b>%{text}</b><br><b>Risk</b>: %{x:.6f}<br><b>Return</b>: %{y:.6f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Efficient Frontier - Portfolio Optimization with Watchout Assets',
            xaxis_title='Risk (Standard Deviation)',
            yaxis_title='Expected Return',
            hovermode='closest',
            width=1200,
            height=700,
            template='plotly_white',
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='black',
                borderwidth=1
            )
        )
        
        # Show in browser
        fig.show()

        # Save portfolio weights, return, and risk to Excel
        portfolio_df = pd.DataFrame(frontier_weights_list, columns=asset_names)
        portfolio_df.insert(0, 'Risk', frontier_risks)
        portfolio_df.insert(0, 'Return', frontier_returns)
        portfolio_df.index = [f'Portfolio_{i+1}' for i in range(len(portfolio_df))]

        portfolio_path = PROCESSED_DIR / 'Efficient_Frontier_Portfolios.xlsx'
        portfolio_df.to_excel(portfolio_path, index=True, float_format='%.5f')
        print(f"✅ Efficient Frontier portfolios saved to {portfolio_path}")

        return frontier_returns, frontier_risks, fig
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERROR OCCURRED".center(70))
        print("="*70)
        print(f"\nError Message: {str(e)}\n")
        raise
