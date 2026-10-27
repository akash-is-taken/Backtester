import pandas as pd
import numpy as np

# ---- RSI Function ----
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ---- Strategy Runner ----
def run_strategy(df, strategy="ma", short_window=20, long_window=50, initial_capital=10000):
    df_copy = df.copy()

    if strategy == "ma":
        df_copy["SMA_short"] = df_copy["Price"].rolling(short_window).mean()
        df_copy["SMA_long"] = df_copy["Price"].rolling(long_window).mean()
        df_copy["Signal"] = 0
        df_copy.loc[df_copy.index[long_window:], "Signal"] = np.where(
            df_copy["SMA_short"][long_window:] > df_copy["SMA_long"][long_window:], 1, -1
        )

    elif strategy == "rsi":
        df_copy["RSI"] = calculate_rsi(df_copy["Price"])
        df_copy["Signal"] = 0
        df_copy.loc[df_copy["RSI"] < 30, "Signal"] = 1
        df_copy.loc[df_copy["RSI"] > 70, "Signal"] = -1
        # Hold the last signal until the next one fires
        df_copy["Signal"] = df_copy["Signal"].replace(0, np.nan).ffill().fillna(0)

    # Backtest
    df_copy["Position"] = df_copy["Signal"].shift(1)
    df_copy["Daily_Return"] = df_copy["Price"].pct_change() * df_copy["Position"]
    df_copy["Equity_Curve"] = (1 + df_copy["Daily_Return"]).cumprod() * initial_capital

    total_return = (df_copy["Equity_Curve"].iloc[-1] / initial_capital - 1) * 100
    sharpe_ratio = (df_copy["Daily_Return"].mean() / df_copy["Daily_Return"].std()) * np.sqrt(252)

    return float(total_return), float(sharpe_ratio), df_copy["Equity_Curve"]

# ---- Load CSV ----
def load_prices(file_path):
    df = pd.read_csv(file_path, parse_dates=["Date"], index_col="Date", dayfirst=True)
    return df.sort_index()

# ---- Tkinter UI ----
def main():
    import matplotlib
    matplotlib.use('TkAgg')  # Forces interactive GUI backend
    import matplotlib.pyplot as plt
    from tkinter import Tk, Label, Button, Entry, filedialog, StringVar, IntVar, Checkbutton

    state = {}

    def load_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            state["df"] = load_prices(file_path)
            status_var.set(f"Loaded: {file_path.split('/')[-1]}")

    def run_backtest():
        if "df" not in state:
            status_var.set("Please load a CSV file first")
            return

        strategies_selected = []
        if ma_var.get():
            strategies_selected.append("ma")
        if rsi_var.get():
            strategies_selected.append("rsi")

        if not strategies_selected:
            status_var.set("Select at least one strategy")
            return

        plt.figure(figsize=(10, 6))
        results_text = []

        for strategy in strategies_selected:
            total_return, sharpe_ratio, curve = run_strategy(
                state["df"], strategy,
                short_window=int(short_window_var.get()),
                long_window=int(long_window_var.get()),
            )
            curve.plot(label=f"{strategy.upper()} Strategy")
            results_text.append(f"{strategy.upper()} → Return: {total_return:.2f}%, Sharpe: {sharpe_ratio:.2f}")

        plt.title("Equity Curve Comparison")
        plt.legend()
        plt.show(block=False)

        # Show results
        if len(strategies_selected) == 1:
            total_return_var.set(results_text[0].split("→")[1].split(",")[0].strip())
            sharpe_var.set(results_text[0].split("Sharpe:")[1].strip())
        else:
            total_return_var.set(" | ".join(r.split("→")[1].split(",")[0].strip() for r in results_text))
            sharpe_var.set(" | ".join(r.split("Sharpe:")[1].strip() for r in results_text))

        status_var.set(" | ".join(results_text))

    root = Tk()
    root.title("Backtesting App")

    # Short & Long window entries
    Label(root, text="Short Window:").grid(row=0, column=0)
    short_window_var = StringVar(value="20")
    Entry(root, textvariable=short_window_var).grid(row=0, column=1)

    Label(root, text="Long Window:").grid(row=1, column=0)
    long_window_var = StringVar(value="50")
    Entry(root, textvariable=long_window_var).grid(row=1, column=1)

    # Strategy checkboxes
    Label(root, text="Select Strategies:").grid(row=2, column=0)
    ma_var = IntVar(value=1)
    rsi_var = IntVar(value=0)
    Checkbutton(root, text="MA Crossover", variable=ma_var).grid(row=2, column=1, sticky="w")
    Checkbutton(root, text="RSI", variable=rsi_var).grid(row=3, column=1, sticky="w")

    # Buttons
    Button(root, text="Load CSV", command=load_csv).grid(row=4, column=0, columnspan=2, pady=5)
    Button(root, text="Run Backtest", command=run_backtest).grid(row=5, column=0, columnspan=2, pady=5)

    # Output labels
    Label(root, text="Total Return:").grid(row=6, column=0)
    total_return_var = StringVar(value="N/A")
    Label(root, textvariable=total_return_var).grid(row=6, column=1)

    Label(root, text="Sharpe Ratio:").grid(row=7, column=0)
    sharpe_var = StringVar(value="N/A")
    Label(root, textvariable=sharpe_var).grid(row=7, column=1)

    status_var = StringVar(value="No file loaded")
    Label(root, textvariable=status_var).grid(row=8, column=0, columnspan=2)

    root.mainloop()


if __name__ == "__main__":
    main()
